import rustworkx as rx
from rustworkx.visualization import mpl_draw as draw_graph
import numpy as np

from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from scipy.optimize import minimize

from utils import get_least_busy_backend, get_simulator_backend, get_local_aer_backend
from plot import plot_objective_function_values, plot_final_distribution

def create_graph(n, edge_list):
    graph = rx.PyGraph()
    graph.add_nodes_from(np.arange(0, n, 1))
    graph.add_edges_from(edge_list)

    return graph

def build_max_cut_paulis(graph: rx.PyGraph) -> list[tuple[str, float]]:
    """Convert the graph to Pauli list.

    This function does the inverse of `build_max_cut_graph`
    """
    pauli_list = []
    for edge in list(graph.edge_list()):
        paulis = ["I"] * len(graph)
        paulis[edge[0]], paulis[edge[1]] = "Z", "Z"

        weight = graph.get_edge_data(edge[0], edge[1])

        pauli_list.append(("".join(paulis)[::-1], weight))

    return pauli_list

def sample_circuit(circuit, backend):

    from qiskit_ibm_runtime import SamplerV2 as Sampler

    # If using qiskit-ibm-runtime<0.24.0, change `mode=` to `backend=`
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = 10000

    # Set simple error suppression/mitigation options
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XY4"
    sampler.options.twirling.enable_gates = True
    sampler.options.twirling.num_randomizations = "auto"

    pub= (circuit, )
    job = sampler.run([pub], shots=int(1e4))
    counts_int = job.result()[0].data.meas.get_int_counts()
    counts_bin = job.result()[0].data.meas.get_counts()
    shots = sum(counts_int.values())
    # change final_distribution_int to a dict with keys as bitstrings
    final_distribution_int = {int(k, 2): v / shots for k, v in counts_bin.items()}
    plot_final_distribution(final_distribution_int)

def test_run_qaoa_circuit(init_params, backend, cost_hamiltonian, isa_circuit):

    from cost_func import cost_func_estimator

    # Define a local list to store costs
    objective_func_vals = []

    def callback(params):
        # Evaluate and store the cost at current params
        cost = cost_func_estimator(params, isa_circuit, cost_hamiltonian, estimator)
        objective_func_vals.append(cost)

    with Session(backend=backend) as session:
        # If using qiskit-ibm-runtime<0.24.0, change `mode=` to `session=`
        estimator = Estimator(mode=session)
        estimator.options.default_shots = 1000

        # Set simple error suppression/mitigation options
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XY4"
        estimator.options.twirling.enable_gates = True
        estimator.options.twirling.num_randomizations = "auto"
        # Run the optimizer with the callback
        result = minimize(
            cost_func_estimator,
            init_params,
            args=(isa_circuit, cost_hamiltonian, estimator),
            method="COBYLA",
            tol=1e-2,
            callback=callback
        )
    print(result)
    plot_objective_function_values(objective_func_vals)
    return result

def test_solve_max_cut_by_qaoa():
    n = 5
    edge_list = [(0, 1, 1.0), (0, 2, 1.0), (0, 4, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 4, 1.0)]
    graph = create_graph(n, edge_list)
    # draw_graph(graph, node_size=600, with_labels=True)
    # The graph is converted to a Pauli list

    max_cut_paulis = build_max_cut_paulis(graph)
    cost_hamiltonian = SparsePauliOp.from_list(max_cut_paulis)
    print("Cost Function Hamiltonian:", cost_hamiltonian)

    # reps is the number of layers in the QAOA circuit
    qaoa_round = 5
    circuit = QAOAAnsatz(cost_operator=cost_hamiltonian, reps=qaoa_round)
    circuit.measure_all()
    backend = get_local_aer_backend()
    pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
    isa_circuit = pm.run(circuit)
    # isa_circuit.draw('mpl', fold=False, idle_wires=False)
    initial_gamma = np.pi
    initial_beta = np.pi/2
    # init_params for 5 layers qaoa circuit
    init_params = [initial_gamma, initial_beta] * qaoa_round
    result = test_run_qaoa_circuit(init_params, backend, cost_hamiltonian, isa_circuit)
    optimized_circuit = isa_circuit.assign_parameters(result.x)
    optimized_circuit.draw('mpl', fold=False, idle_wires=False)
    sample_circuit(optimized_circuit, backend)

if __name__ == "__main__":
    test_solve_max_cut_by_qaoa()