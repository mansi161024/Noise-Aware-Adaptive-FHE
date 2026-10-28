from openfhe import *


def main():
    print("Creating CKKS context...")

    parameters = CCParamsCKKSRNS()

    parameters.SetMultiplicativeDepth(4)
    parameters.SetScalingModSize(50)
    parameters.SetBatchSize(8)

    crypto_context = GenCryptoContext(parameters)

    crypto_context.Enable(PKE)
    crypto_context.Enable(KEYSWITCH)
    crypto_context.Enable(LEVELEDSHE)

    print("CKKS context created successfully.")

    # Generate keys
    key_pair = crypto_context.KeyGen()

    if not key_pair.good():
        raise RuntimeError("Key generation failed")

    print("Keys generated successfully.")

    # Generate evaluation keys
    crypto_context.EvalMultKeyGen(key_pair.secretKey)

    # Original data
    data = [1.0, 2.0, 3.0, 4.0]

    print("Original data:", data)

    # Encode
    plaintext = crypto_context.MakeCKKSPackedPlaintext(data)

    # Encrypt
    ciphertext = crypto_context.Encrypt(
        key_pair.publicKey,
        plaintext
    )

    print("Encryption successful.")

    # Homomorphic multiplication
    result_ciphertext = crypto_context.EvalMult(
        ciphertext,
        ciphertext
    )

    print("Homomorphic multiplication successful.")

    # Decrypt
    decrypted = crypto_context.Decrypt(
        key_pair.secretKey,
        result_ciphertext
    )

    decrypted.SetLength(len(data))

    print("Decrypted result:", decrypted.GetRealPackedValue())


if __name__ == "__main__":
    main()
