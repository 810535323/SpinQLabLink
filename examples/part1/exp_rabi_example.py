from spinqlablink import SpinQLabLink, ExperimentType, Pulse

# Drawing charts
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
import time
from scipy.optimize import curve_fit

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

        exp_info = spinqlablink.get_experiment_result()
        width_real_map[width] = exp_info["result"]["real"]

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
    
    # Execute fitting and display results
    fit_results = fit_rabi_oscillations(x_data, y_data, plot)
    
    # Start Qt event loop
    app.exec_()

def fit_rabi_oscillations(x_data, y_data, plot):
    """
    Fit Rabi oscillation data with a sine function and display the results on the specified plot
    
    Parameters:
        x_data: List of pulse widths
        y_data: Corresponding experimental data
        plot: pyqtgraph Plot object to display the results
    
    Returns:
        Fitting parameters and results
    """
    # Draw experimental data points
    scatter = pg.ScatterPlotItem(x=x_data, y=y_data, pen=None, brush=pg.mkBrush(0, 0, 255, 200), size=10)
    plot.addItem(scatter)
    
    # Prepare fitting parameters
    max_sig = max(y_data)
    max_width_index = y_data.index(max_sig)
    max_width = x_data[max_width_index]
    
    # Sine fitting function A * sin(Ω * x)
    def sin_model(x, A, omega):
        return A * np.sin(omega * x)
    
    p0 = [max_sig, np.pi/(2*max_width)]
    
    # Execute fitting
    try:
        popt, pcov = curve_fit(sin_model, x_data, y_data, p0=p0)
        
        # Get fitting parameters
        A_fit, omega_fit = popt
        
        # Calculate fitting quality R²
        residuals = y_data - sin_model(np.array(x_data), *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_data - np.mean(y_data))**2)
        r = np.sqrt(1 - (ss_res / ss_tot))
        
        # Calculate π pulse width
        width_180 = np.pi / omega_fit
        
        # Generate fitting curve
        x_fit = np.linspace(min(x_data), max(max(x_data), width_180*2), 1000)
        y_fit = sin_model(x_fit, *popt)
        
        # Draw fitting curve
        fit_curve = pg.PlotCurveItem(x=x_fit, y=y_fit, pen=pg.mkPen('r', width=2))
        plot.addItem(fit_curve)
        
        # Add legend
        legend = plot.addLegend()
        legend.addItem(scatter, 'experimental data')
        legend.addItem(fit_curve, 'fitting curve')
        
        # Display fitting parameters
        text = pg.TextItem(text=f"A = {A_fit:.4f}\nΩ = {omega_fit*1000000/(2*np.pi):.4f} Hz\nR² = {r:.4f}\nπ/2 pulse width = {width_180/2:.2f} us", 
                          color=(0, 0, 0), anchor=(0, 0))
        text.setPos(min(x_data), max(y_data) * 0.5)
        plot.addItem(text)
        
        print("fitting parameters:")
        print(f"A = {A_fit:.4f}")
        print(f"fitting quality R² = {r:.4f}")
        print(f"π/2 pulse width = {width_180 / 2:.2f} us")
        
        return {
            "A": A_fit,
            "omega": omega_fit,
            "r_squared": r,
            "pi_half_width": width_180 / 2
        }
    
    except Exception as e:
        print(f"fitting error: {e}")
        return None

if __name__ == "__main__":
    main()
