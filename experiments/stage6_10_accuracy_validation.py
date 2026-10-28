from openfhe import *
import time
import os
import csv

print("=" * 70)
print("STAGE 6.10 - ADAPTIVE BOOTSTRAP ACCURACY VALIDATION")
print("=" * 70)

# --------------------------------------------------
# 1. CKKS PARAMETERS
# --------------------------------------------------

parameters = CCParamsCKKSRNS()

parameters.SetSecurityLevel(HEStd_NotSet)
parameters.SetRingDim(4096)

secret_key_dist = SecretKeyDist.UNIFORM_TERNARY
parameters.SetSecretKeyDist(secret_key_dist)

parameters.SetScalingModSize(59)
parameters.SetFirstModSize(60)

level_budget = [4, 4]
levels_available_after_bootstrap = 10

depth = (
    levels_available_after_bootstrap
    + FHECKKSRNS.GetBootstrapDepth(
        level_budget,
        secret_key_dist
    )
)

parameters.SetMultiplicativeDepth(depth)

# --------------------------------------------------
# 2. CRYPTO CONTEXT
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
# 3. BOOTSTRAP SETUP
# --------------------------------------------------

num_slots = int(cc.GetRingDimension() / 2)

cc.EvalBootstrapSetup(
    level_budget,
    [0, 0],
    num_slots
)

print("Bootstrap setup completed.")

# --------------------------------------------------
# 4. KEY GENERATION
# --------------------------------------------------

keys = cc.KeyGen()

if not keys:
    print("ERROR: Key generation failed.")
    exit()

cc.EvalMultKeyGen(
    keys.secretKey
)

cc.EvalBootstrapKeyGen(
    keys.secretKey,
    num_slots
)

print("Keys generated.")
print("Multiplication keys generated.")
print("Bootstrap keys generated.")

# --------------------------------------------------
# 5. INPUT DATA
# --------------------------------------------------

input_data = [
    0.1,
    0.2,
    0.3,
    0.4
]

plaintext = cc.MakeCKKSPackedPlaintext(
    input_data
)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 6. PERFORM TWO MULTIPLICATIONS
# --------------------------------------------------

print("\nPerforming two multiplications...")

ciphertext = cc.EvalMult(
    ciphertext,
    ciphertext
)

ciphertext = cc.EvalMult(
    ciphertext,
    ciphertext
)

level_before = ciphertext.GetLevel()

print("Level before bootstrap:", level_before)

# --------------------------------------------------
# 7. DECRYPT BEFORE BOOTSTRAP
# --------------------------------------------------

plaintext_before = cc.Decrypt(
    keys.secretKey,
    ciphertext
)

plaintext_before.SetLength(
    len(input_data)
)

result_before = plaintext_before.GetRealPackedValue()

print("\nResult before bootstrap:")
print(result_before)

# --------------------------------------------------
# 8. EXPECTED RESULT
# --------------------------------------------------

expected_result = [
    x ** 4 for x in input_data
]

# --------------------------------------------------
# 9. ERROR BEFORE BOOTSTRAP
# --------------------------------------------------

error_before = max(
    abs(a - b)
    for a, b in zip(
        expected_result,
        result_before
    )
)

print("\nExpected result:")
print(expected_result)

print("\nError before bootstrap:")
print(f"{error_before:.6e}")

# --------------------------------------------------
# 10. ACTUAL BOOTSTRAP
# --------------------------------------------------

print("\nStarting adaptive bootstrap...")

start_time = time.time()

ciphertext = cc.EvalBootstrap(
    ciphertext
)

bootstrap_time = time.time() - start_time

print("Bootstrap completed.")
print(
    "Bootstrap time:",
    f"{bootstrap_time:.6f}",
    "seconds"
)

print(
    "Level after bootstrap:",
    ciphertext.GetLevel()
)

# --------------------------------------------------
# 11. DECRYPT AFTER BOOTSTRAP
# --------------------------------------------------

plaintext_after = cc.Decrypt(
    keys.secretKey,
    ciphertext
)

plaintext_after.SetLength(
    len(input_data)
)

result_after = plaintext_after.GetRealPackedValue()

print("\nResult after bootstrap:")
print(result_after)

# --------------------------------------------------
# 12. ERROR AFTER BOOTSTRAP
# --------------------------------------------------

error_after = max(
    abs(a - b)
    for a, b in zip(
        expected_result,
        result_after
    )
)

print("\nError after bootstrap:")
print(f"{error_after:.6e}")

# --------------------------------------------------
# 13. SAVE RESULTS
# --------------------------------------------------

os.makedirs(
    "results",
    exist_ok=True
)

file_path = (
    "results/stage6_10_accuracy.csv"
)

with open(
    file_path,
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "Metric",
        "Value"
    ])

    writer.writerow([
        "Error Before Bootstrap",
        error_before
    ])

    writer.writerow([
        "Error After Bootstrap",
        error_after
    ])

    writer.writerow([
        "Bootstrap Time",
        bootstrap_time
    ])

    writer.writerow([
        "Level Before Bootstrap",
        level_before
    ])

    writer.writerow([
        "Level After Bootstrap",
        ciphertext.GetLevel()
    ])

print("\n" + "=" * 70)
print("STAGE 6.10 RESULTS")
print("=" * 70)

print(
    "Maximum error before bootstrap:",
    f"{error_before:.6e}"
)

print(
    "Maximum error after bootstrap:",
    f"{error_after:.6e}"
)

print(
    "Bootstrap time:",
    f"{bootstrap_time:.6f}",
    "seconds"
)

print("\nResults saved to:")
print(file_path)

print("=" * 70)
print("STAGE 6.10 COMPLETED")
print("=" * 70)
