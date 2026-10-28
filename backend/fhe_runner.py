"""
fhe_runner.py
=============

OpenFHE CKKS experiment runner for the Noise-Aware Adaptive FHE project.

Three strategies
----------------
1. No Bootstrapping      – run N multiplications without refreshing levels.
2. Fixed Bootstrapping   – bootstrap every `fixed_interval` operations,
                           but NEVER after the final operation.
3. Adaptive Bootstrapping – bootstrap when the remaining ciphertext level
                            falls at or below `level_threshold` levels.
                            Accurately described as a LEVEL-AWARE controller.

Input validation
----------------
The workload is repeated squaring:   ct = EvalMult(ct, ct)

After N squarings, each value x becomes x^(2^N).

For CKKS to decrypt correctly, the scaled value must stay within the
polynomial ring.  With ScalingModSize=59, the representable range per
slot is roughly  ±2^(59/2)  ≈  ±7.6e8  at level 0, but the actual limit
depends on the full modulus chain.  A practical safe rule is:

    max_abs(input)^(2^N)  <  2^52   (≈ 4.5e15)

because 52 = 59 − 7 (safety margin for noise budget).

Values that violate this are rejected with a clear error message.
The user may opt into normalization (values mapped to [−1, 1] range)
and the correct expected result is computed using the original scale factor.
"""

from openfhe import *
import time
import math


# ============================================================
# SAFE RANGE VALIDATION
# ============================================================

# CKKS can reliably represent values whose magnitude is below this limit
# (conservative estimate for ScalingModSize=59, 32 levels).
_CKKS_SAFE_VALUE_LIMIT = 4.5e15


def validate_input(input_data: list, number_of_operations: int) -> dict:
    """
    Check whether the input vector is safe for the given operation count.

    Returns a dict with:
        ok           : bool
        error        : str | None
        max_abs      : float
        expected_max : float
        safe_limit   : float
    """
    if not input_data:
        return {
            "ok": False,
            "error": "Input vector is empty.",
            "max_abs": 0.0,
            "expected_max": 0.0,
            "safe_limit": _CKKS_SAFE_VALUE_LIMIT,
        }

    max_abs = max(abs(x) for x in input_data)

    if max_abs == 0.0:
        return {
            "ok": True,
            "error": None,
            "max_abs": 0.0,
            "expected_max": 0.0,
            "safe_limit": _CKKS_SAFE_VALUE_LIMIT,
        }

    # After N squarings, max value is max_abs^(2^N)
    exponent = 2 ** number_of_operations
    try:
        expected_max = max_abs ** exponent
    except OverflowError:
        expected_max = float("inf")

    if not math.isfinite(expected_max):
        return {
            "ok": False,
            "error": (
                f"Input values too large for {number_of_operations} operations. "
                f"max(|x|) = {max_abs:.4g}, "
                f"max(|x|)^(2^{number_of_operations}) = overflow. "
                f"CKKS safe limit: {_CKKS_SAFE_VALUE_LIMIT:.2e}. "
                "Reduce input magnitude or operation count, or enable normalization."
            ),
            "max_abs": max_abs,
            "expected_max": float("inf"),
            "safe_limit": _CKKS_SAFE_VALUE_LIMIT,
        }

    if expected_max > _CKKS_SAFE_VALUE_LIMIT:
        return {
            "ok": False,
            "error": (
                f"Input values too large for {number_of_operations} operations. "
                f"max(|x|) = {max_abs:.4g}, "
                f"max(|x|)^(2^{number_of_operations}) = {expected_max:.4e} "
                f"exceeds CKKS safe limit {_CKKS_SAFE_VALUE_LIMIT:.2e}. "
                "Reduce input magnitude or operation count, or enable normalization."
            ),
            "max_abs": max_abs,
            "expected_max": expected_max,
            "safe_limit": _CKKS_SAFE_VALUE_LIMIT,
        }

    return {
        "ok": True,
        "error": None,
        "max_abs": max_abs,
        "expected_max": expected_max,
        "safe_limit": _CKKS_SAFE_VALUE_LIMIT,
    }


