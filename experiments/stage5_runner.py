from openfhe import *

import time
import csv
import os

from stage5_config import (
    WORKLOADS,
    ADAPTIVE_THRESHOLDS,
    INPUT_DATA,
    FIXED_BOOTSTRAP_INTERVAL
)

from stage5_framework import (
    create_crypto_context,
    generate_keys,
    setup_bootstrap,
    run_no_bootstrap,
    run_fixed_bootstrap,
    run_adaptive_bootstrap,
    decrypt_result,
    calculate_expected,
    calculate_max_error
)


# ==================================================
# Run No-Bootstrap Experiment
# ==================================================

def run_no_experiment(operations):

    print(
        f"\n[NO BOOTSTRAP] "
        f"Operations = {operations}"
    )

    start_time = time.perf_counter()

    cc = create_crypto_context(
        operations,
        enable_bootstrap=False
    )

    key_pair = generate_keys(cc)

    ciphertext = run_no_bootstrap(
        cc,
        key_pair,
        INPUT_DATA,
        operations
    )

    actual = decrypt_result(
        cc,
        key_pair.secretKey,
        ciphertext
    )

    total_time = (
        time.perf_counter()
        - start_time
    )

    expected = calculate_expected(
        INPUT_DATA,
        operations
    )

    error = calculate_max_error(
        expected,
        actual
    )

    final_level = ciphertext.GetLevel()

    print(
        f"Bootstrap Count: 0"
    )

    print(
        f"Final Level: {final_level}"
    )

    print(
        f"Maximum Error: {error:.6e}"
    )

    print(
        f"Total Time: {total_time:.6f} seconds"
    )

    return {
        "Experiment": "No Bootstrapping",
        "Operations": operations,
        "Threshold": "",
        "Bootstrap Count": 0,
        "Bootstrap Time": 0.0,
        "Final Level": final_level,
        "Maximum Absolute Error": error,
        "Total Execution Time": total_time
    }


# ==================================================
# Run Fixed-Bootstrap Experiment
# ==================================================

def run_fixed_experiment(operations):

    print(
        f"\n[FIXED BOOTSTRAP] "
        f"Operations = {operations}"
    )

    start_time = time.perf_counter()

    cc = create_crypto_context(
        32,
        enable_bootstrap=True
    )

    key_pair = generate_keys(cc)

    setup_bootstrap(
        cc,
        key_pair
    )

    (
        ciphertext,
        bootstrap_count,
        bootstrap_time
    ) = run_fixed_bootstrap(
        cc,
        key_pair,
        INPUT_DATA,
        operations,
        FIXED_BOOTSTRAP_INTERVAL
    )

    actual = decrypt_result(
        cc,
        key_pair.secretKey,
        ciphertext
    )

    total_time = (
        time.perf_counter()
        - start_time
    )

    expected = calculate_expected(
        INPUT_DATA,
        operations
    )

    error = calculate_max_error(
        expected,
        actual
    )

    final_level = ciphertext.GetLevel()

    print(
        f"Bootstrap Count: "
        f"{bootstrap_count}"
    )

    print(
        f"Final Level: "
        f"{final_level}"
    )

    print(
        f"Maximum Error: "
        f"{error:.6e}"
    )

    print(
        f"Total Time: "
        f"{total_time:.6f} seconds"
    )

    return {
        "Experiment": "Fixed Bootstrapping",
        "Operations": operations,
        "Threshold": FIXED_BOOTSTRAP_INTERVAL,
        "Bootstrap Count": bootstrap_count,
        "Bootstrap Time": bootstrap_time,
        "Final Level": final_level,
        "Maximum Absolute Error": error,
        "Total Execution Time": total_time
    }


# ==================================================
# Run Adaptive-Bootstrap Experiment
# ==================================================

def run_adaptive_experiment(
    operations,
    threshold
):

    print(
        f"\n[ADAPTIVE BOOTSTRAP] "
        f"Operations = {operations}, "
        f"Threshold = {threshold}"
    )

    start_time = time.perf_counter()

    cc = create_crypto_context(
        32,
        enable_bootstrap=True
    )

    key_pair = generate_keys(cc)

    setup_bootstrap(
        cc,
        key_pair
    )

    (
        ciphertext,
        bootstrap_count,
        bootstrap_time
    ) = run_adaptive_bootstrap(
        cc,
        key_pair,
        INPUT_DATA,
        operations,
        threshold
    )

    actual = decrypt_result(
        cc,
        key_pair.secretKey,
        ciphertext
    )

    total_time = (
        time.perf_counter()
        - start_time
    )

    expected = calculate_expected(
        INPUT_DATA,
        operations
    )

    error = calculate_max_error(
        expected,
        actual
    )

    final_level = ciphertext.GetLevel()

    print(
        f"Bootstrap Count: "
        f"{bootstrap_count}"
    )

    print(
        f"Final Level: "
        f"{final_level}"
    )

    print(
        f"Maximum Error: "
        f"{error:.6e}"
    )

    print(
        f"Total Time: "
        f"{total_time:.6f} seconds"
    )

    return {
        "Experiment": "Adaptive Bootstrapping",
        "Operations": operations,
        "Threshold": threshold,
        "Bootstrap Count": bootstrap_count,
        "Bootstrap Time": bootstrap_time,
        "Final Level": final_level,
        "Maximum Absolute Error": error,
        "Total Execution Time": total_time
    }


# ==================================================
# Main Stage 5 Experiment
# ==================================================

def main():

    results = []

    print("\n")
    print("=" * 60)
    print("STAGE 5 EXPERIMENT")
    print("=" * 60)

    # ----------------------------------------------
    # No Bootstrapping
    # ----------------------------------------------

    for operations in WORKLOADS:

        try:

            result = run_no_experiment(
                operations
            )

            results.append(result)

        except Exception as e:

            print(
                f"No-bootstrap experiment failed "
                f"for {operations} operations:"
            )

            print(e)

    # ----------------------------------------------
    # Fixed Bootstrapping
    # ----------------------------------------------

    for operations in WORKLOADS:

        try:

            result = run_fixed_experiment(
                operations
            )

            results.append(result)

        except Exception as e:

            print(
                f"Fixed-bootstrap experiment failed "
                f"for {operations} operations:"
            )

            print(e)

    # ----------------------------------------------
    # Adaptive Bootstrapping
    # ----------------------------------------------

    for operations in WORKLOADS:

        for threshold in ADAPTIVE_THRESHOLDS:

            try:

                result = run_adaptive_experiment(
                    operations,
                    threshold
                )

                results.append(result)

            except Exception as e:

                print(
                    f"Adaptive experiment failed "
                    f"for {operations} operations "
                    f"with threshold {threshold}:"
                )

                print(e)

    # ----------------------------------------------
    # Save Results
    # ----------------------------------------------

    os.makedirs(
        "results",
        exist_ok=True
    )

    output_file = (
        "results/stage5_results.csv"
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

    print("\n")
    print("=" * 60)
    print("STAGE 5 COMPLETED")
    print("=" * 60)

    print(
        f"\nResults saved to:"
    )

    print(
        output_file
    )


if __name__ == "__main__":

    main()
