import csv
import os

print("=" * 75)
print("STAGE 7.1 - FINAL RESEARCH SUMMARY")
print("=" * 75)

results = [
    [
        "Stage 4",
        "No Bootstrapping",
        4,
        0,
        0.266490,
        1.513652e-15
    ],
    [
        "Stage 4",
        "Fixed Bootstrapping",
        4,
        1,
        1.485345,
        9.648271e-16
    ],
    [
        "Stage 4",
        "Adaptive Bootstrapping",
        4,
        2,
        2.594903,
        1.865892e-15
    ],
    [
        "Stage 6",
        "Adaptive Bootstrap",
        6,
        2,
        2.759992,
        None
    ],
    [
        "Stage 6",
        "Accuracy Validation",
        2,
        1,
        1.883093,
        1.291041e-15
    ]
]

print("\nFINAL EXPERIMENTAL SUMMARY")
print("-" * 75)

print(
    f"{'Stage':10}"
    f"{'Experiment':25}"
    f"{'Operations':12}"
    f"{'Bootstraps':12}"
    f"{'Time (s)':12}"
    f"{'Max Error':15}"
)

print("-" * 75)

for row in results:

    stage = row[0]
    experiment = row[1]
    operations = row[2]
    bootstraps = row[3]
    time = row[4]
    error = row[5]

    error_text = (
        f"{error:.6e}"
        if error is not None
        else "N/A"
    )

    print(
        f"{stage:10}"
        f"{experiment:25}"
        f"{operations:12}"
        f"{bootstraps:12}"
        f"{time:12.6f}"
        f"{error_text:15}"
    )

# Save results

os.makedirs("results", exist_ok=True)

file_path = "results/stage7_1_final_summary.csv"

with open(file_path, "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "Stage",
        "Experiment",
        "Operations",
        "Bootstrap Count",
        "Execution/Bootstrap Time",
        "Maximum Absolute Error"
    ])

    writer.writerows(results)

print("\n" + "=" * 75)
print("SUMMARY")
print("=" * 75)

print("""
Stage 4 demonstrated the difference between
no bootstrapping, fixed bootstrapping and adaptive bootstrapping.

Stage 5 evaluated the adaptive approach under
different computation depths and thresholds.

Stage 6 developed practical adaptive monitoring,
performed actual CKKS bootstrapping and validated accuracy.

The complete results will be used for the final
research analysis.
""")

print("=" * 75)
print("STAGE 7.1 COMPLETED")
print("=" * 75)

print("\nResults saved to:")
print(file_path)
