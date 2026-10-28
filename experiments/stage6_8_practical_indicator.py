from openfhe import *
import csv
import os
import time

print("=" * 70)
print("STAGE 6.8 - PRACTICAL ADAPTIVE INDICATOR")
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

parameters.SetMultiplicativeDepth(8)

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
# 3. BOOTSTRAPPING SETUP
# --------------------------------------------------

level_budget = [4, 4]
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
# 6. ADAPTIVE PARAMETERS
# --------------------------------------------------

WINDOW_SIZE = 3
MAX_LEVEL = 6

operations_since_bootstrap = 0
bootstrap_count = 0
total_bootstrap_time = 0.0

results = []

# --------------------------------------------------
# 7. HOMOMORPHIC COMPUTATION
# --------------------------------------------------

for operation in range(1, 7):

    print("\n" + "-" * 60)
    print("Operation:", operation)

    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    operations_since_bootstrap += 1

    current_level = ciphertext.GetLevel()

    remaining_capacity = MAX_LEVEL - current_level

    print("Current ciphertext level:", current_level)
    print(
        "Operations since bootstrap:",
        operations_since_bootstrap
    )
    print(
        "Remaining capacity:",
        remaining_capacity
    )

    # --------------------------------------------------
    # ADAPTIVE INDICATOR
    # --------------------------------------------------

    if (
        operations_since_bootstrap >= WINDOW_SIZE
        or current_level >= MAX_LEVEL
    ):

        condition = "HIGH"
        decision = "BOOTSTRAP"

        print("Adaptive condition:", condition)
        print("Decision:", decision)

        start_time = time.time()

        ciphertext = cc.EvalBootstrap(
            ciphertext
        )

        bootstrap_time = time.time() - start_time

        bootstrap_count += 1
        total_bootstrap_time += bootstrap_time

        print("Bootstrap completed.")
        print(
            "Bootstrap time:",
            f"{bootstrap_time:.6f}",
            "seconds"
        )

        operations_since_bootstrap = 0

    else:

        condition = "SAFE"
        decision = "CONTINUE"
        bootstrap_time = 0.0

        print("Adaptive condition:", condition)
        print("Decision:", decision)

    # --------------------------------------------------
    # RECORD RESULT
    # --------------------------------------------------

    results.append([
        operation,
        current_level,
        operations_since_bootstrap,
        remaining_capacity,
        condition,
        decision,
        bootstrap_time
    ])

# --------------------------------------------------
# 8. SAVE RESULTS
# --------------------------------------------------

os.makedirs(
    "results",
    exist_ok=True
)

file_path = (
    "results/stage6_8_results.csv"
)

with open(
    file_path,
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "Operation",
        "Ciphertext Level",
        "Operations Since Bootstrap",
        "Remaining Capacity",
        "Adaptive Condition",
        "Decision",
        "Bootstrap Time"
    ])

    writer.writerows(results)

# --------------------------------------------------
# 9. FINAL RESULTS
# --------------------------------------------------

print("\n" + "=" * 70)
print("STAGE 6.8 RESULTS")
print("=" * 70)

print("Total operations:", 6)
print("Bootstrap count:", bootstrap_count)
print(
    "Total bootstrap time:",
    f"{total_bootstrap_time:.6f}",
    "seconds"
)
print(
    "Final ciphertext level:",
    ciphertext.GetLevel()
)

print("\nResults saved to:")
print(file_path)

print("\n" + "=" * 70)
print("STAGE 6.8 COMPLETED")
print("=" * 70)
