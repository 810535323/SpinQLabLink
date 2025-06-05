# Copyright 2025 SpinQ Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
实验相关类定义
"""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
import time
from pydantic import BaseModel
import uuid

from ..utils import LoggerManager
from ..utils.types import MachineType, ExperimentState
logger = LoggerManager.get_logger(name='experiment')

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
        raise NotImplementedError("get_result method must be implemented in subclass")

class ExperimentParameter(BaseModel):
    """实验参数基类"""        
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
        raise NotImplementedError("get_parameters method must be implemented in subclass")
    
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
    def get_experiment_parameter(self) -> Dict[str, Any]:
        """
        获取实验参数
        
        Returns:
            Dict[str, Any]: 实验参数
        """
        raise NotImplementedError("get_experiment_parameter method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_added(self, data: Dict[str, Any]) -> None:
        """处理实验添加"""
        raise NotImplementedError("handle_exp_added method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_started(self, data: Dict[str, Any]) -> None:
        """处理实验开始"""
        raise NotImplementedError("handle_exp_started method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_terminated(self, data: Dict[str, Any]) -> None:
        """处理实验终止"""
        raise NotImplementedError("handle_exp_terminated method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_removed(self, data: Dict[str, Any]) -> None:
        """处理实验移除"""
        raise NotImplementedError("handle_exp_removed method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_step_changed(self, data: Dict[str, Any]) -> None:
        """处理实验步骤变化"""
        raise NotImplementedError("handle_exp_step_changed method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验数据更新"""
        raise NotImplementedError("handle_exp_data_updated method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新开始"""
        raise NotImplementedError("handle_exp_chart_data_updated_started method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_chart_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新"""
        raise NotImplementedError("handle_exp_chart_data_updated method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_chart_data_updated_finished(self) -> None:
        """处理实验图表数据更新完成"""
        raise NotImplementedError("handle_exp_chart_data_updated_finished method must be implemented in subclass")
    
    @abstractmethod
    def handle_exp_finished(self, data: Dict[str, Any]) -> None:
        """处理实验完成"""
        raise NotImplementedError("handle_exp_finished method must be implemented in subclass")
    
    def get_status(self) -> str:
        """获取实验状态"""
        raise NotImplementedError("get_status method must be implemented in subclass")
    
    def get_result(self) -> Dict[str, Any]:
        """获取实验结果"""
        raise NotImplementedError("get_result method must be implemented in subclass")
    