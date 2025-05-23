"""
请求分发器

负责解析API请求并将其分发给相应的实验对象执行
"""

from typing import Dict, Any, Optional, Union, List, Callable, Type
from uuid import UUID
import importlib

from .utils import LoggerManager
from .experiment.experiment_base import BaseExperiment

from .connection.client import Client

# 创建logger
logger = LoggerManager.get_logger(name='dispatcher')


class ExperimentDispatcher:
    """实验请求分发器，负责将API请求分发给相应的实验对象"""
    
    # 实验类型映射
    EXPERIMENT_TYPE_MAP = {
        'exp_nmr': 'exp_nmr',
        'exp_rabi': 'exp_rabi',
        'exp_qbit': 'exp_qbit',
        'exp_qdeco': 'exp_qdeco',
        'exp_qcontrol': 'exp_qcontrol',
        'exp_sysinit': 'exp_sysinit',
        'exp_qcircuit': 'exp_qcircuit',
        'exp_qtomography': 'exp_qtomography',
        'exp_qcomputetask': 'exp_qcomputetask'
    }
    
    def __init__(self):
        # 实验客户端
        self._client = None
        # 保存正在运行的实验实例
        self._running_experiment: BaseExperiment = None
        # 保存实验结果
        self._experiment_results: Dict[str, Any] = {}
        # 实验数据回调
        self._data_callback: Callable[[Dict[str, Any]], None] = None
        # 实验完成回调
        self._finish_callback: Callable[[Dict[str, Any]], None] = None

    def connect(self, lab_ip: str, lab_port: int, lab_user: str, lab_password: str):
        """连接到设备"""
        self._client = Client(lab_ip, lab_port, lab_user, lab_password)
        self._client.connect()

    def disconnect(self):
        """断开连接"""
        self._client.disconnect()

    def is_connected(self) -> bool:
        """检查是否连接"""
        return self._client._is_connected()
    
    def get_connection(self) -> Client:
        """获取连接"""
        return self._client.connection

    def _get_experiment_class(self, experiment_type: str) -> Type[BaseExperiment]:
        """
        根据实验类型获取对应的实验类
        
        Args:
            experiment_type: 实验类型
            
        Returns:
            实验类
        
        Raises:
            ValueError: 实验类型不支持
        """
        if experiment_type not in self.EXPERIMENT_TYPE_MAP:
            raise ValueError(f"不支持的实验类型: {experiment_type}")
            
        class_name = self.EXPERIMENT_TYPE_MAP[experiment_type]
        try:
            # 动态导入实验类
            module = importlib.import_module('.experiment', package='src')
            experiment_class = getattr(module, class_name)
            return experiment_class
        except (ImportError, AttributeError) as e:
            logger.error(f"导入实验类失败: {e}")
            raise ValueError(f"无法加载实验类型: {experiment_type}")
    
    def dispatch_start_experiment(self, experiment_type: str,
                            parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        分发启动实验请求
        
        Args:
            experiment_id: 实验ID
            experiment_type: 实验类型
            parameters: 实验参数
            data_callback: 数据回调函数
            finish_callback: 结束回调函数
            
        Returns:
            bool: 是否成功启动实验
        """
        logger.info(f"分发启动实验请求: {experiment_type}")
        
        # 检查实验是否已经存在
        if self._running_experiments:
            logger.warning(f"实验正在运行中")
            return False
            
        try:
            # 获取实验类
            experiment_class = self._get_experiment_class(experiment_type)
            # 创建实验实例
            experiment = experiment_class(experiment_type=experiment_type, parameters=parameters, connection=self._client)
            # 启动实验
            success = experiment.start()
            
            if success:
                # 保存实验实例
                self._running_experiment = experiment
                logger.info(f"实验启动成功,实验类型: {experiment_type},实验参数: {parameters}")
                return True
            else:
                logger.error(f"实验启动失败")
                
                return False
                
        except Exception as e:
            logger.error(f"启动实验异常: {e}")
            
            return False
    
    def dispatch_data_callback(self, data: Dict[str, Any]) -> None:
        """
        数据回调函数，用于处理实验过程中产生的数据
        
        Args:
            data: 实验数据
        """
        logger.info(f"收到实验数据: {data}")
        if self._data_callback:
            self._data_callback(data)
    
    def dispatch_finish_callback(self, result: Dict[str, Any]) -> None:
        """
        实验完成回调函数，用于处理实验完成后的结果
        
        Args:
            result: 实验结果
        """
        logger.info("实验完成")

        if self._finish_callback:
            self._finish_callback(result)
        else:
            logger.warning("未知实验结果!")

    def dispatch_get_result(self) -> Dict[str, Any]:
        """
        分发获取实验结果请求
        
        Args:
            experiment_id: 实验ID
            result_format: 结果格式
            
        Returns:
            Dict[str, Any]: 实验结果
        """
        logger.info(f"分发获取结果请求")
        
        # 检查实验结果是否存在
        if not self._experiment_results:
            logger.warning(f"实验结果不存在")
            return {"success": False, "error": "实验结果不存在"}
            
        try:
            result = self._experiment_results
                
            return {"success": True, "result": result}
            
        except Exception as e:
            logger.error(f"获取结果异常: {e}")
            return {"success": False, "error": str(e)}
    
    def dispatch_get_status(self) -> Dict[str, Any]:
        """
        分发获取实验状态请求
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            Dict[str, Any]: 实验状态
        """
        logger.info(f"分发获取状态请求")
        
        # 检查实验是否存在
        if self._running_experiments:
            status = self._running_experiments.get_status()
            return {"success": True, "status": status, "is_running": True}
        
        # 检查是否有结果
        elif self._experiment_results:
            return {"success": True, "status": "completed", "is_running": False}
            
        else:
            logger.warning(f"实验不存在")
            return {"success": False, "error": "实验不存在"}

# 创建单例实例
dispatcher = ExperimentDispatcher() 