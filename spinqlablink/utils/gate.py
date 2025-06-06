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
量子门类
"""
from pydantic import Field, BaseModel
from typing import List, ClassVar
from .pulse import Pulse
from abc import abstractmethod

class Gate(BaseModel):
    """
    量子门类，表示可以添加到量子电路的量子门
    """
    allowed_types: ClassVar[List[str]] = ['H','I','X','Y','Z','X90','Y90','Z90','Rx','Ry','Rz','T','Td','S','Sd','CNOT','CZ']
    
    angle : float = Field(default=0, description="The rotation angle of the gate (for rotation gates)")
    controlQubit : int = Field(default=-1, description="The control qubit (for controlled gates)")
    controlQubit2 : int = Field(default=-1, description="The second control qubit (for Toffoli gate)")
    delay : float = Field(default=0, description="The delay before the gate is applied")
    qubitIndex : int = Field(default=0, description="The index of the qubit that the gate operates on")
    timeslot : int = Field(default=0, description="The timeslot of the gate in the circuit")
    type : str = Field(default='X', description="The type of the gate (e.g., 'X', 'Y', 'Z', 'H', 'CNOT')")

    def __init__(self, type: str, **kwargs):
        super().__init__(**kwargs)
        if type not in self.allowed_types:
            raise ValueError(f"Gate type '{type}' not supported. Allowed types are {self.allowed_types}.")
        self.type = type

    class Config:
        arbitrary_types_allowed = True

    def to_dict(self) -> dict:
        """
        将门对象转换为字典
        """
        return {
            "angle": self.angle,
            "controlQubit": self.controlQubit,
            "controlQubit2": self.controlQubit2,
            "delay": self.delay,
            "qubitIndex": self.qubitIndex,
            "timeslot": self.timeslot,
            "type": self.type
        }
    
class CustomGate(Gate):
    customType: str = Field(default='custom', description="The type of the custom gate")
    gateJson: str = Field(default="", description="The json of the custom gate")

    def __init__(self, customType: str, gateJson: str, **kwargs):
        super().__init__(**kwargs)
        self.customType = customType
        self.gateJson = gateJson

    def to_dict(self) -> dict:
        gate_dict = super().to_dict()
        gate_dict['customType'] = self.customType
        gate_dict['gateJson'] = self.gateJson
        return gate_dict