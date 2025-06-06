from spinqlablink import SpinQLabLink, ExperimentType, Pulse
from ..toolsfunc import print_graph

def main():
    # Create connection
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("Login failed")
        return

    _, exp_sysinit_para = spinqlablink.register_experiment(ExperimentType.QUANTUM_SYSTEM_INITIALIZATION)

    # Set other parameters
    exp_sysinit_para.repeat = 6

    exp_sysinit_para.pulses = [Pulse(path=0,phase=90,amplitude=100,width=40),
                                Pulse(path=0,phase=0,amplitude=0,width=718),
                                Pulse(path=0,phase=0,amplitude=100,width=40),
                                Pulse(path=0,phase=0,amplitude=0,width=718),
                                Pulse(path=0,phase=0,amplitude=0,width=40),
                                Pulse(path=0,phase=0,amplitude=0,width=300000),
                                Pulse(path=1,phase=0,amplitude=0,width=40),
                                Pulse(path=1,phase=0,amplitude=0,width=718),
                                Pulse(path=1,phase=90,amplitude=100,width=40),
                                Pulse(path=1,phase=0,amplitude=0,width=718),
                                Pulse(path=1,phase=0,amplitude=100,width=40),
                                Pulse(path=1,phase=0,amplitude=0,width=300000)]
    
    spinqlablink.run_experiment()
    print("Waiting for experiment completion")
    spinqlablink.wait_for_experiment_completion()

    exp_info = spinqlablink.get_experiment_result()

    spinqlablink.deregister_experiment()
        
    spinqlablink.disconnect()

    exp_result = exp_info["result"]
    for key, value in exp_result.items():
        if key != "graph":
            print(f"{key}: {value}")

    print_graph(exp_info["result"])

if __name__ == "__main__":
    main()
