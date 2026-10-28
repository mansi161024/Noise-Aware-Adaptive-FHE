from openfhe import *
import time

print("=" * 60)
print("STAGE 6.5 VALIDATION TEST")
print("=" * 60)

# --------------------------------------------------
# CKKS parameters
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
# Crypto context
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
# Bootstrap setup
# --------------------------------------------------

num_slots = int(cc.GetRingDimension() / 2)

cc.EvalBootstrapSetup(
    level_budget,
    [0, 0],
    num_slots
)

print("Bootstrap setup completed.")

# --------------------------------------------------
# Keys
# --------------------------------------------------

keys = cc.KeyGen()

cc.EvalMultKeyGen(keys.secretKey)

cc.EvalBootstrapKeyGen(
    keys.secretKey,
    num_slots
)

print("Keys generated.")

# --------------------------------------------------
# Encrypt
# --------------------------------------------------

data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(data)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# Perform two multiplications
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

print("Level before bootstrap:",
      ciphertext.GetLevel())

# --------------------------------------------------
# Decrypt BEFORE bootstrap
# --------------------------------------------------

before_plaintext = cc.Decrypt(
    keys.secretKey,
    ciphertext
)

before_plaintext.SetLength(len(data))

before_result = (
    before_plaintext.GetRealPackedValue()
)

print("\nResult before bootstrap:")
print(before_result)

# --------------------------------------------------
# Bootstrap
# --------------------------------------------------

print("\nStarting bootstrap...")

start = time.time()

ciphertext = cc.EvalBootstrap(
    ciphertext
)

bootstrap_time = time.time() - start

print("Bootstrap completed.")
print("Bootstrap time:",
      round(bootstrap_time, 6),
      "seconds")

print("Level after bootstrap:",
      ciphertext.GetLevel())

# --------------------------------------------------
# Decrypt AFTER bootstrap
# --------------------------------------------------

after_plaintext = cc.Decrypt(
    keys.secretKey,
    ciphertext
)

after_plaintext.SetLength(len(data))

after_result = (
    after_plaintext.GetRealPackedValue()
)

print("\nResult after bootstrap:")
print(after_result)

# --------------------------------------------------
# Calculate errors
# --------------------------------------------------

expected = [
    x ** 4
    for x in data
]

before_error = max(
    abs(a - b)
    for a, b in zip(
        expected,
        before_result
    )
)

after_error = max(
    abs(a - b)
    for a, b in zip(
        expected,
        after_result
    )
)

print("\n" + "=" * 60)
print("VALIDATION RESULTS")
print("=" * 60)

print("Expected result:")
print(expected)

print("\nError before bootstrap:")
print(f"{before_error:.6e}")

print("\nError after bootstrap:")
print(f"{after_error:.6e}")

print("\nBootstrap time:")
print(f"{bootstrap_time:.6f} seconds")

print("=" * 60)
print("VALIDATION TEST COMPLETED")
print("=" * 60)
