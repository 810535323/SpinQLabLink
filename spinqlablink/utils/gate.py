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

class Gate(BaseModel):
    """
    The Gate class represents a quantum gate that can be added to a quantum circuit.
    """
    def __init__(self):
        # Allowed types of gates
        allowed_types = ['H','I','X','Y','Z','X90','Y90','Z90','Rx','Ry','Rz','T','Td','S','Sd','CNOT','CZ']
        
        angle : float = Field(default=0, description="The rotation angle of the gate (for rotation gates)")
        controlQubit : int = Field(default=-1, description="The control qubit (for controlled gates)")
        controlQubit2 : int = Field(default=-1, description="The second control qubit (for Toffoli gate)")
        delay : float = Field(default=0, description="The delay before the gate is applied")
        qubitIndex : int = Field(default=0, description="The index of the qubit that the gate operates on")
        timeslot : int = Field(default=0, description="The timeslot of the gate in the circuit")
        type : str = Field(default='X', description="The type of the gate (e.g., 'X', 'Y', 'Z', 'H', 'CNOT')")

        if type not in allowed_types:
            raise ValueError(f"Gate type '{type}' not supported. Allowed types are {allowed_types}.")
        