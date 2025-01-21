

## ISA

### ISA Observables

- A Linear Combination of Pauli Operators with Real Coefficients.
    - Hermitian Operator.
- Each Pauli is defined on the same number of qubits as the ISA circuit.



# Transpiler

## Target

## Preset Pass Manager

#### Init Stage

- Parse multi qubit gates to single / double qubit gates.
- Logically optimize the circuit (Not aware of the hardware).
- Layout the circuit meaning drawing the DAG of the circuit which can only be done from single / double qubit gates.

#### Layout Stage

- Pick the best Qubits and the layout requires minimum SWAP gates.
- Uses the VF2Layout (Virtual to Physical Qubit Mapping).
- VF2Layout (Virtual to Physical Qubit Mapping).
    - Find all the 2 qubit interactions in the circuit.
    - Build the interaction graph.
    - Check the HW connectivity graph.
    - Find an isomorphic subgraph of the 2.
    - Uses the rustworkx library.
- If VF2Layout fails, uses SabreLayout.
- SabreLayout picks a layout that minimizes the number of SWAP gates.
- Qiskit parrallelizes the SabreLayout.

#### Routing Stage

- Insert the SWAP gates to map the HW qubits connections.
- SabreSwap is essentially SabreLayout really doing the SWAP gates.
- VF2PostLayout

#### Translation Stage

- Basis Translator
    - Looks at the graph and run DIJKSTRA to find the shortest path.
    - Replace the gates with native gates.
- NOW the circuit is ready to be run on the hardware.

#### Optimization Stage

- Reduce the number of gates.
- 1 qubit unitary peep hole optimization.
- commutative cancellation.
    - idetify the commutative gates and combine them.
- NOW we have the optimized circuit.

#### Scheduling Stage

- Find free time slots for the gates to execute on the hardware.
- Often insert delay gates


# Noise in near-term quantum computers

## SPAM errors (State Preparation and Measurement)

## Kraus Operators for Noise