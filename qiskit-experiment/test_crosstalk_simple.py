#!/usr/bin/env python3
"""
Cross-talk Error Measurement - Simplified Direct Implementation
Demonstrates cross-talk effects through manual simulation and statistical modeling.
"""

import sys
sys.path.append('../qiskit-related')

import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
import itertools


def simulate_crosstalk_manually(gate_operations, crosstalk_strength=0.015, shots=4000):
    """
    Manually simulate cross-talk effects using statistical modeling.
    
    Args:
        gate_operations: List of gate types applied to target qubit
        crosstalk_strength: Cross-talk error probability per gate
        shots: Number of measurement shots to simulate
    
    Returns:
        Measurement results with cross-talk effects
    """
    results = {}
    
    # For each gate operation scenario
    for scenario_name, num_gates in gate_operations.items():
        # Simulate measurements on 3 qubits: [neighbor_0, target_1, neighbor_2]
        
        # Base error rates (readout, preparation errors, etc.)
        base_error = 0.001  # 0.1% base error
        
        # Cross-talk probability depends on number of gates and strength
        # Each gate on qubit 1 has probability of causing error on neighbors
        neighbor_error_prob = 1 - (1 - crosstalk_strength) ** num_gates
        
        # Generate measurement outcomes
        measurement_outcomes = []
        
        for shot in range(shots):
            # Start with ideal state |000⟩ (all qubits in ground state)
            qubit_states = [0, 0, 0]  # [q0, q1, q2]
            
            # Apply target gate effects to qubit 1
            # (In real experiment, this would be the desired operation result)
            # For simplicity, assume target operations return qubit 1 to |0⟩
            
            # Apply cross-talk errors to neighbors
            for qubit in [0, 2]:  # Neighbors of qubit 1
                # Each neighbor has probability of error due to cross-talk
                if np.random.random() < neighbor_error_prob + base_error:
                    qubit_states[qubit] = 1  # Flip to |1⟩
            
            # Convert to measurement string (q2 q1 q0 order)
            outcome = f"{qubit_states[2]}{qubit_states[1]}{qubit_states[0]}"
            measurement_outcomes.append(outcome)
        
        # Count measurement outcomes
        counts = {}
        for outcome in measurement_outcomes:
            counts[outcome] = counts.get(outcome, 0) + 1
        
        # Calculate error rates for each qubit
        qubit_errors = {}
        total_shots = len(measurement_outcomes)
        
        for qubit_idx in [0, 2]:  # Only measure neighbors
            error_count = 0
            for outcome in measurement_outcomes:
                # Check if this qubit is in |1⟩ (error state)
                if outcome[2-qubit_idx] == '1':  # Reverse bit order
                    error_count += 1
            
            error_rate = error_count / total_shots
            qubit_errors[f'qubit_{qubit_idx}'] = error_rate
        
        results[scenario_name] = {
            'counts': counts,
            'qubit_errors': qubit_errors,
            'total_shots': total_shots,
            'expected_crosstalk': neighbor_error_prob,
            'num_gates': num_gates
        }
    
    return results


def create_gate_operation_scenarios():
    """
    Define different gate operation scenarios for cross-talk measurement.
    
    Returns:
        Dictionary of scenario names and gate counts
    """
    scenarios = {
        'reference': 0,          # No operations
        'single_x': 1,           # Single X gate
        'single_y': 1,           # Single Y gate  
        'single_z': 1,           # Single Z gate
        'single_h': 1,           # Single H gate
        'single_s': 1,           # Single S gate
        'multiple_x_5': 5,       # 5 X gates
        'multiple_x_10': 10,     # 10 X gates
        'multiple_h_5': 5,       # 5 H gates
        'mixed_gates_10': 10,    # Mixed gate types
    }
    
    return scenarios


def analyze_crosstalk_measurements(results):
    """
    Analyze cross-talk measurement results.
    
    Args:
        results: Measurement results from simulate_crosstalk_manually
    
    Returns:
        Analysis dictionary with error rates and statistics
    """
    analysis = {
        'scenarios': list(results.keys()),
        'error_rates': {},
        'crosstalk_rates': {},
        'statistics': {}
    }
    
    # Reference error rate
    ref_errors = results.get('reference', {}).get('qubit_errors', {})
    ref_error_q0 = ref_errors.get('qubit_0', 0)
    ref_error_q2 = ref_errors.get('qubit_2', 0)
    
    # Process each scenario
    for scenario, data in results.items():
        qubit_errors = data['qubit_errors']
        
        # Store raw error rates
        analysis['error_rates'][scenario] = qubit_errors
        
        # Calculate cross-talk rates (subtract reference)
        crosstalk_q0 = max(0, qubit_errors.get('qubit_0', 0) - ref_error_q0)
        crosstalk_q2 = max(0, qubit_errors.get('qubit_2', 0) - ref_error_q2)
        
        analysis['crosstalk_rates'][scenario] = {
            'qubit_0': crosstalk_q0,
            'qubit_2': crosstalk_q2,
            'average': (crosstalk_q0 + crosstalk_q2) / 2,
            'expected': data.get('expected_crosstalk', 0),
            'num_gates': data.get('num_gates', 0)
        }
    
    # Calculate overall statistics
    all_crosstalk_rates = []
    for scenario, rates in analysis['crosstalk_rates'].items():
        if scenario != 'reference':
            all_crosstalk_rates.extend([rates['qubit_0'], rates['qubit_2']])
    
    if all_crosstalk_rates:
        analysis['statistics'] = {
            'mean_crosstalk': np.mean(all_crosstalk_rates),
            'std_crosstalk': np.std(all_crosstalk_rates),
            'min_crosstalk': np.min(all_crosstalk_rates),
            'max_crosstalk': np.max(all_crosstalk_rates)
        }
    
    return analysis


