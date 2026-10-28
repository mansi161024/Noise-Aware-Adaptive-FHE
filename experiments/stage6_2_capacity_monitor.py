from openfhe import *

print("=" * 60)
print("STAGE 6.2 - CKKS CAPACITY MONITOR")
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
# 2. Crypto Context
# --------------------------------------------------

cc = GenCryptoContext(parameters)

cc.Enable(PKE)
cc.Enable(KEYSWITCH)
cc.Enable(LEVELEDSHE)

print("\nCrypto context created.")
print("Ring dimension:", cc.GetRingDimension())

# --------------------------------------------------
# 3. Key Generation
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
# 5. Capacity Monitoring
# --------------------------------------------------

MAX_DEPTH = 8

print("\n")
print("=" * 60)
print("CAPACITY MONITORING")
print("=" * 60)

for operation in range(0, 7):

    if operation > 0:
        ciphertext = cc.EvalMult(
            ciphertext,
            ciphertext
        )

    current_level = ciphertext.GetLevel()

    remaining_capacity = MAX_DEPTH - current_level

    print("\nOperation:", operation)
    print("Current Ciphertext Level:", current_level)
    print("Maximum Depth:", MAX_DEPTH)
    print("Remaining Capacity:", remaining_capacity)

    if remaining_capacity <= 2:
        print("Condition: HIGH")
    else:
        print("Condition: SAFE")

print("\n")
print("=" * 60)
print("STAGE 6.2 TEST COMPLETED")
print("=" * 60)
