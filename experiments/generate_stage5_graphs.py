import pandas as pd
import matplotlib.pyplot as plt
import os


# ==================================================
# Load Results
# ==================================================

input_file = "results/stage5_clean_results.csv"

df = pd.read_csv(input_file)


# Create graphs directory

os.makedirs(
    "graphs/stage5",
    exist_ok=True
)


# ==================================================
# Graph 1: Execution Time vs Operations
# ==================================================

plt.figure()

for experiment in [
    "No Bootstrapping",
    "Fixed Bootstrapping"
]:

    data = df[
        df["Experiment"] == experiment
    ]

    plt.plot(
        data["Operations"],
        data["Total Execution Time"],
        marker="o",
        label=experiment
    )

plt.xlabel(
    "Number of Homomorphic Operations"
)

plt.ylabel(
    "Total Execution Time (seconds)"
)

plt.title(
    "Execution Time vs Number of Operations"
)

plt.legend()

plt.grid(True)

plt.savefig(
    "graphs/stage5/execution_time_vs_operations.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==================================================
# Graph 2: Bootstrap Count vs Operations
# ==================================================

plt.figure()

fixed_data = df[
    df["Experiment"] == "Fixed Bootstrapping"
]

plt.plot(
    fixed_data["Operations"],
    fixed_data["Bootstrap Count"],
    marker="o",
    label="Fixed"
)


for threshold in [2, 3, 4]:

    adaptive_data = df[
        (df["Experiment"] == "Adaptive Bootstrapping")
        &
        (df["Threshold"] == threshold)
    ]

    if len(adaptive_data) > 0:

        plt.plot(
            adaptive_data["Operations"],
            adaptive_data["Bootstrap Count"],
            marker="o",
            label=f"Adaptive Threshold {threshold}"
        )


plt.xlabel(
    "Number of Homomorphic Operations"
)

plt.ylabel(
    "Bootstrap Count"
)

plt.title(
    "Bootstrap Count vs Number of Operations"
)

plt.legend()

plt.grid(True)

plt.savefig(
    "graphs/stage5/bootstrap_count_vs_operations.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==================================================
# Graph 3: Maximum Error vs Operations
# ==================================================

plt.figure()

no_bootstrap = df[
    df["Experiment"] == "No Bootstrapping"
]

fixed = df[
    df["Experiment"] == "Fixed Bootstrapping"
]

plt.plot(
    no_bootstrap["Operations"],
    no_bootstrap["Maximum Absolute Error"],
    marker="o",
    label="No Bootstrapping"
)

plt.plot(
    fixed["Operations"],
    fixed["Maximum Absolute Error"],
    marker="o",
    label="Fixed Bootstrapping"
)


for threshold in [2, 3, 4]:

    adaptive_data = df[
        (df["Experiment"] == "Adaptive Bootstrapping")
        &
        (df["Threshold"] == threshold)
    ]

    if len(adaptive_data) > 0:

        plt.plot(
            adaptive_data["Operations"],
            adaptive_data["Maximum Absolute Error"],
            marker="o",
            label=f"Adaptive Threshold {threshold}"
        )


plt.xlabel(
    "Number of Homomorphic Operations"
)

plt.ylabel(
    "Maximum Absolute Error"
)

plt.title(
    "Maximum Absolute Error vs Number of Operations"
)

plt.yscale("log")

plt.legend()

plt.grid(True)

plt.savefig(
    "graphs/stage5/maximum_error_vs_operations.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==================================================
# Graph 4: Adaptive Threshold vs Execution Time
# ==================================================

adaptive = df[
    df["Experiment"] == "Adaptive Bootstrapping"
]

plt.figure()

for operations in sorted(
    adaptive["Operations"].unique()
):

    data = adaptive[
        adaptive["Operations"] == operations
    ]

    plt.plot(
        data["Threshold"],
        data["Total Execution Time"],
        marker="o",
        label=f"{operations} Operations"
    )


plt.xlabel(
    "Adaptive Threshold"
)

plt.ylabel(
    "Total Execution Time (seconds)"
)

plt.title(
    "Adaptive Threshold vs Execution Time"
)

plt.legend()

plt.grid(True)

plt.savefig(
    "graphs/stage5/adaptive_threshold_vs_time.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ==================================================
# Graph 5: Adaptive Threshold vs Bootstrap Count
# ==================================================

plt.figure()

for operations in sorted(
    adaptive["Operations"].unique()
):

    data = adaptive[
        adaptive["Operations"] == operations
    ]

    plt.plot(
        data["Threshold"],
        data["Bootstrap Count"],
        marker="o",
        label=f"{operations} Operations"
    )


plt.xlabel(
    "Adaptive Threshold"
)

plt.ylabel(
    "Bootstrap Count"
)

plt.title(
    "Adaptive Threshold vs Bootstrap Count"
)

plt.legend()

plt.grid(True)

plt.savefig(
    "graphs/stage5/adaptive_threshold_vs_bootstrap_count.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()


print(
    "\nStage 5 graphs generated successfully."
)

print(
    "\nGraphs saved in:"
)

print(
    "graphs/stage5/"
)
