from fhe_runner import run_adaptive_experiment


input_data = [
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6
]

print("Starting direct 6-operation test...")
print("Input:", input_data)
print("Operations:", 6)
print("Threshold:", 2)

result = run_adaptive_experiment(
    input_data=input_data,
    number_of_operations=6,
    operation_threshold=2
)

print("\n===================================")
print("TEST COMPLETED")
print("===================================")

print("Strategy:")
print(result["strategy"])

print("Operations:")
print(result["operations"])

print("Threshold:")
print(result["threshold"])

print("Bootstrap count:")
print(result["bootstrap_count"])

print("Final ciphertext level:")
print(result["final_ciphertext_level"])

print("Maximum absolute error:")
print(result["maximum_absolute_error"])

print("Total bootstrap time:")
print(result["total_bootstrap_time"])

print("Total execution time:")
print(result["total_execution_time"])

print("\nOperation data:")

for operation in result["operation_data"]:
    print(operation)