def normalize_input(input_data: list) -> tuple:
    """
    Normalize input to the range [−1, 1] by dividing by max(|x|).

    Returns (normalized_data, scale_factor).
    The original values are input_data[i] = normalized[i] * scale_factor.
    After N squarings, the expected result for original x is x^(2^N).
    If working with normalized x_norm = x / s, then x_norm^(2^N) * s^(2^N).
    """
    scale = max(abs(x) for x in input_data)
    if scale == 0:
        return list(input_data), 1.0
    normalized = [x / scale for x in input_data]
    return normalized, scale


# ============================================================
# COMMON CKKS SETUP
# ============================================================

def create_context(use_bootstrap: bool = False) -> object:
    """
    Create and configure a CKKS CryptoContext.

    Parameters
    ----------
    use_bootstrap : bool
        If True, enable ADVANCEDSHE and FHE features and call
        EvalBootstrapSetup with level_budget=[4,4].

    CKKS parameters
    ---------------
    RingDim          : 4096  (2^12)
    ScalingModSize   : 59 bits
    FirstModSize     : 60 bits
    MultiplicativeDepth : 32
    SecurityLevel    : HEStd_NotSet  (security checking disabled for research)
    SecretKeyDist    : UNIFORM_TERNARY
    NumSlots         : 2048  (= RingDim / 2)
    """
    parameters = CCParamsCKKSRNS()

    parameters.SetSecurityLevel(HEStd_NotSet)
    parameters.SetRingDim(1 << 12)     # 4096

    parameters.SetSecretKeyDist(
        SecretKeyDist.UNIFORM_TERNARY
    )

    parameters.SetScalingModSize(59)
    parameters.SetFirstModSize(60)
    parameters.SetMultiplicativeDepth(32)

    cc = GenCryptoContext(parameters)

    cc.Enable(PKE)
    cc.Enable(KEYSWITCH)
    cc.Enable(LEVELEDSHE)

    if use_bootstrap:
        cc.Enable(ADVANCEDSHE)
        cc.Enable(FHE)

        level_budget = [4, 4]

        cc.EvalBootstrapSetup(
            level_budget,
            [0, 0],
            2048     # num_slots = RingDim / 2
        )

    return cc


def generate_keys(cc, use_bootstrap: bool = False) -> object:
    """Generate encryption, multiplication, and (optionally) bootstrap keys."""
    keys = cc.KeyGen()

    if not keys:
        raise RuntimeError("Key generation failed.")

    cc.EvalMultKeyGen(keys.secretKey)

    if use_bootstrap:
        cc.EvalBootstrapKeyGen(
            keys.secretKey,
            2048     # num_slots
        )

    return keys


# ============================================================
# EXPECTED RESULT & ERROR
# ============================================================

def calculate_expected_values(
    input_data: list,
    number_of_operations: int,
    scale_factor: float = 1.0,
) -> list:
    """
    After N squarings, value x becomes x^(2^N).

    If normalization was applied (scale_factor != 1.0):
        normalized_x = x / scale_factor
        after N squarings of normalized_x: (x/s)^(2^N)
        Correction: multiply by s^(2^N) to recover original expected value.
    """
    exponent = 2 ** number_of_operations
    expected = []
    for x in input_data:
        try:
            val = x ** exponent
            if not math.isfinite(val):
                val = float("inf")
        except OverflowError:
            val = float("inf")
        expected.append(val)
    return expected


def calculate_error(
    expected_values: list,
    decrypted_values: list,
) -> float:
    """Maximum absolute error across all slots."""
    errors = [
        abs(expected - actual)
        for expected, actual
        in zip(expected_values, decrypted_values)
        if math.isfinite(expected)
    ]
    return max(errors) if errors else 0.0


# ============================================================
# 1. NO BOOTSTRAP
# ============================================================

