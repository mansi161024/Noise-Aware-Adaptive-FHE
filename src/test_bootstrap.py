from openfhe import *
import time

print("CKKS Single Bootstrap Test")
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

# --------------------------------------------------
# 2. Create CryptoContext
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

num_slots = int(cc.GetRingDimension() / 2)

cc.EvalBootstrapSetup(
    level_budget,
    [0, 0],
    num_slots
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
    num_slots
)

print("Bootstrap keys generated.")

# --------------------------------------------------
# 5. Create plaintext
# --------------------------------------------------

input_data = [0.10, 0.20, 0.30, 0.40]

plaintext = cc.MakeCKKSPackedPlaintext(input_data)

print("\nOriginal data:")
print(input_data)

# --------------------------------------------------
# 6. Encrypt
# --------------------------------------------------

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 7. Perform a small homomorphic computation
# --------------------------------------------------

ciphertext = cc.EvalAdd(
    ciphertext,
    ciphertext
)

print("Homomorphic addition completed.")

# --------------------------------------------------
# 8. Bootstrap
# --------------------------------------------------

print("\nStarting bootstrap...")

start_time = time.perf_counter()

ciphertext_bootstrapped = cc.EvalBootstrap(
    ciphertext
)

end_time = time.perf_counter()

bootstrap_time = end_time - start_time

print("Bootstrap completed.")

print("Bootstrap time: {:.4f} seconds".format(bootstrap_time))

# --------------------------------------------------
# 9. Decrypt
# --------------------------------------------------

result = cc.Decrypt(
    keys.secretKey,
    ciphertext_bootstrapped
)

result.SetLength(len(input_data))

print("\nDecrypted result:")
print(result.GetRealPackedValue())

decrypted_values = result.GetRealPackedValue()

print("\nDecrypted result:")
print(decrypted_values)

expected_values = [0.2, 0.4, 0.6, 0.8]

print("\nAbsolute errors:")

errors = []

for expected, actual in zip(expected_values, decrypted_values):
    error = abs(expected - actual)
    errors.append(error)
    print("Expected:", expected,
          "Decrypted:", actual,
          "Error:", error)

max_error = max(errors)

print("\nMaximum absolute error:", max_error)

# --------------------------------------------------
# 10. Final information
# --------------------------------------------------

print("\n========================================")
print("Stage 2.6 completed.")
print("========================================")
