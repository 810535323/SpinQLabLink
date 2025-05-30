"""
通信协议模块

负责实验协议数据的打包和解析
"""

import json
from typing import Dict, Any, Tuple
import struct

from utils import LoggerManager
from . import message_pb2

# 创建logger
logger = LoggerManager.get_logger(name='protocol')

class Protocol:
    """通信协议类，负责数据的打包和解包"""
    def __init__(self):
        self.remaining_data = b''
        self.next_data = b''
        # 包头标识
        self.HEADER_MAGIC = 0xCAFEBABE
    
    def serialize_message(self, msg_id: str, metadata: Dict[str, Any], json_data: Dict[str, Any]) -> bytes:
        """
        将protobuf消息打包成二进制数据
        
        Args:
            dict_data: 要发送的JSON数据
            
        Returns:
            打包后的二进制数据
        """
        try:
            # 序列化protobuf消息
            message_data = message_pb2.BaseMessage()
            message_data.msg_id = msg_id
            message_data.metadata.sequence_id = metadata.get("sequence_id")
            message_data.metadata.timestamp = metadata.get("timestamp")
            message_data.metadata.account = metadata.get("account")
            message_data.metadata.session_id = metadata.get("session_id")
            message_data.json_data = json.dumps(json_data)
            
            # 计算数据长度
            serialized_message = message_data.SerializeToString()
            data_length = len(serialized_message)
            
            # 组装包头: 魔数(4字节) + 长度(4字节)
            # '>II'中的'>'表示大端字节序，'I'表示无符号整型(4字节)，'I'表示无符号整型(4字节)
            header = struct.pack('>II', self.HEADER_MAGIC, data_length)
            # 组装完整消息
            packed_data = header + serialized_message
            
            return packed_data
            
        except Exception as e:
            logger.error(f"消息打包失败: {str(e)}")
            raise
    
    def deserialize_message(self, data: bytes) -> Tuple[bool, Dict[str, Any]]:
        """
        解析二进制数据为protobuf消息，处理粘包和分包问题
        
        Args:
            data: 接收到的二进制数据
            
        Returns:
            (是否成功, 解析出的消息数据字典, 剩余数据)
        """
        self.remaining_data += data
        
        # 检查数据长度，至少需要包含完整的包头(8字节)
        if len(self.remaining_data) < 8:
            # 数据不足，返回原始数据等待更多数据
            return False, {}
        
        # 解析包头
        magic, length = struct.unpack('>II', self.remaining_data[:8])

        # 验证魔数
        if magic != self.HEADER_MAGIC:
            logger.error(f"无效的包头魔数: 0x{magic:04X}")
            return False, {}
        
        # 检查是否有足够的数据接收完整消息
        total_length = 8 + length  # 包头(8字节) + 消息体
        if len(self.remaining_data) < total_length:
            # 数据不完整，保留所有数据等待更多数据
            return False, {}
        
        # 提取消息数据
        message_data = self.remaining_data[8:total_length]
        # 保存剩余数据用于处理粘包
        self.next_data = self.remaining_data[total_length:]
        
        try:
            # 解析protobuf消息
            message = message_pb2.BaseMessage()
            message.ParseFromString(message_data)
            
            # 构建返回的数据字典
            dict_data = {}
            metadata = {}
            metadata["sequence_id"] = message.metadata.sequence_id
            metadata["timestamp"] = message.metadata.timestamp
            metadata["account"] = message.metadata.account
            metadata["session_id"] = message.metadata.session_id
            dict_data["msg_id"] = message.msg_id
            dict_data["metadata"] = metadata
            
            # 处理不同类型的消息内容
            if message.HasField("chart_data"):
                chart_data = {}
                chart_data["taskId"] = message.chart_data.task_id
                chart_data["group"] = message.chart_data.group
                chart_data["chart_name"] = message.chart_data.chart_name
                chart_data["path"] = message.chart_data.path
                chart_data["qubit"] = message.chart_data.qubit
                chart_data["step"] = message.chart_data.step
                points = []
                for point in message.chart_data.points:
                    points.append([point.x, point.y])
                chart_data["points"] = points
                dict_data["chart_data"] = chart_data
            elif message.HasField("json_data"):
                json_data = json.loads(message.json_data)
                dict_data["json_data"] = json_data

            self.remaining_data = self.next_data
            self.next_data = b''
            return True, dict_data
        except Exception as e:
            logger.error(f"消息解包失败: {str(e)}")
            # 解析失败，丢弃当前包，返回剩余数据
            return False, {}
