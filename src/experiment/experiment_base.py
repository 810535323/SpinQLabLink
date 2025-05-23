"""
实验相关类定义
"""

import enum
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import time
import uuid

from ..utils.logger import LoggerManager
from ..connection.client import Client

logger = LoggerManager.get_logger(name='experiment')
class Pulse:
    """脉冲类"""
    def __init__(self, width: int, amp: int, phase: int, detune: int):
        self.width = width
        self.amp = amp
        self.phase = phase
        self.detune = detune

class Gate:
    """
    The Gate class represents a quantum gate that can be added to a quantum circuit.
    """
    def __init__(self, angle=0, controlQubit=-1, controlQubit2=-1, delay=0, qubitIndex=0, type='X'):
        # Allowed types of gates
        allowed_types = ['H','I','X','Y','Z','X90','Y90','Z90','Rx','Ry','Rz','T','Td','S','Sd','CNOT','CZ']
        
        if type not in allowed_types:
            raise ValueError(f"Gate type '{type}' not supported. Allowed types are {allowed_types}.")
        
        self.angle = angle          # The rotation angle of the gate (for rotation gates)
        self.controlQubit = controlQubit    # The control qubit (for controlled gates)
        self.controlQubit2 = controlQubit2  # The second control qubit (for Toffoli gate)
        self.delay = delay          # The delay before the gate is applied
        self.qubitIndex = qubitIndex       # The index of the qubit that the gate operates on
        self.timeslot = 0           # The timeslot of the gate in the circuit
        self.type = type            # The type of the gate (e.g., 'X', 'Y', 'Z', 'H', 'CNOT')

class ExperimentStatus(enum.Enum):
    """实验状态枚举"""
    CREATED = "created"       # 实验已创建
    QUEUED = "queued"         # 实验已加入队列
    RUNNING = "running"       # 实验正在运行
    COMPLETED = "completed"   # 实验已完成
    FAILED = "failed"         # 实验失败
    CANCELED = "canceled"     # 实验已取消

class ExperimentResult:
    """实验结果类"""
    
    def __init__(self):
        self.data = {}
        self.plots = []
        self.raw_data = {}
        self.metadata = {}
        self.success = False
        self.error_message = ""
        self.execution_time = 0
    
    def add_data(self, key: str, value: Any) -> None:
        """添加数据"""
        self.data[key] = value
    
    def add_plot(self, name: str, plot_data: Dict[str, Any]) -> None:
        """添加图表数据"""
        self.plots[name] = plot_data
    
    def set_success(self, success: bool, message: str = "") -> None:
        """设置执行状态"""
        self.success = success
        self.error_message = message
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "data": self.data,
            "plots": self.plots,
            "raw_data": self.raw_data,
            "metadata": self.metadata,
            "success": self.success,
            "error_message": self.error_message,
            "execution_time": self.execution_time
        }

class Experiment(ABC):
    """实验基类"""
    def __init__(self, parameters: Any = None, connection: Client = None):
        self.name = f"实验-{uuid.uuid4()[:8]}"
        self.experiment_type = "base"
        self.status = ExperimentStatus.CREATED
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.parameters = parameters or {}
        self.result = ExperimentResult()
        self.metadata = {}
        self.connection = connection
        
        self._data_callback = None
        self._status_callback = None
        self._error_callback = None
        self._finish_callback = None
    
    @abstractmethod
    def data_update_callback(self, data: Dict[str, Any]) -> None:
        """处理实验数据，实现具体实验类型的数据处理"""
        if self._data_callback:
            self._data_callback(data)

    @abstractmethod
    def status_update_callback(self, status: ExperimentStatus) -> None:
        """处理实验状态，实现具体实验类型的状态处理"""
        if self._status_callback:
            self._status_callback(status)

    @abstractmethod
    def error_callback(self, error: Exception) -> None:
        """处理实验错误，实现具体实验类型的错误处理"""
        if self._error_callback:
            self._error_callback(error)
    
    @abstractmethod
    def finish_callback(self, result: ExperimentResult) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        if self._finish_callback:
            self._finish_callback(result)

    def start(self) -> None:
        """开始实验"""
        try:
            # 运行实验
            success = self.connection.start_experiment(self.experiment_type, self.parameters)
            if success:
                self.status = ExperimentStatus.RUNNING
                self.started_at = time.time()
                logger.info(f"开始实验成功: {self.experiment_type}, 参数: {self.parameters}")
            else:
                self.status = ExperimentStatus.CANCELED
                self.result.set_success(False, "实验启动失败")
                logger.info(f"实验启动失败: {self.experiment_type}, 参数: {self.parameters}")
        except Exception as e:
            # 异常处理
            self.status = ExperimentStatus.FAILED
            self.result.set_success(False, str(e))
            raise
    
    def cancel(self) -> None:
        """取消实验"""
        if self.status in [ExperimentStatus.RUNNING, ExperimentStatus.QUEUED]:
            self.status = ExperimentStatus.CANCELED
            self.completed_at = time.time()
    
    def get_status(self) -> ExperimentStatus:
        """获取实验状态"""
        return self.status
    
    def get_result(self) -> ExperimentResult:
        """获取实验结果"""
        return self.result
    
    def get_type(self) -> str:
        """获取实验类型"""
        return self.experiment_type
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "experiment_type": self.experiment_type,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "execution_time": self.result.execution_time if self.finished_at else 0,
        }