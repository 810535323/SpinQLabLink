from spinqlablink import SpinQLabLink
from utils.types import ExperimentType
from utils.pulse import Pulse

# Drawing charts
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
import time

def main():
    # Create connection
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("Login failed")
        return
    
    width_real_map = {}
    width_list = []
    # Register NMR experiment
    for i in range(10):
        width_list.append(i * 40)

    for width in width_list:
        _, exp_pulse_para = spinqlablink.register_experiment(ExperimentType.RABI_OSCILLATIONS)

        # Set other parameters
        exp_pulse_para.freq_h = 37.852105  # Hydrogen resonance frequency (MHz)
        exp_pulse_para.freq_p = 15.322872  # Phosphorus resonance frequency (MHz)
        exp_pulse_para.makePps = True  # Generate PPS signal
        exp_pulse_para.samplePath = 0  # Sampling path: 0=Hydrogen channel, 1=Phosphorus channel
        exp_pulse_para.custom_freq = False  # Use custom frequency (true: use custom freq_h and freq_p, false: use device's lock field frequency)
        
        exp_pulse_para.pulses = [Pulse(path=0,width=width, amplitude=100, phase=90, detuning=0)]
            
        spinqlablink.run_experiment()
        print("Waiting for experiment completion")
        spinqlablink.wait_for_experiment_completion()

        result = spinqlablink.get_experiment_result()
        width_real_map[width] = result["result"]["real"]

        time.sleep(10)
        
        spinqlablink.deregister_experiment()
        
    spinqlablink.disconnect()

    # Convert data to format suitable for fitting
    x_data = list(width_real_map.keys())
    y_data = list(width_real_map.values())
    
    # Plot experiment results and fitting curve
    app = QtWidgets.QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title="Rabi Oscillation Experiment Results")
    win.resize(800, 600)
    
    # Set background to white
    win.setBackground('w')
    
    # Add plot area
    plot = win.addPlot(title="Rabi Oscillations")
    plot.setLabel('left', 'Amplitude')
    plot.setLabel('bottom', 'Pulse Width (ns)')
    
    # Plot experimental data points
    scatter = pg.ScatterPlotItem(x=x_data, y=y_data, pen=None, brush=pg.mkBrush(0, 0, 255, 200), size=10)
    plot.addItem(scatter)
    
    # Prepare fitting parameters
    max_sig = max(y_data)
    max_width_index = y_data.index(max_sig)
    max_width = x_data[max_width_index]
    
    # Simple sine fitting, simulating the provided C++ code
    import numpy as np
    from scipy.optimize import curve_fit
    
    # Sine fitting function A * sin(Ω * x + φ)
    def sin_model(x, A, omega, phi):
        return A * np.sin(omega * x + phi)
    
    p0 = [max_sig, np.pi/(2*max_width), 0]
    
    # Perform fitting
    try:
        popt, pcov = curve_fit(sin_model, x_data, y_data, p0=p0)
        
        # Get fitting parameters
        A_fit, omega_fit, phi_fit = popt
        
        # Calculate fit quality R²
        residuals = y_data - sin_model(np.array(x_data), *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_data - np.mean(y_data))**2)
        r = np.sqrt(1 - (ss_res / ss_tot))
        
        # Calculate π pulse width
        width_180 = np.pi / omega_fit
        
        # Generate fitting curve
        x_fit = np.linspace(min(x_data), max(max(x_data), width_180*2), 1000)
        y_fit = sin_model(x_fit, *popt)
        
        # Plot fitting curve
        fit_curve = pg.PlotCurveItem(x=x_fit, y=y_fit, pen=pg.mkPen('r', width=2))
        plot.addItem(fit_curve)
        
        # Add legend
        legend = plot.addLegend()
        legend.addItem(scatter, 'Experimental Data')
        legend.addItem(fit_curve, 'Fitting Curve')
        
        # Display fitting parameters
        text = pg.TextItem(text=f"A = {A_fit:.4f}\nΩ = {omega_fit*1000000/(2*np.pi):.4f} Hz\nR² = {r:.4f}\nπ/2 pulse width = {width_180/2:.2f} us", 
                          color=(0, 0, 0), anchor=(0, 0))
        text.setPos(min(x_data), max(y_data) * 0.5)
        plot.addItem(text)
        
        print("Fitting parameters:")
        print(f"A = {A_fit:.4f}")
        print(f"Fit quality R² = {r:.4f}")
        print(f"π/2 pulse width = {width_180 / 2:.2f} us")
    
    except Exception as e:
        print(f"Fitting failed: {e}")
    
    # Start Qt event loop
    app.exec_()

if __name__ == "__main__":
    main()
