#!/usr/bin/env python3
"""
Direct T1 measurement without using complex noise models.
Instead, we'll create a simple custom experiment.
"""

import sys
sys.path.append('../qiskit-related')

import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram


def create_t1_circuit(delay_time):
    """Create a simple T1 measurement circuit."""
    qc = QuantumCircuit(1, 1)
    
    # Prepare |1⟩ state
    qc.x(0)
    
    # Add delay
    if delay_time > 0:
        qc.delay(delay_time, 0, unit='s')
    
    # Measure
    qc.measure(0, 0)
    
    return qc


def simulate_t1_decay(delay_times, t1_time, shots=1000):
    """
    Simulate T1 decay using exponential decay formula.
    P(|1⟩) = exp(-t/T1)
    """
    results = []
    
    for delay_time in delay_times:
        # Calculate theoretical probability
        prob_1 = np.exp(-delay_time / t1_time)
        
        # Add some noise for realism
        noise_level = 0.02  # 2% noise
        prob_1 += np.random.normal(0, noise_level * prob_1)
        prob_1 = max(0, min(1, prob_1))  # Clamp to [0,1]
        
        # Simulate shot noise
        count_1 = np.random.binomial(shots, prob_1)
        count_0 = shots - count_1
        
        results.append({
            'counts': {'0': count_0, '1': count_1},
            'prob_1': count_1 / shots
        })
    
    return results


def fit_exponential_decay(delays, probabilities):
    """Fit exponential decay to extract T1."""
    from scipy.optimize import curve_fit
    
    def exponential_decay(t, A, T1, B):
        return A * np.exp(-t / T1) + B
    
    try:
        # Initial guess: A=1, T1=50μs, B=0
        p0 = [1.0, 50e-6, 0.0]
        
        # Fit the curve
        popt, pcov = curve_fit(exponential_decay, delays, probabilities, p0=p0, maxfev=10000)
        
        A, T1_fit, B = popt
        T1_error = np.sqrt(pcov[1,1]) if pcov[1,1] > 0 else 0
        
        return T1_fit, T1_error, popt
        
    except Exception as e:
        print(f"Fitting failed: {e}")
        return None, None, None


def run_simple_t1_experiment():
    """Run a simple T1 experiment with manual simulation."""
    
    print("="*60)
    print("DIRECT T1 RELAXATION TIME MEASUREMENT")
    print("="*60)
    
    # Experiment parameters
    t1_true = 50e-6  # 50 microseconds
    delay_times = np.linspace(0, 200e-6, 21)  # 0 to 200 μs
    shots = 2000
    
    print(f"True T1: {t1_true*1e6:.1f} μs")
    print(f"Delay range: {delay_times[0]*1e6:.1f} to {delay_times[-1]*1e6:.1f} μs")
    print(f"Number of points: {len(delay_times)}")
    print(f"Shots per point: {shots}")
    
    # Simulate the experiment
    print("\nRunning simulation...")
    results = simulate_t1_decay(delay_times, t1_true, shots)
    
    # Extract probabilities
    probabilities = [r['prob_1'] for r in results]
    
    # Fit exponential decay
    print("\nFitting exponential decay...")
    t1_fit, t1_error, fit_params = fit_exponential_decay(delay_times, probabilities)
    
    if t1_fit is not None:
        print("\n" + "="*50)
        print("RESULTS")
        print("="*50)
        print(f"True T1: {t1_true*1e6:.2f} μs")
        print(f"Fitted T1: {t1_fit*1e6:.2f} ± {t1_error*1e6:.2f} μs")
        
        error_pct = abs(t1_fit - t1_true) / t1_true * 100
        print(f"Relative error: {error_pct:.1f}%")
        
        A, T1_fitted, B = fit_params
        print(f"Fit parameters: A={A:.3f}, T1={T1_fitted*1e6:.2f}μs, B={B:.3f}")
        print(f"Fit equation: P(|1⟩) = {A:.3f} * exp(-t/{T1_fitted*1e6:.1f}μs) + {B:.3f}")
    
    # Plot results
    print("\nGenerating plot...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Raw data and fit
    delays_us = delay_times * 1e6
    ax1.plot(delays_us, probabilities, 'bo', label='Simulated data', markersize=6)
    
    if t1_fit is not None:
        # Plot fit
        t_fit = np.linspace(0, delay_times[-1], 100)
        A, T1_fitted, B = fit_params
        p_fit = A * np.exp(-t_fit / T1_fitted) + B
        ax1.plot(t_fit * 1e6, p_fit, 'r-', label=f'Fit: T1={T1_fitted*1e6:.1f}μs', linewidth=2)
    
    ax1.set_xlabel('Delay (μs)')
    ax1.set_ylabel('P(|1⟩)')
    ax1.set_title('T1 Relaxation Measurement')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Plot 2: Histogram of a few measurement points
    sample_indices = [0, len(results)//3, 2*len(results)//3, -1]
    sample_results = [results[i] for i in sample_indices]
    sample_delays = [delay_times[i]*1e6 for i in sample_indices]
    
    colors = ['blue', 'green', 'orange', 'red']
    x_pos = np.arange(len(sample_indices))
    
    for i, (result, delay, color) in enumerate(zip(sample_results, sample_delays, colors)):
        counts = result['counts']
        prob_1 = result['prob_1']
        ax2.bar(x_pos[i], prob_1, color=color, alpha=0.7, 
                label=f't={delay:.1f}μs')
    
    ax2.set_xlabel('Measurement Point')
    ax2.set_ylabel('P(|1⟩)')
    ax2.set_title('Sample Measurement Results')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([f'{d:.1f}μs' for d in sample_delays], rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('t1_measurement_direct.png', dpi=300, bbox_inches='tight')
    print("Plot saved as 't1_measurement_direct.png'")
    plt.show()
    
    print("\n" + "="*60)
    print("EXPERIMENT SUMMARY")
    print("="*60)
    print("This demonstrates the principle of T1 measurement:")
    print("1. Prepare qubit in |1⟩ state")
    print("2. Wait for various delay times")
    print("3. Measure population remaining in |1⟩")
    print("4. Fit exponential decay: P(|1⟩) = A·exp(-t/T1) + B")
    print("5. Extract T1 relaxation time")
    
    return t1_fit, t1_error


if __name__ == "__main__":
    # Install scipy if needed
    try:
        import scipy
    except ImportError:
        print("Installing scipy for curve fitting...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])
        import scipy
    
    # Run the experiment
    t1_fit, t1_error = run_simple_t1_experiment()
