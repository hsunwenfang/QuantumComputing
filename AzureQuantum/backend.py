from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
# from qiskit import Aer, execute
from qiskit_aer import AerSimulator
from qiskit.circuit.random import random_circuit
import numpy as np
from qiskit import transpile
from qiskit.circuit import QuantumCircuit

def get_available_backends_info(provider):
    print("Available Azure Quantum backends and their status:\n")
    for backend in provider.backends():
        backend_name = backend.name()
        config = backend.configuration()
        print(f"Backend: {backend_name}")
        print(f"  Simulator: {getattr(config, 'simulator', None)}")
        print(f"  Number of qubits: {getattr(config, 'num_qubits', None)}")
        print(f"  Basis gates: {getattr(config, 'basis_gates', None)}")
        print(f"  Online: {getattr(config, 'online_date', None)}")
        print(f"  Version: {getattr(config, 'version', None)}")
        print(f"  Noise model: {getattr(config, 'noise', None)}")
        print("-" * 40)


if __name__ == "__main__":

    # Set up your Azure Quantum workspace details
    resource_id = "/subscriptions/e4420dbb-ea34-41cf-b047-230c73836759/resourceGroups/AzureQuantum/providers/Microsoft.Quantum/Workspaces/hsunq"
    location = "japaneast"

    # Connect to the Azure Quantum workspace
    workspace = Workspace(resource_id=resource_id, location=location)
    provider = AzureQuantumProvider(workspace=workspace)

    # get_available_backends_info(provider)

    # Parameters for XEB
    num_qubits = 5
    circuit_depth = 10
    shots = 1024
    seed = 42

    # Generate a random circuit (measured)
    qc = random_circuit(num_qubits, circuit_depth, max_operands=3, measure=True, seed=seed)
    print("\nRandom circuit for XEB:")
    # this will print the circuit in text format
    # print(qc)

    # Prepare ideal (noiseless) simulation circuit (remove all measurements and classical registers)
    qc_ideal = qc.remove_final_measurements(inplace=False)
    qc_ideal_no_meas = QuantumCircuit(qc_ideal.num_qubits)
    for instr in qc_ideal.data:
        if instr.operation.name != "measure":
            qc_ideal_no_meas.append(instr.operation, instr.qubits, instr.clbits)

    sim_backend = AerSimulator(method="statevector")
    # Transpile the circuit for the simulator
    qc_ideal_t = transpile(qc_ideal_no_meas, sim_backend)
    # Run the simulation
    result = sim_backend.run(qc_ideal_t).result()

    print(result.__dict__)


    psi = result.get_statevector(0)  # Specify experiment index 0
    probs_ideal = np.abs(psi) ** 2
    bitstrings = [format(i, f"0{num_qubits}b") for i in range(2 ** num_qubits)]
    ideal_probs_dict = {b: probs_ideal[i] for i, b in enumerate(bitstrings)}

    print("\nPerforming XEB on all available backends:\n")
    for backend in provider.backends():
        backend_name = backend.name()
        try:
            print(f"Running on backend: {backend_name}")
            job = provider.get_backend(backend_name).run(qc, shots=shots)
            result = job.result()
            counts_exp = result.get_counts()
            total_counts = sum(counts_exp.values())
            exp_probs_dict = {k: v / total_counts for k, v in counts_exp.items()}
            # XEB = sum_x p_exp(x) * p_ideal(x)
            xeb = sum(exp_probs_dict.get(b, 0) * ideal_probs_dict.get(b, 0) for b in bitstrings)
            print(f"  XEB (Linear Cross-Entropy Benchmarking) score: {xeb:.4f}")
            print(f"  Top measured bitstrings:")
            for k, v in sorted(exp_probs_dict.items(), key=lambda x: -x[1])[:5]:
                print(f"    {k}: {v:.4f}")
        except Exception as e:
            print(f"  Failed on backend {backend_name}: {e}")
        print("-" * 40)