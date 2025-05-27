"""
实验类型枚举结构体
"""
from enum import Enum, auto

class ExperimentType(Enum):
    # 核磁共振
    NMR_PHENOMENON_AND_SIGNAL = auto()
    # Rabi振荡实验
    RABI_OSCILLATIONS = auto()
    # 量子比特控制实验
    QUANTUM_BIT = auto()
    # 量子退相干实验
    QUANTUM_DECOHERENCE = auto()
    # 量子比特控制实验
    QUANTUM_CONTROL = auto()
    # 量子系统初始化实验
    QUANTUM_SYSTEM_INITIALIZATION = auto()
    # 量子电路实验
    QUANTUM_GATES_AND_CIRCUIT = auto()
    # 量子初态制备实验
    QUANTUM_STATE_TOMOGRAPHY = auto()
    # 量子计算任务实验
    QUANTUM_COMPUTING_TASK = auto()
