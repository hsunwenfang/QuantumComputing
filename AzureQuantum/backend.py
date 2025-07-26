from azure.quantum import Workspace
from azure.quantum.qiskit import AzureQuantumProvider
import sys
import os
# Add the qiskit-related directory to the path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'qiskit-related'))
from utils import get_local_aer_backend
from qiskit.circuit.random import random_circuit
import numpy as np
from qiskit import transpile
from qiskit.circuit import QuantumCircuit

def get_available_backends_info(provider):
    """Print information about all available Azure Quantum backends."""
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


def compute_ideal_distribution(qc, num_qubits, seed=42):
    """
    Compute the ideal (noiseless) output distribution for a quantum circuit.
    
    Args:
        qc: Quantum circuit with measurements
        num_qubits: Number of qubits in the circuit
        seed: Random seed for the simulator
    
    Returns:
        dict: Ideal probability distribution {bitstring: probability}
    """
    # Prepare ideal (noiseless) simulation circuit (remove all measurements and classical registers)
    qc_ideal = qc.remove_final_measurements(inplace=False)
    qc_ideal_no_meas = QuantumCircuit(qc_ideal.num_qubits)
    for instr in qc_ideal.data:
        if instr.operation.name != "measure":
            qc_ideal_no_meas.append(instr.operation, instr.qubits, instr.clbits)

    # Use the local AerSimulator from utils for ideal simulation
    sim_backend = get_local_aer_backend(seed)
    
    # Transpile the circuit for the simulator
    qc_ideal_t = transpile(qc_ideal_no_meas, sim_backend)
    
    # Run the simulation
    result = sim_backend.run(qc_ideal_t).result()
    psi = result.get_statevector(0)  # Specify experiment index 0
    probs_ideal = np.abs(psi) ** 2
    bitstrings = [format(i, f"0{num_qubits}b") for i in range(2 ** num_qubits)]
    ideal_probs_dict = {b: probs_ideal[i] for i, b in enumerate(bitstrings)}
    
    return ideal_probs_dict


def compute_xeb_score(exp_probs_dict, ideal_probs_dict, bitstrings):
    """
    Compute the Cross-Entropy Benchmarking (XEB) score.
    
    Args:
        exp_probs_dict: Experimental probability distribution
        ideal_probs_dict: Ideal probability distribution
        bitstrings: List of all possible bitstrings
    
    Returns:
        float: XEB score
    """
    # XEB = sum_x p_exp(x) * p_ideal(x)
    xeb = sum(exp_probs_dict.get(b, 0) * ideal_probs_dict.get(b, 0) for b in bitstrings)
    return xeb


def run_xeb_on_backend(qc, backend_name, provider, ideal_probs_dict, bitstrings, shots=1024):
    """
    Run XEB experiment on a specific backend.
    
    Args:
        qc: Quantum circuit to run
        backend_name: Name of the backend
        provider: Azure Quantum provider
        ideal_probs_dict: Ideal probability distribution
        bitstrings: List of all possible bitstrings
        shots: Number of shots for the experiment
    
    Returns:
        tuple: (xeb_score, exp_probs_dict) or (None, None) if failed
    """
    try:
        print(f"Running on backend: {backend_name}")
        job = provider.get_backend(backend_name).run(qc, shots=shots)
        result = job.result()
        counts_exp = result.get_counts()
        total_counts = sum(counts_exp.values())
        exp_probs_dict = {k: v / total_counts for k, v in counts_exp.items()}
        
        xeb = compute_xeb_score(exp_probs_dict, ideal_probs_dict, bitstrings)
        
        print(f"  XEB (Linear Cross-Entropy Benchmarking) score: {xeb:.4f}")
        print(f"  Top measured bitstrings:")
        for k, v in sorted(exp_probs_dict.items(), key=lambda x: -x[1])[:5]:
            print(f"    {k}: {v:.4f}")
        
        return xeb, exp_probs_dict
        
    except Exception as e:
        print(f"  Failed on backend {backend_name}: {e}")
        return None, None


if __name__ == "__main__":
    # Set up your Azure Quantum workspace details
    resource_id = "/subscriptions/e4420dbb-ea34-41cf-b047-230c73836759/resourceGroups/AzureQuantum/providers/Microsoft.Quantum/Workspaces/hsunq"
    location = "japaneast"

    # Connect to the Azure Quantum workspace
    workspace = Workspace(resource_id=resource_id, location=location)
    provider = AzureQuantumProvider(workspace=workspace)

    # Uncomment to see available backends
    # get_available_backends_info(provider)

    # Parameters for XEB
    num_qubits = 5
    circuit_depth = 10
    shots = 1024
    seed = 42

    print("="*60)
    print("CROSS-ENTROPY BENCHMARKING (XEB) ON AZURE QUANTUM")
    print("="*60)

    # Generate a random circuit (measured)
    qc = random_circuit(num_qubits, circuit_depth, max_operands=3, measure=True, seed=seed)
    print(f"\nGenerated random circuit:")
    print(f"  Qubits: {num_qubits}")
    print(f"  Depth: {circuit_depth}")
    print(f"  Seed: {seed}")

    # Compute ideal distribution using utils
    print("\nComputing ideal (noiseless) distribution...")
    ideal_probs_dict = compute_ideal_distribution(qc, num_qubits, seed)
    bitstrings = [format(i, f"0{num_qubits}b") for i in range(2 ** num_qubits)]
    
    print(f"Top ideal bitstrings:")
    for k, v in sorted(ideal_probs_dict.items(), key=lambda x: -x[1])[:5]:
        print(f"  {k}: {v:.4f}")

    # Run XEB on all available backends
    print(f"\nPerforming XEB on all available backends (shots={shots}):\n")
    
    xeb_results = {}
    for backend in provider.backends():
        backend_name = backend.name()
        xeb_score, exp_probs = run_xeb_on_backend(
            qc, backend_name, provider, ideal_probs_dict, bitstrings, shots
        )
        if xeb_score is not None:
            xeb_results[backend_name] = xeb_score
        print("-" * 40)

    # Summary of results
    print("\n" + "="*60)
    print("XEB RESULTS SUMMARY")
    print("="*60)
    
    if xeb_results:
        # Sort backends by XEB score (higher is better)
        sorted_results = sorted(xeb_results.items(), key=lambda x: -x[1])
        
        print("Backend Rankings (by XEB score, higher is better):")
        for i, (backend_name, xeb_score) in enumerate(sorted_results, 1):
            print(f"{i:2d}. {backend_name:25s} XEB: {xeb_score:.4f}")
        
        print(f"\nBest performing backend: {sorted_results[0][0]} (XEB: {sorted_results[0][1]:.4f})")
        print(f"Worst performing backend: {sorted_results[-1][0]} (XEB: {sorted_results[-1][1]:.4f})")
    else:
        print("No successful XEB measurements obtained.")
    
    print("\nXEB Analysis complete!")