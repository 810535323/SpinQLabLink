from src.spinqlablink import SpinQLabLink
from src.utils.types import ExperimentType

def main():
    # 创建连接
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("登录失败")
        return
    
    # 注册 NMR 实验
    nmr, nmr_para = spinqlablink.register_experiment(ExperimentType.NMR_PHENOMENON_AND_SIGNAL)
    
    # 设置磷脉冲序列
    import json
    nmr_para.set_pulse(json.dumps({"hpulse":{"width": 40, "amp": 100, "phase": 90, "detune": 0},
                                    "ppulse":{"width": 40, "amp": 0, "phase": 0, "detune": 0}}))
    
    # 设置其他参数
    nmr_para.freq_h = 27.551385  # 氢共振频率 (MHz)
    nmr_para.freq_p = 11.2  # 磷共振频率 (MHz)
    nmr_para.makePps = False  # 生成 PPS 信号
    nmr_para.samplePath = 0  # 采样路径：0=氢通道，1=磷通道
    nmr_para.custom_freq = True  # 使用自定义频率
    
    spinqlablink.run_experiment()
    print("等待实验完成")
    spinqlablink.wait_for_experiment_completion()

    result = spinqlablink.get_experiment_result()
    
    spinqlablink.disconnect()
    for key, value in result.items():
        if key != "graph":
            print(f"{key}: {value}")
    # 获取图表数据
    graph_data = result["graph"]
    
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
    # 绘制图表
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtWidgets
    import numpy as np
    
    # 创建应用和窗口
    app = QtWidgets.QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title="NMR 实验结果")
    win.resize(1200, 600)
    
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
