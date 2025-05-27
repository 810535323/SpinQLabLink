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
    
    # 包头标识
    HEADER_MAGIC = 0xFEFE
    
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
            message_data.metadata.device_id = metadata.get("device_id")
            message_data.metadata.username = metadata.get("device_name")
            message_data.metadata.session_id = metadata.get("session_id")
            message_data.json_data = json.dumps(json_data)
            
            # 计算数据长度
            serialized_message = message_data.SerializeToString()
            data_length = len(serialized_message)
            
            # 组装包头: 魔数(2字节) + 长度(4字节)
            # '>HI'中的'>'表示大端字节序，'H'表示无符号短整型(2字节)，'I'表示无符号整型(4字节)
            header = struct.pack('>HI', self.HEADER_MAGIC, data_length)
            
            # 组装完整消息
            packed_data = header + serialized_message
            
            return packed_data
            
        except Exception as e:
            logger.error(f"消息打包失败: {str(e)}")
            raise
    
    def deserialize_message(self, data: bytes) -> Tuple[bool, Dict[str, Any]]:
        """
        解析二进制数据为protobuf消息
        
        Args:
            data: 接收到的二进制数据
            
        Returns:
            (是否成功, 解析出的BaseMessage对象, 剩余数据(JSON数据))
        """
        remaining_data = data
        
        # 检查数据长度，至少需要包含完整的包头(6字节)
        if len(remaining_data) < 6:
            return False, None, remaining_data
        
        # 解析包头
        magic, length = struct.unpack('>HI', remaining_data[:6])
        
        # 验证魔数
        if magic != self.HEADER_MAGIC:
            logger.error(f"无效的包头魔数: 0x{magic:04X}")
            # 尝试查找有效的包头
            pos = remaining_data[1:].find(struct.pack('>H', self.HEADER_MAGIC))
            if pos >= 0:
                return False, None, remaining_data[pos+1:]
            return False, None, b''
        
        # 检查是否有足够的数据
        total_length = 6 + length
        if len(remaining_data) < total_length:
            return False, None, remaining_data
        
        # 提取消息数据
        message_data = remaining_data[6:total_length]
        
        try:
            # 解析protobuf消息
            message = message_pb2.BaseMessage()
            message.ParseFromString(message_data)
            
            dict_data = {}
            metadata = {}
            metadata["sequence_id"] = message.metadata.sequence_id
            metadata["timestamp"] = message.metadata.timestamp
            metadata["device_id"] = message.metadata.device_id
            # metadata["device_name"] = message.metadata.device_name
            metadata["device_name"] = message.metadata.username
            metadata["session_id"] = message.metadata.session_id
            dict_data["msg_id"] = message.msg_id
            dict_data["metadata"] = metadata
            if message.HasField("chart_data"):
                chart_data = {}
                chart_data["task_id"] = message.chart_data.task_id
                chart_data["group"] = message.chart_data.group
                chart_data["chart_name"] = message.chart_data.chart_name
                chart_data["path"] = message.chart_data.path
                chart_data["qubit"] = message.chart_data.qubit
                chart_data["step"] = message.chart_data.step
                points = []
                for point in message.chart_data.points:
                    points.append({
                        "x": point.x,
                        "y": point.y
                    })
                chart_data["points"] = points
                dict_data["chart_data"] = chart_data
            elif message.HasField("json_data"):
                json_data = json.loads(message.json_data)
                dict_data["json_data"] = json_data

            # 返回解析结果和剩余数据
            return True, dict_data
        except Exception as e:
            logger.error(f"消息解包失败: {str(e)}")
            return False, {}
