"""
实验相关类定义
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from pydantic import BaseModel
import uuid

from utils import LoggerManager
from utils.types import MachineType, ExperimentState
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
        pass

    @abstractmethod
    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        pass

    @abstractmethod
    def get_result(self) -> Dict[str, Any]:
        """获取实验结果"""
        """
        获取实验结果的抽象方法，所有实验子类必须实现此方法。
        此方法应返回包含所有实验结果的字典，用于实验执行。
        
        Returns:
            Dict[str, Any]: 包含实验参数的字典
        
        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("必须在子类中实现get_result方法")

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
                    "range_check": lambda x: 0 <= x <= 2000000,
                    "range_error": "必须在[0, 2000000]范围内"
                },
                "amp": {
                    "type_check": lambda x: isinstance(x, (int, float)),
                    "type_error": "必须是数字类型",
                    "range_check": lambda x: 0 <= x <= 100,
                    "range_error": "必须在[0, 100]范围内"
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
        
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取实验参数"""
        """
        获取实验参数的抽象方法，所有实验子类必须实现此方法。
        此方法应返回包含所有实验参数的字典，用于实验执行。
        
        Returns:
            Dict[str, Any]: 包含实验参数的字典
        
        Raises:
            NotImplementedError: 如果子类未实现此方法
        """
        raise NotImplementedError("必须在子类中实现get_parameters方法")
    
    class Config:
        validate_assignment = True

class Experiment(ABC):
    """实验基类"""
    def __init__(self, parameters: Optional[ExperimentParameter] = None):
        self.experiment_type = ""
        self.id = str(uuid.uuid4())
        self.name = ""
        self.step = ""
        self.state = "PENDING"
        self.created_at = int(time.time() * 1000)  # 转换为毫秒级时间戳
        self.started_at = None
        self.completed_at = None
        self.parameters = parameters
        self.graph_data = []
        self.result = ExperimentResult()

    def register_handler(self, handler_map: dict) -> None:
        """注册消息处理函数"""
        handler_map[MachineType.MSG_RES_ADD_EXP_TASK_RES] = self.handle_exp_added
        handler_map[MachineType.MSG_POST_EXP_STARTED] = self.handle_exp_started
        handler_map[MachineType.MSG_POST_EXP_TERMINATED] = self.handle_exp_terminated
        handler_map[MachineType.MSG_POST_EXP_REMOVED] = self.handle_exp_removed
        handler_map[MachineType.MSG_POST_EXP_STEP_CHANGED] = self.handle_exp_step_changed
        handler_map[MachineType.MSG_POST_EXP_DATA_UPDATED] = self.handle_exp_data_updated
        handler_map[MachineType.MSG_POST_EXP_CHART_UPDATED_STARTED] = self.handle_exp_chart_data_updated_started
        handler_map[MachineType.MSG_POST_EXP_CHART_UPDATED] = self.handle_exp_chart_data_updated
        handler_map[MachineType.MSG_POST_EXP_CHART_UPDATED_FINISHED] = self.handle_exp_chart_data_updated_finished
        handler_map[MachineType.MSG_POST_EXP_FINISHED] = self.handle_exp_finished
    
    @abstractmethod
    def handle_exp_added(self, data: Dict[str, Any]) -> None:
        """处理实验队列更新"""
        raise NotImplementedError("必须在子类中实现handle_exp_added方法")
    
    @abstractmethod
    def get_experiment_parameter(self) -> Dict[str, Any]:
        """获取实验参数"""
        raise NotImplementedError("必须在子类中实现get_experiment_parameter方法")

    @abstractmethod
    def handle_exp_added(self, data: Dict[str, Any]) -> None:
        """处理实验添加，实现具体实验类型的添加处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_added方法")
    
    @abstractmethod
    def handle_exp_started(self) -> None:
        """处理实验开始，实现具体实验类型的开始处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_started方法")
    
    @abstractmethod
    def handle_exp_terminated(self) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_terminated方法")
    
    @abstractmethod
    def handle_exp_removed(self) -> None:
        """处理实验移除，实现具体实验类型的移除处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_removed方法")
    
    @abstractmethod
    def handle_exp_step_changed(self, step: int) -> None:
        """处理实验步骤变化，实现具体实验类型的步骤变化处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_step_changed方法")
    
    @abstractmethod
    def handle_exp_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验数据更新，实现具体实验类型的数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_data_updated方法")
    
    @abstractmethod
    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_chart_data_updated_started方法")
    
    @abstractmethod
    def handle_exp_chart_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_chart_data_updated方法")
    @abstractmethod
    def handle_exp_chart_data_updated_finished(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_chart_data_updated_finished方法")

    @abstractmethod
    def handle_exp_finished(self, data: Dict[str, Any]) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_finished方法")

    @abstractmethod
    def get_status(self) -> ExperimentState:
        """获取实验状态"""
        raise NotImplementedError("必须在子类中实现get_status方法")

    @abstractmethod
    def get_result(self) -> ExperimentResult:
        """获取实验结果"""
        raise NotImplementedError("必须在子类中实现get_result方法")
    