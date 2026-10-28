import csv
import os


# ==================================================
# Successful Stage 5 Results
# ==================================================

results = [

    # ----------------------------------------------
    # No Bootstrapping
    # ----------------------------------------------

    {
        "Experiment": "No Bootstrapping",
        "Operations": 4,
        "Threshold": "",
        "Bootstrap Count": 0,
        "Bootstrap Time": 0.0,
        "Final Level": 4,
        "Maximum Absolute Error": 1.163922e-15,
        "Total Execution Time": 0.338870
    },

    {
        "Experiment": "No Bootstrapping",
        "Operations": 6,
        "Threshold": "",
        "Bootstrap Count": 0,
        "Bootstrap Time": 0.0,
        "Final Level": 6,
        "Maximum Absolute Error": 1.163922e-15,
        "Total Execution Time": 0.381611
    },

    {
        "Experiment": "No Bootstrapping",
        "Operations": 8,
        "Threshold": "",
        "Bootstrap Count": 0,
        "Bootstrap Time": 0.0,
        "Final Level": 8,
        "Maximum Absolute Error": 1.241751e-15,
        "Total Execution Time": 0.206767
    },

    {
        "Experiment": "No Bootstrapping",
        "Operations": 10,
        "Threshold": "",
        "Bootstrap Count": 0,
        "Bootstrap Time": 0.0,
        "Final Level": 10,
        "Maximum Absolute Error": 1.055562e-15,
        "Total Execution Time": 0.165543
    },


    # ----------------------------------------------
    # Fixed Bootstrapping
    # ----------------------------------------------

    {
        "Experiment": "Fixed Bootstrapping",
        "Operations": 4,
        "Threshold": 2,
        "Bootstrap Count": 2,
        "Bootstrap Time": 3.149504022,
        "Final Level": 4,
        "Maximum Absolute Error": 1.097921e-15,
        "Total Execution Time": 4.118179
    },

    {
        "Experiment": "Fixed Bootstrapping",
        "Operations": 6,
        "Threshold": 2,
        "Bootstrap Count": 3,
        "Bootstrap Time": 5.192300,
        "Final Level": 6,
        "Maximum Absolute Error": 2.179381e-15,
        "Total Execution Time": 5.192300
    },

    {
        "Experiment": "Fixed Bootstrapping",
        "Operations": 8,
        "Threshold": 2,
        "Bootstrap Count": 4,
        "Bootstrap Time": 8.027879,
        "Final Level": 8,
        "Maximum Absolute Error": 1.432869e-15,
        "Total Execution Time": 8.027879
    },

    {
        "Experiment": "Fixed Bootstrapping",
        "Operations": 10,
        "Threshold": 2,
        "Bootstrap Count": 5,
        "Bootstrap Time": 10.830837,
        "Final Level": 10,
        "Maximum Absolute Error": 1.199597e-15,
        "Total Execution Time": 10.830837
    },


    # ----------------------------------------------
    # Adaptive Bootstrapping
    # ----------------------------------------------

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 4,
        "Threshold": 2,
        "Bootstrap Count": 2,
        "Bootstrap Time": 3.205324974,
        "Final Level": 4,
        "Maximum Absolute Error": 8.935221902609504e-16,
        "Total Execution Time": 4.064881469999818
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 4,
        "Threshold": 3,
        "Bootstrap Count": 1,
        "Bootstrap Time": 2.161068671,
        "Final Level": 4,
        "Maximum Absolute Error": 6.463752401690735e-16,
        "Total Execution Time": 3.15539284700003
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 4,
        "Threshold": 4,
        "Bootstrap Count": 1,
        "Bootstrap Time": 2.178310515,
        "Final Level": 4,
        "Maximum Absolute Error": 1.6701830064673776e-15,
        "Total Execution Time": 2.8768477229998553
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 6,
        "Threshold": 2,
        "Bootstrap Count": 3,
        "Bootstrap Time": 0.0,
        "Final Level": 6,
        "Maximum Absolute Error": 8.826998e-16,
        "Total Execution Time": 9.442110
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 6,
        "Threshold": 3,
        "Bootstrap Count": 2,
        "Bootstrap Time": 0.0,
        "Final Level": 6,
        "Maximum Absolute Error": 8.022355e-16,
        "Total Execution Time": 6.633301
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 6,
        "Threshold": 4,
        "Bootstrap Count": 1,
        "Bootstrap Time": 0.0,
        "Final Level": 6,
        "Maximum Absolute Error": 1.682798e-15,
        "Total Execution Time": 5.164665
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 8,
        "Threshold": 2,
        "Bootstrap Count": 4,
        "Bootstrap Time": 0.0,
        "Final Level": 8,
        "Maximum Absolute Error": 1.729477e-15,
        "Total Execution Time": 12.577176
    },

    {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": 8,
        "Threshold": 3,
        "Bootstrap Count": 2,
        "Bootstrap Time": 0.0,
        "Final Level": 8,
        "Maximum Absolute Error": 1.526703e-15,
        "Total Execution Time": 8.572425
    }
]


# ==================================================
# Save CSV
# ==================================================

os.makedirs(
    "results",
    exist_ok=True
)

output_file = (
    "results/stage5_clean_results.csv"
)

fieldnames = [
    "Experiment",
    "Operations",
    "Threshold",
    "Bootstrap Count",
    "Bootstrap Time",
    "Final Level",
    "Maximum Absolute Error",
    "Total Execution Time"
]


with open(
    output_file,
    "w",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    writer.writerows(
        results
    )


print(
    f"Clean Stage 5 results saved to:"
)

print(
    output_file
)

print(
    f"Total successful configurations: "
    f"{len(results)}"
)
