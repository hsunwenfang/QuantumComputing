#!/usr/bin/env python3
"""
Simple T1 relaxation time measurement using qiskit-experiments.

This script creates a clean implementation that works reliably with
the qiskit-experiments framework.
"""

import sys
sys.path.append('../qiskit-related')

from utils import get_local_aer_backend, get_least_busy_backend, get_simulator_backend
from qiskit_experiments.library import T1
import numpy as np
import matplotlib.pyplot as plt

def create_thermal_noise_backend(t1_time=50e-6):
    """
    Create a backend with thermal relaxation noise using a more direct approach.
    """
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, thermal_relaxation_error
    
    # Create a basic AerSimulator
    backend = AerSimulator()
    
    # Create a noise model based on our desired T1 time
    noise_model = NoiseModel()
    
    # Set T2 = T1 (pure amplitude damping limit)
    t2_time = t1_time
    
    # Gate time (typical duration)
    gate_time = 100e-9  # 100 ns
    
    # Add thermal relaxation to all qubits (limit to 5 for efficiency)
    for qubit in range(5):
        # For gates - use gate_time duration
        thermal_error = thermal_relaxation_error(t1_time, t2_time, gate_time)
        noise_model.add_quantum_error(thermal_error, ['x', 'sx', 'rz', 'id'], [qubit])
        
        # For delays - the actual delay duration will be used by the simulator
        # We just need to register that delays should have thermal relaxation
        delay_error = thermal_relaxation_error(t1_time, t2_time, 1e-6)  # 1μs as reference
        noise_model.add_quantum_error(delay_error, ['delay'], [qubit])
    
    # Create simulator with our noise model
    backend.set_options(noise_model=noise_model)
    
    return backend


def run_t1_experiment(backend_type="local_noisy"):
    """Run a T1 experiment on the specified backend."""
    
    print("="*60)
    print("SIMPLE T1 RELAXATION TIME MEASUREMENT")
    print("="*60)
    
    # Get backend
    if backend_type == "local_noisy":
        print("Creating local backend with thermal noise...")
        backend = create_thermal_noise_backend(t1_time=50e-6)
        expected_t1 = 50e-6  # seconds
    elif backend_type == "local_ideal":
        print("Using local ideal backend...")
        backend = get_local_aer_backend()
        expected_t1 = None  # No decoherence
    elif backend_type == "ibm_real":
        print("Using real IBM Quantum device...")
        backend = get_least_busy_backend()
        expected_t1 = None  # Unknown
    else:
        print("Using IBM Quantum simulator...")
        backend = get_simulator_backend()
        expected_t1 = None
    
    print(f"Backend: {backend.name}")
    
    # Set up T1 experiment
    print("\nSetting up T1 experiment...")
    
    # Define delay range - start small for better fitting
    delays = np.linspace(0, 150e-6, 16)  # 0 to 150 μs, 16 points
    
    # Create T1 experiment
    t1_exp = T1(physical_qubits=[0], delays=delays)
    
    print(f"Measuring T1 on qubit 0")
    print(f"Delays: {delays[0]*1e6:.1f} to {delays[-1]*1e6:.1f} μs ({len(delays)} points)")
    if expected_t1:
        print(f"Expected T1: {expected_t1*1e6:.1f} μs")
    
    # Run experiment
    print("\nRunning experiment...")
    exp_data = t1_exp.run(backend, shots=2000, seed_simulator=42)
    
    # Wait for completion
    exp_data.block_for_results()
    
    # Get results
    print("\n" + "="*50)
    print("RESULTS")
    print("="*50)
    
    results = exp_data.analysis_results()
    
    if results:
        for result in results:
            if result.name == "T1":
                t1_measured = result.value  # in seconds
                t1_std = getattr(result, 'std_dev', 0)
                
                print(f"Measured T1: {t1_measured*1e6:.2f} ± {t1_std*1e6:.2f} μs")
                
                if expected_t1:
                    error_pct = abs(t1_measured - expected_t1) / expected_t1 * 100
                    print(f"Expected T1: {expected_t1*1e6:.2f} μs")
                    print(f"Relative error: {error_pct:.1f}%")
                
                # Quality metrics
                print(f"Fit quality: {result.quality}")
                if hasattr(result, 'extra'):
                    print(f"Extra info: {result.extra}")
    else:
        print("No analysis results found!")
    
    # Plot results
    print("\nGenerating plot...")
    try:
        # Use the experiment's plotting capability
        fig = exp_data.figure(0)
        fig.savefig('t1_measurement_simple.png', dpi=300, bbox_inches='tight')
        print("Plot saved as 't1_measurement_simple.png'")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        print(f"Plotting failed: {e}")
        
        # Try manual plot
        try:
            data = exp_data.data()
            delays_us = delays * 1e6  # Convert to microseconds
            
            probs = []
            for i, datum in enumerate(data):
                counts = datum.counts
                total = sum(counts.values())
                prob_1 = counts.get('1', 0) / total if total > 0 else 0
                probs.append(prob_1)
            
            plt.figure(figsize=(10, 6))
            plt.plot(delays_us, probs, 'bo-', label='|1⟩ population')
            plt.xlabel('Delay (μs)')
            plt.ylabel('Population')
            plt.title('T1 Relaxation Measurement')
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.tight_layout()
            plt.savefig('t1_measurement_simple.png', dpi=300, bbox_inches='tight')
            plt.show()
            print("Manual plot saved as 't1_measurement_simple.png'")
            
        except Exception as e2:
            print(f"Manual plotting also failed: {e2}")
    
    print("\nExperiment completed!")
    return exp_data


if __name__ == "__main__":
    # Run the experiment
    exp_data = run_t1_experiment(backend_type="local_noisy")
