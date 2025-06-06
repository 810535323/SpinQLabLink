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
实验管理器

负责管理实验的注册、运行、等待完成和获取结果
"""

from typing import Type, Dict, Any, Callable, List, Optional
import importlib
import time

from ..utils import LoggerManager
from .experiment_base import Experiment, ExperimentParameter, ExperimentState
from ..utils.types import ExperimentType

# 创建logger
logger = LoggerManager.get_logger(name='experiment_manager')

class ExperimentManager:
    """实验管理器"""
    def __init__(self):
        self.EXPERIMENT_TYPE_MAP = {
            ExperimentType.NMR_PHENOMENON_AND_SIGNAL: ('spinqlablink.experiment.exp_pulse', 'ExpPulse', 'ExpPulseParameters'),
            ExperimentType.RABI_OSCILLATIONS: ('spinqlablink.experiment.exp_rabi', 'ExpRabi', 'ExpRabiParameters'),
            ExperimentType.QUANTUM_BIT: ('spinqlablink.experiment.exp_qubit', 'ExpQubit', 'ExpQubitParameters'),
            ExperimentType.QUANTUM_DECOHERENCE_T1: ('spinqlablink.experiment.exp_decot1', 'ExpT1', 'ExpT1Parameters'),
            ExperimentType.QUANTUM_DECOHERENCE_T2: ('spinqlablink.experiment.exp_decot2', 'ExpT2', 'ExpT2Parameters'),
            ExperimentType.QUANTUM_CONTROL: ('spinqlablink.experiment.exp_qcontrol', 'ExpQControl', 'ExpQControlParameters'),
            ExperimentType.QUANTUM_SYSTEM_INITIALIZATION: ('spinqlablink.experiment.exp_sysinit', 'ExpSysInit', 'ExpSysInitParameters'),
            ExperimentType.SPIN_ECHO: ('spinqlablink.experiment.exp_spinecho', 'ExpSpinecho', 'ExpSpinechoParameters'),
        }
        self.current_experiment = None
        self.current_experiment_params = None

    def _get_experiment_class(self, experiment_type: ExperimentType) -> tuple[Type[Experiment], Type[ExperimentParameter]]:
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
            raise ValueError(f"Unknown experiment type: {experiment_type}")
            
        module_path, class_name, parameter_class_name = self.EXPERIMENT_TYPE_MAP[experiment_type]
        try:
            # 动态导入实验类
            module = importlib.import_module(module_path)
            experiment_class = getattr(module, class_name)
            parameter_class = getattr(module, parameter_class_name)
            return experiment_class, parameter_class
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import experiment class: {e}")
            raise ValueError(f"Cannot load experiment type: {experiment_type}")
        
    def register_experiment(self, experiment_type: ExperimentType, handler_map: dict) -> tuple[Experiment, ExperimentParameter]:
        """
        注册实验
        
        Args:
            experiment_type: 实验类型
        """
        if self.current_experiment is not None:
            raise ValueError("Cannot register experiment more than once")
        
        experiment_class, parameter_class = self._get_experiment_class(experiment_type)
        
        self.current_experiment_params = parameter_class()
        self.current_experiment = experiment_class(self.current_experiment_params)
        self.current_experiment.register_handler(handler_map)
        return self.current_experiment, self.current_experiment_params

    def deregister_experiment(self):
        """
        注销实验
        """
        if self.current_experiment is not None or self.current_experiment_params is not None:
            self.current_experiment = None
            self.current_experiment_params = None
        else:
            logger.warning("No experiment registered")

    def get_experiment_parameter(self):
        if self.current_experiment is None:
            logger.error("No experiment registered")
            return {}
        return self.current_experiment.get_experiment_parameter()

    def wait_for_experiment_completion(self):
        """
        等待实验完成
        """
        if self.current_experiment is None:
            logger.error("No experiment registered or experiment was deregistered due to errors")
            return False
        
        try:
            while(True):
                if self.current_experiment is None:
                    logger.error("Experiment was deregistered during execution")
                    return False

                status = self.current_experiment.get_status()
                if status == ExperimentState.COMPLETED or status == ExperimentState.FAILED:
                    break

                time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Error waiting for experiment completion: {e}")
            self.deregister_experiment()
            return False

    def get_experiment_result(self):
        """
        获取实验结果
        """
        if self.current_experiment is None:
            logger.error("No experiment registered or experiment was deregistered due to errors")
            return {"result": {}}
        
        return self.current_experiment.get_result()
