
# https://learning.quantum.ibm.com/course/variational-algorithm-design/instances-and-extensions

import numpy as np
from scipy.optimize import minimize

from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import TwoLocal
from qiskit.primitives import StatevectorEstimator

from qiskit_ibm_runtime import SamplerV2 as Sampler
from qiskit_ibm_runtime import EstimatorV2 as Estimator
from qiskit_ibm_runtime import SamplerOptions, EstimatorOptions
from qiskit_ibm_runtime import Session
from qiskit_ibm_runtime import options

from utils import optimize_circuit_on_backend

def ansatz_vqe_sample():

    observable=SparsePauliOp.from_list([("II", 2), ("XX", -2), ("YY", 3), ("ZZ", -3)])

    reference_circuit = QuantumCircuit(2)
    reference_circuit.x(0)

    variational_form = TwoLocal(
        2,
        rotation_blocks=["rz", "ry"],
        entanglement_blocks="cx",
        entanglement="linear",
        reps=1,
    )
    ansatz = reference_circuit.compose(variational_form)

    # ansatz.decompose().draw('mpl')
    ansatz.measure_active()

    return ansatz, observable



def main():

    ansatz, observable = ansatz_vqe_sample()
    print(ansatz.decompose())

    from utils import get_least_busy_backend, get_simulator_backend, get_local_aer_backend
    # backend = get_least_busy_backend()
    # backend = get_simulator_backend()
    backend = get_local_aer_backend()

    print(backend)
    isa_ansatz, isa_observable = optimize_circuit_on_backend(ansatz, observable, backend)

    # bootstrap strategy [TODO]
    # x0 = [0.1] * ansatz.num_parameters
    x0 = np.random.uniform(low=-np.pi, high=np.pi, size=ansatz.num_parameters)

    sampler_options = options.SamplerOptions(default_shots=32)
    estimator_options = options.EstimatorOptions(default_shots=32)

    from cost_func import cost_func_ssvqe

    with Session(backend=backend) as session:
        sampler = Sampler(mode=session, options=sampler_options)
        estimator = Estimator(mode=session, options=estimator_options)

        # Optimize the parameters using COBYLA
        # result = minimize(cost_func_vqe, x0, method="COBYLA")
        result = minimize(cost_func_ssvqe, x0, args=(isa_ansatz, isa_observable, estimator), method="COBYLA")

        optimized_parameters = result.x

    print("Optimized Parameters:", optimized_parameters)

if __name__ == "__main__":
    main()