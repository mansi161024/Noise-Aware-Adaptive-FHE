from openfhe import *
import time


print("Experiment A - No Bootstrapping")
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

# No bootstrap is used in this experiment.
# We only need enough depth for the multiplications.
parameters.SetMultiplicativeDepth(6)


# --------------------------------------------------
# 2. Create crypto context
# --------------------------------------------------

cc = GenCryptoContext(parameters)

cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)

print("\nCrypto context created.")
print("Ring dimension:", cc.GetRingDimension())


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


# --------------------------------------------------
# 4. Input data
# --------------------------------------------------

input_data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(
    input_data
)


# --------------------------------------------------
# 5. Encryption
# --------------------------------------------------

start_total = time.perf_counter()

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("\nData encrypted.")


# --------------------------------------------------
# 6. Homomorphic computation
# --------------------------------------------------

number_of_operations = 4

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
# 7. Decryption
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
# 8. Calculate expected result
# --------------------------------------------------

# Each multiplication squares the previous result.
#
# Starting value:
# x
#
# After operation 1:
# x^2
#
# After operation 2:
# x^4
#
# After operation 3:
# x^8
#
# After operation 4:
# x^16

expected_values = [
    x ** 16 for x in input_data
]


# --------------------------------------------------
# 9. Calculate errors
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
# 10. Results
# --------------------------------------------------

print("\n========================================")
print("EXPERIMENT A RESULTS")
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
print(0)

print("\nTotal execution time:")
print("{:.6f} seconds".format(total_time))

print("\n========================================")
print("Experiment A completed.")
print("========================================")
