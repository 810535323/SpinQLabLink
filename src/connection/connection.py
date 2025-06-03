"""
TCP连接底层实现

提供线程化的队列缓冲收发功能
"""

import socket
import time
import threading
import queue
from typing import Dict, Any, Callable

# 自定义超时异常
class TimeoutError(Exception):
    """连接超时异常"""
    pass

from utils import LoggerManager

# 创建logger
logger = LoggerManager.get_logger(name='connection')

class TCPConnection:
    """TCP连接类，用于与远程设备通信"""
    
    def __init__(self, host: str, port: int, timeout: float = 10.0):
        """
        初始化TCP连接
        
        Args:
            host: 服务器主机名或IP
            port: 服务器端口
            timeout: 连接超时时间（秒）
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        # 连接状态
        self.socket = None
        self.connected = False
        self.buffer_size = 32768
        
        # 线程控制
        self._lock = threading.Lock()
        self._running = False
        self._send_thread = None
        self._recv_thread = None
        
        # 消息队列
        self._send_queue = queue.Queue()
        
        # 回调和等待响应
        self._waiting_responses = {}
        self._message_callback = None
    
    def connect(self) -> bool:
        """
        连接到服务器
        
        Returns:
            bool: 连接是否成功
        """
        if self.connected:
            return True
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            # 设置非阻塞模式
            self.socket.setblocking(0)
            
            # 启动接收线程
            self._running = True
            self.connected = True
            self._recv_thread = threading.Thread(target=self._recv_worker, daemon=True)
            self._recv_thread.start()
            
            # 启动发送线程
            self._send_thread = threading.Thread(target=self._send_worker, daemon=True)
            self._send_thread.start()
            
            logger.info(f"Connected successfully: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        断开连接
        
        Returns:
            bool: 是否成功断开连接
        """
        if not self.connected:
            return True
            
        try:
            self._running = False
            
            # 等待线程结束
            if self._recv_thread and self._recv_thread.is_alive():
                self._recv_thread.join(1.0)  # 最多等待1秒
            
            if self._send_thread and self._send_thread.is_alive():
                self._send_thread.join(1.0)  # 最多等待1秒
                
            # 关闭socket
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except Exception as e:
                logger.error(f"Disconnect exception: {str(e)}")
            
            self.connected = False
            logger.warn("Connection disconnected")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {str(e)}")
            return False
    
    def _start_threads(self) -> None:
        """启动工作线程"""
        # 发送线程
        self._send_thread = threading.Thread(
            target=self._send_worker,
            name="SendWorker"
        )
        self._send_thread.daemon = True
        self._send_thread.start()
        
        # 接收线程
        self._recv_thread = threading.Thread(
            target=self._recv_worker,
            name="RecvWorker"
        )
        self._recv_thread.daemon = True
        self._recv_thread.start()
    
    def _wait_threads_end(self) -> None:
        """等待线程结束"""
        threads = []
        if self._send_thread and self._send_thread.is_alive():
            threads.append(self._send_thread)
        if self._recv_thread and self._recv_thread.is_alive():
            threads.append(self._recv_thread)
            
        # 等待线程结束，最多等待5秒
        for thread in threads:
            thread.join(timeout=5.0)
            
        # 重置线程变量
        self._send_thread = None
        self._recv_thread = None
    
    def _clear_queues(self) -> None:
        """清空所有队列"""
        try:
            while not self._send_queue.empty():
                self._send_queue.get()
            
            while not self._recv_queue.empty():
                self._recv_queue.get()
        except Exception as e:
            logger.error(f"Queue clearing exception: {e}")
    
    def _send_worker(self) -> None:
        """发送线程工作函数"""
        
        while self._running and self.connected:
            try:
                # 从队列获取待发送的数据，如果队列为空最多等待1秒
                try:
                    data = self._send_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # 发送数据
                if self.socket and self.connected:
                    with self._lock:
                        self.socket.sendall(data)
                else:
                    logger.warning("Send failed: Not connected")
                    
                # 标记任务完成
                self._send_queue.task_done()
                
            except socket.error as e:
                logger.error(f"Send error: {e}")
                self.connected = False
                self._running = False
                break
            except Exception as e:
                logger.error(f"Send thread exception: {e}")
        
    
    def _recv_worker(self) -> None:
        """接收线程工作函数"""
        
        # 用于存储未完整处理的数据
        buffer = b''
        
        while self._running and self.connected:
            try:
                # 接收数据
                if self.socket and self.connected:
                    # 设置非阻塞接收
                    self.socket.settimeout(0.5)
                    
                    try:
                        with self._lock:
                            data = self.socket.recv(self.buffer_size)
                            
                        if not data:
                            time.sleep(0.1)
                            continue
                        
                        # 将新接收的数据添加到缓冲区
                        buffer += data

                        # 尝试从缓冲区解析完整消息
                        while buffer:
                            self._handle_received_message(buffer)
                            buffer = b''
                            
                    except socket.timeout:
                        # 超时，继续循环
                        continue
                    except socket.error as e:
                        logger.error(f"Receive error: {e}")
                        self.connected = False
                        self._running = False
                        break
                else:
                    # 未连接，等待
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Receive thread exception: {e}")
                time.sleep(0.1)
    
    def _handle_received_message(self, data: bytes) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 解析后的 BaseMessage 对象
        """
        if self._message_callback:
            try:
                self._message_callback(data)
            except Exception as e:
                logger.error(f"Message callback execution error: {e}")
    
    def send(self, data: bytes) -> bool:
        """
        发送数据
        
        Args:
            data: 要发送的数据
            
        Returns:
            bool: 是否成功发送
        """
        if not self.connected:
            logger.warning("Send failed: Not connected")
            return False
            
        try:
            with self._lock:
                self._send_queue.put(data)
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            return False
    
    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        设置消息回调函数
        
        Args:
            callback: 回调函数，接收解析后的消息
        """
        self._message_callback = callback
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            bool: 是否已连接
        """
        return self.connected