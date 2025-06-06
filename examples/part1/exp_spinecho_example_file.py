from spinqlablink import SpinQLabLink, ExperimentType

from ..toolsfunc import print_graph, parse_spinq_file
def main():
    # Create connection
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("Login failed")
        return
    
    # Register spinecho experiment
    _, exp_pulse_para = spinqlablink.register_experiment(ExperimentType.SPIN_ECHO)
    
    parse_spinq_file(exp_pulse_para.pulses,"./examples/lab_file.spinq")

    # Set other parameters
    exp_pulse_para.sampleCount = 16000  # Sample count
    exp_pulse_para.sampleFre = 10000  # Sample frequency
    exp_pulse_para.sampleDelay = 0  # Sample delay
    exp_pulse_para.h_freShift = 0  # Hydrogen frequency shift
    exp_pulse_para.p_freShift = 0  # Phosphorus frequency shift
    exp_pulse_para.h_freDemo = 0  # Hydrogen frequency demo
    exp_pulse_para.p_freDemo = 0  # Phosphorus frequency demo
    exp_pulse_para.samplePath = 0  # Sampling path: 0=Hydrogen channel, 1=Phosphorus channel

    spinqlablink.run_experiment()
    print("Waiting for experiment completion")
    spinqlablink.wait_for_experiment_completion()

    exp_info = spinqlablink.get_experiment_result()
    
    spinqlablink.disconnect()

    print_graph(exp_info["result"])

if __name__ == "__main__":
    main()
