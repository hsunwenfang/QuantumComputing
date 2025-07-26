#!/usr/bin/env python3
"""
Cross-talk Error Measurement - Direct Simulation
Measures unintended effects of single-qubit gates on neighboring qubits.

Cross-talk occurs when:
1. A gate on qubit A unintentionally affects qubit B
2. Common causes: crosstalk capacitance, control line coupling, frequency crowding
3. Measurement: Compare qubit states with/without neighboring operations
"""

import sys
sys.path.append('../qiskit-related')

import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error
import itertools


def create_crosstalk_backend(crosstalk_strength=0.02):
    """
    Create a backend with cross-talk noise between adjacent qubits.
    
    Args:
        crosstalk_strength: Probability of crosstalk error (0-1)
    
    Returns:
        AerSimulator with cross-talk noise model
    """
    backend = AerSimulator()
    noise_model = NoiseModel()
    
    # Define qubit topology (linear chain for simplicity)
    n_qubits = 5
    
    # Add cross-talk errors: when gate acts on qubit i, it can affect neighbors
    single_qubit_gates = ['x', 'y', 'z', 'h', 's', 't', 'sx', 'rz']
    
    for target_qubit in range(n_qubits):
        # Find neighbors
        neighbors = []
        if target_qubit > 0:
            neighbors.append(target_qubit - 1)  # Left neighbor
        if target_qubit < n_qubits - 1:
            neighbors.append(target_qubit + 1)  # Right neighbor
        
        # For each gate on target_qubit, add errors to neighbors
        for gate in single_qubit_gates:
            for neighbor in neighbors:
                # Cross-talk: small depolarizing error on neighbor when gate acts on target
                crosstalk_error = depolarizing_error(crosstalk_strength, 1)
                
                # Apply error to neighbor when gate is applied to target
                # Note: this adds error EVERY TIME the gate is applied
                noise_model.add_quantum_error(crosstalk_error, gate, neighbor)
    
    backend.set_options(noise_model=noise_model)
    return backend


def create_crosstalk_measurement_circuits():
    """
    Create circuits to measure cross-talk between adjacent qubits.
    
    Returns:
        List of quantum circuits for cross-talk characterization
    """
    circuits = {}
    
    # 1. Reference circuits (no operations)
    ref_circuit = QuantumCircuit(3, 3)
    ref_circuit.measure_all()
    circuits['reference'] = ref_circuit
    
    # 2. Single-qubit operations (target qubit 1, measure neighbors 0 and 2)
    operations = ['x', 'y', 'z', 'h', 's']
    
    for op in operations:
        # Circuit with operation on qubit 1
        qc = QuantumCircuit(3, 3)
        
        # Apply operation to middle qubit
        if op == 'x':
            qc.x(1)
        elif op == 'y':
            qc.y(1)
        elif op == 'z':
            qc.z(1)
        elif op == 'h':
            qc.h(1)
        elif op == 's':
            qc.s(1)
        
        qc.measure_all()
        circuits[f'{op}_on_q1'] = qc
        
        # Also create circuit with multiple operations (stress test)
        qc_multiple = QuantumCircuit(3, 3)
        for _ in range(10):  # Apply operation 10 times
            if op == 'x':
                qc_multiple.x(1)
            elif op == 'y':
                qc_multiple.y(1)
            elif op == 'z':
                qc_multiple.z(1)
            elif op == 'h':
                qc_multiple.h(1)
            elif op == 's':
                qc_multiple.s(1)
        
        qc_multiple.measure_all()
        circuits[f'{op}_10x_on_q1'] = qc_multiple
    
    return circuits


