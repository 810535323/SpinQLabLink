"""
实验相关类定义
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from pydantic import BaseModel

from utils import LoggerManager

logger = LoggerManager.get_logger(name='experiment')

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

class ExperimentParameter(BaseModel):
    """实验参数基类"""


    def _validate_pulse_json(self, s: str) -> bool:
        """验证脉冲序列是否合法"""
        try:
            j = json.loads(s)
            # 验证json结构是否包含必要字段
            if "ppulse" not in j or "hpulse" not in j:
                raise ValueError("脉冲序列必须包含ppulse和hpulse字段")
            
            # 定义有效字段和验证规则
            valid_keys = ["width", "amp", "phase", "detune"]
            validation_rules = {
                "width": {
                    "type_check": lambda x: isinstance(x, (int)),
                    "type_error": "必须是整数类型",
                    "range_check": lambda x: 0 < x <= 2000000,
                    "range_error": "必须在(0, 2000000]范围内"
                },
                "amp": {
                    "type_check": lambda x: isinstance(x, (int, float)),
                    "type_error": "必须是数字类型",
                    "range_check": lambda x: 0 < x <= 100,
                    "range_error": "必须在(0, 100]范围内"
                },
                "phase": {
                    "type_check": lambda x: isinstance(x, (int, float)),
                    "type_error": "必须是数字类型",
                    "range_check": lambda x: True,
                    "range_error": "无范围限制"
                },
                "detune": {
                    "type_check": lambda x: isinstance(x, (int)),
                    "type_error": "必须是整数类型",
                    "range_check": lambda x: -10000 <= x <= 10000,
                    "range_error": "必须在[-10000, 10000]范围内"
                }
            }
            
            # 验证ppulse和hpulse字段
            for pulse_name, pulse_data in [("ppulse", j["ppulse"]), ("hpulse", j["hpulse"])]:
                # 检查字段是否有效
                for key in pulse_data:
                    if key not in valid_keys:
                        raise ValueError(f"{pulse_name}中包含无效字段: {key}")
                
                # 验证每个字段的类型和值范围
                for key, value in pulse_data.items():
                    rules = validation_rules[key]
                    
                    # 类型检查
                    if not rules["type_check"](value):
                        raise TypeError(f"{pulse_name}.{key}{rules['type_error']}，当前为{type(value)}")
                    
                    # 范围检查
                    if not rules["range_check"](value):
                        raise ValueError(f"{pulse_name}.{key}{rules['range_error']}，当前值为{value}")
            
            return True
        except json.JSONDecodeError:
            return False
    class Config:
        validate_assignment = True

class Experiment(ABC):
    """实验基类"""
    def __init__(self, parameters: Optional[ExperimentParameter] = None):
        self.experiment_type = ""
        self.step = 0
        self.created_at = time.time()
        self.started_at = None
        self.completed_at = None
        self.parameters = parameters
        self.result = ExperimentResult()
        self.metadata = {}
        
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
    def error_callback(self, error: Exception) -> None:
        """处理实验错误，实现具体实验类型的错误处理"""
        if self._error_callback:
            self._error_callback(error)
    
    @abstractmethod
    def finish_callback(self, result: ExperimentResult) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        if self._finish_callback:
            self._finish_callback(result)

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