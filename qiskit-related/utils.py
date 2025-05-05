
from qiskit_ibm_runtime import QiskitRuntimeService

def get_least_busy_backend():

    service = QiskitRuntimeService(channel='ibm_quantum')
    backend = service.least_busy(operational=True, simulator=False)

    return backend

def get_simulator_backend():
    service = QiskitRuntimeService(channel='ibm_quantum')
    # Use a simulator backend instead of the least busy real device
    backend = service.backend("ibmq_qasm_simulator")
    return backend

def get_local_aer_backend():
    from qiskit_aer import Aer
    return Aer.get_backend("aer_simulator")