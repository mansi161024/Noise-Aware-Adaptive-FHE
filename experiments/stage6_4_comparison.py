import csv
import os

print("=" * 70)
print("STAGE 6.4 - ADAPTIVE METHOD COMPARISON")
print("=" * 70)

print("\nComparison of adaptive decision methods:")
print()
print("Method 1: Operation-count based")
print("Method 2: Remaining-capacity based")

print("\n" + "-" * 70)

# Example decision sequences from the experimental design

operation_threshold = 2
capacity_threshold = 2
maximum_depth = 6

print("\nOperation-count based method")
print("Threshold:", operation_threshold)

operations_since_bootstrap = 0

for operation in range(1, 7):

    operations_since_bootstrap += 1

    if operations_since_bootstrap >= operation_threshold:
        decision = "BOOTSTRAP"
        operations_since_bootstrap = 0
    else:
        decision = "CONTINUE"

    print(
        "Operation:",
        operation,
        "Decision:",
        decision
    )

print("\n" + "-" * 70)

print("\nRemaining-capacity based method")
print("Maximum depth:", maximum_depth)
print("Capacity threshold:", capacity_threshold)

for level in range(1, 7):

    remaining_capacity = maximum_depth - level

    if remaining_capacity <= capacity_threshold:
        decision = "BOOTSTRAP"
    else:
        decision = "CONTINUE"

    print(
        "Level:",
        level,
        "Remaining capacity:",
        remaining_capacity,
        "Decision:",
        decision
    )

print("\n" + "=" * 70)
print("STAGE 6.4 COMPLETED")
print("=" * 70)
