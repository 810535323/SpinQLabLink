"""
实验客户端模块

提供和实验服务器交互的高级接口
"""

import time
import logging
import threading
import json
from typing import Dict, Any, List, Optional, Tuple, Union, Type, Callable
from uuid import UUID

from .connection import TCPConnection
from ..experiment.experiment_base import Experiment, ExperimentStatus
from ..utils.exceptions import ConnectionError, ExperimentError, AuthenticationError
from ..utils import LoggerManager
from .protocol import protocol, MessageType, CommandType

# 创建logger
logger = LoggerManager.get_logger(name='client')

class Client:
    """实验客户端类，用于与实验服务器交互"""
    
    def __init__(self, host: str, port: int, client_account: str, client_password: str,
                timeout: float = 30.0, auto_reconnect: bool = True,
                max_reconnect_attempts: int = 3):
        """
        初始化实验客户端
        
        Args:
            host: 服务器主机名或IP
            port: 服务器端口
            client_account: 客户端账号
            client_password: 客户端密码
            timeout: 请求超时时间（秒）
            auto_reconnect: 是否自动重连
            max_reconnect_attempts: 最大重连尝试次数
        """
        self.host = host
        self.port = port
        self.client_account = client_account
        self.client_password = client_password
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        
        # 创建连接
        self.connection = TCPConnection(host, port, timeout)
        
        # 认证状态
        self.authenticated = False
        
        # 回调函数
        self._experiment_status_callback = None
        self._data_update_callback = None
        self._error_callback = None
        
        self._experiments = {}  # 存储正在运行的实验
        self._callback_handlers = {}  # 存储回调处理函数
        self._data_handlers = {}  # 存储数据处理函数
        self._lock = threading.Lock()
        
        logger.info(f"已创建实验客户端: {host}:{port}")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
        return False  # 不抑制异常
    
    def connect(self) -> bool:
        """
        连接到实验服务器
        
        Returns:
            bool: 是否连接成功
        
        Raises:
            ConnectionError: 连接失败
        """
        try:
            # 连接
            success = self.connection.connect()
            
            if success and self.api_key:
                # 设置消息回调
                self.connection.set_message_callback(self._handle_message)
                
                # 进行身份验证
                self._authenticate()
            
            return success
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise ConnectionError(f"连接实验服务器失败: {str(e)}")
    
    def disconnect(self) -> None:
        """断开与实验服务器的连接"""
        if self.connection.is_connected():
            self.connection.disconnect()
            logger.info("已断开连接")
        self.authenticated = False
    
    def _authenticate(self) -> bool:
        """
        进行身份验证
        
        Returns:
            bool: 是否认证成功
        
        Raises:
            ConnectionError: 认证失败
        """
        if not self.api_key:
            logger.warning("未提供API密钥，跳过身份验证")
            self.authenticated = True
            return True
            
        logger.info("正在进行身份验证...")
        
        try:
            # 发送认证请求
            response = self.connection.send_message(
                CommandType.AUTH,
                {"api_key": self.api_key},
                wait_response=True,
                timeout=self.timeout
            )
            
            # 验证响应
            if response['type'] == MessageType.ERROR:
                error = response.get('data', {}).get('error', '未知错误')
                logger.error(f"身份验证失败: {error}")
                self.authenticated = False
                raise ConnectionError(f"身份验证失败: {error}")
                
            # 成功认证
            self.authenticated = True
            logger.info("身份验证成功")
            return True
            
        except Exception as e:
            logger.error(f"身份验证异常: {e}")
            self.authenticated = False
            raise ConnectionError(f"身份验证失败: {str(e)}")
    
    def _is_connected(self) -> bool:
        """检查是否连接"""
        return self.connection.is_connected()

    def _ensure_connected(self) -> bool:
        """
        确保已连接和认证
        
        Returns:
            bool: 是否已连接和认证
            
        Raises:
            ConnectionError: 未连接或未认证
        """
        if not self.connection.is_connected():
            if self.auto_reconnect:
                logger.warning("连接已断开，尝试重连...")
                for attempt in range(1, self.max_reconnect_attempts + 1):
                    try:
                        logger.info(f"重连尝试 {attempt}/{self.max_reconnect_attempts}")
                        self.connect()
                        return True
                    except ConnectionError as e:
                        logger.error(f"重连尝试 {attempt} 失败: {e}")
                        time.sleep(1)  # 等待一秒再次尝试
                
                # 所有重连尝试都失败
                raise ConnectionError("重连失败，无法连接到实验服务器")
            else:
                raise ConnectionError("未连接到实验服务器")
                
        if not self.authenticated and self.api_key:
            logger.warning("未认证，尝试重新认证...")
            self._authenticate()
            
        return True
    
    def _handle_message(self, message: Dict[str, Any]) -> None:
        """
        处理接收到的消息
        
        Args:
            message: 接收到的消息
        """
        message_type = message.get('type')
        command = message.get('command')
        data = message.get('data', {})
        
        logger.debug(f"收到消息: {command}, 类型: {message_type}")
        
        # 处理错误消息
        if message_type == MessageType.ERROR:
            error_msg = data.get('error', '未知错误')
            logger.error(f"收到错误: {error_msg}")
            if self._error_callback:
                try:
                    self._error_callback(error_msg)
                except Exception as e:
                    logger.error(f"错误回调执行异常: {e}")
            return
            
        # 处理实验状态更新
        if command == CommandType.GET_STATUS and self._experiment_status_callback:
            try:
                experiment_id = data.get('experiment_id')
                status = data.get('status')
                if experiment_id and status:
                    self._experiment_status_callback(experiment_id, status, data)
            except Exception as e:
                logger.error(f"状态回调执行异常: {e}")
                
        # 处理数据更新
        if command == CommandType.UPLOAD_DATA and self._data_update_callback:
            try:
                experiment_id = data.get('experiment_id')
                if experiment_id:
                    self._data_update_callback(experiment_id, data)
            except Exception as e:
                logger.error(f"数据回调执行异常: {e}")
    
    def start_experiment(self, experiment_type: str, 
                     parameters: Dict[str, Any]) -> bool:
        """
        启动实验
        
        Args:
            experiment_type: 实验类型
            parameters: 实验参数
            
        Returns:
            bool: 是否成功启动实验
            
        Raises:
            ConnectionError: 连接错误
            ExperimentError: 实验错误
        """
        self._ensure_connected()
        
        logger.info(f"启动实验: {experiment_type}, 配置: {parameters}")
        
        try:
            # 发送启动实验请求
            response = self.connection.send_message(
                CommandType.START_EXPERIMENT,
                {
                    "experiment_type": experiment_type,
                    "parameters": parameters
                },
                wait_response=True,
                timeout=self.timeout
            )
            
            # 处理响应
            if response['type'] == MessageType.ERROR:
                error = response.get('data', {}).get('error', '未知错误')
                logger.error(f"启动实验失败: {error}")
                raise ExperimentError(f"启动实验失败: {error}")
                
            # 检查响应数据
            result = response.get('data', {})
            success = result.get('success', False)
            
            if success:
                logger.info(f"实验启动成功: {experiment_type}")
            else:
                error = result.get('error', '未知错误')
                logger.error(f"启动实验失败: {error}")
                raise ExperimentError(f"启动实验失败: {error}")
                
            return success
            
        except TimeoutError:
            logger.error(f"启动实验超时: {experiment_type}")
            raise ExperimentError(f"启动实验超时")
        except Exception as e:
            if not isinstance(e, ExperimentError):
                logger.error(f"启动实验异常: {e}")
                raise ExperimentError(f"启动实验失败: {str(e)}")
            raise e
    
    def upload_experiment_data(self, experiment_type: str, 
                           data: Dict[str, Any]) -> bool:
        """
        上传实验数据
        
        Args:
            experiment_type: 实验类型
            data: 实验数据
            
        Returns:
            bool: 是否成功上传数据
            
        Raises:
            ConnectionError: 连接错误
            ExperimentError: 实验错误
        """
        self._ensure_connected()
        
        logger.info(f"上传实验数据: {experiment_type}")
        
        try:
            # 发送上传数据请求
            response = self.connection.send_message(
                CommandType.UPLOAD_DATA,
                {
                    "experiment_type": experiment_type,
                    "data": data,
                    "timestamp": time.time()
                },
                wait_response=True,
                timeout=self.timeout
            )
            
            # 处理响应
            if response['type'] == MessageType.ERROR:
                error = response.get('data', {}).get('error', '未知错误')
                logger.error(f"上传数据失败: {error}")
                raise ExperimentError(f"上传数据失败: {error}")
                
            # 检查响应数据
            result = response.get('data', {})
            success = result.get('success', False)
            
            if success:
                logger.info(f"数据上传成功: {experiment_type}")
            else:
                error = result.get('error', '未知错误')
                logger.error(f"上传数据失败: {error}")
                raise ExperimentError(f"上传数据失败: {error}")
                
            return success
            
        except TimeoutError:
            logger.error(f"上传数据超时: {experiment_type}")
            raise ExperimentError(f"上传数据超时")
        except Exception as e:
            if not isinstance(e, ExperimentError):
                logger.error(f"上传数据异常: {e}")
                raise ExperimentError(f"上传数据失败: {str(e)}")
            raise e
    
    def finish_experiment(self, experiment_type: str, 
                      status: str, message: Optional[str] = None) -> bool:
        """
        结束实验
        
        Args:
            experiment_type: 实验类型
            status: 结束状态
            message: 附加信息
            
        Returns:
            bool: 是否成功结束实验
            
        Raises:
            ConnectionError: 连接错误
            ExperimentError: 实验错误
        """
        self._ensure_connected()
        
        logger.info(f"结束实验: {experiment_type}, 状态: {status}")
        
        try:
            # 发送结束实验请求
            request_data = {
                "experiment_type": experiment_type,
                "status": status
            }
            
            if message:
                request_data["message"] = message
                
            response = self.connection.send_message(
                CommandType.FINISH_EXPERIMENT,
                request_data,
                wait_response=True,
                timeout=self.timeout
            )
            
            # 处理响应
            if response['type'] == MessageType.ERROR:
                error = response.get('data', {}).get('error', '未知错误')
                logger.error(f"结束实验失败: {error}")
                raise ExperimentError(f"结束实验失败: {error}")
                
            # 检查响应数据
            result = response.get('data', {})
            success = result.get('success', False)
            
            if success:
                logger.info(f"实验结束成功: {experiment_type}")
            else:
                error = result.get('error', '未知错误')
                logger.error(f"结束实验失败: {error}")
                raise ExperimentError(f"结束实验失败: {error}")
                
            return success
            
        except TimeoutError:
            logger.error(f"结束实验超时: {experiment_type}")
            raise ExperimentError(f"结束实验超时")
        except Exception as e:
            if not isinstance(e, ExperimentError):
                logger.error(f"结束实验异常: {e}")
                raise ExperimentError(f"结束实验失败: {str(e)}")
            raise e
    
    def get_experiment_result(self, experiment_type: str, 
                          result_format: Optional[str] = None) -> Dict[str, Any]:
        """
        获取实验结果
        
        Args:
            experiment_type: 实验类型
            result_format: 结果格式
            
        Returns:
            Dict[str, Any]: 实验结果
            
        Raises:
            ConnectionError: 连接错误
            ExperimentError: 实验错误
        """
        self._ensure_connected()
        
        logger.info(f"获取实验结果: {experiment_type}")
        
        try:
            # 发送获取结果请求
            request_data = {
                "experiment_type": experiment_type
            }
            
            if result_format:
                request_data["format"] = result_format
                
            response = self.connection.send_message(
                CommandType.GET_RESULT,
                request_data,
                wait_response=True,
                timeout=self.timeout
            )
            
            # 处理响应
            if response['type'] == MessageType.ERROR:
                error = response.get('data', {}).get('error', '未知错误')
                logger.error(f"获取结果失败: {error}")
                raise ExperimentError(f"获取结果失败: {error}")
                
            # 返回结果数据
            result = response.get('data', {})
            
            if not result.get('success', False):
                error = result.get('error', '未知错误')
                logger.error(f"获取结果失败: {error}")
                raise ExperimentError(f"获取结果失败: {error}")
                
            logger.info(f"获取结果成功: {experiment_type}")
            return result
            
        except TimeoutError:
            logger.error(f"获取结果超时: {experiment_type}")
            raise ExperimentError(f"获取结果超时")
        except Exception as e:
            if not isinstance(e, ExperimentError):
                logger.error(f"获取结果异常: {e}")
                raise ExperimentError(f"获取结果失败: {str(e)}")
            raise e
    
    def get_experiment_status(self, experiment_type: str) -> Dict[str, Any]:
        """
        获取实验状态
        
        Args:
            experiment_type: 实验类型
            
        Returns:
            Dict[str, Any]: 实验状态信息
            
        Raises:
            ConnectionError: 连接错误
            ExperimentError: 实验错误
        """
        self._ensure_connected()
        
        logger.info(f"获取实验状态: {experiment_type}")
        
        try:
            # 发送获取状态请求
            response = self.connection.send_message(
                CommandType.GET_STATUS,
                {"experiment_type": experiment_type},
                wait_response=True,
                timeout=self.timeout
            )
            
            # 处理响应
            if response['type'] == MessageType.ERROR:
                error = response.get('data', {}).get('error', '未知错误')
                logger.error(f"获取状态失败: {error}")
                raise ExperimentError(f"获取状态失败: {error}")
                
            # 返回状态数据
            result = response.get('data', {})
            
            if not result.get('success', False):
                error = result.get('error', '未知错误')
                logger.error(f"获取状态失败: {error}")
                raise ExperimentError(f"获取状态失败: {error}")
                
            logger.info(f"获取状态成功: {experiment_type}")
            return result
            
        except TimeoutError:
            logger.error(f"获取状态超时: {experiment_type}")
            raise ExperimentError(f"获取状态超时")
        except Exception as e:
            if not isinstance(e, ExperimentError):
                logger.error(f"获取状态异常: {e}")
                raise ExperimentError(f"获取状态失败: {str(e)}")
            raise e

    def wait_for_completion(self, experiment_type: str, 
                        timeout: float = 600.0, 
                        poll_interval: float = 2.0) -> Dict[str, Any]:
        """
        等待实验完成
        
        Args:
            experiment_type: 实验类型
            timeout: 等待超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            Dict[str, Any]: 实验状态
            
        Raises:
            ConnectionError: 连接错误
            ExperimentError: 实验错误
            TimeoutError: 等待超时
        """
        logger.info(f"等待实验完成: {experiment_type}, 超时: {timeout}秒")
        
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            try:
                # 获取状态
                status = self.get_experiment_status(experiment_type)
                
                # 检查是否已完成
                if not status.get('is_running', True):
                    logger.info(f"实验已完成: {experiment_type}, 状态: {status.get('status')}")
                    return status
                    
                # 等待一段时间再次检查
                time.sleep(poll_interval)
                
            except ConnectionError as e:
                logger.warning(f"连接错误，尝试重连: {e}")
                try:
                    self._ensure_connected()
                except:
                    # 仍然失败，等待一段时间再试
                    time.sleep(poll_interval)
                    
            except Exception as e:
                logger.error(f"等待过程中出错: {e}")
                raise
        
        # 超时
        raise TimeoutError(f"等待实验完成超时: {experiment_type}")
    
    def register_status_callback(self, callback: Callable[[str, str, Dict[str, Any]], None]) -> None:
        """
        注册实验状态回调函数
        
        Args:
            callback: 回调函数，接收实验类型、状态和其他数据
        """
        self._experiment_status_callback = callback
        logger.debug("已注册状态回调")
    
    def register_data_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """
        注册数据更新回调函数
        
        Args:
            callback: 回调函数，接收实验类型和数据
        """
        self._data_update_callback = callback
        logger.debug("已注册数据回调")
    
    def register_error_callback(self, callback: Callable[[str], None]) -> None:
        """
        注册错误回调函数
        
        Args:
            callback: 回调函数，接收错误信息
        """
        self._error_callback = callback
        logger.debug("已注册错误回调") 