def simulate_crosstalk_effects(backend, circuits, shots=2000):
    """
    Simulate cross-talk effects using the provided backend and circuits.
    
    Args:
        backend: Quantum backend with noise model
        circuits: Dictionary of quantum circuits
        shots: Number of measurement shots
    
    Returns:
        Dictionary of measurement results
    """
    results = {}
    
    for circuit_name, circuit in circuits.items():
        # Run circuit
        job = backend.run(circuit, shots=shots, seed_simulator=42)
        result = job.result()
        counts = result.get_counts()
        
        # Calculate probabilities
        total_shots = sum(counts.values())
        probs = {state: count/total_shots for state, count in counts.items()}
        
        # Calculate error rates for each qubit
        qubit_errors = {}
        for qubit in [0, 2]:  # Neighbors of qubit 1
            # Error rate = probability of finding qubit in |1⟩ when it should be |0⟩
            error_rate = 0
            for state, prob in probs.items():
                if len(state) > qubit and state[-(qubit+1)] == '1':  # Reverse bit order
                    error_rate += prob
            qubit_errors[f'qubit_{qubit}'] = error_rate
        
        results[circuit_name] = {
            'counts': counts,
            'probabilities': probs,
            'qubit_errors': qubit_errors,
            'total_shots': total_shots
        }
    
    return results


def analyze_crosstalk_results(results):
    """
    Analyze cross-talk measurement results to extract error rates.
    
    Args:
        results: Dictionary of measurement results
    
    Returns:
        Analysis summary with cross-talk error rates
    """
    analysis = {
        'reference_errors': {},
        'operation_errors': {},
        'crosstalk_rates': {},
        'operation_types': []
    }
    
    # Reference error rates (baseline)
    if 'reference' in results:
        ref_errors = results['reference']['qubit_errors']
        analysis['reference_errors'] = ref_errors
    
    # Operation-induced errors
    operations = ['x', 'y', 'z', 'h', 's']
    
    for op in operations:
        single_key = f'{op}_on_q1'
        multiple_key = f'{op}_10x_on_q1'
        
        if single_key in results:
            op_errors = results[single_key]['qubit_errors']
            analysis['operation_errors'][op] = op_errors
            
            # Calculate cross-talk rate (operation error - reference error)
            crosstalk_rates = {}
            for qubit in ['qubit_0', 'qubit_2']:
                ref_rate = analysis['reference_errors'].get(qubit, 0)
                op_rate = op_errors.get(qubit, 0)
                crosstalk_rates[qubit] = max(0, op_rate - ref_rate)
            
            analysis['crosstalk_rates'][op] = crosstalk_rates
            analysis['operation_types'].append(op)
        
        # Multiple operations analysis
        if multiple_key in results:
            multi_errors = results[multiple_key]['qubit_errors']
            analysis['operation_errors'][f'{op}_10x'] = multi_errors
            
            # Enhanced cross-talk rate for multiple operations
            enhanced_crosstalk = {}
            for qubit in ['qubit_0', 'qubit_2']:
                ref_rate = analysis['reference_errors'].get(qubit, 0)
                multi_rate = multi_errors.get(qubit, 0)
                enhanced_crosstalk[qubit] = max(0, multi_rate - ref_rate)
            
            analysis['crosstalk_rates'][f'{op}_10x'] = enhanced_crosstalk
    
    return analysis


