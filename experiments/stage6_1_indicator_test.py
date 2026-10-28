from openfhe import *

print("=" * 60)
print("STAGE 6.1 - CKKS INDICATOR TEST")
print("=" * 60)

# --------------------------------------------------
# 1. CKKS Parameters
# --------------------------------------------------

parameters = CCParamsCKKSRNS()

parameters.SetMultiplicativeDepth(8)
parameters.SetScalingModSize(59)
parameters.SetFirstModSize(60)
parameters.SetBatchSize(8)
parameters.SetRingDim(32768)

# --------------------------------------------------
# 2. Create Crypto Context
# --------------------------------------------------

cc = GenCryptoContext(parameters)

cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)

print("\nCrypto context created.")
print("Ring dimension:", cc.GetRingDimension())

# --------------------------------------------------
# 3. Generate Keys
# --------------------------------------------------

keys = cc.KeyGen()

if not keys:
    print("ERROR: Key generation failed.")
    exit()

print("Keys generated.")

cc.EvalMultKeyGen(keys.secretKey)

print("Multiplication keys generated.")

# --------------------------------------------------
# 4. Encrypt Data
# --------------------------------------------------

data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(data)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 5. Monitor Ciphertext
# --------------------------------------------------

print("\n")
print("=" * 60)
print("INDICATOR MONITORING")
print("=" * 60)

for operation in range(0, 7):

    if operation > 0:
        ciphertext = cc.EvalMult(
            ciphertext,
            ciphertext
        )

    level = ciphertext.GetLevel()

    noise_scale_degree = ciphertext.GetNoiseScaleDeg()

    try:
        noise_estimate = cc.GetNoiseEstimate()
    except Exception:
        noise_estimate = "Unavailable"

    print("\nOperation:", operation)
    print("Ciphertext Level:", level)
    print("Noise Scale Degree:", noise_scale_degree)
    print("Noise Estimate:", noise_estimate)

print("\n")
print("=" * 60)
print("STAGE 6.1 TEST COMPLETED")
print("=" * 60)
