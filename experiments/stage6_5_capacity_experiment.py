from openfhe import *
import time
import csv
import os

print("=" * 70)
print("STAGE 6.5 - CORRECTED CAPACITY-BASED ADAPTIVE EXPERIMENT")
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

print("Encryption keys generated.")

cc.EvalMultKeyGen(
    keys.secretKey
)

print("Multiplication keys generated.")

cc.EvalBootstrapKeyGen(
    keys.secretKey,
    num_slots
)

print("Bootstrap keys generated.")

# --------------------------------------------------
# 5. ENCRYPT DATA
# --------------------------------------------------

data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(data)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 6. ADAPTIVE SETTINGS
# --------------------------------------------------

TOTAL_OPERATIONS = 6

# Maximum number of operations allowed
# inside one adaptive window.
WINDOW_SIZE = 3

operations_since_bootstrap = 0
bootstrap_count = 0
total_bootstrap_time = 0.0

# --------------------------------------------------
# 7. HOMOMORPHIC COMPUTATION
# --------------------------------------------------

start_total = time.time()

for operation in range(1, TOTAL_OPERATIONS + 1):

    print("\n" + "-" * 60)
    print("Operation:", operation)

    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    operations_since_bootstrap += 1

    current_level = ciphertext.GetLevel()

    print(
        "Current ciphertext level:",
        current_level
    )

    print(
        "Operations in current adaptive window:",
        operations_since_bootstrap
    )

    # --------------------------------------------------
    # ADAPTIVE DECISION
    # --------------------------------------------------

    if operations_since_bootstrap >= WINDOW_SIZE:

        print("Adaptive condition: HIGH")
        print("Decision: BOOTSTRAP")

        start_bootstrap = time.time()

        ciphertext = cc.EvalBootstrap(
            ciphertext
        )

        bootstrap_time = (
            time.time() - start_bootstrap
        )

        bootstrap_count += 1

        total_bootstrap_time += bootstrap_time

        print("Bootstrap completed.")

        print(
            "Bootstrap time:",
            round(bootstrap_time, 6),
            "seconds"
        )

        # Reset adaptive window
        operations_since_bootstrap = 0

        print(
            "Adaptive window reset."
        )

    else:

        print("Adaptive condition: SAFE")
        print("Decision: CONTINUE")

# --------------------------------------------------
# 8. TOTAL TIME
# --------------------------------------------------

total_time = time.time() - start_total

# --------------------------------------------------
# 9. DECRYPTION
# --------------------------------------------------

decrypted_plaintext = cc.Decrypt(
    keys.secretKey,
    ciphertext
)

decrypted_plaintext.SetLength(
    len(data)
)

result = (
    decrypted_plaintext.GetRealPackedValue()
)

# --------------------------------------------------
# 10. EXPECTED RESULT
# --------------------------------------------------

expected = [
    x ** TOTAL_OPERATIONS
    for x in data
]

# --------------------------------------------------
# 11. ERROR
# --------------------------------------------------

max_error = max(
    abs(original - decrypted)
    for original, decrypted
    in zip(expected, result)
)

# --------------------------------------------------
# 12. RESULTS
# --------------------------------------------------

print("\n")
print("=" * 70)
print("STAGE 6.5 CORRECTED RESULTS")
print("=" * 70)

print("Total operations:", TOTAL_OPERATIONS)

print(
    "Bootstrap count:",
    bootstrap_count
)

print(
    "Total bootstrap time:",
    round(total_bootstrap_time, 6),
    "seconds"
)

print(
    "Maximum absolute error:",
    f"{max_error:.6e}"
)

print(
    "Total execution time:",
    round(total_time, 6),
    "seconds"
)

print(
    "Final ciphertext level:",
    ciphertext.GetLevel()
)

# --------------------------------------------------
# 13. SAVE RESULTS
# --------------------------------------------------

os.makedirs(
    "results",
    exist_ok=True
)

file_path = (
    "results/stage6_5_corrected_results.csv"
)

with open(
    file_path,
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "Experiment",
        "Operations",
        "Window Size",
        "Bootstrap Count",
        "Bootstrap Time",
        "Final Level",
        "Maximum Absolute Error",
        "Total Execution Time"
    ])

    writer.writerow([
        "Corrected Capacity-Based Adaptive",
        TOTAL_OPERATIONS,
        WINDOW_SIZE,
        bootstrap_count,
        total_bootstrap_time,
        ciphertext.GetLevel(),
        max_error,
        total_time
    ])

print("\nResults saved to:")
print(file_path)

print("\n" + "=" * 70)
print("STAGE 6.5 CORRECTED COMPLETED")
print("=" * 70)
