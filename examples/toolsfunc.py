import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
from typing import List
from spinqlablink import Pulse

def print_graph(result):
    # Get chart data
    if "graph" in result:
        graph_data = result["graph"]
    else:
        print("No graph data found")
        return
    
    # Create application and window
    app = QtWidgets.QApplication([])
    
    # Create main window
    main_window = QtWidgets.QWidget()
    main_window.setWindowTitle("Experiment Signal Result")
    main_window.resize(1200, 700)
    
    # Create main layout
    main_layout = QtWidgets.QVBoxLayout()
    main_window.setLayout(main_layout)
    
    # Create control area
    control_layout = QtWidgets.QHBoxLayout()
    main_layout.addLayout(control_layout)
    
    # Create dropdown
    control_layout.addWidget(QtWidgets.QLabel("Select Step Data:"))
    step_selector = QtWidgets.QComboBox()
    control_layout.addWidget(step_selector)
    control_layout.addStretch()  # Add elastic space to left-align controls
    
    # Fill dropdown options
    for i in range(len(graph_data)):
        step_selector.addItem(f"Step {i+1}")
    
    # Create chart area
    plot_layout = QtWidgets.QVBoxLayout()
    main_layout.addLayout(plot_layout)
    
    # Create plotting window
    win = pg.GraphicsLayoutWidget()
    plot_layout.addWidget(win)
    
    # Set window background to white
    win.setBackground('w')

    
    # Add two plotting areas
    p1 = win.addPlot(title="FID Signal and Lorenz Fitting")
    win.nextRow()
    p2 = win.addPlot(title="FFT Spectrum")
    
    # Set plot area labels
    p1.setLabel('left', 'Amplitude')
    p1.setLabel('bottom', 'Time (ms) / Frequency (Hz)')
    # Set p1 to display grid
    p1.showGrid(x=True, y=True, alpha=0.2)
    p1.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
    p1.getAxis('left').setPen(pg.mkPen(color='k', width=1))
    p2.setLabel('left', 'Amplitude')
    p2.setLabel('bottom', 'Frequency (Hz)')
    # Set p2 to display grid
    p2.showGrid(x=True, y=True, alpha=0.2)
    p2.getAxis('bottom').setPen(pg.mkPen(color='k', width=1))
    p2.getAxis('left').setPen(pg.mkPen(color='k', width=1))
    
    # Add legend
    p1_legend = p1.addLegend()
    p2_legend = p2.addLegend()
    
    # Define function to update chart
    def update_plot(index):
        # Clear existing charts
        p1.clear()
        p2.clear()
        
        # Re-add legends
        p1_legend = p1.addLegend()
        p2_legend = p2.addLegend()
        
        # Get selected step data
        step_data = graph_data[index]
        
        # Extract different types of chart data
        fftRe, fftIm, fftMod, fftFit, fidRe, fidIm, fidMod, lorenz = [], [], [], [], [], [], [], []

        colors = {
            'fidRe': '#2557d5',     # Blue
            'fidIm': '#df265a',     # Red
            'fidMod': '#32325D',    # Green
            'lorenz': '#800000',    # Purple
            'fftRe': '#2557d5',     # Blue
            'fftIm': '#df265a',     # Red
            'fftMod': '#32325D',    # Green
            'fftFit': '#800000'     # Purple
        }
        
        for chart_name, points in step_data.items():
            if chart_name == "fftRe":
                fftRe = points
            elif chart_name == "fftIm":
                fftIm = points
            elif chart_name == "fftMod":
                fftMod = points
            elif chart_name == "fftFit":
                fftFit = points
            elif chart_name == "fidRe":
                fidRe = points
            elif chart_name == "fidIm":
                fidIm = points
            elif chart_name == "fidMod":
                fidMod = points
            elif chart_name == "lorenz":
                lorenz = points
        
        # Plot FID data and Lorenz fitting curve
        if fidRe:
            x_fid = np.array([point[0] for point in fidRe])
            y_fid_re = np.array([point[1] for point in fidRe])
            p1.plot(x_fid, y_fid_re, pen=pg.mkPen(color=colors['fidRe'], width=1), name='FID Real')
        
        if fidIm:
            x_fid = np.array([point[0] for point in fidIm])
            y_fid_im = np.array([point[1] for point in fidIm])
            p1.plot(x_fid, y_fid_im, pen=pg.mkPen(color=colors['fidIm'], width=1), name='FID Imaginary')
            
        if fidMod:
            x_fid = np.array([point[0] for point in fidMod])
            y_fid_mod = np.array([point[1] for point in fidMod])
            p1.plot(x_fid, y_fid_mod, pen=pg.mkPen(color=colors['fidMod'], width=1), name='FID Magnitude')
            
        if lorenz:
            x_lorenz = np.array([point[0] for point in lorenz])
            y_lorenz = np.array([point[1] for point in lorenz])
            p1.plot(x_lorenz, y_lorenz, pen=pg.mkPen(color=colors['lorenz'], width=1), name='Lorenz Fitting Curve')
        
        # Plot FFT data
        if fftRe:
            x_fft = np.array([point[0] for point in fftRe])
            y_fft_re = np.array([point[1] for point in fftRe])
            p2.plot(x_fft, y_fft_re, pen=pg.mkPen(color=colors['fftRe'], width=1), name='FFT Real')
        
        if fftIm:
            x_fft = np.array([point[0] for point in fftIm])
            y_fft_im = np.array([point[1] for point in fftIm])
            p2.plot(x_fft, y_fft_im, pen=pg.mkPen(color=colors['fftIm'], width=1), name='FFT Imaginary')
            
        if fftMod:
            x_fft = np.array([point[0] for point in fftMod])
            y_fft_mod = np.array([point[1] for point in fftMod])
            p2.plot(x_fft, y_fft_mod, pen=pg.mkPen(color=colors['fftMod'], width=1), name='FFT Magnitude')

        if fftFit:
            x_fft = np.array([point[0] for point in fftFit])
            y_fft_fit = np.array([point[1] for point in fftFit])
            p2.plot(x_fft, y_fft_fit, pen=pg.mkPen(color=colors['fftFit'], width=1), name='FFT Fitting Curve')

    # Connect dropdown signal to update function
    step_selector.currentIndexChanged.connect(update_plot)
    
    # If there is data, initialize chart
    if graph_data:
        update_plot(0)
    
    # Show main window
    main_window.show()
    
    print("Chart data plotting completed")
    app.exec_()

def parse_spinq_file(pulses: List[Pulse], file_path: str):
    try:
        with open(file_path, "r") as file:
            file_dict = file.read()
            
        # Parse pulse file content
        import json
        file_dict = json.loads(file_dict)
        pulses_dict = file_dict["pulse"]
        
        # Parse hydrogen channel pulses
        for pulse in pulses_dict["channel1_pulse"]:
            pulses.append(Pulse(
                path=0,  # Hydrogen channel
                width=pulse.get("width", 0),
                amplitude=pulse.get("amplitude", 0.0),
                phase=pulse.get("phase", 0.0),
                detuning=pulse.get("detuning", 0.0)
            ))
        
        # Parse phosphorus channel pulses
        for pulse in pulses_dict["channel2_pulse"]:
            pulses.append(Pulse(
                path=1,  # Phosphorus channel
                width=pulse.get("width", 0),
                amplitude=pulse.get("amplitude", 0.0),
                phase=pulse.get("phase", 0.0),
                detuning=pulse.get("detuning", 0.0)
            ))
    except FileNotFoundError:
        print(f"could not find pulse file: {file_path}")
    except json.JSONDecodeError:
        print("pulse file format error, could not parse JSON content")
    except Exception as e:
        print(f"error: {str(e)}")