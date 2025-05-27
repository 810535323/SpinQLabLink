"""
心跳管理模块

负责管理客户端与服务器之间的心跳连接
"""

import time
import threading
from typing import Callable, Optional
from utils import LoggerManager

# 消息类型定义
MSG_HEARTBEAT_REQ = "heartbeat_req"  # 心跳请求
MSG_HEARTBEAT_RES = "heartbeat_res"  # 心跳响应

# 心跳超时时间（秒）
HEARTBEAT_TIMEOUT = 30
# 心跳发送间隔（秒）
HEARTBEAT_INTERVAL = 10

# 创建logger
logger = LoggerManager.get_logger(name='heartbeat')

class HeartbeatManager:
    """心跳管理器"""
    
    def __init__(self, send_message_callback: Callable[[str, dict], None]):
        """
        初始化心跳管理器
        
        Args:
            send_message_callback: 发送消息的回调函数
        """
        self.send_message_callback = send_message_callback
        
        # 心跳相关
        self.heartbeat_timer: Optional[threading.Timer] = None
        self.last_heartbeat_response_time = 0
        self.heartbeat_checking_timer: Optional[threading.Timer] = None
        
        # 状态
        self.is_running = False
        
        # 回调函数
        self.on_timeout_callback: Optional[Callable[[], None]] = None
    
    def set_timeout_callback(self, callback: Callable[[], None]):
        """
        设置心跳超时回调函数
        
        Args:
            callback: 超时时的回调函数
        """
        self.on_timeout_callback = callback
    
    def start(self):
        """开启心跳"""
        if self.is_running:
            logger.warning("心跳已经在运行中")
            return
            
        logger.debug("开启心跳")
        self.is_running = True
        self.last_heartbeat_response_time = time.time()
        
        # 开启心跳发送定时器
        self._send_heartbeat()
        
        # 开启心跳检查定时器
        self._check_heartbeat_timeout()
    
    def stop(self):
        """停止心跳"""
        if not self.is_running:
            return
            
        logger.debug("停止心跳")
        self.is_running = False
        
        # 停止心跳发送定时器
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None
        
        # 停止心跳检查定时器
        if self.heartbeat_checking_timer:
            self.heartbeat_checking_timer.cancel()
            self.heartbeat_checking_timer = None
    
    def on_heartbeat_response(self):
        """处理心跳响应"""
        self.last_heartbeat_response_time = time.time()
        logger.debug("收到心跳响应")
    
    def _send_heartbeat(self):
        """发送心跳"""
        if not self.is_running:
            logger.debug("心跳已停止，不再发送")
            return
            
        try:
            self.send_message_callback(MSG_HEARTBEAT_REQ, {})
            logger.debug("发送心跳请求")
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")
        
        # 设置下一次心跳发送
        if self.is_running:
            self.heartbeat_timer = threading.Timer(HEARTBEAT_INTERVAL, self._send_heartbeat)
            self.heartbeat_timer.daemon = True
            self.heartbeat_timer.start()
    
    def _check_heartbeat_timeout(self):
        """检查心跳超时"""
        if not self.is_running:
            logger.debug("心跳已停止，不再检查超时")
            return
            
        current_time = time.time()
        elapsed_time = current_time - self.last_heartbeat_response_time
        
        if elapsed_time > HEARTBEAT_TIMEOUT:
            logger.error(f"心跳超时（{elapsed_time:.1f}秒），判断为断开连接")
            self.is_running = False
            
            # 调用超时回调
            if self.on_timeout_callback:
                try:
                    self.on_timeout_callback()
                except Exception as e:
                    logger.error(f"心跳超时回调执行失败: {e}")
        else:
            # 继续检查
            if self.is_running:
                self.heartbeat_checking_timer = threading.Timer(5, self._check_heartbeat_timeout)
                self.heartbeat_checking_timer.daemon = True
                self.heartbeat_checking_timer.start()
    
    def get_status(self) -> dict:
        """
        获取心跳状态
        
        Returns:
            dict: 心跳状态信息
        """
        current_time = time.time()
        elapsed_time = current_time - self.last_heartbeat_response_time if self.last_heartbeat_response_time > 0 else 0
        
        return {
            "is_running": self.is_running,
            "last_response_time": self.last_heartbeat_response_time,
            "elapsed_time": elapsed_time,
            "timeout_threshold": HEARTBEAT_TIMEOUT,
            "send_interval": HEARTBEAT_INTERVAL
        } 