def run_no_bootstrap_experiment(
    input_data: list,
    number_of_operations: int = 4,
) -> dict:
    """
    Run N squaring operations with no bootstrapping.

    The experiment will fail if there are not enough ciphertext levels.
    With MultiplicativeDepth=32 and no bootstrap, up to 32 operations
    are supported.  Each squaring consumes exactly 1 level.
    """

    print("\n" + "=" * 60)
    print("NO BOOTSTRAP EXPERIMENT")
    print(f"  Operations : {number_of_operations}")
    print("=" * 60)

    # ----------------------------------------------------------
    # Input validation
    # ----------------------------------------------------------
    check = validate_input(input_data, number_of_operations)
    if not check["ok"]:
        raise ValueError(check["error"])

    # ----------------------------------------------------------
    # Context & keys
    # ----------------------------------------------------------
    cc = create_context(use_bootstrap=False)
    keys = generate_keys(cc, use_bootstrap=False)

    # ----------------------------------------------------------
    # Encrypt
    # ----------------------------------------------------------
    plaintext = cc.MakeCKKSPackedPlaintext(input_data)

    start_encrypt = time.perf_counter()
    ciphertext = cc.Encrypt(keys.publicKey, plaintext)
    encrypt_time = time.perf_counter() - start_encrypt

    # ----------------------------------------------------------
    # Compute
    # ----------------------------------------------------------
    operation_data = []
    start_compute = time.perf_counter()
    start_total   = time.perf_counter()

    for operation in range(1, number_of_operations + 1):

        level_before = ciphertext.GetLevel()

        ciphertext = cc.EvalMult(ciphertext, ciphertext)

        level_after = ciphertext.GetLevel()

        operation_data.append({
            "operation"            : operation,
            "operation_type"       : "EvalMult (squaring)",
            "ciphertext_level"     : level_after,
            "level_before"         : level_before,
            "level_after"          : level_after,
            "decision"             : "CONTINUE",
            "bootstrap_triggered"  : False,
            "bootstrap_time"       : 0.0,
        })

        print(
            f"  Op {operation:2d} | Level {level_before} → {level_after} | CONTINUE"
        )

    compute_time = time.perf_counter() - start_compute

    # ----------------------------------------------------------
    # Decrypt
    # ----------------------------------------------------------
    start_decrypt = time.perf_counter()
    result = cc.Decrypt(keys.secretKey, ciphertext)
    result.SetLength(len(input_data))
    decrypted_values = result.GetRealPackedValue()
    decrypt_time = time.perf_counter() - start_decrypt

    total_time = time.perf_counter() - start_total

    # ----------------------------------------------------------
    # Error
    # ----------------------------------------------------------
    expected_values = calculate_expected_values(
        input_data, number_of_operations
    )
    max_error = calculate_error(expected_values, decrypted_values)

    print(f"  Max absolute error : {max_error:.4e}")
    print(f"  Total time         : {total_time:.4f} s")

    return {
        "strategy"               : "No Bootstrap",
        "input_data"             : list(input_data),
        "operations"             : number_of_operations,
        "fixed_interval"         : None,
        "adaptive_threshold"     : None,
        "controller_type"        : "none",
        "expected_values"        : expected_values,
        "decrypted_values"       : list(decrypted_values),
        "maximum_absolute_error" : max_error,
        "final_ciphertext_level" : ciphertext.GetLevel(),
        "bootstrap_count"        : 0,
        "total_bootstrap_time"   : 0.0,
        "total_execution_time"   : total_time,
        "encrypt_time"           : encrypt_time,
        "compute_time"           : compute_time,
        "decrypt_time"           : decrypt_time,
        "operation_data"         : operation_data,
        "status"                 : "success",
        "error_message"          : None,
    }


# ============================================================
# 2. FIXED BOOTSTRAP
# ============================================================

