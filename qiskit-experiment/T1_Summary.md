# T1 Relaxation Measurement - Quick Summary

## Experiment Overview
**Objective**: Measure T1 relaxation time (how quickly qubit |1⟩ state decays to |0⟩)  
**Method**: Exponential decay fitting of excited state population vs delay time  
**Date**: July 25, 2025

## Key Results
| Metric | Value | Notes |
|--------|--------|-------|
| **Expected T1** | 50.0 μs | Programmed in noise model |
| **Measured T1** | 52.37 ± 0.65 μs | From curve fitting |
| **Relative Error** | 4.7% | Excellent accuracy |
| **Measurement Range** | 0-200 μs | 21 data points |
| **Shots per Point** | 2000 | High statistics |

## Theory Summary
**T1 Relaxation**: Exponential decay of excited state population  
**Physics**: Energy dissipation to environment  
**Equation**: P(|1⟩, t) = A × exp(-t/T1) + B  
**Time Constant**: T1 = 52.37 μs means 1/e decay in ~52 microseconds

## Experimental Process
1. **Prepare**: X gate → |1⟩ state
2. **Wait**: Variable delay time t
3. **Measure**: Population in |1⟩ state
4. **Repeat**: Multiple delay times
5. **Fit**: Exponential decay curve
6. **Extract**: T1 relaxation time

## Implementation Details
- **Framework**: Qiskit + qiskit-experiments 0.11.0
- **Backend**: AerSimulator with thermal noise model
- **Analysis**: Scipy curve fitting
- **Scripts**: 3 implementations (direct simulation works best)

## Generated Files
- `T1_Measurement_Report.md` - Full technical report
- `t1_measurement_direct.png` - Main experimental results
- `test_t1_direct.py` - Working simulation script
- `test_t1.py` - qiskit-experiments framework version

## Scientific Significance
- **Quantum Error Correction**: Determines feasible circuit depths
- **Algorithm Design**: Limits on computation time  
- **Hardware Benchmarking**: Device performance metric
- **Decoherence Studies**: Fundamental quantum physics

## Real-World Context
- **IBM Quantum**: Typical T1 ~ 50-150 μs
- **Google Sycamore**: T1 ~ 100 μs  
- **IonQ (trapped ions)**: T1 > 1 ms
- **Our Simulation**: T1 = 52.37 μs (realistic value)

## Next Steps
- Extend to T2 (dephasing) measurements
- Multi-qubit correlated relaxation
- Real hardware validation
- Process tomography for complete noise characterization

---
*Summary of T1 relaxation time measurement experiment*
