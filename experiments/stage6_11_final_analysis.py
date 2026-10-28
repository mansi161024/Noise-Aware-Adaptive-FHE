import csv
import os

print("=" * 70)
print("STAGE 6.11 - FINAL STAGE 6 ANALYSIS")
print("=" * 70)

# --------------------------------------------------
# Stage 6 results collected from completed tests
# --------------------------------------------------

results = [
    [
        "Stage 6.6 - Level/Error",
        6,
        0,
        0.0,
        7.576310e-16
    ],
    [
        "Stage 6.9 - Adaptive Bootstrap",
        6,
        2,
        2.759992,
        None
    ],
    [
        "Stage 6.10 - Accuracy Validation",
        2,
        1,
        1.883093,
        1.291041e-15
    ]
]

# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\n" + "-" * 70)
print(
    f"{'Experiment':35}"
    f"{'Operations':>12}"
    f"{'Bootstraps':>12}"
    f"{'Bootstrap Time':>18}"
    f"{'Max Error':>18}"
)
print("-" * 70)

for row in results:

    experiment = row[0]
    operations = row[1]
    bootstraps = row[2]
    bootstrap_time = row[3]
    error = row[4]

    error_text = (
        f"{error:.6e}"
        if error is not None
        else "N/A"
    )

    print(
        f"{experiment:35}"
        f"{operations:>12}"
        f"{bootstraps:>12}"
        f"{bootstrap_time:>18.6f}"
        f"{error_text:>18}"
    )

# --------------------------------------------------
# Save CSV
# --------------------------------------------------

os.makedirs(
    "results",
    exist_ok=True
)

file_path = "results/stage6_11_final_analysis.csv"

with open(
    file_path,
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "Experiment",
        "Operations",
        "Bootstrap Count",
        "Bootstrap Time",
        "Maximum Absolute Error"
    ])

    writer.writerows(results)

# --------------------------------------------------
# Final observations
# --------------------------------------------------

print("\n" + "=" * 70)
print("STAGE 6.11 OBSERVATIONS")
print("=" * 70)

print("""
1. Ciphertext level increased with homomorphic operations.

2. The adaptive controller successfully identified HIGH conditions.

3. Actual bootstrapping was successfully performed in Stage 6.9.

4. Stage 6.9 performed 2 bootstrap operations in 6 computations.

5. Total bootstrap time in Stage 6.9 was approximately
   2.759992 seconds.

6. Stage 6.10 showed that numerical error remained extremely small
   after bootstrapping.

7. The maximum error after bootstrap in Stage 6.10 was
   1.291041e-15.

8. These results support the use of an adaptive controller for
   deciding when bootstrapping should be triggered.
""")

print("=" * 70)
print("STAGE 6.11 COMPLETED")
print("=" * 70)

print("\nResults saved to:")
print(file_path)
