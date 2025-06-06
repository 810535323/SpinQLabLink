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
NMR Experiment Module

Provides Nuclear Magnetic Resonance experiment functionality
"""

from typing import Dict, Any, List
import time
import json

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState
from ..utils import LoggerManager
from ..utils.types import ExperimentType
from ..utils.pulse import Pulse
from pydantic import Field

# Create logger
logger = LoggerManager.get_logger(name='exp_decot1')

class ExpT1Result(ExperimentResult):
    """T1 Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.graph = []
        self.width = 0
        self.real = 0
        self.coordinate = {}
        self.matrix = {}
        self.module = []
    
    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        return {
            "graph": self.graph,
            "width": self.width,
            "real": self.real,
            "coordinate": self.coordinate,
            "matrix": self.matrix,
            "module": self.module
        }

class ExpT1Parameters(ExperimentParameter):
    """T1 Experiment Parameters Class"""
    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    freq_h: float = Field(default=27.0, gt=0, lt=100, description="Hydrogen resonance frequency (MHz)")
    freq_p: float = Field(default=11.0, gt=0, lt=100, description="Phosphorus resonance frequency (MHz)")
    makePps: bool = Field(default=False, description="Whether to generate PPS signal")
    samplePath: int = Field(default=0, ge=0, le=1, description="Sampling path selection: 0 for hydrogen channel, 1 for phosphorus channel")
    custom_freq: bool = Field(default=True, description="Whether to use custom frequency(h_freq or p_freq)")

    def append_pulse(self, pulse: Pulse):
        self.pulses.append(pulse)

    def _convert_pulse(self) -> Dict[str, Any]:
        """Convert pulse to dictionary"""
        hpulse, ppulse = [], []
        for pulse in self.pulses:
            if pulse.path == 0:
                hpulse.append(pulse.to_dict())
            else:
                ppulse.append(pulse.to_dict())
        return {"hPulse": hpulse, "pPulse": ppulse}

    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            "custom_freq": self.custom_freq,
            "freq_h": self.freq_h * 1000000,
            "freq_p": self.freq_p * 1000000,
            "repeat": 0,
            "makePps": self.makePps,
            "pulse": self._convert_pulse(),
            "samplePath": self.samplePath,
            "sampleQubit": 0,
            "usingAwgFile": False
        }

class ExpT1(Experiment):
    """T1 Experiment Class"""
    
    def __init__(self, parameters: ExpT1Parameters):
        """
        Initialize T1 experiment
        
        Args:
            parameters: T1 experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.QUANTUM_DECOHERENCE_T1
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpT1Result()
        self.step_graph = {}
        
        logger.info(f"Created T1 experiment: {self.name}")

    def get_experiment_parameter(self) -> Dict[str, Any]:
        """获取实验参数"""
        para = {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "endTime": 0,
            "startTime": 0,
            "state": ExperimentState.PENDING,
            "type": self.experiment_type,
            "extra": "",
            "params": json.dumps(self.parameters.get_parameters())
        }
        return para

    def handle_exp_added(self, data: Dict[str, Any]) -> None:
        """处理实验添加，实现具体实验类型的添加处理"""
        if data["code"] == 0:
            self.id = data["taskId"]
            self.created_at = time.time()
        else:
            raise Exception(f"Experiment addition failed: {data}")

    def handle_exp_started(self, data: Dict[str, Any]) -> None:
        """处理实验开始，实现具体实验类型的开始处理"""
        if data["taskId"] == self.id:
            queue = data["queue"][0]
            self.started_at = queue["startTime"]
            self.name = queue["name"]
            self.state = ExperimentState.RUNNING
            logger.info(f"Experiment chart data updated started:{self.name}")
    
    def handle_exp_step_changed(self, data: Dict[str, Any]) -> None:
        """处理实验步骤变化，实现具体实验类型的步骤变化处理"""
        if data["taskId"] == self.id:
            self.step = data["data"]["step"]
    
    def handle_exp_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验数据更新，实现具体实验类型的数据更新处理"""
        if data["taskId"] == self.id:
            logger.debug(f"Experiment data updated: {data}")
            self.result.width = data["data"]["exp_t1"]["width"]
            self.result.real = data["data"]["exp_t1"]["real"]

    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        if data["taskId"] == self.id:
            self.step_lines = {}
    
    def handle_exp_chart_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        if data["taskId"] == self.id:
            self.step_lines[data["chart_name"]] = data["points"]

    def handle_exp_chart_data_updated_finished(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        if data["taskId"] == self.id:
            self.result.append_graph(self.step_lines)

    def handle_exp_terminated(self, data: Dict[str, Any]) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        self.completed_at = time.time()
        if data["taskId"] == self.id:
            self.state = ExperimentState.FAILED
    
    def handle_exp_removed(self, data: Dict[str, Any]) -> None:
        """处理实验移除，实现具体实验类型的移除处理"""
        self.completed_at = time.time()
        self.state = ExperimentState.FAILED

    def handle_exp_finished(self, data: Dict[str, Any]) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        logger.info(f"Experiment finished:{self.name}")
        if data["taskId"] == self.id:
            self.completed_at = time.time()
            if data["data"]["isTerminated"] == False:
                self.state = ExperimentState.COMPLETED
            else:
                self.state = ExperimentState.FAILED
            result = json.loads(data["data"]["parameters"]["result"])
            self.result.coordinate = result["coordinate"]
            self.result.matrix = {
                "real": result["real"],
                "imag": result["imag"]
            }
            self.result.module = result["module"]

    def get_status(self) -> str:
        """获取实验状态"""
        return self.state

    def get_result(self) -> Dict[str, Any]:
        """获取实验结果"""
        return {
            "id": self.id,
            "name": self.name,
            "createTime": self.created_at,
            "endTime": self.completed_at,
            "startTime": self.started_at,
            "state": self.state,
            "type": self.experiment_type,
            "extra": "",
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
