from typing import Dict, Any
from src.experiment.exp_nmr import EXP_NMR, EXP_NMR_PARAMETERS

def data_update_callback(data: Dict[str, Any]):
    print(data)

def status_update_callback(status: str):
    print(status)

def error_callback(error: str):
    print(error)

def finish_callback(result: Dict[str, Any]):
    print(result)

def main():
    # 创建NMR实验
    exp = EXP_NMR()
    # 设置脉冲序列
    exp_para = EXP_NMR_PARAMETERS()
    exp_para.set_pulse([{"width":40, "amp":100, "phase":90, "detune":0}], [{"width":40, "amp":100, "phase":90, "detune":0}])
    exp_para.set_h_freq(27.0) # mhz
    exp_para.set_p_freq(11.0) # mhz
    exp_para.set_makePps(False)
    exp_para.set_samplePath(0)
    exp.set_parameters(exp_para)
    # 设置回调函数
    exp.set_data_update_callback(data_update_callback)
    exp.set_status_update_callback(status_update_callback)
    exp.set_error_callback(error_callback)
    exp.set_finish_callback(finish_callback)
    # 启动实验
    if exp.start():
        # 等待实验结束
        exp.wait_for_finish()
        # 获取实验结果
        result = exp.get_result()
        print(result)
    else:
        print("实验启动失败")

if __name__ == "__main__":
    main()