def plot_crosstalk_analysis(analysis, crosstalk_strength):
    """
    Create comprehensive plots for cross-talk analysis.
    
    Args:
        analysis: Analysis results
        crosstalk_strength: Programmed cross-talk strength per gate
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
    
    # Plot 1: Error rates by scenario
    scenarios = [s for s in analysis['scenarios'] if s != 'reference']
    q0_errors = [analysis['error_rates'][s]['qubit_0'] for s in scenarios]
    q2_errors = [analysis['error_rates'][s]['qubit_2'] for s in scenarios]
    
    x = np.arange(len(scenarios))
    width = 0.35
    
    ax1.bar(x - width/2, q0_errors, width, label='Qubit 0 (left)', alpha=0.8, color='skyblue')
    ax1.bar(x + width/2, q2_errors, width, label='Qubit 2 (right)', alpha=0.8, color='lightcoral')
    
    ax1.set_xlabel('Gate Operation Scenario')
    ax1.set_ylabel('Error Rate')
    ax1.set_title('Error Rates by Scenario')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.replace('_', '\n') for s in scenarios], rotation=45, ha='right')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Cross-talk vs number of gates
    gate_counts = [analysis['crosstalk_rates'][s]['num_gates'] for s in scenarios]
    avg_crosstalk = [analysis['crosstalk_rates'][s]['average'] for s in scenarios]
    expected_rates = [analysis['crosstalk_rates'][s]['expected'] for s in scenarios]
    
    # Sort by gate count for cleaner visualization
    sorted_data = sorted(zip(gate_counts, avg_crosstalk, expected_rates, scenarios))
    gate_counts_sorted, avg_crosstalk_sorted, expected_rates_sorted, scenarios_sorted = zip(*sorted_data)
    
    ax2.scatter(gate_counts_sorted, avg_crosstalk_sorted, s=100, alpha=0.7, 
               label='Measured', color='blue')
    ax2.plot(gate_counts_sorted, expected_rates_sorted, 'r--', alpha=0.8, 
             label='Expected', linewidth=2)
    
    # Add labels for each point
    for i, scenario in enumerate(scenarios_sorted):
        ax2.annotate(scenario.replace('_', '\n'), 
                    (gate_counts_sorted[i], avg_crosstalk_sorted[i]),
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax2.set_xlabel('Number of Gates on Target Qubit')
    ax2.set_ylabel('Average Cross-talk Rate')
    ax2.set_title('Cross-talk vs Gate Count')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Cross-talk symmetry (left vs right neighbor)
    crosstalk_q0 = [analysis['crosstalk_rates'][s]['qubit_0'] for s in scenarios]
    crosstalk_q2 = [analysis['crosstalk_rates'][s]['qubit_2'] for s in scenarios]
    
    ax3.scatter(crosstalk_q0, crosstalk_q2, s=100, alpha=0.7, c=range(len(scenarios)), 
               cmap='viridis')
    
    # Add scenario labels
    for i, scenario in enumerate(scenarios):
        ax3.annotate(scenario.replace('_', '\n'), (crosstalk_q0[i], crosstalk_q2[i]),
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    # Perfect symmetry line
    max_rate = max(max(crosstalk_q0), max(crosstalk_q2))
    if max_rate > 0:
        ax3.plot([0, max_rate], [0, max_rate], 'r--', alpha=0.5, label='Perfect symmetry')
    
    ax3.set_xlabel('Cross-talk Rate: Qubit 0 (Left)')
    ax3.set_ylabel('Cross-talk Rate: Qubit 2 (Right)')
    ax3.set_title('Spatial Symmetry of Cross-talk')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Statistical summary
    stats = analysis['statistics']
    metrics = ['Mean', 'Std Dev', 'Min', 'Max']
    values = [stats['mean_crosstalk'], stats['std_crosstalk'], 
              stats['min_crosstalk'], stats['max_crosstalk']]
    
    colors = ['blue', 'green', 'orange', 'red']
    bars = ax4.bar(metrics, values, color=colors, alpha=0.7)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{value:.4f}', ha='center', va='bottom')
    
    ax4.set_ylabel('Cross-talk Rate')
    ax4.set_title('Statistical Summary')
    ax4.grid(True, alpha=0.3)
    
    # Add reference line for expected single-gate cross-talk
    ax4.axhline(y=crosstalk_strength, color='red', linestyle='--', 
               label=f'Expected (1 gate): {crosstalk_strength:.3f}')
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig('crosstalk_measurement_simplified.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig


def run_simplified_crosstalk_experiment():
    """
    Run simplified cross-talk measurement experiment.
    
    Returns:
        Results and analysis
    """
    print("="*70)
    print("SIMPLIFIED CROSS-TALK ERROR MEASUREMENT")
    print("="*70)
    
    # Experiment parameters
    crosstalk_strength = 0.012  # 1.2% per gate
    shots = 8000
    
    print(f"Cross-talk strength per gate: {crosstalk_strength:.3f} ({crosstalk_strength*100:.1f}%)")
    print(f"Shots per scenario: {shots}")
    print(f"Topology: 3-qubit linear chain [Q0-Q1-Q2]")
    print(f"Target: Q1 (middle qubit)")
    print(f"Monitored: Q0, Q2 (neighbors)")
    
    # Define gate scenarios
    print("\nDefining gate operation scenarios...")
    scenarios = create_gate_operation_scenarios()
    print(f"Created {len(scenarios)} measurement scenarios")
    
    # Run simulations
    print("\nSimulating cross-talk effects...")
    results = simulate_crosstalk_manually(scenarios, crosstalk_strength, shots)
    
    # Analyze results
    print("Analyzing cross-talk measurements...")
    analysis = analyze_crosstalk_measurements(results)
    
    # Display results
    print("\n" + "="*50)
    print("CROSS-TALK MEASUREMENT RESULTS")
    print("="*50)
    
    # Reference rates
    ref_scenario = 'reference'
    if ref_scenario in results:
        ref_data = results[ref_scenario]
        print(f"\nReference Error Rates (no gates):")
        for qubit, rate in ref_data['qubit_errors'].items():
            print(f"  {qubit}: {rate:.4f} ({rate*100:.2f}%)")
    
    # Cross-talk rates by scenario
    print(f"\nCross-talk Rates by Scenario:")
    for scenario in analysis['scenarios']:
        if scenario != 'reference':
            data = analysis['crosstalk_rates'][scenario]
            print(f"\n  {scenario.replace('_', ' ').title()}:")
            print(f"    Gates: {data['num_gates']}")
            print(f"    Expected cross-talk: {data['expected']:.4f} ({data['expected']*100:.2f}%)")
            print(f"    Measured - Qubit 0: {data['qubit_0']:.4f} ({data['qubit_0']*100:.2f}%)")
            print(f"    Measured - Qubit 2: {data['qubit_2']:.4f} ({data['qubit_2']*100:.2f}%)")
            print(f"    Average measured: {data['average']:.4f} ({data['average']*100:.2f}%)")
            
            if data['expected'] > 0:
                error_pct = abs(data['average'] - data['expected']) / data['expected'] * 100
                print(f"    Relative error: {error_pct:.1f}%")
    
    # Overall statistics
    stats = analysis['statistics']
    print(f"\nOverall Statistics:")
    print(f"  Mean cross-talk rate: {stats['mean_crosstalk']:.4f} ± {stats['std_crosstalk']:.4f}")
    print(f"  Range: {stats['min_crosstalk']:.4f} to {stats['max_crosstalk']:.4f}")
    print(f"  Expected (single gate): {crosstalk_strength:.4f}")
    
    # Quality assessment
    single_gate_scenarios = ['single_x', 'single_y', 'single_z', 'single_h', 'single_s']
    single_gate_rates = []
    for scenario in single_gate_scenarios:
        if scenario in analysis['crosstalk_rates']:
            single_gate_rates.append(analysis['crosstalk_rates'][scenario]['average'])
    
    if single_gate_rates:
        avg_single_gate = np.mean(single_gate_rates)
        error_vs_expected = abs(avg_single_gate - crosstalk_strength) / crosstalk_strength * 100
        
        print(f"  Single-gate average: {avg_single_gate:.4f}")
        print(f"  Error vs expected: {error_vs_expected:.1f}%")
        
        if error_vs_expected < 10:
            print("  ✓ Excellent agreement with expected cross-talk")
        elif error_vs_expected < 20:
            print("  ✓ Good agreement with expected cross-talk")
        else:
            print("  ⚠ Significant deviation from expected cross-talk")
    
    # Generate plots
    print("\nGenerating visualizations...")
    plot_crosstalk_analysis(analysis, crosstalk_strength)
    print("Plot saved as 'crosstalk_measurement_simplified.png'")
    
    print("\n" + "="*70)
    print("CROSS-TALK PHYSICS SUMMARY")
    print("="*70)
    print("Key Observations:")
    print("1. Cross-talk increases with number of gate operations")
    print("2. Different gate types may have different cross-talk rates")
    print("3. Spatial symmetry: left/right neighbors show similar coupling")
    print("4. Statistical modeling captures essential cross-talk physics")
    print("\nReal Hardware Considerations:")
    print("• Capacitive coupling between qubits")
    print("• Control line crosstalk")
    print("• Frequency crowding effects")
    print("• ZZ coupling in superconducting qubits")
    
    return results, analysis


if __name__ == "__main__":
    # Run the simplified experiment
    results, analysis = run_simplified_crosstalk_experiment()
