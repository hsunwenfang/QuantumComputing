
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

def get_least_busy_backend():

    service = QiskitRuntimeService(channel='ibm_quantum')
    backend = service.least_busy(operational=True, simulator=False)

    return backend

def get_simulator_backend():
    service = QiskitRuntimeService(channel='ibm_quantum')
    # Use a simulator backend instead of the least busy real device
    backend = service.backend("ibmq_qasm_simulator")
    return backend

def get_local_aer_backend(seed_simulator):
    from qiskit_aer import AerSimulator
    import warnings
    # Suppress warnings about local testing mode
    warnings.filterwarnings(
        "ignore",
        message="Options .*have no effect in local testing mode.",
        module="qiskit_ibm_runtime.fake_provider.local_service"
    )
    # return Aer.get_backend("aer_simulator", seed_simulator=seed_simulator, method="statevector")
    # return Aer.get_backend(seed_simulator=seed_simulator, method="statevector")
    return AerSimulator(method="statevector", seed_simulator=seed_simulator)

def optimize_circuit_on_backend(ansatz, observable, backend):

    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
    isa_ansatz = pm.run(ansatz)
    isa_observable = observable.apply_layout(layout = isa_ansatz.layout)

    return isa_ansatz, isa_observable