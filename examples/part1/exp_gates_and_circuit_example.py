from spinqlablink import SpinQLabLink, ExperimentType, Pulse, Gate, CustomGate, Circuit
from examples.toolsfunc import print_graph

def main():
    # Create connection
    spinqlablink = SpinQLabLink("192.168.9.121", 8181, "anyword", "anyword")
    spinqlablink.connect()

    if not spinqlablink.wait_for_login():
        print("Login failed")
        return

    exp_gates_and_circuit, exp_gates_and_circuit_para = spinqlablink.register_experiment(ExperimentType.QUANTUM_GATES_AND_CIRCUIT)

    using_pulse = True
    using_custom_gate = False
    using_custom_pps = False
    pps_json = '{"pulse":[{"amplitude":100.0,"detuning":0.0,"phase":0.0,"width":200.0}]}'
    Hlamda = 0.0
    Plamda = 0.0

    # Set other parameters
    exp_gates_and_circuit_para.samplePath = -1 # -1 for all channels, 0 for hydrogen channel, 1 for phosphorus channel
    exp_gates_and_circuit_para.using_pulse = using_pulse # True for using pulse, False for using gate

    if not using_pulse:
        exp_gates_and_circuit_para.using_custom_gate = using_custom_gate # True for using custom gate, False for using default gate
        exp_gates_and_circuit_para.using_custom_pps = using_custom_pps # True for using custom pps, False for using default pps
        if using_custom_pps:
            exp_gates_and_circuit_para.pps_json = pps_json # Custom pps json
            exp_gates_and_circuit_para.Hlamda = Hlamda # Hlamda,which is from exp_system_initialization
            exp_gates_and_circuit_para.Plamda = Plamda # Plamda,which is from exp_system_initialization

        circuit = Circuit(2) 
        if using_custom_gate: # using custom gate
            custom_file_json = '{"pulse":[{"amplitude":100.0,"detuning":0.0,"phase":0.0,"width":200.0}]}'
            custom_gate = CustomGate(type='I',customType='I_anyword',qubitIndex=0,gateJson=custom_file_json)
            circuit << custom_gate
            circuit.print_circuit()
        else: # using built-in gate
            circuit << Gate(type='H', qubitIndex=0)
            circuit << Gate(type='CNOT', qubitIndex=1, controlQubit=0)
            circuit.print_circuit()
        exp_gates_and_circuit_para.set_circuit(circuit)
    else: # using pulse
        exp_gates_and_circuit_para.pulses = [Pulse(path=0,phase=90,amplitude=100,width=40)]

    print(exp_gates_and_circuit.get_experiment_parameter())
    
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
