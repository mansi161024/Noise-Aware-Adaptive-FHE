from openfhe import *
import csv
import os

print("=" * 70)
print("STAGE 6.6 - LEVEL VS NUMERICAL ERROR TEST")
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
# 3. KEY GENERATION
# --------------------------------------------------

keys = cc.KeyGen()

if not keys:
    print("ERROR: Key generation failed.")
    exit()

print("Keys generated.")

cc.EvalMultKeyGen(
    keys.secretKey
)

print("Multiplication keys generated.")

# --------------------------------------------------
# 4. INPUT DATA
# --------------------------------------------------

data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(data)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 5. MEASURE INITIAL ERROR
# --------------------------------------------------

expected = data[:]

results = []

# --------------------------------------------------
# LEVEL 0
# --------------------------------------------------

decrypted = cc.Decrypt(
    keys.secretKey,
    ciphertext
)

decrypted.SetLength(len(data))

result = decrypted.GetRealPackedValue()

error = max(
    abs(a - b)
    for a, b in zip(expected, result)
)

level = ciphertext.GetLevel()

print("\nLevel:", level)
print("Maximum absolute error:", f"{error:.6e}")

results.append([
    0,
    level,
    error
])

# --------------------------------------------------
# 6. REPEATED MULTIPLICATION
# --------------------------------------------------

for operation in range(1, 7):

    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    level = ciphertext.GetLevel()

    decrypted = cc.Decrypt(
        keys.secretKey,
        ciphertext
    )

    decrypted.SetLength(len(data))

    result = decrypted.GetRealPackedValue()

    # Expected x^(2^operation)
    power = 2 ** operation

    expected_result = [
        x ** power
        for x in data
    ]

    error = max(
        abs(a - b)
        for a, b in zip(
            expected_result,
            result
        )
    )

    print("\nOperation:", operation)
    print("Ciphertext level:", level)
    print(
        "Maximum absolute error:",
        f"{error:.6e}"
    )

    results.append([
        operation,
        level,
        error
    ])

# --------------------------------------------------
# 7. SAVE RESULTS
# --------------------------------------------------

os.makedirs(
    "results",
    exist_ok=True
)

file_path = (
    "results/stage6_6_level_error.csv"
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
        "Maximum Absolute Error"
    ])

    writer.writerows(results)

print("\n" + "=" * 70)
print("STAGE 6.6 RESULTS SAVED")
print("=" * 70)

print(file_path)

print("\nStage 6.6 completed.")
