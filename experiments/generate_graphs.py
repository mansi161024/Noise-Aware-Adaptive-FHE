import csv
import os
import matplotlib.pyplot as plt


# --------------------------------------------------
# 1. File paths
# --------------------------------------------------

csv_file = "results/experiment_results.csv"

graphs_directory = "graphs"

os.makedirs(
    graphs_directory,
    exist_ok=True
)


# --------------------------------------------------
# 2. Read CSV
# --------------------------------------------------

experiments = []
bootstrap_counts = []
bootstrap_times = []
errors = []
execution_times = []


with open(csv_file, "r") as file:

    reader = csv.DictReader(file)

    for row in reader:

        experiments.append(
            row["Experiment"]
        )

        bootstrap_counts.append(
            int(row["Bootstrap Count"])
        )

        bootstrap_times.append(
            float(row["Bootstrap Time"])
        )

        errors.append(
            float(
                row["Maximum Absolute Error"]
            )
        )

        execution_times.append(
            float(
                row["Total Execution Time"]
            )
        )


# --------------------------------------------------
# 3. Graph 1 — Total Execution Time
# --------------------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    experiments,
    execution_times
)

plt.xlabel("Bootstrapping Strategy")

plt.ylabel("Total Execution Time (seconds)")

plt.title(
    "Total Execution Time Comparison"
)

plt.xticks(
    rotation=15
)

plt.tight_layout()

plt.savefig(
    "graphs/total_execution_time.png",
    dpi=300
)

plt.close()


# --------------------------------------------------
# 4. Graph 2 — Bootstrap Count
# --------------------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    experiments,
    bootstrap_counts
)

plt.xlabel("Bootstrapping Strategy")

plt.ylabel("Number of Bootstrap Operations")

plt.title(
    "Bootstrap Count Comparison"
)

plt.xticks(
    rotation=15
)

plt.tight_layout()

plt.savefig(
    "graphs/bootstrap_count.png",
    dpi=300
)

plt.close()


# --------------------------------------------------
# 5. Graph 3 — Maximum Absolute Error
# --------------------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(
    experiments,
    errors
)

plt.xlabel("Bootstrapping Strategy")

plt.ylabel("Maximum Absolute Error")

plt.title(
    "Numerical Error Comparison"
)

plt.xticks(
    rotation=15
)

plt.tight_layout()

plt.savefig(
    "graphs/maximum_error.png",
    dpi=300
)

plt.close()


# --------------------------------------------------
# 6. Completion message
# --------------------------------------------------

print("=" * 60)
print("GRAPH GENERATION COMPLETED")
print("=" * 60)

print("\nGraphs created:")

print(
    "1.",
    "graphs/total_execution_time.png"
)

print(
    "2.",
    "graphs/bootstrap_count.png"
)

print(
    "3.",
    "graphs/maximum_error.png"
)
