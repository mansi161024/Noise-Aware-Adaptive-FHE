from openfhe import *


def monitor_ciphertext(cc, ciphertext, operation_name):
    """
    Collect observable ciphertext condition indicators.
    """

    level = ciphertext.GetLevel()
    noise_scale_deg = ciphertext.GetNoiseScaleDeg()
    noise_estimate = cc.GetNoiseEstimate()

    print("\n----------------------------------------")
    print("Operation:", operation_name)
    print("Ciphertext Level:", level)
    print("Noise Scale Degree:", noise_scale_deg)
    print("Noise Estimate:", noise_estimate)
    print("----------------------------------------")

    return {
        "operation": operation_name,
        "level": level,
        "noise_scale_degree": noise_scale_deg,
        "noise_estimate": noise_estimate
    }


print("CKKS Noise/Precision Monitoring Test")
print("=" * 50)

# --------------------------------------------------
# 1. Create CKKS parameters
# --------------------------------------------------

parameters = CCParamsCKKSRNS()

parameters.SetMultiplicativeDepth(8)
parameters.SetScalingModSize(50)
parameters.SetBatchSize(8)

cc = GenCryptoContext(parameters)

cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)
cc.Enable(ADVANCEDSHE)
cc.Enable(FHE)

print("\nCrypto context created.")

# --------------------------------------------------
# 2. Generate keys
# --------------------------------------------------

keys = cc.KeyGen()

if not keys:
    print("ERROR: Key generation failed.")
    exit()

print("Keys generated.")

cc.EvalMultKeyGen(keys.secretKey)

# --------------------------------------------------
# 3. Encrypt data
# --------------------------------------------------

input_data = [0.1, 0.2, 0.3, 0.4]

plaintext = cc.MakeCKKSPackedPlaintext(input_data)

ciphertext = cc.Encrypt(
    keys.publicKey,
    plaintext
)

print("Data encrypted.")

# --------------------------------------------------
# 4. Monitor initial ciphertext
# --------------------------------------------------

monitor_ciphertext(
    cc,
    ciphertext,
    "Encryption"
)

# --------------------------------------------------
# 5. Homomorphic addition
# --------------------------------------------------

ciphertext = cc.EvalAdd(
    ciphertext,
    ciphertext
)

monitor_ciphertext(
    cc,
    ciphertext,
    "Addition"
)

# --------------------------------------------------
# 6. Homomorphic multiplication
# --------------------------------------------------

ciphertext = cc.EvalMult(
    ciphertext,
    ciphertext
)

monitor_ciphertext(
    cc,
    ciphertext,
    "Multiplication"
)

# --------------------------------------------------
# 7. Another multiplication
# --------------------------------------------------

ciphertext = cc.EvalMult(
    ciphertext,
    ciphertext
)

monitor_ciphertext(
    cc,
    ciphertext,
    "Second Multiplication"
)

print("\nMonitoring test completed.")
