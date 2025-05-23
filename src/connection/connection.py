"""
TCP连接底层实现

提供线程化的队列缓冲收发功能
"""

import socket
import time
import json
import logging
import threading
import queue
from typing import Dict, Any, Optional, Callable, Tuple, Union, List

from ..utils import LoggerManager
from ..utils.exceptions import ConnectionError
from .protocol import protocol, MessageType, CommandType


# 创建logger
logger = LoggerManager.get_logger(name='connection')


class TCPConnection:
    """TCP连接类，用于与远程设备通信"""
    
    def __init__(self, host: str, port: int, timeout: float = 10.0, 
                 heartbeat_interval: float = 30.0):
        """
        初始化TCP连接
        
        Args:
            host: 服务器主机名或IP
            port: 服务器端口
            timeout: 连接超时时间（秒）
            heartbeat_interval: 心跳间隔（秒）
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.heartbeat_interval = heartbeat_interval
        
        # 连接状态
        self.socket = None
        self.connected = False
        self.buffer_size = 4096
        
        # 线程控制
        self._lock = threading.Lock()
        self._running = False
        self._send_thread = None
        self._recv_thread = None
        self._heartbeat_thread = None
        
        # 消息队列
        self._send_queue = queue.Queue()
        self._recv_queue = queue.Queue()
        
        # 回调和等待响应
        self._response_handlers = {}
        self._waiting_responses = {}
        self._message_callback = None
    
    def connect(self) -> bool:
        """
        连接服务器
        
        Returns:
            bool: 是否连接成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # 启动收发线程
            self._running = True
            self._start_threads()
            
            logger.info(f"连接成功: {self.host}:{self.port}")
            return True
            
        except socket.error as e:
            self.connected = False
            logger.error(f"连接失败: {str(e)}")
            raise ConnectionError(f"无法连接到 {self.host}:{self.port} - {str(e)}")
    
    def disconnect(self) -> None:
        """断开连接"""
        # 停止所有线程
        self._running = False
        
        # 等待线程结束
        self._wait_threads_end()
        
        # 关闭连接
        if self.socket:
            try:
                self.socket.close()
            except socket.error as e:
                logger.error(f"断开连接异常: {str(e)}")
            finally:
                self.socket = None
                self.connected = False
                logger.info("已断开连接")
        
        # 清空队列
        self._clear_queues()
    
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
        
        # 心跳线程
        if self.heartbeat_interval > 0:
            self._heartbeat_thread = threading.Thread(
                target=self._heartbeat_worker,
                name="HeartbeatWorker"
            )
            self._heartbeat_thread.daemon = True
            self._heartbeat_thread.start()
            
        logger.debug("所有工作线程已启动")
    
    def _wait_threads_end(self) -> None:
        """等待线程结束"""
        threads = []
        if self._send_thread and self._send_thread.is_alive():
            threads.append(self._send_thread)
        if self._recv_thread and self._recv_thread.is_alive():
            threads.append(self._recv_thread)
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            threads.append(self._heartbeat_thread)
            
        # 等待线程结束，最多等待5秒
        for thread in threads:
            thread.join(timeout=5.0)
            
        # 重置线程变量
        self._send_thread = None
        self._recv_thread = None
        self._heartbeat_thread = None
    
    def _clear_queues(self) -> None:
        """清空消息队列"""
        try:
            while not self._send_queue.empty():
                self._send_queue.get_nowait()
                self._send_queue.task_done()
                
            while not self._recv_queue.empty():
                self._recv_queue.get_nowait()
                self._recv_queue.task_done()
        except Exception as e:
            logger.error(f"清空队列异常: {e}")
    
    def _send_worker(self) -> None:
        """发送线程工作函数"""
        logger.debug("发送线程已启动")
        
        while self._running and self.connected:
            try:
                # 从队列获取待发送的数据，如果队列为空最多等待1秒
                try:
                    data = self._send_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # 发送数据
                if self.socket and self.connected:
                    with self._lock:
                        self.socket.sendall(data)
                    logger.debug(f"已发送数据: {len(data)}字节")
                else:
                    logger.warning("发送失败: 未连接")
                    
                # 标记任务完成
                self._send_queue.task_done()
                
            except socket.error as e:
                logger.error(f"发送错误: {e}")
                self.connected = False
                self._running = False
                break
            except Exception as e:
                logger.error(f"发送线程异常: {e}")
        
        logger.debug("发送线程已结束")
    
    def _recv_worker(self) -> None:
        """接收线程工作函数"""
        logger.debug("接收线程已启动")
        
        while self._running and self.connected:
            try:
                # 接收数据
                if self.socket and self.connected:
                    # 设置非阻塞接收
                    self.socket.settimeout(1.0)
                    
                    try:
                        with self._lock:
                            data = self.socket.recv(self.buffer_size)
                            
                        if not data:
                            logger.warning("接收到空数据，可能连接已断开")
                            time.sleep(0.1)
                            continue
                            
                        # 解析接收到的数据
                        success, message = protocol.unpack_message(data)
                        
                        if success:
                            # 处理消息
                            self._handle_received_message(message)
                        else:
                            logger.warning(f"消息解析失败: {message.get('error', '未知错误')}")
                            
                    except socket.timeout:
                        # 超时，继续循环
                        continue
                    except socket.error as e:
                        logger.error(f"接收错误: {e}")
                        self.connected = False
                        self._running = False
                        break
                else:
                    # 未连接，等待
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"接收线程异常: {e}")
                time.sleep(0.1)
        
        logger.debug("接收线程已结束")
    
    def _heartbeat_worker(self) -> None:
        """心跳线程工作函数"""
        logger.debug("心跳线程已启动")
        
        last_heartbeat_time = time.time()
        
        while self._running and self.connected:
            try:
                current_time = time.time()
                
                # 检查是否需要发送心跳
                if current_time - last_heartbeat_time >= self.heartbeat_interval:
                    # 发送心跳
                    heartbeat_message = protocol.create_heartbeat()
                    self._send_queue.put(heartbeat_message)
                    
                    # 更新时间
                    last_heartbeat_time = current_time
                    logger.debug("已发送心跳")
                
                # 等待一段时间
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"心跳线程异常: {e}")
                time.sleep(1.0)
        
        logger.debug("心跳线程已结束")
    
    def _handle_received_message(self, message: Dict[str, Any]) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 解析后的消息
        """
        message_id = message.get("id")
        message_type = message.get("type")
        command = message.get("command")
        
        logger.debug(f"处理消息: {command}, ID: {message_id}, 类型: {message_type}")
        
        # 对于响应消息，检查是否有等待的处理器
        if message_type in [MessageType.RESPONSE, MessageType.ERROR]:
            if message_id in self._waiting_responses:
                # 获取响应事件和回调
                response_event, callback = self._waiting_responses.pop(message_id)
                
                # 如果有回调则执行
                if callback:
                    try:
                        callback(message)
                    except Exception as e:
                        logger.error(f"响应回调执行错误: {e}")
                
                # 设置事件，通知等待线程
                response_event.set()
                
                logger.debug(f"已处理响应: {message_id}")
                return
        
        # 对于心跳消息直接回复
        if message_type == MessageType.HEARTBEAT and command == CommandType.PING:
            # 创建心跳响应
            response = protocol.create_response(
                message_id, CommandType.PING, {"status": "alive"}
            )
            # 放入发送队列
            self._send_queue.put(response)
            logger.debug(f"已响应心跳: {message_id}")
            return
            
        # 将消息放入接收队列
        self._recv_queue.put(message)
        
        # 如果有消息回调则执行
        if self._message_callback:
            try:
                self._message_callback(message)
            except Exception as e:
                logger.error(f"消息回调执行错误: {e}")
    
    def send(self, data: bytes) -> None:
        """
        发送原始数据
        
        Args:
            data: 待发送的数据
        
        Raises:
            ConnectionError: 连接错误
        """
        if not self.connected:
            raise ConnectionError("未连接，无法发送数据")
        
        # 放入发送队列
        self._send_queue.put(data)
        logger.debug(f"数据已加入发送队列: {len(data)}字节")
    
    def send_message(self, command: str, data: Dict[str, Any], 
                   wait_response: bool = True, timeout: float = None) -> Dict[str, Any]:
        """
        发送消息并等待响应
        
        Args:
            command: 命令类型
            data: 消息数据
            wait_response: 是否等待响应
            timeout: 等待超时时间（秒）
            
        Returns:
            Dict[str, Any]: 响应消息
            
        Raises:
            ConnectionError: 连接错误
            TimeoutError: 等待响应超时
        """
        if not self.connected:
            raise ConnectionError("未连接，无法发送消息")
            
        # 打包消息
        message_bytes = protocol.create_request(command, data)
        
        # 解析出消息ID
        _, message = protocol.unpack_message(message_bytes)
        message_id = message.get("id")
        
        if wait_response:
            # 创建响应事件
            response_event = threading.Event()
            response_data = [None]  # 使用列表存储响应，以便在回调中修改
            
            # 定义响应回调
            def response_callback(response):
                response_data[0] = response
            
            # 注册等待响应
            self._waiting_responses[message_id] = (response_event, response_callback)
            
            try:
                # 发送消息
                self.send(message_bytes)
                
                # 等待响应
                if not response_event.wait(timeout=timeout or self.timeout):
                    # 超时，移除等待
                    self._waiting_responses.pop(message_id, None)
                    raise TimeoutError(f"等待响应超时: {command}")
                
                # 返回响应数据
                return response_data[0]
                
            except Exception as e:
                # 确保移除等待
                self._waiting_responses.pop(message_id, None)
                raise e
        else:
            # 不等待响应，直接发送
            self.send(message_bytes)
            return None
    
    def set_message_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        设置消息回调函数
        
        Args:
            callback: 回调函数，接收解析后的消息
        """
        self._message_callback = callback
        logger.debug("已设置消息回调")
    
    def wait_for_message(self, timeout: float = None) -> Optional[Dict[str, Any]]:
        """
        等待接收队列中的消息
        
        Args:
            timeout: 等待超时时间（秒）
            
        Returns:
            Optional[Dict[str, Any]]: 接收到的消息，如果超时则返回None
        """
        try:
            return self._recv_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def wait_for_specific_message(self, command: str, timeout: float = None) -> Optional[Dict[str, Any]]:
        """
        等待特定类型的消息
        
        Args:
            command: 要等待的命令类型
            timeout: 等待超时时间（秒）
            
        Returns:
            Optional[Dict[str, Any]]: 接收到的消息，如果超时则返回None
        """
        end_time = time.time() + (timeout or self.timeout)
        
        while time.time() < end_time:
            # 计算剩余等待时间
            remaining = max(0.1, end_time - time.time())
            
            # 等待消息
            message = self.wait_for_message(timeout=remaining)
            
            if message:
                if message.get("command") == command:
                    return message
                else:
                    # 不是我们等待的消息，放回队列
                    self._recv_queue.put(message)
            
            # 检查连接状态
            if not self.connected or not self._running:
                return None
        
        # 超时
        return None
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        
        Returns:
            bool: 是否已连接
        """
        return self.connected