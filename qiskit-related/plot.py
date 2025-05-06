

import matplotlib.pyplot as plt

def plot_final_distribution(final_distribution_int):
    plt.figure(figsize=(10, 5))
    # Convert keys to bitstrings if needed
    keys = [str(k) for k in final_distribution_int.keys()]
    values = list(final_distribution_int.values())
    plt.bar(keys, values, color="tab:blue")
    plt.xlabel("Bitstring (solution)")
    plt.ylabel("Probability")
    plt.title("QAOA Output Distribution\nEach bar shows the probability of measuring a given bitstring after running the optimized QAOA circuit.")
    plt.xticks(rotation=45)
    plt.tight_layout()
    # save the plot as a JPEG file
    plt.savefig("qaoa_output_distribution.jpeg")

# Example usage after sample_circuit:
# plot_final_distribution(final_distribution_int)

def plot_objective_function_values(objective_func_vals):
    import matplotlib.pyplot as plt
    plt.plot(objective_func_vals)
    plt.xlabel("Iteration")
    plt.ylabel("Cost")
    plt.title("Objective Function Values")
    plt.savefig("objective_function_values.jpeg")
