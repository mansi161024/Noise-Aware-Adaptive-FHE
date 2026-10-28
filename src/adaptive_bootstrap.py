from openfhe import *
import time


print("Adaptive Bootstrap Controller Test")
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

cc = GenCryptoContext(parameters)

cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)
cc.Enable(ADVANCEDSHE)
cc.Enable(FHE)

print("\nCrypto context created.")
print("Ring dimension:", cc.GetRingDimension())


# --------------------------------------------------
# 2. Bootstrap setup
# --------------------------------------------------

num_slots = int(cc.GetRingDimension() / 2)

cc.EvalBootstrapSetup(
    level_budget,
    [0, 0],
    num_slots
)

print("Bootstrap setup completed.")


# --------------------------------------------------
# 3. Generate keys
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
# 4. Encrypt data
# --------------------------------------------------

input_data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(input_data)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("\nData encrypted.")


# --------------------------------------------------
# 5. Adaptive controller
# --------------------------------------------------

LEVEL_THRESHOLD = 2

# Number of multiplication operations
# performed since the last bootstrap.
operations_since_bootstrap = 0

bootstrap_count = 0

print("\nAdaptive threshold:", LEVEL_THRESHOLD)


# --------------------------------------------------
# 6. Perform adaptive computation
# --------------------------------------------------

for operation in range(1, 7):

    print("\n========================================")
    print("Operation:", operation)

    # Homomorphic multiplication
    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    operations_since_bootstrap += 1

    current_level = ciphertext.GetLevel()

    print("Current ciphertext level:", current_level)

    print(
        "Operations since last bootstrap:",
        operations_since_bootstrap
    )

    # --------------------------------------------------
    # Adaptive decision
    # --------------------------------------------------

    if operations_since_bootstrap >= LEVEL_THRESHOLD:

        print("Adaptive condition reached.")
        print("Decision: BOOTSTRAP")

        level_before_bootstrap = ciphertext.GetLevel()

        print(
            "Level before bootstrap:",
            level_before_bootstrap
        )

        start_time = time.perf_counter()

        ciphertext = cc.EvalBootstrap(
            ciphertext
        )

        end_time = time.perf_counter()

        bootstrap_time = end_time - start_time

        level_after_bootstrap = ciphertext.GetLevel()

        bootstrap_count += 1

        print("Bootstrap completed.")

        print(
            "Level after bootstrap:",
            level_after_bootstrap
        )

        print(
            "Bootstrap time: {:.4f} seconds".format(
                bootstrap_time
            )
        )

        # Reset our controller counter.
        operations_since_bootstrap = 0

        print(
            "Operations since last bootstrap reset to 0."
        )

    else:

        print("Adaptive condition not reached.")
        print("Decision: CONTINUE")


# --------------------------------------------------
# 7. Final information
# --------------------------------------------------

print("\n========================================")
print("Adaptive computation completed.")
print("Total bootstrap operations:", bootstrap_count)
print("========================================")
