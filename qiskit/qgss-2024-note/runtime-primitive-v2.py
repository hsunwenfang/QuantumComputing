

# import all the necessary modules
import numpy as np
from qiskit import QuantumCircuit, Aer
from qiskit.circuit import Parameter
from qiskit.compiler import transpile
from qiskit import quantum_info as qi



def estimator_primitives():

    theta = Parameter('θ')
    par_bell = QuantumCircuit(2)
    par_bell.ry(theta, 0)
    par_bell.cx(0, 1)


    # The backend is a simulator, so we can use the Aer provider
    backend = Aer.get_backend('qasm_simulator')


    # Transpile to an ISA Circuit for the backend
    isa_par_bell = transpile(par_bell, backend)

    params = np.linspace(0, np.pi, 20)

    par_bell_obs = [
        qi.SparsePauliOp(["XX"]),
        qi.SparsePauliOp(["YY"]),
        qi.SparsePauliOp(["ZZ"]),
    ]

    # Transpile the observable to the ISA Circuit
    isa_par_bell_obs = [
        [op.apply_layout(layout=isa_par_bell.layout) for op in par_bell_obs]
    ]

    pub = (isa_par_bell, isa_par_bell_obs, params)
