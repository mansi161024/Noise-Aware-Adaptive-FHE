from openfhe import *
import time


print("Experiment C - Adaptive Bootstrapping")
print("=" * 50)


# --------------------------------------------------
# 1. CKKS parameters
# --------------------------------------------------

parameters = CCParamsCKKSRNS()

parameters.SetSecurityLevel(HEStd_NotSet)
parameters.SetRingDim(1 << 12)

secret_key_dist = SecretKeyDist.UNIFORM_TERNARY
parameters.SetSecretKeyDist(secret_key_dist)

parameters.SetScalingModSize(59)
parameters.SetFirstModSize(60)

# Enough depth for the experiment and bootstrapping.
parameters.SetMultiplicativeDepth(32)


# --------------------------------------------------
# 2. Create crypto context
# --------------------------------------------------

cc = GenCryptoContext(parameters)

cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)
cc.Enable(ADVANCEDSHE)
cc.Enable(FHE)

print("\nCrypto context created.")
print("Ring dimension:", cc.GetRingDimension())


# --------------------------------------------------
# 3. Bootstrap setup
# --------------------------------------------------

level_budget = [4, 4]

print("\nSetting up bootstrapping...")

cc.EvalBootstrapSetup(
    level_budget,
    [0, 0],
    2048
)

print("Bootstrap setup completed.")


# --------------------------------------------------
# 4. Generate keys
# --------------------------------------------------

keys = cc.KeyGen()

if not keys:
    print("ERROR: Key generation failed.")
    exit()

print("Encryption keys generated.")

cc.EvalMultKeyGen(keys.secretKey)

print("Multiplication keys generated.")

cc.EvalBootstrapKeyGen(
    keys.secretKey,
    2048
)

print("Bootstrap keys generated.")


# --------------------------------------------------
# 5. Input data
# --------------------------------------------------

input_data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(
    input_data
)


# --------------------------------------------------
# 6. Adaptive controller settings
# --------------------------------------------------

number_of_operations = 4

# The controller triggers a bootstrap when
# the number of operations since the previous
# bootstrap reaches this threshold.

OPERATION_THRESHOLD = 2

operations_since_bootstrap = 0

bootstrap_count = 0

total_bootstrap_time = 0.0


# --------------------------------------------------
# 7. Encryption
# --------------------------------------------------

start_total = time.perf_counter()

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("\nData encrypted.")


# --------------------------------------------------
# 8. Adaptive homomorphic computation
# --------------------------------------------------

print("\nStarting adaptive homomorphic computation...")

for operation in range(1, number_of_operations + 1):

    # Perform one homomorphic multiplication.
    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    # Update controller state.
    operations_since_bootstrap += 1

    current_level = ciphertext.GetLevel()

    print(
        "\nOperation",
        operation
    )

    print(
        "Ciphertext level:",
        current_level
    )

    print(
        "Operations since bootstrap:",
        operations_since_bootstrap
    )


    # --------------------------------------------------
    # Adaptive decision
    # --------------------------------------------------

    if operations_since_bootstrap >= OPERATION_THRESHOLD:

        print("Adaptive condition: BOOTSTRAP")

        bootstrap_start = time.perf_counter()

        ciphertext = cc.EvalBootstrap(
            ciphertext
        )

        bootstrap_end = time.perf_counter()

        bootstrap_time = (
            bootstrap_end - bootstrap_start
        )

        total_bootstrap_time += bootstrap_time

        bootstrap_count += 1

        print(
            "Bootstrap completed."
        )

        print(
            "Bootstrap time:",
            "{:.6f} seconds".format(
                bootstrap_time
            )
        )

        # Reset the controller's operation counter.
        operations_since_bootstrap = 0

    else:

        print("Adaptive condition: CONTINUE")


# --------------------------------------------------
# 9. Decryption
# --------------------------------------------------

result = cc.Decrypt(
    keys.secretKey,
    ciphertext
)

result.SetLength(len(input_data))

decrypted_values = result.GetRealPackedValue()

end_total = time.perf_counter()

total_time = end_total - start_total


# --------------------------------------------------
# 10. Calculate expected result
# --------------------------------------------------

# Four squaring operations produce x^16.

expected_values = [
    x ** 16 for x in input_data
]


# --------------------------------------------------
# 11. Calculate errors
# --------------------------------------------------

errors = []

for expected, actual in zip(
    expected_values,
    decrypted_values
):

    error = abs(expected - actual)

    errors.append(error)


max_error = max(errors)


# --------------------------------------------------
# 12. Results
# --------------------------------------------------

print("\n========================================")
print("EXPERIMENT C RESULTS")
print("========================================")

print("Original data:")
print(input_data)

print("\nExpected result:")
print(expected_values)

print("\nDecrypted result:")
print(decrypted_values)

print("\nMaximum absolute error:")
print(max_error)

print("\nFinal ciphertext level:")
print(ciphertext.GetLevel())

print("\nBootstrap count:")
print(bootstrap_count)

print("\nTotal bootstrap time:")
print(
    "{:.6f} seconds".format(
        total_bootstrap_time
    )
)

print("\nTotal execution time:")
print(
    "{:.6f} seconds".format(
        total_time
    )
)

print("\n========================================")
print("Experiment C completed.")
print("========================================")
