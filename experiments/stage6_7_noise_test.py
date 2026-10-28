from openfhe import *
import csv
import os

print("=" * 70)
print("STAGE 6.7 - NOISE ESTIMATE TEST")
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
# 5. RESULTS STORAGE
# --------------------------------------------------

results = []

# --------------------------------------------------
# 6. MONITOR INITIAL STATE
# --------------------------------------------------

level = ciphertext.GetLevel()
noise_scale = ciphertext.GetNoiseScaleDeg()
noise_estimate = cc.GetNoiseEstimate()

print("\n" + "-" * 60)
print("Operation: 0")
print("Ciphertext Level:", level)
print("Noise Scale Degree:", noise_scale)
print("Noise Estimate:", noise_estimate)

results.append([
    0,
    level,
    noise_scale,
    noise_estimate
])

# --------------------------------------------------
# 7. HOMOMORPHIC OPERATIONS
# --------------------------------------------------

for operation in range(1, 7):

    ciphertext = cc.EvalMult(
        ciphertext,
        ciphertext
    )

    level = ciphertext.GetLevel()
    noise_scale = ciphertext.GetNoiseScaleDeg()
    noise_estimate = cc.GetNoiseEstimate()

    print("\n" + "-" * 60)
    print("Operation:", operation)
    print("Ciphertext Level:", level)
    print("Noise Scale Degree:", noise_scale)
    print("Noise Estimate:", noise_estimate)

    results.append([
        operation,
        level,
        noise_scale,
        noise_estimate
    ])

# --------------------------------------------------
# 8. SAVE RESULTS
# --------------------------------------------------

os.makedirs(
    "results",
    exist_ok=True
)

file_path = (
    "results/stage6_7_noise_results.csv"
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
        "Noise Scale Degree",
        "Noise Estimate"
    ])

    writer.writerows(results)

print("\n" + "=" * 70)
print("STAGE 6.7 RESULTS SAVED")
print("=" * 70)

print(file_path)

print("\nStage 6.7 completed.")
