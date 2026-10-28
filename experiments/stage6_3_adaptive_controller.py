from openfhe import *
import time

print("=" * 60)
print("STAGE 6.3 - ADAPTIVE DECISION CONTROLLER")
print("=" * 60)

# --------------------------------------------------
# 1. CKKS Parameters
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
# 2. Crypto Context
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
# 3. Bootstrap Setup
# --------------------------------------------------

num_slots = int(cc.GetRingDimension() / 2)

cc.EvalBootstrapSetup(
    level_budget,
    [0, 0],
    num_slots
)

print("Bootstrap setup completed.")

# --------------------------------------------------
# 4. Key Generation
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
    num_slots
)

print("Bootstrap keys generated.")

# --------------------------------------------------
# 5. Encryption
# --------------------------------------------------

input_data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(
    input_data
)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 6. Adaptive Parameters
# --------------------------------------------------

MAX_DEPTH = 6
CAPACITY_THRESHOLD = 2

total_bootstraps = 0
total_bootstrap_time = 0.0

print("\nMaximum depth:", MAX_DEPTH)
print("Capacity threshold:", CAPACITY_THRESHOLD)

# --------------------------------------------------
# 7. Adaptive Computation
# --------------------------------------------------

for operation in range(1, 7):

    print("\n" + "=" * 50)
    print("Operation:", operation)

    # Homomorphic multiplication
    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    current_level = ciphertext.GetLevel()

    remaining_capacity = (
        MAX_DEPTH - current_level
    )

    print(
        "Current ciphertext level:",
        current_level
    )

    print(
        "Remaining capacity:",
        remaining_capacity
    )

    # --------------------------------------------------
    # Adaptive Decision
    # --------------------------------------------------

    if remaining_capacity <= CAPACITY_THRESHOLD:

        print("Condition: HIGH")
        print("Decision: BOOTSTRAP")

        start_time = time.time()

        ciphertext = cc.EvalBootstrap(
            ciphertext
        )

        bootstrap_time = (
            time.time() - start_time
        )

        total_bootstraps += 1
        total_bootstrap_time += bootstrap_time

        print("Bootstrap completed.")
        print(
            "Bootstrap time:",
            round(bootstrap_time, 4),
            "seconds"
        )

    else:

        print("Condition: SAFE")
        print("Decision: CONTINUE")

# --------------------------------------------------
# 8. Final Results
# --------------------------------------------------

print("\n")
print("=" * 60)
print("STAGE 6.3 RESULTS")
print("=" * 60)

print(
    "Total bootstrap operations:",
    total_bootstraps
)

print(
    "Total bootstrap time:",
    round(total_bootstrap_time, 4),
    "seconds"
)

print(
    "Final ciphertext level:",
    ciphertext.GetLevel()
)

print("=" * 60)
print("STAGE 6.3 COMPLETED")
print("=" * 60)
