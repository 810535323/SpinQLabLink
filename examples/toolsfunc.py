import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
from typing import List
from spinqlablink import Pulse

def print_graph(result):
    # Get chart data
    graph_data = result["result"]["graph"]
    
    # Initialize data lists
    fftRe, fftIm, fftMod, fidRe, fidIm, fidMod, lorenz = [], [], [], [], [], [], []
    
    # Extract different types of chart data
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
    # Create application and window
    app = QtWidgets.QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title="NMR Result")
    win.resize(1200, 600)
    
    # Set background to white
    win.setBackground('w')
    
    # Add two plotting areas
    p1 = win.addPlot(title="FID Signal and Lorenz Fitting")
    win.nextRow()
    p2 = win.addPlot(title="FFT Spectrum")
    
    # Set labels for plotting areas
    p1.setLabel('left', 'Amplitude')
    p1.setLabel('bottom', 'Time (ms) / Frequency (Hz)')
    p2.setLabel('left', 'Amplitude')
    p2.setLabel('bottom', 'Frequency (Hz)')
    # Add legends
    p1_legend = p1.addLegend()
    p2_legend = p2.addLegend()
    
    # Plot FID data and Lorenz fitting curve
    if fidRe:
        x_fid = np.array([point[0] for point in fidRe])
        y_fid_re = np.array([point[1] for point in fidRe])
        p1.plot(x_fid, y_fid_re, pen='r', name='FID Real Part')
    
    if fidIm:
        x_fid = np.array([point[0] for point in fidIm])
        y_fid_im = np.array([point[1] for point in fidIm])
        p1.plot(x_fid, y_fid_im, pen='b', name='FID Imaginary Part')
        
    if fidMod:
        x_fid = np.array([point[0] for point in fidMod])
        y_fid_mod = np.array([point[1] for point in fidMod])
        p1.plot(x_fid, y_fid_mod, pen='g', name='FID Magnitude')
        
    if lorenz:
        x_lorenz = np.array([point[0] for point in lorenz])
        y_lorenz = np.array([point[1] for point in lorenz])
        p1.plot(x_lorenz, y_lorenz, pen='m', name='Lorenz Fitting Curve')
    
    # Plot FFT data
    if fftRe:
        x_fft = np.array([point[0] for point in fftRe])
        y_fft_re = np.array([point[1] for point in fftRe])
        p2.plot(x_fft, y_fft_re, pen='r', name='FFT Real Part')
    
    if fftIm:
        x_fft = np.array([point[0] for point in fftIm])
        y_fft_im = np.array([point[1] for point in fftIm])
        p2.plot(x_fft, y_fft_im, pen='b', name='FFT Imaginary Part')
        
    if fftMod:
        x_fft = np.array([point[0] for point in fftMod])
        y_fft_mod = np.array([point[1] for point in fftMod])
        p2.plot(x_fft, y_fft_mod, pen='g', name='FFT Magnitude')
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
        