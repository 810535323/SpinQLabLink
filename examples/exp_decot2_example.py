from spinqlablink import SpinQLabLink
from utils.types import ExperimentType
from utils.pulse import Pulse

# Drawing charts
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
import numpy as np
from scipy.optimize import curve_fit

def main():
    # Create connection
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("Login failed")
        return
    
    width_mod_map = {}
    width_list = []
    
    for i in range(10):
        width_list.append(i * 500000)

    for width in width_list:
        _, exp_decot2_para = spinqlablink.register_experiment(ExperimentType.QUANTUM_DECOHERENCE_T2)

        # Set other parameters
        exp_decot2_para.freq_h = 37.852105  # Hydrogen resonance frequency (MHz)
        exp_decot2_para.freq_p = 15.322872  # Phosphorus resonance frequency (MHz)
        exp_decot2_para.makePps = True  # Generate PPS signal
        exp_decot2_para.samplePath = 0  # Sampling path: 0=Hydrogen channel, 1=Phosphorus channel
        exp_decot2_para.custom_freq = False  # Use custom frequency (true: use custom freq_h and freq_p, false: use device's lock field frequency)
        
        exp_decot2_para.pulses = [Pulse(path=0,width=40, amplitude=100, phase=90, detuning=0)
                                ,Pulse(path=0,width=width/2, amplitude=0, phase=0, detuning=0)
                                ,Pulse(path=0,width=80, amplitude=100, phase=90, detuning=0)
                                ,Pulse(path=0,width=width/2, amplitude=0, phase=0, detuning=0)]
        
        spinqlablink.run_experiment()
        print("Waiting for experiment completion")
        spinqlablink.wait_for_experiment_completion()

        result = spinqlablink.get_experiment_result()

        width_mod_map[width] = result["result"]["mod"]

        spinqlablink.deregister_experiment()
        
    spinqlablink.disconnect()

    print("width_mod_map: ", width_mod_map)
    # Convert data to format suitable for fitting
    x_data = list(width_mod_map.keys())
    y_data = list(width_mod_map.values())
    
    # Plot experiment results and fitting curve
    app = QtWidgets.QApplication([])
    win = pg.GraphicsLayoutWidget(show=True, title="Decoherence T2 Experiment Results")
    win.resize(800, 600)
    
    # Set background to white
    win.setBackground('w')
    
    # Add plot area
    plot = win.addPlot(title="Decoherence T2")
    plot.setLabel('left', 'Amplitude')
    plot.setLabel('bottom', 'Pulse Width (us)')
    
    # Execute fitting and display results
    fit_results = fit_decot2_oscillations(x_data, y_data, plot)
    
    # Start Qt event loop
    app.exec_()
    
def fit_decot2_oscillations(x_data, y_data, plot):
    """
    Fit Decoherence t2 oscillation data with a sine function and display the results on the specified plot
    
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
    
    # Decoherence T2 fitting function A * exp(- x / B)
    def t2_model(x, A, t2):
        return abs(A) * np.exp(- x / t2);
    
    p0 = [max_sig, 500000]
    
    # Execute fitting
    try:
        popt, pcov = curve_fit(t2_model, x_data, y_data, p0=p0)
        
        # Get fitting parameters
        A_fit, t2_fit = popt
        
        # Calculate fitting quality R²
        residuals = y_data - t2_model(np.array(x_data), *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_data - np.mean(y_data))**2)
        r = np.sqrt(1 - (ss_res / ss_tot))
        
        # Generate fitting curve
        x_fit = np.linspace(0, 3000000, 1000)
        y_fit = t2_model(x_fit, *popt)
        
        # Draw fitting curve
        fit_curve = pg.PlotCurveItem(x=x_fit, y=y_fit, pen=pg.mkPen('r', width=2))
        plot.addItem(fit_curve)
        
        # Add legend
        legend = plot.addLegend()
        legend.addItem(scatter, 'experimental data')
        legend.addItem(fit_curve, 'fitting curve')
        
        # Display fitting parameters
        text = pg.TextItem(text=f"A = {A_fit:.4f}\nt2 = {t2_fit:.4f}\nR = {r:.4f}", 
                          color=(0, 0, 0), anchor=(0, 0))
        text.setPos(min(x_data), max(y_data) * 0.5)
        plot.addItem(text)
        
        print("fitting parameters:")
        print(f"A = {A_fit:.4f}")
        print(f"t2 = {t2_fit:.4f}")
        print(f"fitting quality R = {r:.4f}")
        
        return {
            "A": A_fit,
            "t2": t2_fit,
            "r": r
        }
    
    except Exception as e:
        print(f"fitting error: {e}")
        return None


if __name__ == "__main__":
    main()
