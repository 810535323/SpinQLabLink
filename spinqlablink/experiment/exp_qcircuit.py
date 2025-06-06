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
Quantum Control Experiment Module

Provides Quantum Control experiment functionality
"""

from typing import Dict, Any, List
import time
import json

from ..experiment.experiment_base import Experiment, ExperimentParameter, ExperimentResult, ExperimentState
from ..utils import LoggerManager
from ..utils.types import ExperimentType
from ..utils.pulse import Pulse
from ..utils.gate import Gate
from ..utils.circuit import Circuit
from pydantic import Field

# Create logger
logger = LoggerManager.get_logger(name='exp_qcircuit')

class ExpQCircuitResult(ExperimentResult):
    """Quantum Circuit Experiment Result Class"""
    def __init__(self):
        super().__init__()
        self.graph = []
        self.fidelity = 0
        self.matrix = {}
        self.module = []
    
    def append_graph(self, lines: Dict[str, Any]):
        """Append Line Graph"""
        self.graph.append(lines)

    def get_result(self) -> Dict[str, Any]:
        """Get experiment result"""
        return {
            "graph": self.graph,
            "fidelity": self.fidelity,
            "matrix": self.matrix,
            "module": self.module
        }

class ExpQCircuitParameters(ExperimentParameter):
    """Quantum Circuit Experiment Parameters Class"""
    pulses: List[Pulse] = Field(default=[], description="Pulse sequence")
    freq_h: float = Field(default=27.0, gt=0, lt=100, description="Hydrogen resonance frequency (MHz)")
    freq_p: float = Field(default=11.0, gt=0, lt=100, description="Phosphorus resonance frequency (MHz)")
    custom_freq: bool = Field(default=False, description="Whether to use custom frequency(h_freq or p_freq)")
    repeat: int = Field(default=0, ge=0, description="Repeat times")
    samplePath: int = Field(default=0, ge=-1, le=1, description="Sampling path selection: -1 for all channels, 0 for hydrogen channel, 1 for phosphorus channel")
    circuit: Circuit = None  # quantum circuit
    using_pulse: bool = Field(default=True, description="Whether to use pulse instead of gate")
    using_custom_gate: bool = Field(default=False, description="Whether to use custom gate")
    using_custom_pps: bool = Field(default=False, description="Whether to use custom pps file")
    pps_json: str = Field(default="", description="Custom pps file json")
    Hlamda: float = Field(default=0.0, description="Hlamda,which is from exp_system_initialization")
    Plamda: float = Field(default=0.0, description="Plamda,which is from exp_system_initialization")

    class Config:
        arbitrary_types_allowed = True

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
    
    def set_circuit(self, circuit: Circuit):
        self.circuit = circuit

    def get_parameters(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        para = {
            "using_pulse": self.using_pulse,
            "using_custom_gate": self.using_custom_gate,
            "using_custom_pps": self.using_custom_pps,
            "custom_freq": self.custom_freq,
            "freq_h": self.freq_h * 1000000,
            "freq_p": self.freq_p * 1000000,
            "repeat": self.repeat,
            "samplePath": self.samplePath
        }
        if self.using_custom_pps and self.pps_json == "":
            logger.warning("using custom pps but pps_json is empty!")
        if self.using_pulse:
            para["pulse"] = self._convert_pulse()
        else:
            para["circuit"] = self.circuit.to_dict()
        return para

class ExpQCircuit(Experiment):
    """Quantum Circuit Experiment Class"""
    
    def __init__(self, parameters: ExpQCircuitParameters):
        """
        Initialize Quantum System Initialization experiment
        
        Args:
            parameters: Quantum System Initialization experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = ExperimentType.QUANTUM_GATES_AND_CIRCUIT
        self.name = self.experiment_type + "-" + self.id[:8]
        self.result = ExpQCircuitResult()
        self.step_graph = {}
        self.extra = {}
        
        logger.info(f"Created Quantum System Initialization experiment: {self.name}")

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
            "params": json.dumps(self.parameters.get_parameters())
        }
        if self.parameters.using_custom_gate:
            circuit = self.parameters.circuit.to_dict()
            for gate in circuit:
                if "customType" in gate:
                    self.extra[gate["customType"] + ".spinq"] = gate["gateJson"]
        if self.parameters.using_custom_pps:
            self.extra["customized_pps.spinq"] = self.parameters.pps_json

        para["extra"] = json.dumps(self.extra)

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
        logger.debug(f"Experiment finished data:{data}")
        if data["taskId"] == self.id:
            self.completed_at = time.time()
            if data["data"]["isTerminated"] == False:
                self.state = ExperimentState.COMPLETED
            else:
                self.state = ExperimentState.FAILED
            parameters = data["data"]["parameters"]
            self.result.Hlamda = parameters["Hlamda"]
            self.result.Plamda = parameters["Plamda"]
            result = json.loads(parameters["result"])
            self.result.matrix = {
                "real": result["real"],
                "imag": result["imag"]
            }
            self.result.module = result["module"]
            self.result.fidelity = result["fidelity"]

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
            "type": self.experiment_type + "_CIRCUIT" if self.parameters.is_pulse else self.experiment_type + "_GATES",
            "extra": json.dumps(self.extra),
            "params": json.dumps(self.parameters.get_parameters()),
            "result": self.result.get_result()
        }
