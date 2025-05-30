"""
实验类型枚举结构体
"""
class MachineType():
    # 消息类型定义
    MSG_REQ_USER_LOGIN = "c_user_login_req"  # 登录
    MSG_RES_USER_LOGIN = "s_user_login_res"  # 登录响应
    MSG_REQ_USER_LOGOUT = "c_user_logout_req"  # 登出
    MSG_RES_USER_LOGOUT = "s_user_logout_res"  # 登出响应

    MSG_RES_HEARTBEAT = "heartbeat_res"  # 心跳响应

    # 实验消息类型定义
    MSG_REQ_ADD_EXP_TASK_REQ = "c_add_exp_task_req"  # 实验运行
    MSG_RES_ADD_EXP_TASK_RES = "s_add_exp_task_res"  # 实验运行响应
    MSG_POST_EXP_TERMINATED = "s_terminate_exp_task_res"  # 实验终止响应
    MSG_POST_EXP_REMOVED = "s_post_exp_removed"  # 实验移除
    MSG_POST_EXP_STARTED = "s_post_exp_started"  # 实验开始
    MSG_POST_EXP_STEP_CHANGED = "s_post_exp_step_changed"  # 实验步骤改变
    MSG_POST_EXP_DATA_UPDATED = "s_post_exp_data_updated"  # 实验数据更新
    MSG_POST_EXP_CHART_UPDATED_STARTED = "s_post_exp_chart_updated_started"  # 实验图表更新开始
    MSG_POST_EXP_CHART_UPDATED = "s_post_exp_chart_updated"  # 实验图表更新
    MSG_POST_EXP_CHART_UPDATED_FINISHED = "s_post_exp_chart_updated_finished"  # 实验图表更新完成
    MSG_POST_EXP_FINISHED = "s_post_exp_finished"  # 实验任务完成

    # 设备主动消息
    MSG_POST_PARAM = "s_post_device_param"  # 设备参数
    MSG_POST_LOCK_DATA = "s_post_lock_data"  # 设备锁数据更新
    MSG_POST_INFO = "s_post_device_info"  # 设备信息
    MSG_POST_SAMPLE_CALIBRATION = "s_post_sample_calibration_data"  # 样品校准
    MSG_POST_EXP_QUEUE_UPDATE = "s_post_exp_queue_update"  # 实验队列更新


class ExperimentType():
    NMR_PHENOMENON_AND_SIGNAL = "EXP_PULSE"
    RABI_OSCILLATIONS = "EXP_RABI"
    QUANTUM_BIT = "EXP_QUBIT"
    QUANTUM_DECOHERENCE_T1 = "EXP_DECOT1"
    QUANTUM_DECOHERENCE_T2 = "EXP_DECOT2"
    QUANTUM_CONTROL = "EXP_QCONTROL"
    QUANTUM_SYSTEM_INITIALIZATION = "EXP_PSTATE"
    QUANTUM_GATES_AND_CIRCUIT_PULSE = "EXP_QCIRCUIT_PULSE"
    QUANTUM_GATES_AND_CIRCUIT_CIRCUIT = "EXP_QCIRCUIT_CIRCUIT"
    QUANTUM_STATE_TOMOGRAPHY = "EXP_QREFACTOR"
    QUANTUM_COMPUTING_TASK = "EXP_QALGORITHM"
    
    INTRODUCTION_TO_QUANTUM_COMPUTING = "EXP_QALGORITHM_BASIC"
    DEUTSCH_ALGORITHM = "EXP_DEUTSCH"
    BERNSTEIN_VARIRANI_ALGORITHM = "EXP_BERNSTEIN"
    GROVER_ALGORITHM = "EXP_GROVER"
    QFT_ALGORITHM = "EXP_QFT"
    HHL_ALGORITHM = "EXP_HHL"
    VQE_ALGORITHM = "EXP_VQE"
    QAOA_ALGORITHM = "EXP_QAOA"

    SPIN_ECHO = "EXP_SPINECHO"
    DYNAMIC_DECOUPLING = "EXP_DYDECO"
    SHAPE_PULSE = "EXP_SHAPEPULSE"
    NUMERICAL_OPTIMIZATION_PULSE = "EXP_NPOPTI"

    PHYSICAL_LAYER_EXPERIMENT = "EXP_LAYER_PHYSICAL"
    CIRCUIT_LAYER_EXPERIMENT_PULSE = "EXP_LAYER_CIRCUIT_PULSE"
    CIRCUIT_LAYER_EXPERIMENT_CIRCUIT = "EXP_LAYER_CIRCUIT_CIRCUIT"
    
class ExperimentState():
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"