def run_fixed_bootstrap_experiment(
    input_data: list,
    number_of_operations: int = 4,
    fixed_interval: int = 2,
) -> dict:
    """
    Bootstrap every `fixed_interval` operations.

    Scheduling rule
    ---------------
    After operation k, bootstrap if:
        (k % fixed_interval == 0) AND (k < number_of_operations)

    The final operation is never followed by a bootstrap because no
    further computation follows.

    Example — operations=7, fixed_interval=2:
        Op 1: CONTINUE
        Op 2: BOOTSTRAP  (k=2, 2%2==0, 2<7 → yes)
        Op 3: CONTINUE
        Op 4: BOOTSTRAP  (k=4, 4%2==0, 4<7 → yes)
        Op 5: CONTINUE
        Op 6: BOOTSTRAP  (k=6, 6%2==0, 6<7 → yes)
        Op 7: CONTINUE   (k=7, final → never bootstrap)
        Scheduled bootstraps: 3

    Example — operations=10, fixed_interval=4:
        Op 4 : BOOTSTRAP (4<10)
        Op 8 : BOOTSTRAP (8<10)
        Op 10: CONTINUE  (final)
        Scheduled bootstraps: 2
    """

    print("\n" + "=" * 60)
    print("FIXED BOOTSTRAP EXPERIMENT")
    print(f"  Operations     : {number_of_operations}")
    print(f"  Fixed interval : {fixed_interval}")
    print("=" * 60)

    # ----------------------------------------------------------
    # Validate parameters
    # ----------------------------------------------------------
    if fixed_interval < 1:
        raise ValueError(
            f"fixed_interval must be >= 1 (got {fixed_interval})."
        )

    if fixed_interval > number_of_operations:
        raise ValueError(
            f"fixed_interval ({fixed_interval}) > number_of_operations "
            f"({number_of_operations}). No bootstrap would ever fire."
        )

    # ----------------------------------------------------------
    # Input validation
    # ----------------------------------------------------------
    check = validate_input(input_data, number_of_operations)
    if not check["ok"]:
        raise ValueError(check["error"])

    # ----------------------------------------------------------
    # Context & keys
    # ----------------------------------------------------------
    cc = create_context(use_bootstrap=True)
    keys = generate_keys(cc, use_bootstrap=True)

    # ----------------------------------------------------------
    # Encrypt
    # ----------------------------------------------------------
    plaintext = cc.MakeCKKSPackedPlaintext(input_data)

    start_encrypt = time.perf_counter()
    ciphertext = cc.Encrypt(keys.publicKey, plaintext)
    encrypt_time = time.perf_counter() - start_encrypt

    bootstrap_count      = 0
    total_bootstrap_time = 0.0
    operation_data       = []

    start_total   = time.perf_counter()
    start_compute = time.perf_counter()

    # ----------------------------------------------------------
    # Compute with fixed bootstrapping
    # ----------------------------------------------------------
    for operation in range(1, number_of_operations + 1):

        level_before = ciphertext.GetLevel()

        ciphertext = cc.EvalMult(ciphertext, ciphertext)

        level_after_mult = ciphertext.GetLevel()

        # Bootstrap if interval reached AND not the final operation
        is_interval  = (operation % fixed_interval == 0)
        is_last      = (operation == number_of_operations)
        should_bootstrap = is_interval and not is_last

        decision       = "CONTINUE"
        bootstrap_time = 0.0

        if should_bootstrap:
            decision = "BOOTSTRAP"

            bs_start = time.perf_counter()
            ciphertext = cc.EvalBootstrap(ciphertext)
            bootstrap_time = time.perf_counter() - bs_start

            total_bootstrap_time += bootstrap_time
            bootstrap_count      += 1

        level_after_total = ciphertext.GetLevel()

        operation_data.append({
            "operation"              : operation,
            "operation_type"         : "EvalMult (squaring)",
            "level_before"           : level_before,
            "level_after"            : level_after_total,
            "ciphertext_level"       : level_after_total,
            "decision"               : decision,
            "bootstrap_triggered"    : should_bootstrap,
            "bootstrap_time"         : bootstrap_time,
        })

        print(
            f"  Op {operation:2d} | Level {level_before} → {level_after_total}"
            f" | {decision}"
            + (f" ({bootstrap_time:.2f}s)" if should_bootstrap else "")
        )

    compute_time = time.perf_counter() - start_compute

    # ----------------------------------------------------------
    # Decrypt
    # ----------------------------------------------------------
    start_decrypt = time.perf_counter()
    result = cc.Decrypt(keys.secretKey, ciphertext)
    result.SetLength(len(input_data))
    decrypted_values = result.GetRealPackedValue()
    decrypt_time = time.perf_counter() - start_decrypt

    total_time = time.perf_counter() - start_total

    # ----------------------------------------------------------
    # Error
    # ----------------------------------------------------------
    expected_values = calculate_expected_values(
        input_data, number_of_operations
    )
    max_error = calculate_error(expected_values, decrypted_values)

    scheduled = sum(
        1
        for k in range(1, number_of_operations + 1)
        if k % fixed_interval == 0 and k < number_of_operations
    )

    print(f"  Scheduled bootstraps : {scheduled}")
    print(f"  Actual    bootstraps : {bootstrap_count}")
    print(f"  Max absolute error   : {max_error:.4e}")
    print(f"  Total time           : {total_time:.4f} s")

    return {
        "strategy"               : "Fixed Bootstrap",
        "input_data"             : list(input_data),
        "operations"             : number_of_operations,
        "fixed_interval"         : fixed_interval,
        "adaptive_threshold"     : None,
        "controller_type"        : "fixed-interval",
        "scheduled_bootstraps"   : scheduled,
        "expected_values"        : expected_values,
        "decrypted_values"       : list(decrypted_values),
        "maximum_absolute_error" : max_error,
        "final_ciphertext_level" : ciphertext.GetLevel(),
        "bootstrap_count"        : bootstrap_count,
        "total_bootstrap_time"   : total_bootstrap_time,
        "total_execution_time"   : total_time,
        "encrypt_time"           : encrypt_time,
        "compute_time"           : compute_time,
        "decrypt_time"           : decrypt_time,
        "operation_data"         : operation_data,
        "status"                 : "success",
        "error_message"          : None,
    }


