from openfhe import *
import csv
import os

print("=" * 70)
print("STAGE 6.8 - PRACTICAL ADAPTIVE INDICATOR TEST")
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

print("\nCrypto context created.")
print("Ring dimension:", cc.GetRingDimension())

# --------------------------------------------------
# 3. KEYS
# --------------------------------------------------

keys = cc.KeyGen()

if not keys:
    print("ERROR: Key generation failed.")
    exit()

cc.EvalMultKeyGen(keys.secretKey)

print("Keys generated.")
print("Multiplication keys generated.")

# --------------------------------------------------
# 4. ENCRYPT DATA
# --------------------------------------------------

data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(data)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 5. ADAPTIVE PARAMETERS
# --------------------------------------------------

WINDOW_SIZE = 3
MAX_LEVEL = 6

operations_since_bootstrap = 0

results = []

# --------------------------------------------------
# 6. ADAPTIVE INDICATOR TEST
# --------------------------------------------------

for operation in range(1, 7):

    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    operations_since_bootstrap += 1

    current_level = ciphertext.GetLevel()

    remaining_capacity = (
        MAX_LEVEL - current_level
    )

    if (
        operations_since_bootstrap >= WINDOW_SIZE
        or current_level >= MAX_LEVEL
    ):
        condition = "HIGH"
        decision = "BOOTSTRAP"

    else:
        condition = "SAFE"
        decision = "CONTINUE"

    print("\n" + "-" * 60)
    print("Operation:", operation)
    print("Current ciphertext level:", current_level)
    print(
        "Operations since bootstrap:",
        operations_since_bootstrap
    )
    print(
        "Remaining capacity:",
        remaining_capacity
    )
    print("Adaptive condition:", condition)
    print("Decision:", decision)

    results.append([
        operation,
        current_level,
        operations_since_bootstrap,
        remaining_capacity,
        condition,
        decision
    ])

    # Only simulate the controller reset.
    # Actual bootstrap will be tested separately.
    if decision == "BOOTSTRAP":
        print("Bootstrap trigger recorded.")
        operations_since_bootstrap = 0

# --------------------------------------------------
# 7. SAVE
# --------------------------------------------------

os.makedirs("results", exist_ok=True)

file_path = "results/stage6_8_indicator_results.csv"

with open(file_path, "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "Operation",
        "Ciphertext Level",
        "Operations Since Bootstrap",
        "Remaining Capacity",
        "Adaptive Condition",
        "Decision"
    ])

    writer.writerows(results)

print("\n" + "=" * 70)
print("STAGE 6.8 INDICATOR TEST COMPLETED")
print("=" * 70)

print("Results saved to:")
print(file_path)
