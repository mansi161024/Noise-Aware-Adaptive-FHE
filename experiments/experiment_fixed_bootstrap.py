from openfhe import *
import time


print("Experiment B - Fixed Bootstrapping")
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

# We need enough depth for the computation
# and the bootstrapping operation.
level_budget = [4, 4]
levels_available_after_bootstrap = 10

depth = 32

parameters.SetMultiplicativeDepth(depth)


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
# 6. Encryption
# --------------------------------------------------

start_total = time.perf_counter()

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("\nData encrypted.")


# --------------------------------------------------
# 7. Fixed homomorphic computation
# --------------------------------------------------

number_of_operations = 4

# Fixed bootstrap point:
# Bootstrap after operation 2.

fixed_bootstrap_after = 2

bootstrap_count = 0

print("\nStarting homomorphic computation...")

for operation in range(1, number_of_operations + 1):

    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    current_level = ciphertext.GetLevel()

    print(
        "Operation",
        operation,
        "- Ciphertext level:",
        current_level
    )

    # --------------------------------------------------
    # Fixed bootstrapping
    # --------------------------------------------------

    if operation == fixed_bootstrap_after:

        print("\nFixed bootstrap triggered.")

        bootstrap_start = time.perf_counter()

        ciphertext = cc.EvalBootstrap(
            ciphertext
        )

        bootstrap_end = time.perf_counter()

        bootstrap_time = bootstrap_end - bootstrap_start

        bootstrap_count += 1

        print(
            "Bootstrap completed."
        )

        print(
            "Bootstrap time:",
            "{:.6f} seconds".format(bootstrap_time)
        )


# --------------------------------------------------
# 8. Decryption
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
# 9. Calculate expected result
# --------------------------------------------------

# Four squaring operations produce x^16.

expected_values = [
    x ** 16 for x in input_data
]


# --------------------------------------------------
# 10. Calculate errors
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
# 11. Results
# --------------------------------------------------

print("\n========================================")
print("EXPERIMENT B RESULTS")
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

print("\nTotal execution time:")
print(
    "{:.6f} seconds".format(total_time)
)

print("\n========================================")
print("Experiment B completed.")
print("========================================")
