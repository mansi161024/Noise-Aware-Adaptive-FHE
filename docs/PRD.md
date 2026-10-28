# Product Requirements Document

## Product

Noise-Aware Adaptive Bootstrapping for CKKS Fully Homomorphic Encryption

## Document Status

Research prototype specification

## 1. Overview

This project develops an adaptive controller for CKKS fully homomorphic encryption (FHE). The controller monitors the condition of an encrypted computation and triggers bootstrapping when the ciphertext is approaching an unsafe state.

The goal is to preserve numerical accuracy while avoiding unnecessary bootstrapping operations. Bootstrapping refreshes a ciphertext and restores its ability to support more homomorphic computation, but it is computationally expensive.

## 2. Problem Statement

Homomorphic multiplication increases ciphertext noise and consumes available ciphertext levels. If computation continues after the ciphertext has insufficient capacity, decryption accuracy can degrade or the computation can fail.

Always bootstrapping at a fixed interval can perform unnecessary expensive operations. Never bootstrapping can make longer computations unreliable. The system needs a decision mechanism that selects when bootstrapping is necessary based on observable ciphertext indicators.

## 3. Product Goal

    Build and evaluate a controller that:

    1. Executes computations on encrypted CKKS data.
    2. Measures ciphertext condition after homomorphic operations.
    3. Classifies the ciphertext as safe or high-risk.
    4. Bootstraps only when the configured condition is reached.
    5. Continues computation after bootstrapping.
    6. Measures runtime, bootstrap count, and numerical accuracy.
    7. Compares adaptive bootstrapping with no bootstrapping and fixed bootstrapping.

## 4. Target Users

### Primary User

Researchers and students studying FHE performance, ciphertext noise, CKKS precision, and bootstrapping strategies.

### Secondary User

Developers who need to choose a bootstrapping policy for an encrypted numerical workload.

## 5. Scope

### In Scope

- CKKS encrypted numerical computation using OpenFHE.
- Homomorphic addition and multiplication experiments.
- Ciphertext level and capacity monitoring.
- Noise or precision indicator collection where supported by the library.
- Adaptive bootstrap decisions.
- Fixed-interval and no-bootstrap baselines.
- Accuracy validation against plaintext expected results.
- CSV result collection.
- Graphs for runtime, bootstrap count, ciphertext condition, and error.

### Out of Scope

- Production deployment of an FHE service.
- Distributed key management.
- Security proofs for the controller.
- Automatic selection of all OpenFHE parameters.
- Support for schemes other than CKKS in the first version.
- Claims that adaptive bootstrapping is faster without experiments over multiple computation depths.

## 6. Current Prototype

The repository already contains experiments for:

- baseline computations without bootstrapping,
- fixed bootstrapping,
- adaptive bootstrapping,
- ciphertext level and noise monitoring,
- practical adaptive indicators,
- actual OpenFHE bootstrapping,
- accuracy validation, and
- final result summaries and graphs.

The current controller uses operation count and ciphertext level/capacity thresholds. The collected noise estimate is not yet the primary decision input, so the current implementation should be described as level-aware or operation-aware until a noise or precision value controls the decision directly.

The final graph script currently uses hardcoded completed results. It is suitable for displaying the current experiment, but the final system should load results from CSV files to prevent discrepancies between experiments and graphs.

## 6.1 Recommended Frontend Structure

The current repository does not contain a frontend application. The existing `src/` and `experiments/` directories are Python research code, not frontend code. A frontend should be added as a separate client application so it can display experiment status and results without mixing UI code with OpenFHE execution logic.

```text
frontend/
    package.json
    vite.config.ts
    tsconfig.json
    src/
        main.tsx
        App.tsx
        api/
            experiments.ts
            results.ts
        components/
            Layout.tsx
            MetricCard.tsx
            ExperimentTable.tsx
            ExperimentStatus.tsx
            ResultChart.tsx
        pages/
            Dashboard.tsx
            Experiments.tsx
            ExperimentDetails.tsx
            Settings.tsx
        hooks/
            useExperiments.ts
            useResults.ts
        types/
            experiment.ts
            result.ts
        styles/
            globals.css
    public/
```

The frontend should initially provide a dashboard with experiment status, execution time, bootstrap count, maximum error, and links to generated graphs. It should consume CSV-derived or API-served results; it should not import OpenFHE or perform encryption in the browser.

## 7. Functional Requirements

### FR-1: Configure CKKS

The system shall configure CKKS parameters including multiplicative depth, scaling modulus size, ring dimension, batch size, and bootstrapping settings.

### FR-2: Encrypt Input

The system shall encode and encrypt a numerical input vector using a generated public key.

### FR-3: Execute Encrypted Operations

The system shall execute a configurable sequence of homomorphic operations without decrypting intermediate values.

### FR-4: Monitor Ciphertext Condition

After each configured operation, the system shall record at least:

