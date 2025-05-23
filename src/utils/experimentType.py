"""
实验类型枚举结构体
"""
class ExperimentType:
    # 核磁共振
    NMR_PHENOMENON_AND_SIGNAL = "exp_nmr"
    # Rabi振荡实验
    RABI_OSCILLATIONS = "exp_rabi"
    # 量子比特控制实验
    QUANTUM_BIT = "exp_qbit"
    # 量子退相干实验
    QUANTUM_DECOHERENCE = "exp_qdeco"
    # 量子比特控制实验
    QUANTUM_CONTROL = "exp_qcontrol"
    # 量子系统初始化实验
    QUANTUM_SYSTEM_INITIALIZATION = "exp_sysinit"
    # 量子电路实验
    QUANTUM_GATES_AND_CIRCUIT = "exp_qcircuit"
    # 量子初态制备实验
    QUANTUM_STATE_TOMOGRAPHY = "exp_qtomography"
    # 量子计算任务实验
    QUANTUM_COMPUTING_TASK = "exp_qcomputetask"
