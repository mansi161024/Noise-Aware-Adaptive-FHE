import csv


# --------------------------------------------------
# 1. CSV file
# --------------------------------------------------

csv_file = "results/experiment_results.csv"


# --------------------------------------------------
# 2. Read experimental results
# --------------------------------------------------

results = []

with open(csv_file, "r") as file:

    reader = csv.DictReader(file)

    for row in reader:
        results.append(row)


# --------------------------------------------------
# 3. Display comparison table
# --------------------------------------------------

print("=" * 90)
print("EXPERIMENTAL COMPARISON")
print("=" * 90)

print(
    "{:<25} {:>12} {:>15} {:>18} {:>18}".format(
        "Experiment",
        "Bootstraps",
        "Final Level",
        "Max Error",
        "Total Time (s)"
    )
)

print("-" * 90)


for result in results:

    print(
        "{:<25} {:>12} {:>15} {:>18.6e} {:>18.6f}".format(
            result["Experiment"],
            int(result["Bootstrap Count"]),
            int(result["Final Level"]),
            float(result["Maximum Absolute Error"]),
            float(result["Total Execution Time"])
        )
    )


# --------------------------------------------------
# 4. Extract experiments
# --------------------------------------------------

no_bootstrap = results[0]
fixed_bootstrap = results[1]
adaptive_bootstrap = results[2]


# --------------------------------------------------
# 5. Convert values
# --------------------------------------------------

no_time = float(
    no_bootstrap["Total Execution Time"]
)

fixed_time = float(
    fixed_bootstrap["Total Execution Time"]
)

adaptive_time = float(
    adaptive_bootstrap["Total Execution Time"]
)


no_count = int(
    no_bootstrap["Bootstrap Count"]
)

fixed_count = int(
    fixed_bootstrap["Bootstrap Count"]
)

adaptive_count = int(
    adaptive_bootstrap["Bootstrap Count"]
)


# --------------------------------------------------
# 6. Time differences
# --------------------------------------------------

fixed_vs_no = fixed_time - no_time

adaptive_vs_no = adaptive_time - no_time

adaptive_vs_fixed = adaptive_time - fixed_time


# --------------------------------------------------
# 7. Bootstrap differences
# --------------------------------------------------

fixed_count_vs_no = fixed_count - no_count

adaptive_count_vs_no = adaptive_count - no_count

adaptive_count_vs_fixed = adaptive_count - fixed_count


# --------------------------------------------------
# 8. Display analysis
# --------------------------------------------------

print("\n" + "=" * 90)
print("TIME COMPARISON")
print("=" * 90)

print(
    "Fixed vs No Bootstrap:      "
    "{:.6f} seconds".format(fixed_vs_no)
)

print(
    "Adaptive vs No Bootstrap:   "
    "{:.6f} seconds".format(adaptive_vs_no)
)

print(
    "Adaptive vs Fixed:          "
    "{:.6f} seconds".format(adaptive_vs_fixed)
)


print("\n" + "=" * 90)
print("BOOTSTRAP COUNT COMPARISON")
print("=" * 90)

print(
    "Fixed vs No Bootstrap:      "
    "{}".format(fixed_count_vs_no)
)

print(
    "Adaptive vs No Bootstrap:   "
    "{}".format(adaptive_count_vs_no)
)

print(
    "Adaptive vs Fixed:          "
    "{}".format(adaptive_count_vs_fixed)
)


# --------------------------------------------------
# 9. Error comparison
# --------------------------------------------------

print("\n" + "=" * 90)
print("NUMERICAL ERROR")
print("=" * 90)

for result in results:

    print(
        "{:<25}: {:.6e}".format(
            result["Experiment"],
            float(
                result["Maximum Absolute Error"]
            )
        )
    )


# --------------------------------------------------
# 10. Completion
# --------------------------------------------------

print("\n" + "=" * 90)
print("Comparison completed.")
print("=" * 90)
