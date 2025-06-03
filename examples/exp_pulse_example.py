from spinqlablink import SpinQLabLink
from utils.types import ExperimentType
from utils.pulse import Pulse

# 绘制图表
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np

def main():
    # 创建连接
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("登录失败")
        return
    
    # 注册 NMR 实验
    _, exp_pulse_para = spinqlablink.register_experiment(ExperimentType.NMR_PHENOMENON_AND_SIGNAL)
    
    exp_pulse_para.pulses = [Pulse(path=0,width=40, amplitude=100, phase=90, detuning=0)]
    
    # 设置其他参数
    exp_pulse_para.freq_h = 37.852105  # 氢共振频率 (MHz)
    exp_pulse_para.freq_p = 15.322872  # 磷共振频率 (MHz)
    exp_pulse_para.makePps = True  # 生成 PPS 信号
    exp_pulse_para.samplePath = 0  # 采样路径：0=氢通道，1=磷通道
    exp_pulse_para.custom_freq = False  # 使用自定义频率(true:使用自定义频率freq_h和freq_p,false:采用设备锁场的频率)
    
    spinqlablink.run_experiment()
    print("等待实验完成")
    spinqlablink.wait_for_experiment_completion()

    result = spinqlablink.get_experiment_result()
    
    spinqlablink.disconnect()

    print_graph(result)

def print_graph(result):
    # 获取图表数据
    graph_data = result["result"]["graph"]
    
    # 初始化数据列表
    fftRe, fftIm, fftMod, fidRe, fidIm, fidMod, lorenz = [], [], [], [], [], [], []
    
    # 提取各类图表数据
    for step_data in graph_data:
        for chart_name, points in step_data.items():
            if chart_name == "fftRe":
                fftRe = points
            elif chart_name == "fftIm":
                fftIm = points
            elif chart_name == "fftMod":
                fftMod = points
            elif chart_name == "fidRe":
                fidRe = points
            elif chart_name == "fidIm":
                fidIm = points
            elif chart_name == "fidMod":
                fidMod = points
            elif chart_name == "lorenz":
                lorenz = points
    # 创建应用和窗口
    app = QtWidgets.QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title="NMR 实验结果")
    win.resize(1200, 600)
    
    # 设置背景为白色
    win.setBackground('w')
    
    # 添加两个绘图区域
    p1 = win.addPlot(title="FID 信号和 Lorenz 拟合")
    win.nextRow()
    p2 = win.addPlot(title="FFT 频谱")
    
    # 设置绘图区域的标签
    p1.setLabel('left', '幅度')
    p1.setLabel('bottom', '时间 (ms) / 频率 (Hz)')
    p2.setLabel('left', '幅度')
    p2.setLabel('bottom', '频率 (Hz)')
    
    # 添加图例
    p1_legend = p1.addLegend()
    p2_legend = p2.addLegend()
    
    # 绘制 FID 数据和 Lorenz 拟合曲线
    if fidRe:
        x_fid = np.array([point[0] for point in fidRe])
        y_fid_re = np.array([point[1] for point in fidRe])
        p1.plot(x_fid, y_fid_re, pen='r', name='FID 实部')
    
    if fidIm:
        x_fid = np.array([point[0] for point in fidIm])
        y_fid_im = np.array([point[1] for point in fidIm])
        p1.plot(x_fid, y_fid_im, pen='b', name='FID 虚部')
        
    if fidMod:
        x_fid = np.array([point[0] for point in fidMod])
        y_fid_mod = np.array([point[1] for point in fidMod])
        p1.plot(x_fid, y_fid_mod, pen='g', name='FID 幅值')
        
    if lorenz:
        x_lorenz = np.array([point[0] for point in lorenz])
        y_lorenz = np.array([point[1] for point in lorenz])
        p1.plot(x_lorenz, y_lorenz, pen='m', name='Lorenz 拟合曲线')
    
    # 绘制 FFT 数据
    if fftRe:
        x_fft = np.array([point[0] for point in fftRe])
        y_fft_re = np.array([point[1] for point in fftRe])
        p2.plot(x_fft, y_fft_re, pen='r', name='FFT 实部')
    
    if fftIm:
        x_fft = np.array([point[0] for point in fftIm])
        y_fft_im = np.array([point[1] for point in fftIm])
        p2.plot(x_fft, y_fft_im, pen='b', name='FFT 虚部')
        
    if fftMod:
        x_fft = np.array([point[0] for point in fftMod])
        y_fft_mod = np.array([point[1] for point in fftMod])
        p2.plot(x_fft, y_fft_mod, pen='g', name='FFT 幅值')
    print("图表数据已绘制完成")
    app.exec_()

if __name__ == "__main__":
    main()
