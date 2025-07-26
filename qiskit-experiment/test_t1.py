#!/usr/bin/env python3
"""
T1 Relaxation Time Measurement for X Gate
Using Qiskit Experiments (latest version)

This script measures how long a qubit stays in the excited state |1⟩ 
after applying an X gate, which is the T1 relaxation time.
"""

from qiskit import QuantumCircuit
import sys
import os
# Add the qiskit-related directory to the path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'qiskit-related'))
from utils import get_local_aer_backend, get_least_busy_backend, get_simulator_backend
from qiskit_experiments.library import T1
from qiskit_experiments.framework import ParallelExperiment
import numpy as np
import matplotlib.pyplot as plt

def create_noisy_backend(t1_time=50e-6, gate_time=100e-9):
    """
    Create a noisy AerSimulator backend with T1 relaxation noise.
    
    Args:
        t1_time: T1 relaxation time in seconds (default: 50 microseconds)
        gate_time: Gate execution time in seconds (default: 100 nanoseconds)
    
    Returns:
        AerSimulator with thermal relaxation noise
    """
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, thermal_relaxation_error
    
    backend = AerSimulator()
    noise_model = NoiseModel()
    
    # Limit to 5 qubits for practical simulation
    n_qubits = min(5, backend.configuration().n_qubits)
    
    # T2 should be ≤ 2*T1, often T2 ≈ T1 for amplitude damping dominated systems
    t2_time = t1_time  # Conservative estimate
    
    for qubit in range(n_qubits):
        # Add thermal relaxation to all single-qubit gates
        thermal_error = thermal_relaxation_error(t1_time, t2_time, gate_time)
        
        # Apply to all single-qubit gates
        noise_model.add_quantum_error(thermal_error, ['id', 'x', 'y', 'z', 'h', 's', 't', 'sx', 'rz'], [qubit])
        
        # Add thermal relaxation specifically for delay gates
        # For delays, we use the actual delay duration
        # Note: This will be overridden per circuit by the actual delay duration
        noise_model.add_quantum_error(thermal_error, ['delay'], [qubit])
    
    backend.set_options(noise_model=noise_model)
    return backend


def select_backend(backend_type="local_noisy"):
    """
    Select and configure a backend for T1 experiments.
    
    Args:
        backend_type: Type of backend to use
            - "local_noisy": Local AerSimulator with T1 noise
            - "local_ideal": Local ideal AerSimulator  
            - "ibm_simulator": IBM Quantum simulator
            - "ibm_real": Least busy IBM Quantum device
    
    Returns:
        Configured backend
    """
    if backend_type == "local_noisy":
        print("Using local AerSimulator with T1 noise model...")
        return create_noisy_backend()
    
    elif backend_type == "local_ideal":
        print("Using local ideal AerSimulator...")
        return get_local_aer_backend(seed_simulator=42)
    
    elif backend_type == "ibm_simulator":
        print("Using IBM Quantum simulator...")
        try:
            return get_simulator_backend()
        except Exception as e:
            print(f"Failed to get IBM simulator, falling back to local: {e}")
            return get_local_aer_backend(seed_simulator=42)
    
    elif backend_type == "ibm_real":
        print("Using least busy IBM Quantum device...")
        try:
            return get_least_busy_backend()
        except Exception as e:
            print(f"Failed to get IBM real device, falling back to local: {e}")
            return create_noisy_backend()
    
    else:
        print(f"Unknown backend type '{backend_type}', using local noisy backend")
        return create_noisy_backend()


