"""
通信协议模块

负责实验协议数据的打包和解析
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, Tuple, Union

from ..utils import LoggerManager


# 创建logger
logger = LoggerManager.get_logger(name='protocol')


class MessageType:
    """消息类型定义"""
    REQUEST = "request"            # 请求消息
    RESPONSE = "response"          # 响应消息
    ERROR = "error"                # 错误消息
    NOTIFICATION = "notification"  # 通知消息
    HEARTBEAT = "heartbeat"        # 心跳消息


class CommandType:
    """命令类型定义"""
    # 实验控制命令
    START_EXPERIMENT = "start_experiment"    # 启动实验
    UPLOAD_DATA = "upload_data"              # 上传数据
    FINISH_EXPERIMENT = "finish_experiment"  # 结束实验
    GET_RESULT = "get_result"                # 获取结果
    GET_STATUS = "get_status"                # 获取状态
    LIST_EXPERIMENTS = "list_experiments"    # 获取实验列表
    
    # 系统命令
    PING = "ping"                # 心跳检测
    AUTH = "auth"                # 身份认证
    DISCONNECT = "disconnect"    # 断开连接


class Protocol:
    """实验通信协议类"""
    
    # 协议版本
    VERSION = "1.0"
    
    # 编码格式
    ENCODING = "utf-8"
    
    def __init__(self):
        """初始化协议处理器"""
        self.message_handlers = {}
    
    def register_handler(self, command_type: str, handler_func):
        """
        注册消息处理器
        
        Args:
            command_type: 命令类型
            handler_func: 处理函数
        """
        self.message_handlers[command_type] = handler_func
        logger.debug(f"注册处理器: {command_type}")
    
    def pack_message(self, command: str, message_type: str = MessageType.REQUEST,
                    data: Optional[Dict[str, Any]] = None,
                    message_id: Optional[str] = None) -> bytes:
        """
        打包消息
        
        Args:
            command: 命令类型
            message_type: 消息类型
            data: 消息数据
            message_id: 消息ID，如果为None则自动生成
            
        Returns:
            bytes: 打包后的消息字节
        """
        if message_id is None:
            message_id = str(uuid.uuid4())
            
        if data is None:
            data = {}
            
        message = {
            "version": self.VERSION,
            "id": message_id,
            "type": message_type,
            "command": command,
            "timestamp": time.time(),
            "data": data
        }
        
        try:
            packed_message = json.dumps(message).encode(self.ENCODING)
            logger.debug(f"消息打包: {command}, ID: {message_id}, 大小: {len(packed_message)}字节")
            return packed_message
        except Exception as e:
            logger.error(f"消息打包错误: {e}")
            # 返回一个错误消息
            error_message = {
                "version": self.VERSION,
                "id": message_id,
                "type": MessageType.ERROR,
                "command": command,
                "timestamp": time.time(),
                "data": {"error": f"消息打包错误: {str(e)}"}
            }
            return json.dumps(error_message).encode(self.ENCODING)
    
    def unpack_message(self, message_bytes: bytes) -> Tuple[bool, Dict[str, Any]]:
        """
        解析消息
        
        Args:
            message_bytes: 消息字节
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (是否成功, 解析后的消息)
        """
        try:
            message = json.loads(message_bytes.decode(self.ENCODING))
            
            # 验证消息格式
            required_fields = ["version", "id", "type", "command", "timestamp", "data"]
            if not all(field in message for field in required_fields):
                missing_fields = [field for field in required_fields if field not in message]
                logger.error(f"消息格式错误，缺少字段: {missing_fields}")
                return False, {"error": f"消息格式错误，缺少字段: {missing_fields}"}
            
            logger.debug(f"消息解析: {message['command']}, ID: {message['id']}")
            return True, message
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            return False, {"error": f"JSON解析错误: {str(e)}"}
        except UnicodeDecodeError as e:
            logger.error(f"编码解析错误: {e}")
            return False, {"error": f"编码解析错误: {str(e)}"}
        except Exception as e:
            logger.error(f"消息解析错误: {e}")
            return False, {"error": f"消息解析错误: {str(e)}"}
    
    def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理消息
        
        Args:
            message: 解析后的消息
            
        Returns:
            Optional[Dict[str, Any]]: 处理结果
        """
        command = message.get("command")
        
        if command in self.message_handlers:
            try:
                handler = self.message_handlers[command]
                result = handler(message)
                return result
            except Exception as e:
                logger.error(f"处理消息错误: {command}, {e}")
                return {
                    "id": message.get("id"),
                    "type": MessageType.ERROR,
                    "command": command,
                    "data": {"error": f"处理消息错误: {str(e)}"}
                }
        else:
            logger.warning(f"未注册的命令: {command}")
            return {
                "id": message.get("id"),
                "type": MessageType.ERROR,
                "command": command,
                "data": {"error": f"未知命令: {command}"}
            }
    
    def create_request(self, command: str, data: Dict[str, Any]) -> bytes:
        """
        创建请求消息
        
        Args:
            command: 命令类型
            data: 请求数据
            
        Returns:
            bytes: 打包后的请求消息
        """
        return self.pack_message(command, MessageType.REQUEST, data)
    
    def create_response(self, request_id: str, command: str, data: Dict[str, Any]) -> bytes:
        """
        创建响应消息
        
        Args:
            request_id: 对应请求的ID
            command: 命令类型
            data: 响应数据
            
        Returns:
            bytes: 打包后的响应消息
        """
        return self.pack_message(command, MessageType.RESPONSE, data, request_id)
    
    def create_error(self, request_id: str, command: str, error_message: str) -> bytes:
        """
        创建错误消息
        
        Args:
            request_id: 对应请求的ID
            command: 命令类型
            error_message: 错误消息
            
        Returns:
            bytes: 打包后的错误消息
        """
        return self.pack_message(command, MessageType.ERROR, {"error": error_message}, request_id)
    
    def create_heartbeat(self) -> bytes:
        """
        创建心跳消息
        
        Returns:
            bytes: 打包后的心跳消息
        """
        return self.pack_message(CommandType.PING, MessageType.HEARTBEAT, {"status": "alive"})


# 创建协议实例
protocol = Protocol()
