from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.circuit import Parameter, QuantumCircuit
from utils import get_local_aer_backend
from qiskit_ibm_runtime import (
    EstimatorV2 as Estimator,
    SamplerV2 as Sampler,
)
from qiskit.transpiler import generate_preset_pass_manager
from qiskit.quantum_info import SparsePauliOp
import numpy as np
import matplotlib.pyplot as plt
 
# Instantiate runtime service and get
# the least busy backend
service = QiskitRuntimeService()
# backend = service.least_busy(operational=True, simulator=False)
backend = get_local_aer_backend(seed_simulator=42)
 
# Define a circuit with two parameters.
circuit = QuantumCircuit(2)
circuit.h(0)
circuit.cx(0, 1)
circuit.ry(Parameter("a"), 0)
circuit.rz(Parameter("b"), 0)
circuit.cx(0, 1)
circuit.h(0)
 
# Transpile the circuit
pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
transpiled_circuit = pm.run(circuit)
layout = transpiled_circuit.layout
 
 
# Now define a sweep over parameter values, the last axis of dimension 2 is
# for the two parameters "a" and "b"
n = 10
params = np.vstack(
    [
        np.linspace(-np.pi, np.pi, n),
        np.linspace(-4 * np.pi, 4 * np.pi, n),
    ]
).T
 
# Define three observables. The inner length-1 lists cause this array of
# observables to have shape (3, 1), rather than shape (3,) if they were
# omitted.
observables = [
    [SparsePauliOp(["XX", "IY"], [0.5, 0.5])],
    [SparsePauliOp("XX")],
    [SparsePauliOp("IY")],
]
# Apply the same layout as the transpiled circuit.
observables = [
    [observable.apply_layout(layout) for observable in observable_set]
    for observable_set in observables
]
 
# Estimate the expectation value for all 300 combinations of observables
# and parameter values, where the pub result will have shape (3, 100).
#
# This shape is due to our array of parameter bindings having shape
# (100, 2), combined with our array of observables having shape (3, 1).
estimator_pub = (transpiled_circuit, observables, params)
 
# Instantiate the new estimator object, then run the transpiled circuit
# using the set of parameters and observables.
estimator = Estimator(mode=backend)
job1 = estimator.run([estimator_pub, estimator_pub])
job2 = estimator.run([estimator_pub, estimator_pub])
result1 = job1.result()
result2 = job2.result()

# Print the result object to inspect its structure
# print(result.__dict__)
print(result1._pub_results[0].data.evs)
print(result2._pub_results[0].data.evs)
# print(result._pub_results[0].data.evs)