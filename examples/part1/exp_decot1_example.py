from spinqlablink import SpinQLabLink, ExperimentType, Pulse

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
    
    width_real_map = {}
    width_list = []
    
    for i in range(5):
        width_list.append(i * 100000)

    for width in width_list:
        _, exp_decot1_para = spinqlablink.register_experiment(ExperimentType.QUANTUM_DECOHERENCE_T1)

        # Set other parameters
        exp_decot1_para.samplePath = 0  # Sampling path: 0=Hydrogen channel, 1=Phosphorus channel
        
        exp_decot1_para.pulses = [Pulse(path=0,width=80, amplitude=100, phase=90, detuning=0)
                                ,Pulse(path=0,width=width, amplitude=0, phase=0, detuning=0)
                                ,Pulse(path=0,width=40, amplitude=100, phase=90, detuning=0)]
            
        spinqlablink.run_experiment()
        print("Waiting for experiment completion")
        spinqlablink.wait_for_experiment_completion()

        exp_info = spinqlablink.get_experiment_result()

        width_real_map[width] = exp_info["result"]["real"]

        spinqlablink.deregister_experiment()
        
    spinqlablink.disconnect()

    print("width_real_map: ", width_real_map)
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
    plot = win.addPlot(title="Decoherence T1")
    plot.setLabel('left', 'Amplitude')
    plot.setLabel('bottom', 'Pulse Width (us)')
    
    # Execute fitting and display results
    fit_results = fit_decot1_oscillations(x_data, y_data, plot)
    
    # Start Qt event loop
    app.exec_()
    
def fit_decot1_oscillations(x_data, y_data, plot):
    """
    Fit Decoherence T1 oscillation data with a sine function and display the results on the specified plot
    
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
    min_sig = min(y_data)
    
    # Decoherence T1 fitting function A * sin(Ω * x)
    def t1_model(x, A, t1):
        return A + (np.abs(A) - A) * (1 - np.exp(-x / t1));
    
    p0 = [min_sig, 5000000]
    
    # Execute fitting
    try:
        popt, pcov = curve_fit(t1_model, x_data, y_data, p0=p0)
        
        # Get fitting parameters
        A_fit, t1_fit = popt
        
        # Calculate fitting quality R²
        residuals = y_data - t1_model(np.array(x_data), *popt)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_data - np.mean(y_data))**2)
        r = np.sqrt(1 - (ss_res / ss_tot))
        
        # Generate fitting curve
        x_fit = np.linspace(0, 20000000, 5000)
        y_fit = t1_model(x_fit, *popt)
        
        # Draw fitting curve
        fit_curve = pg.PlotCurveItem(x=x_fit, y=y_fit, pen=pg.mkPen('r', width=2))
        plot.addItem(fit_curve)
        
        # Add legend
        legend = plot.addLegend()
        legend.addItem(scatter, 'experimental data')
        legend.addItem(fit_curve, 'fitting curve')
        
        # Display fitting parameters
        text = pg.TextItem(text=f"A = {A_fit:.4f}\nt1 = {t1_fit:.4f}\nR = {r:.4f}", 
                          color=(0, 0, 0), anchor=(0, 0))
        text.setPos(min(x_data), max(y_data) * 0.5)
        plot.addItem(text)
        
        print("fitting parameters:")
        print(f"A = {A_fit:.4f}")
        print(f"t1 = {t1_fit:.4f}")
        print(f"fitting quality R = {r:.4f}")
        
        return {
            "A": A_fit,
            "t1": t1_fit,
            "r": r
        }
    
    except Exception as e:
        print(f"fitting error: {e}")
        return None


if __name__ == "__main__":
    main()
