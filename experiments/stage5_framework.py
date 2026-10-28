from openfhe import *

import time


# ==================================================
# Create CKKS Crypto Context
# ==================================================

def create_crypto_context(
    multiplicative_depth,
    enable_bootstrap=False
):

    parameters = CCParamsCKKSRNS()

    parameters.SetSecurityLevel(
        HEStd_NotSet
    )

    parameters.SetRingDim(
        1 << 12
    )

    parameters.SetSecretKeyDist(
        SecretKeyDist.UNIFORM_TERNARY
    )

    parameters.SetScalingModSize(
        59
    )

    parameters.SetFirstModSize(
        60
    )

    parameters.SetMultiplicativeDepth(
        multiplicative_depth
    )

    cc = GenCryptoContext(
        parameters
    )

    # Basic features

    cc.Enable(
        PKESchemeFeature.PKE
    )

    cc.Enable(
        PKESchemeFeature.KEYSWITCH
    )

    cc.Enable(
        PKESchemeFeature.LEVELEDSHE
    )

    # Bootstrapping features

    if enable_bootstrap:

        cc.Enable(
            PKESchemeFeature.ADVANCEDSHE
        )

        cc.Enable(
            PKESchemeFeature.FHE
        )

    return cc

# ==================================================
# Generate Keys
# ==================================================

def generate_keys(cc):

    key_pair = cc.KeyGen()

    if not key_pair.good():
        raise RuntimeError(
            "Key generation failed."
        )

    cc.EvalMultKeyGen(
        key_pair.secretKey
    )

    return key_pair

# ==================================================
# Setup Bootstrapping
# ==================================================

def setup_bootstrap(
    cc,
    key_pair
):

    level_budget = [4, 4]

    bsgs_dim = [0, 0]

    num_slots = 2048

    cc.EvalBootstrapSetup(
        level_budget,
        bsgs_dim,
        num_slots
    )

    cc.EvalBootstrapKeyGen(
        key_pair.secretKey,
        num_slots
    )


# ==================================================
# Encrypt Input Data
# ==================================================

def encrypt_data(
    cc,
    public_key,
    input_data
):

    plaintext = cc.MakeCKKSPackedPlaintext(
        input_data
    )

    ciphertext = cc.Encrypt(
        public_key,
        plaintext
    )

    return ciphertext


# ==================================================
# Homomorphic Squaring
# ==================================================

def perform_operation(
    cc,
    ciphertext
):

    return cc.EvalMult(
        ciphertext,
        ciphertext
    )


# ==================================================
# Decrypt Result
# ==================================================

def decrypt_result(
    cc,
    secret_key,
    ciphertext
):

    plaintext = cc.Decrypt(
        secret_key,
        ciphertext
    )

    plaintext.SetLength(
        4
    )

    return plaintext.GetRealPackedValue()


# ==================================================
# Calculate Expected Result
# ==================================================

def calculate_expected(
    input_data,
    operations
):

    exponent = 2 ** operations

    return [
        x ** exponent
        for x in input_data
    ]


# ==================================================
# Calculate Maximum Absolute Error
# ==================================================

def calculate_max_error(
    expected,
    actual
):

    errors = [
        abs(e - a)
        for e, a in zip(
            expected,
            actual
        )
    ]

    return max(errors)


# ==================================================
# No-Bootstrap Computation
# ==================================================

def run_no_bootstrap(
    cc,
    key_pair,
    input_data,
    operations
):

    ciphertext = encrypt_data(
        cc,
        key_pair.publicKey,
        input_data
    )

    for _ in range(operations):

        ciphertext = perform_operation(
            cc,
            ciphertext
        )

    return ciphertext


# ==================================================
# Fixed-Bootstrap Computation
# ==================================================

def run_fixed_bootstrap(
    cc,
    key_pair,
    input_data,
    operations,
    interval
):

    ciphertext = encrypt_data(
        cc,
        key_pair.publicKey,
        input_data
    )

    bootstrap_count = 0

    bootstrap_time = 0.0

    operations_since_bootstrap = 0

    for _ in range(operations):

        ciphertext = perform_operation(
            cc,
            ciphertext
        )

        operations_since_bootstrap += 1

        if (
            operations_since_bootstrap
            >= interval
        ):

            start = time.perf_counter()

            ciphertext = cc.EvalBootstrap(
                ciphertext
            )

            elapsed = (
                time.perf_counter()
                - start
            )

            bootstrap_time += elapsed

            bootstrap_count += 1

            operations_since_bootstrap = 0

    return (
        ciphertext,
        bootstrap_count,
        bootstrap_time
    )


# ==================================================
# Adaptive-Bootstrap Computation
# ==================================================

def run_adaptive_bootstrap(
    cc,
    key_pair,
    input_data,
    operations,
    threshold
):

    ciphertext = encrypt_data(
        cc,
        key_pair.publicKey,
        input_data
    )

    bootstrap_count = 0

    bootstrap_time = 0.0

    operations_since_bootstrap = 0

    for _ in range(operations):

        ciphertext = perform_operation(
            cc,
            ciphertext
        )

        operations_since_bootstrap += 1

        if (
            operations_since_bootstrap
            >= threshold
        ):

            start = time.perf_counter()

            ciphertext = cc.EvalBootstrap(
                ciphertext
            )

            elapsed = (
                time.perf_counter()
                - start
            )

            bootstrap_time += elapsed

            bootstrap_count += 1

            operations_since_bootstrap = 0

    return (
        ciphertext,
        bootstrap_count,
        bootstrap_time
    )