def main():
    print("="*60)
    print("T1 RELAXATION TIME MEASUREMENT")
    print("="*60)
    
    # Backend selection - you can change this
    backend_type = "local_noisy"  # Options: "local_noisy", "local_ideal", "ibm_simulator", "ibm_real"
    backend = select_backend(backend_type)
    
    # Expected T1 time (only relevant for noisy local backend)
    expected_t1 = 50e-6  # 50 microseconds
    
    print("Setting up T1 experiment...")
    
    # Create T1 experiment for qubit 0
    # The delays should be in seconds for the T1 experiment
    delays = np.linspace(0, 200e-6, 21)  # 0 to 200 microseconds, 21 points
    
    # Create T1 experiment - use delays in seconds directly
    t1_exp = T1(physical_qubits=[0], delays=delays)
    
    # Print experiment details
    print(f"Running T1 experiment on qubit 0")
    print(f"Backend: {backend.__class__.__name__}")
    print(f"Delays: {delays[0] * 1e6:.1f} μs (min) to {delays[-1] * 1e6:.1f} μs (max)")
    print(f"Number of delay points: {len(delays)}")
    if backend_type == "local_noisy":
        print(f"Expected T1: {expected_t1 * 1e6:.1f} μs")
    
    # Run the experiment
    print("\nRunning experiment...")
    exp_data = t1_exp.run(backend, shots=1000, seed_simulator=42)
    
    # Get the results
    results = exp_data.analysis_results()
    
    print("\n" + "="*50)
    print("T1 MEASUREMENT RESULTS")
    print("="*50)
    
    # Extract T1 value
    for result in results:
        if result.name == "T1":
            t1_measured = result.value  # T1 is already in seconds
            t1_stderr = result.extra.get('stderr', 0)
            print(f"Measured T1: {t1_measured * 1e6:.2f} ± {t1_stderr * 1e6:.2f} μs")
            if backend_type == "local_noisy":
                print(f"Expected T1: {expected_t1 * 1e6:.2f} μs")
                print(f"Relative error: {abs(t1_measured - expected_t1) / expected_t1 * 100:.1f}%")
            else:
                print(f"Backend type: {backend_type} (no expected value)")
    
    # Plot the results
    print("\nGenerating plot...")
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Use the built-in visualization
    try:
        # Try to use the experiment's built-in plotting
        fig = exp_data.figure(0)
        fig.show()
        print("Using built-in experiment visualization")
    except Exception as e:
        print(f"Built-in plotting failed: {e}")
        # Fallback to manual plotting
        try:
            data = exp_data.data()
            delays_us = [d * 1e6 for d in delays]  # Convert to microseconds
            
            # Extract measurement probabilities
            counts_list = []
            for datum in data:
                if hasattr(datum, 'counts'):
                    counts = datum.counts
                    total_shots = sum(counts.values())
                    prob_0 = counts.get('0', 0) / total_shots if total_shots > 0 else 0
                    counts_list.append(prob_0)
            
            if counts_list:
                ax.plot(delays_us, counts_list, 'bo-', label='Data')
                ax.set_xlabel('Delay (μs)')
                ax.set_ylabel('Population in |0⟩')
                ax.set_title(f'T1 Relaxation Time Measurement\nBackend: {backend.__class__.__name__}')
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                plt.tight_layout()
                plt.savefig('t1_measurement.png', dpi=300, bbox_inches='tight')
                print("Plot saved as 't1_measurement.png'")
            else:
                print("No data available for plotting")
        except Exception as e2:
            print(f"Manual plotting also failed: {e2}")
    
    # Save the plot
    plt.tight_layout()
    output_file = f'/Users/hsunwenfang/Documents/QuantumComputing/qiskit-experiment/t1_measurement_{backend_type}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved as 't1_measurement_{backend_type}.png'")
    
    # Display the fit equation
    print(f"\nFit equation: P(|1⟩) = A * exp(-t/T1) + B")
    print(f"where t is the delay time and T1 is the relaxation time")
    
    plt.show()
    
    print("\nExperiment completed successfully!")
    print(f"To run with different backends, change 'backend_type' in the script to:")
    print("  - 'local_noisy': Local simulator with T1 noise")
    print("  - 'local_ideal': Local ideal simulator")  
    print("  - 'ibm_simulator': IBM Quantum simulator")
    print("  - 'ibm_real': Real IBM Quantum device")

if __name__ == "__main__":
    main()
