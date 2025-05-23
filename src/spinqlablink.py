"""
远程实验API接口定义

提供实验生命周期的各个阶段的API接口，包括：
1. 实验开始
2. 实验数据上传
3. 实验结束
4. 获取实验结果
"""

from typing import Dict, Any, List, Optional, Callable, Union
from uuid import UUID

from .dispatcher import dispatcher
from .utils import LoggerManager
from .utils.experimentType import ExperimentType

# 创建logger
logger = LoggerManager.get_logger(name='SpinQLabLink')


class SpinQLabLink:
    """SpinQ Lab Remote Experiment Python Interface"""
    
    def __init__(self):
        """初始化API实例"""
        self._dispatcher = dispatcher

    def connect(self, lab_ip: str, lab_port: int, lab_user: str, lab_password: str):
        """连接到设备"""
        self._dispatcher.connect(lab_ip, lab_port, lab_user, lab_password)

    def disconnect(self):
        """断开连接"""
        self._dispatcher.disconnect()
    
    def start_experiment(self, experiment_type: str, config: Dict[str, Any],
                         data_callback: Optional[Callable] = None,
                         finish_callback: Optional[Callable] = None) -> bool:
        """
        启动实验
        
        Args:
            experiment_type: 实验类型，如'exp_nmr', 'exp_rabi', 'exp_qbit'等
            config: 实验配置信息
            data_callback: 回调函数，实验数据上传后调用,即时获取数据
            finish_callback: 回调函数，实验结束时调用,即时获取数据
            
        Returns:
            bool: 是否成功启动实验
        """
        logger.info(f"API请求: 启动实验 {experiment_type}")
        return self._dispatcher.dispatch_start_experiment(
            experiment_type=experiment_type,
            config=config,
            data_callback=data_callback,
            finish_callback=finish_callback
        )
    
    def get_experiment_result(self) -> Dict[str, Any]:
        """
        获取实验结果
        
        Args:
            experiment_id: 实验ID
            result_format: 结果格式，如'json', 'csv'等
            
        Returns:
            Dict[str, Any]: 实验结果数据
        """
        logger.info(f"API请求: 获取实验结果")
        return self._dispatcher.dispatch_get_result()
    
    def get_experiment_status(self, experiment_id: Union[str, UUID]) -> Dict[str, Any]:
        """
        获取实验状态
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            Dict[str, Any]: 实验状态信息
        """
        logger.info(f"API请求: 获取实验状态 {experiment_id}")
        return self._dispatcher.dispatch_get_status(
            experiment_id=experiment_id
        )
    
# 创建单例实例，方便导入使用
api = SpinQLabLink()