- operation number,
- operation type,
- ciphertext level,
- remaining capacity or configured depth,
- bootstrap count,
- decision condition, and
- bootstrap time when applicable.

Where supported, it should also record noise scale degree and a noise or precision estimate.

### FR-5: Make Adaptive Decisions

The controller shall classify the ciphertext as `SAFE` or `HIGH` using documented thresholds. When the high-risk condition is reached, it shall perform bootstrapping and reset the relevant monitoring state.

### FR-6: Validate Accuracy

The system shall decrypt the final result and compare it with the equivalent plaintext computation. It shall report the maximum absolute error.

### FR-7: Compare Policies

The experiment runner shall support at least these policies:

- no bootstrapping,
- fixed-interval bootstrapping, and
- adaptive bootstrapping.

### FR-8: Save Reproducible Results

Each experiment shall save structured results as CSV with configuration values, operation count, bootstrap count, timing, and error metrics.

### FR-9: Generate Graphs

The graph generator shall read experiment results from CSV and produce comparisons for:

- total execution time,
- bootstrap count,
- maximum absolute error,
- computation depth, and
- remaining ciphertext capacity where available.

## 8. Non-Functional Requirements

- The experiment must never decrypt ciphertext to make an adaptive decision.
- All adaptive decisions must be logged and explainable from recorded indicators.
- Results must be reproducible using the same OpenFHE parameters and input data.
- Timing measurements must use a high-resolution timer.
- The system must clearly distinguish measured results from manually entered or illustrative values.
- Scripts should fail with a clear message when required OpenFHE functionality or keys are unavailable.
- Graph output paths should be independent of the directory from which the script is launched.

## 9. Success Metrics

The project is successful when:

1. Adaptive computation completes without decryption failure.
2. The controller triggers bootstrapping when its documented condition is met.
3. The final decrypted result remains within the defined CKKS error tolerance.
4. Every bootstrap decision can be traced to recorded ciphertext indicators.
5. Results are available for all three comparison policies.
6. Experiments cover multiple computation depths rather than only one short run.
7. The results show whether adaptive bootstrapping reduces unnecessary bootstraps or runtime for at least one workload.

## 10. Accuracy Criterion

For each experiment, calculate:

```text
maximum_absolute_error = max(abs(expected_value - decrypted_value))
```

The acceptable tolerance shall be defined in the experiment configuration. The current prototype reports errors around `1e-15`, but this value must be measured again for each run rather than assumed as a universal requirement.

## 11. Experiment Plan

### Phase 1: Baseline

Run the same encrypted workload with no bootstrapping and record the maximum supported computation depth and error.

### Phase 2: Fixed Policy

Bootstrap at a fixed interval and record runtime, number of bootstraps, and error.

### Phase 3: Adaptive Level Policy

Bootstrap when ciphertext level or remaining capacity crosses a threshold.

### Phase 4: Noise/Precision Policy

Use an observable noise, scale, or precision indicator as part of the bootstrap decision. Compare it with the level-based policy.

### Phase 5: Scaling Evaluation

Repeat the comparison for increasing computation depths, such as 4, 8, 12, and 20 operations, subject to available OpenFHE capacity and runtime.

## 12. Expected Interpretation of Current Results

The current short experiment shows that:

- no bootstrapping is fastest,
- adaptive bootstrapping currently performs two bootstraps,
- bootstrapping adds substantial runtime,
- all reported numerical errors are very small, and
- bootstrapping preserves accuracy in the tested workload.

These results demonstrate correctness and controller operation. They do not yet demonstrate that the adaptive policy is more efficient than fixed bootstrapping because the tested workload is short and the adaptive policy performs more bootstraps than the fixed policy.

## 13. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Thresholds are chosen arbitrarily | Run threshold sensitivity experiments and document the selection method. |
| Noise estimate is not predictive of accuracy | Compare the indicator with measured decryption error over many workloads. |
| Short workloads hide adaptive benefits | Evaluate several computation depths and operation patterns. |
| Hardcoded graph values become stale | Load graph data directly from experiment CSV files. |
| Relative output paths write files to the wrong directory | Resolve paths from the project root or the script location. |
| Runtime varies between machines | Repeat runs and report averages, variance, and environment details. |

## 14. Deliverables

- Adaptive bootstrap controller.
- Baseline, fixed, and adaptive experiment scripts.
- Noise/capacity monitoring data.
- Accuracy validation results.
- CSV result files.
- Runtime, bootstrap-count, capacity, and error graphs.
- Final research summary explaining trade-offs and limitations.

## 15. Recommended Final Claim

The project should claim that it implements and evaluates adaptive ciphertext refreshing for CKKS, preserving numerical accuracy while making bootstrap decisions from ciphertext condition indicators. It should claim performance improvement only if the expanded experiments demonstrate fewer unnecessary bootstraps or lower total runtime for a defined workload.