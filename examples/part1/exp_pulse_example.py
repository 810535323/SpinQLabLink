from spinqlablink import SpinQLabLink, ExperimentType, Pulse

from ..toolsfunc import print_graph

def main():
    # Create connection
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("Login failed")
        return
    
    # Register Pulse experiment
    _, exp_pulse_para = spinqlablink.register_experiment(ExperimentType.NMR_PHENOMENON_AND_SIGNAL)
    
    exp_pulse_para.pulses = [Pulse(path=0,width=40, amplitude=100, phase=90, detuning=0)]
    
    # Set other parameters
    exp_pulse_para.freq_h = 37.852105  # Hydrogen resonance frequency (MHz)
    exp_pulse_para.freq_p = 15.322872  # Phosphorus resonance frequency (MHz)
    exp_pulse_para.makePps = True  # Generate PPS signal
    exp_pulse_para.samplePath = 0  # Sampling path: 0=Hydrogen channel, 1=Phosphorus channel
    exp_pulse_para.custom_freq = False  # Use custom frequency (true: use custom freq_h and freq_p, false: use device's lock field frequency)
    
    spinqlablink.run_experiment()
    print("Waiting for experiment completion")
    spinqlablink.wait_for_experiment_completion()

    exp_info = spinqlablink.get_experiment_result()
    
    spinqlablink.disconnect()

    print_graph(exp_info["result"])

if __name__ == "__main__":
    main()
