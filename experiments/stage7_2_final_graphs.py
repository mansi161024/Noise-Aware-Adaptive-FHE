import matplotlib.pyplot as plt
import numpy as np
import os

# Create graph directory
os.makedirs("graphs", exist_ok=True)

# Reliable completed results
experiments = [
    "No Bootstrap",
    "Fixed Bootstrap",
    "Adaptive Bootstrap"
]

execution_time = [
    0.266490,
    1.485345,
    2.594903
]

bootstrap_count = [
    0,
    1,
    2
]

maximum_error = [
    1.513652e-15,
    9.648271e-16,
    1.865892e-15
]

# ---------------------------------------------------------
# 1. Execution Time
# ---------------------------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(experiments, execution_time)

plt.xlabel("Experiment")
plt.ylabel("Total Execution Time (seconds)")
plt.title("Execution Time Comparison")

plt.tight_layout()

plt.savefig(
    "graphs/stage7_execution_time.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 2. Bootstrap Count
# ---------------------------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(experiments, bootstrap_count)

plt.xlabel("Experiment")
plt.ylabel("Number of Bootstraps")
plt.title("Bootstrap Count Comparison")

plt.tight_layout()

plt.savefig(
    "graphs/stage7_bootstrap_count.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# 3. Numerical Error
# ---------------------------------------------------------

plt.figure(figsize=(8, 5))

plt.bar(experiments, maximum_error)

plt.xlabel("Experiment")
plt.ylabel("Maximum Absolute Error")
plt.title("Numerical Error Comparison")

plt.ticklabel_format(
    axis="y",
    style="scientific",
    scilimits=(0, 0)
)

plt.tight_layout()

plt.savefig(
    "graphs/stage7_numerical_error.png",
    dpi=300
)

plt.close()


# ---------------------------------------------------------
# Final message
# ---------------------------------------------------------

print("=" * 70)
print("STAGE 7.2 - FINAL GRAPH GENERATION")
print("=" * 70)

print("\nGraphs created successfully:")

print("1. graphs/stage7_execution_time.png")
print("2. graphs/stage7_bootstrap_count.png")
print("3. graphs/stage7_numerical_error.png")

print("\nStage 7.2 completed.")