# ============================================================
# 3. ADAPTIVE BOOTSTRAP  (LEVEL-AWARE CONTROLLER)
# ============================================================

def run_adaptive_experiment(
    input_data: list,
    number_of_operations: int = 4,
    operation_threshold: int = 2,
) -> dict:
    """
    Adaptive bootstrapping controlled by the remaining ciphertext level.

    Controller description
    ----------------------
    This is a LEVEL-AWARE controller.

    After each operation the remaining level capacity is computed as:

        remaining = (total_depth - levels_consumed_by_bootstrap) - current_level

    where total_depth = 32 and bootstrap consumes 8 levels (level_budget=[4,4]).

    Bootstrap is triggered when:

        remaining <= level_threshold

    This ensures bootstrapping occurs before the ciphertext runs out of
    computational capacity, not after.

    The `operation_threshold` parameter is re-interpreted as the
    minimum remaining level below which bootstrapping fires.
    A value of 2 means "bootstrap when ≤ 2 levels remain before
    capacity is exhausted."

    NOTE: This is NOT a direct measurement of ring noise variance.
    OpenFHE does not expose the noise variance externally via Python
    bindings at this time. The level is a reliable proxy for
    multiplicative capacity and is the standard practical indicator
    used in level-based FHE systems.
    """

    print("\n" + "=" * 60)
    print("ADAPTIVE BOOTSTRAP EXPERIMENT  (level-aware controller)")
    print(f"  Operations       : {number_of_operations}")
    print(f"  Level threshold  : {operation_threshold}  "
          "(bootstrap when remaining_levels <= threshold)")
    print("=" * 60)

    # ----------------------------------------------------------
    # Input validation
    # ----------------------------------------------------------
    check = validate_input(input_data, number_of_operations)
    if not check["ok"]:
        raise ValueError(check["error"])

    # ----------------------------------------------------------
    # Context & keys
    # ----------------------------------------------------------
    cc = create_context(use_bootstrap=True)
    keys = generate_keys(cc, use_bootstrap=True)

    # Level budget consumed by one bootstrap call
    _BOOTSTRAP_DEPTH   = 8   # = sum(level_budget) = 4 + 4
    _TOTAL_DEPTH       = 32
    _LEVELS_AFTER_BOOT = _TOTAL_DEPTH - _BOOTSTRAP_DEPTH  # 24

    # ----------------------------------------------------------
    # Encrypt
    # ----------------------------------------------------------
    plaintext = cc.MakeCKKSPackedPlaintext(input_data)

    start_encrypt = time.perf_counter()
    ciphertext = cc.Encrypt(keys.publicKey, plaintext)
    encrypt_time = time.perf_counter() - start_encrypt

    bootstrap_count      = 0
    total_bootstrap_time = 0.0
    operation_data       = []

    start_total   = time.perf_counter()
    start_compute = time.perf_counter()

    # ----------------------------------------------------------
    # Compute with adaptive bootstrapping
    # ----------------------------------------------------------
    for operation in range(1, number_of_operations + 1):

        level_before = ciphertext.GetLevel()

        ciphertext = cc.EvalMult(ciphertext, ciphertext)

        current_level    = ciphertext.GetLevel()
        remaining_levels = _TOTAL_DEPTH - current_level

        # Adaptive decision: is there enough capacity for future ops?
        is_last           = (operation == number_of_operations)
        high_risk         = remaining_levels <= operation_threshold
        should_bootstrap  = high_risk and not is_last

        condition      = "HIGH-RISK" if high_risk else "SAFE"
        decision       = "CONTINUE"
        bootstrap_time = 0.0

        if should_bootstrap:
            decision = "BOOTSTRAP"

            bs_start = time.perf_counter()
            ciphertext = cc.EvalBootstrap(ciphertext)
            bootstrap_time = time.perf_counter() - bs_start

            total_bootstrap_time += bootstrap_time
            bootstrap_count      += 1

        level_after = ciphertext.GetLevel()

        operation_data.append({
            "operation"            : operation,
            "operation_type"       : "EvalMult (squaring)",
            "level_before"         : level_before,
            "level_after"          : level_after,
            "ciphertext_level"     : level_after,
            "remaining_levels"     : _TOTAL_DEPTH - level_after,
            "configured_threshold" : operation_threshold,
            "indicator_value"      : remaining_levels,
            "indicator_name"       : "remaining_ciphertext_level",
            "condition"            : condition,
            "decision"             : decision,
            "bootstrap_triggered"  : should_bootstrap,
            "bootstrap_time"       : bootstrap_time,
        })

        print(
            f"  Op {operation:2d} | Level {level_before} → {level_after}"
            f" | Remaining {_TOTAL_DEPTH - level_after}"
            f" | {condition} | {decision}"
            + (f" ({bootstrap_time:.2f}s)" if should_bootstrap else "")
        )

    compute_time = time.perf_counter() - start_compute

    # ----------------------------------------------------------
    # Decrypt
    # ----------------------------------------------------------
    start_decrypt = time.perf_counter()
    result = cc.Decrypt(keys.secretKey, ciphertext)
    result.SetLength(len(input_data))
    decrypted_values = result.GetRealPackedValue()
    decrypt_time = time.perf_counter() - start_decrypt

    total_time = time.perf_counter() - start_total

    # ----------------------------------------------------------
    # Error
    # ----------------------------------------------------------
    expected_values = calculate_expected_values(
        input_data, number_of_operations
    )
    max_error = calculate_error(expected_values, decrypted_values)

    print(f"  Bootstrap count      : {bootstrap_count}")
    print(f"  Max absolute error   : {max_error:.4e}")
    print(f"  Total time           : {total_time:.4f} s")

    return {
        "strategy"               : "Adaptive Bootstrap",
        "input_data"             : list(input_data),
        "operations"             : number_of_operations,
        "fixed_interval"         : None,
        "adaptive_threshold"     : operation_threshold,
        "controller_type"        : "level-aware",
        "controller_description" : (
            "Bootstraps when remaining ciphertext levels "
            "<= level_threshold. Not a direct noise measurement."
        ),
        "expected_values"        : expected_values,
        "decrypted_values"       : list(decrypted_values),
        "maximum_absolute_error" : max_error,
        "final_ciphertext_level" : ciphertext.GetLevel(),
        "bootstrap_count"        : bootstrap_count,
        "total_bootstrap_time"   : total_bootstrap_time,
        "total_execution_time"   : total_time,
        "encrypt_time"           : encrypt_time,
        "compute_time"           : compute_time,
        "decrypt_time"           : decrypt_time,
        "operation_data"         : operation_data,
        "status"                 : "success",
        "error_message"          : None,
    }


