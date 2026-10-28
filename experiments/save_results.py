import csv
import os


# --------------------------------------------------
# 1. Results directory
# --------------------------------------------------

results_directory = "results"

os.makedirs(
    results_directory,
    exist_ok=True
)


# --------------------------------------------------
# 2. CSV file path
# --------------------------------------------------

csv_file = os.path.join(
    results_directory,
    "experiment_results.csv"
)


# --------------------------------------------------
# 3. Experimental results
# --------------------------------------------------

results = [

    {
        "Experiment": "No Bootstrapping",
        "Operations": 4,
        "Bootstrap Count": 0,
        "Bootstrap Time": 0.0,
        "Final Level": 4,
        "Maximum Absolute Error": 1.5136523236664078e-15,
        "Total Execution Time": 0.266490
    },

    {
        "Experiment": "Fixed Bootstrapping",
        "Operations": 4,
        "Bootstrap Count": 1,
        "Bootstrap Time": 1.363564,
        "Final Level": 4,
        "Maximum Absolute Error": 9.648271193114365e-16,
        "Total Execution Time": 1.485345
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 4,
        "Bootstrap Count": 2,
        "Bootstrap Time": 2.495961,
        "Final Level": 4,
        "Maximum Absolute Error": 1.8658923547140486e-15,
        "Total Execution Time": 2.594903
    }

]


# --------------------------------------------------
# 4. CSV column names
# --------------------------------------------------

fieldnames = [
    "Experiment",
    "Operations",
    "Bootstrap Count",
    "Bootstrap Time",
    "Final Level",
    "Maximum Absolute Error",
    "Total Execution Time"
]


# --------------------------------------------------
# 5. Write CSV
# --------------------------------------------------

with open(
    csv_file,
    "w",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(results)


# --------------------------------------------------
# 6. Confirmation
# --------------------------------------------------

print("=" * 50)
print("Experimental results saved successfully.")
print("=" * 50)

print("\nCSV file:")
print(csv_file)

print("\nNumber of experiments:")
print(len(results))

print("\nExperiments stored:")

for result in results:
    print(
        "-",
        result["Experiment"]
    )