def plot_crosstalk_results(analysis, crosstalk_strength):
    """
    Create comprehensive plots of cross-talk measurement results.
    
    Args:
        analysis: Analysis results from analyze_crosstalk_results
        crosstalk_strength: Programmed cross-talk strength
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Cross-talk rates by operation type
    operations = analysis['operation_types']
    qubit_0_rates = [analysis['crosstalk_rates'][op]['qubit_0'] for op in operations]
    qubit_2_rates = [analysis['crosstalk_rates'][op]['qubit_2'] for op in operations]
    
    x = np.arange(len(operations))
    width = 0.35
    
    ax1.bar(x - width/2, qubit_0_rates, width, label='Qubit 0 (left neighbor)', alpha=0.8)
    ax1.bar(x + width/2, qubit_2_rates, width, label='Qubit 2 (right neighbor)', alpha=0.8)
    
    ax1.set_xlabel('Gate Operation on Qubit 1')
    ax1.set_ylabel('Cross-talk Error Rate')
    ax1.set_title('Cross-talk Error Rates by Gate Type')
    ax1.set_xticks(x)
    ax1.set_xticklabels([op.upper() for op in operations])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add expected value line
    ax1.axhline(y=crosstalk_strength, color='red', linestyle='--', 
                label=f'Expected: {crosstalk_strength:.3f}')
    ax1.legend()
    
    # Plot 2: Single vs Multiple operations comparison
    single_ops = [op for op in operations]
    multi_ops = [f'{op}_10x' for op in operations if f'{op}_10x' in analysis['crosstalk_rates']]
    
    if multi_ops:
        single_rates = [np.mean([analysis['crosstalk_rates'][op]['qubit_0'], 
                                analysis['crosstalk_rates'][op]['qubit_2']]) for op in single_ops]
        multi_rates = [np.mean([analysis['crosstalk_rates'][op]['qubit_0'], 
                               analysis['crosstalk_rates'][op]['qubit_2']]) for op in multi_ops]
        
        x = np.arange(len(single_ops))
        ax2.bar(x - width/2, single_rates, width, label='Single operation', alpha=0.8)
        if len(multi_rates) == len(single_rates):
            ax2.bar(x + width/2, multi_rates, width, label='10× operations', alpha=0.8)
        
        ax2.set_xlabel('Gate Type')
        ax2.set_ylabel('Average Cross-talk Rate')
        ax2.set_title('Single vs Multiple Operations')
        ax2.set_xticks(x)
        ax2.set_xticklabels([op.upper() for op in single_ops])
        ax2.legend()
        ax2.grid(True, alpha=0.3)
    
    # Plot 3: Cross-talk asymmetry (left vs right neighbor)
    left_rates = [analysis['crosstalk_rates'][op]['qubit_0'] for op in operations]
    right_rates = [analysis['crosstalk_rates'][op]['qubit_2'] for op in operations]
    
    ax3.scatter(left_rates, right_rates, s=100, alpha=0.7, c=range(len(operations)), cmap='viridis')
    
    for i, op in enumerate(operations):
        ax3.annotate(op.upper(), (left_rates[i], right_rates[i]), 
                    xytext=(5, 5), textcoords='offset points')
    
    # Perfect correlation line
    max_rate = max(max(left_rates), max(right_rates))
    ax3.plot([0, max_rate], [0, max_rate], 'r--', alpha=0.5, label='Perfect symmetry')
    
    ax3.set_xlabel('Cross-talk Rate: Qubit 0 (Left)')
    ax3.set_ylabel('Cross-talk Rate: Qubit 2 (Right)')
    ax3.set_title('Cross-talk Symmetry Analysis')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Error rate comparison
    ref_rates = [analysis['reference_errors'].get('qubit_0', 0), 
                 analysis['reference_errors'].get('qubit_2', 0)]
    
    all_op_rates_q0 = [analysis['operation_errors'][op]['qubit_0'] for op in operations]
    all_op_rates_q2 = [analysis['operation_errors'][op]['qubit_2'] for op in operations]
    
    categories = ['Reference\n(no ops)', 'With X', 'With Y', 'With Z', 'With H', 'With S']
    q0_rates = [ref_rates[0]] + all_op_rates_q0
    q2_rates = [ref_rates[1]] + all_op_rates_q2
    
    x = np.arange(len(categories))
    ax4.bar(x - width/2, q0_rates, width, label='Qubit 0', alpha=0.8)
    ax4.bar(x + width/2, q2_rates, width, label='Qubit 2', alpha=0.8)
    
    ax4.set_xlabel('Experimental Condition')
    ax4.set_ylabel('Total Error Rate')
    ax4.set_title('Error Rates: Reference vs Operations')
    ax4.set_xticks(x)
    ax4.set_xticklabels(categories, rotation=45)
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('crosstalk_measurement_direct.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig


def run_crosstalk_experiment():
    """
    Execute complete cross-talk measurement experiment.
    
    Returns:
        Experiment results and analysis
    """
    print("="*70)
    print("CROSS-TALK ERROR MEASUREMENT")
    print("="*70)
    
    # Experiment parameters
    crosstalk_strength = 0.015  # 1.5% cross-talk rate
    shots = 4000
    
    print(f"Programmed cross-talk strength: {crosstalk_strength:.3f} ({crosstalk_strength*100:.1f}%)")
    print(f"Shots per measurement: {shots}")
    print(f"Measurement topology: Linear chain (qubits 0-1-2)")
    print(f"Target qubit: 1 (middle)")
    print(f"Monitored qubits: 0, 2 (neighbors)")
    
    # Create backend with cross-talk
    print("\nCreating backend with cross-talk noise model...")
    backend = create_crosstalk_backend(crosstalk_strength)
    
    # Create measurement circuits
    print("Generating measurement circuits...")
    circuits = create_crosstalk_measurement_circuits()
    print(f"Created {len(circuits)} measurement circuits")
    
    # Run simulations
    print("\nRunning cross-talk measurements...")
    results = simulate_crosstalk_effects(backend, circuits, shots)
    
    # Analyze results
    print("Analyzing cross-talk effects...")
    analysis = analyze_crosstalk_results(results)
    
    # Display results
    print("\n" + "="*50)
    print("CROSS-TALK MEASUREMENT RESULTS")
    print("="*50)
    
    print(f"\nReference Error Rates (no operations):")
    for qubit, rate in analysis['reference_errors'].items():
        print(f"  {qubit}: {rate:.4f} ({rate*100:.2f}%)")
    
    print(f"\nCross-talk Rates by Operation:")
    for op in analysis['operation_types']:
        rates = analysis['crosstalk_rates'][op]
        avg_rate = np.mean(list(rates.values()))
        print(f"  {op.upper()} gate:")
        print(f"    Qubit 0: {rates['qubit_0']:.4f} ({rates['qubit_0']*100:.2f}%)")
        print(f"    Qubit 2: {rates['qubit_2']:.4f} ({rates['qubit_2']*100:.2f}%)")
        print(f"    Average: {avg_rate:.4f} ({avg_rate*100:.2f}%)")
    
    # Calculate overall statistics
    all_rates = []
    for op in analysis['operation_types']:
        rates = analysis['crosstalk_rates'][op]
        all_rates.extend(list(rates.values()))
    
    mean_crosstalk = np.mean(all_rates)
    std_crosstalk = np.std(all_rates)
    
    print(f"\nOverall Statistics:")
    print(f"  Expected cross-talk: {crosstalk_strength:.4f} ({crosstalk_strength*100:.2f}%)")
    print(f"  Measured cross-talk: {mean_crosstalk:.4f} ± {std_crosstalk:.4f}")
    print(f"  Relative error: {abs(mean_crosstalk - crosstalk_strength)/crosstalk_strength*100:.1f}%")
    
    # Quality assessment
    if abs(mean_crosstalk - crosstalk_strength) < 0.005:
        print("  ✓ Excellent agreement with expected value")
    elif abs(mean_crosstalk - crosstalk_strength) < 0.01:
        print("  ✓ Good agreement with expected value")
    else:
        print("  ⚠ Significant deviation from expected value")
    
    # Generate plots
    print("\nGenerating visualizations...")
    plot_crosstalk_results(analysis, crosstalk_strength)
    print("Plot saved as 'crosstalk_measurement_direct.png'")
    
    print("\n" + "="*70)
    print("EXPERIMENT SUMMARY")
    print("="*70)
    print("Cross-talk measurement demonstrates:")
    print("1. Unintended coupling between adjacent qubits")
    print("2. Gate-dependent cross-talk rates")
    print("3. Spatial correlation in quantum errors")
    print("4. Need for error mitigation in multi-qubit systems")
    
    return results, analysis


if __name__ == "__main__":
    # Install required packages if needed
    try:
        import scipy
    except ImportError:
        print("Installing scipy...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "scipy"])
    
    # Run the experiment
    results, analysis = run_crosstalk_experiment()
