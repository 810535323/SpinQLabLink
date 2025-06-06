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
量子电路类
"""
from typing import List, Tuple, Union, Dict, Any
from .gate import Gate

class Circuit():
    """
    量子电路类，用于构建和操作量子电路
    
    示例:
        from spinqlablink.utils.gate import H, X, CNOT
        from spinqlablink.utils.circuit import Circuit
        
        # 创建一个量子电路
        circuit = Circuit()
        qreg = circuit.allocateQubits(2)
        
        # 添加量子门
        circuit.append(H, [qreg[0]])
        circuit.append(CNOT, [qreg[0], qreg[1]])
        
        # 获取电路的JSON表示
        circuit_json = circuit.to_dict()
    """
    def __init__(self,qubits_num: int = 0) -> None:
        if qubits_num <= 0 or qubits_num > 2:
            raise ValueError("Invalid qubits number, must be 1 or 2")
        
        self.qubits_num = qubits_num
        self.circuit = []
        
    def __lshift__(self, gate: Gate):
        """使用 << 操作符添加量子门到电路"""
        self.append(gate)
        return self
        
    def append(self, gate: Gate):
        """
        添加量子门到电路
        
        Args:
            gate: 量子门
        """
        # 初始化当前时间槽为0
        current_timeslot = gate.timeslot
        
        # 检查每个时间槽是否已被占用
        while True:
            # 检查是否存在冲突
            conflict = False
            
            # 收集已占用的位置
            occupied_positions = set()
            for existing_gate in self.circuit:
                if existing_gate.timeslot == current_timeslot:
                    # 添加门作用的比特位置
                    occupied_positions.add(existing_gate.qubitIndex)
                    
                    # 添加控制比特位置（如果有）
                    if existing_gate.controlQubit >= 0:
                        occupied_positions.add(existing_gate.controlQubit)
                    
                    # 添加第二控制比特位置（如果有）
                    if existing_gate.controlQubit2 >= 0:
                        occupied_positions.add(existing_gate.controlQubit2)
            
            # 检查当前门是否与已占用位置冲突
            if gate.qubitIndex in occupied_positions:
                conflict = True
            elif gate.controlQubit >= 0 and gate.controlQubit in occupied_positions:
                conflict = True
            elif gate.controlQubit2 >= 0 and gate.controlQubit2 in occupied_positions:
                conflict = True
            
            # 如果没有冲突，使用当前时间槽
            if not conflict:
                gate.timeslot = current_timeslot
                break
            
            # 如果有冲突，尝试下一个时间槽
            current_timeslot += 1
        self.circuit.append(gate)

    def to_dict(self) -> dict:
        """
        将电路转换为字典表示
        
        Returns:
            dict: 电路的字典表示
        """
        circuit = []
        for gate in self.circuit:
            circuit.append(gate.to_dict())
        return circuit
    
    def print_circuit(self):
        """
        打印电路
        """
        """
        打印电路结构，按时间槽（timeslot）组织门操作
        """
        print("--------------------------------")
        
        # 按时间槽组织门
        gates_by_timeslot = {}
        for gate in self.circuit:
            timeslot = gate.timeslot
            if timeslot not in gates_by_timeslot:
                gates_by_timeslot[timeslot] = []
            gates_by_timeslot[timeslot].append(gate)
        
        
        # 按时间槽顺序打印
        for timeslot in sorted(gates_by_timeslot.keys()):
            gates = gates_by_timeslot[timeslot]
            gate_strs = []
            
            for gate in gates:
                gate_str = gate.type
                
                # 单量子比特门
                if gate.controlQubit < 0 and gate.controlQubit2 < 0:
                    gate_str += f"({gate.qubitIndex})"
                
                # 双量子比特门
                elif gate.controlQubit >= 0 and gate.controlQubit2 < 0:
                    gate_str += f"({gate.qubitIndex},{gate.controlQubit})"
                
                # 三量子比特门
                elif gate.controlQubit >= 0 and gate.controlQubit2 >= 0:
                    gate_str += f"({gate.qubitIndex},{gate.controlQubit},{gate.controlQubit2})"
                
                gate_strs.append(gate_str)
            
            print(f"TS {timeslot}: {' '.join(gate_strs)}")
        
        print("--------------------------------")