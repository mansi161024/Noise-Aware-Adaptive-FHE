import pandas as pd


# ==================================================
# Load Results
# ==================================================

file = "results/stage5_clean_results.csv"

df = pd.read_csv(file)


# ==================================================
# Display All Results
# ==================================================

print("\n")
print("=" * 70)
print("STAGE 5 RESULTS")
print("=" * 70)

print(
    df.to_string(index=False)
)


# ==================================================
# Summary by Experiment Type
# ==================================================

print("\n")
print("=" * 70)
print("SUMMARY BY EXPERIMENT")
print("=" * 70)

summary = (
    df
    .groupby("Experiment")
    .agg(
        Configurations=("Operations", "count"),
        Average_Time=("Total Execution Time", "mean"),
        Average_Error=("Maximum Absolute Error", "mean"),
        Total_Bootstraps=("Bootstrap Count", "sum")
    )
    .reset_index()
)

print(
    summary.to_string(index=False)
)


# ==================================================
# Adaptive Threshold Analysis
# ==================================================

adaptive = df[
    df["Experiment"] == "Adaptive Bootstrapping"
].copy()


print("\n")
print("=" * 70)
print("ADAPTIVE THRESHOLD ANALYSIS")
print("=" * 70)

adaptive_summary = (
    adaptive
    .groupby("Threshold")
    .agg(
        Configurations=("Operations", "count"),
        Average_Time=("Total Execution Time", "mean"),
        Average_Error=("Maximum Absolute Error", "mean"),
        Total_Bootstraps=("Bootstrap Count", "sum")
    )
    .reset_index()
)

print(
    adaptive_summary.to_string(index=False)
)


# ==================================================
# Best Time Within Each Adaptive Workload
# ==================================================

print("\n")
print("=" * 70)
print("ADAPTIVE WORKLOAD COMPARISON")
print("=" * 70)

for operations in sorted(
    adaptive["Operations"].unique()
):

    data = adaptive[
        adaptive["Operations"] == operations
    ]

    fastest = data.loc[
        data["Total Execution Time"].idxmin()
    ]

    print(
        f"\nOperations: {operations}"
    )

    print(
        f"Threshold: "
        f"{int(fastest['Threshold'])}"
    )

    print(
        f"Bootstrap Count: "
        f"{int(fastest['Bootstrap Count'])}"
    )

    print(
        f"Execution Time: "
        f"{fastest['Total Execution Time']:.6f} seconds"
    )

    print(
        f"Maximum Error: "
        f"{fastest['Maximum Absolute Error']:.6e}"
    )


# ==================================================
# Error Range
# ==================================================

print("\n")
print("=" * 70)
print("ERROR RANGE")
print("=" * 70)

minimum_error = df[
    "Maximum Absolute Error"
].min()

maximum_error = df[
    "Maximum Absolute Error"
].max()

print(
    f"Minimum observed error: "
    f"{minimum_error:.6e}"
)

print(
    f"Maximum observed error: "
    f"{maximum_error:.6e}"
)


# ==================================================
# Execution Time Range
# ==================================================

print("\n")
print("=" * 70)
print("EXECUTION TIME RANGE")
print("=" * 70)

minimum_time = df[
    "Total Execution Time"
].min()

maximum_time = df[
    "Total Execution Time"
].max()

print(
    f"Minimum execution time: "
    f"{minimum_time:.6f} seconds"
)

print(
    f"Maximum execution time: "
    f"{maximum_time:.6f} seconds"
)


# ==================================================
# Bootstrap Count Range
# ==================================================

print("\n")
print("=" * 70)
print("BOOTSTRAP COUNT RANGE")
print("=" * 70)

minimum_bootstrap = df[
    "Bootstrap Count"
].min()

maximum_bootstrap = df[
    "Bootstrap Count"
].max()

print(
    f"Minimum bootstrap count: "
    f"{minimum_bootstrap}"
)

print(
    f"Maximum bootstrap count: "
    f"{maximum_bootstrap}"
)