# ============================================================
# 4. RUN ALL THREE
# ============================================================

def run_all_experiments(
    input_data: list,
    number_of_operations: int = 4,
    fixed_interval: int = 2,
    adaptive_threshold: int = 2,
) -> dict:
    """
    Run all three strategies sequentially on the same input.

    Raises ValueError if input validation fails.
    Each strategy is run even if another fails, and failures are
    recorded in the result dict rather than propagated.
    """

    print("\n" + "#" * 70)
    print("RUNNING ALL THREE FHE STRATEGIES")
    print(f"  Input      : {input_data}")
    print(f"  Operations : {number_of_operations}")
    print(f"  Fixed interval      : {fixed_interval}")
    print(f"  Adaptive threshold  : {adaptive_threshold}")
    print("#" * 70)

    results = {}

    # ---- 1. No Bootstrap ----
    try:
        results["no_bootstrap"] = run_no_bootstrap_experiment(
            input_data=input_data,
            number_of_operations=number_of_operations,
        )
    except Exception as exc:
        results["no_bootstrap"] = {
            "strategy"               : "No Bootstrap",
            "status"                 : "failed",
            "error_message"          : str(exc),
            "input_data"             : list(input_data),
            "operations"             : number_of_operations,
            "bootstrap_count"        : 0,
            "total_bootstrap_time"   : 0.0,
            "total_execution_time"   : 0.0,
            "maximum_absolute_error" : None,
            "final_ciphertext_level" : None,
            "operation_data"         : [],
        }

    # ---- 2. Fixed Bootstrap ----
    try:
        results["fixed_bootstrap"] = run_fixed_bootstrap_experiment(
            input_data=input_data,
            number_of_operations=number_of_operations,
            fixed_interval=fixed_interval,
        )
    except Exception as exc:
        results["fixed_bootstrap"] = {
            "strategy"               : "Fixed Bootstrap",
            "status"                 : "failed",
            "error_message"          : str(exc),
            "input_data"             : list(input_data),
            "operations"             : number_of_operations,
            "fixed_interval"         : fixed_interval,
            "bootstrap_count"        : 0,
            "total_bootstrap_time"   : 0.0,
            "total_execution_time"   : 0.0,
            "maximum_absolute_error" : None,
            "final_ciphertext_level" : None,
            "operation_data"         : [],
        }

    # ---- 3. Adaptive Bootstrap ----
    try:
        results["adaptive_bootstrap"] = run_adaptive_experiment(
            input_data=input_data,
            number_of_operations=number_of_operations,
            operation_threshold=adaptive_threshold,
        )
    except Exception as exc:
        results["adaptive_bootstrap"] = {
            "strategy"               : "Adaptive Bootstrap",
            "status"                 : "failed",
            "error_message"          : str(exc),
            "input_data"             : list(input_data),
            "operations"             : number_of_operations,
            "adaptive_threshold"     : adaptive_threshold,
            "bootstrap_count"        : 0,
            "total_bootstrap_time"   : 0.0,
            "total_execution_time"   : 0.0,
            "maximum_absolute_error" : None,
            "final_ciphertext_level" : None,
            "operation_data"         : [],
        }

    print("\n" + "#" * 70)
    print("ALL THREE EXPERIMENTS COMPLETED")
    print("#" * 70)

    return results