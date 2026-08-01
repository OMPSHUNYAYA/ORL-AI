# ORL-AI Quickstart

## Requirements

- Python 3.9 or later
- Node.js 18 or later for JavaScript parity stages

The Python resolver uses only the standard library.

## Run the Reference Self-Test

```bash
python -B demo/ORL_AI_Reference_Kernel_v5_0_0.py --self-test
```

Expected final line:

```text
TOTAL 26/26 PASS
```

## Resolve the Representative Case

```bash
python -B demo/ORL_AI_Reference_Kernel_v5_0_0.py --resolve examples/ORL_AI_resolved-consensus_Input_v5_0_0.json --output VERIFY/Representative_Bundle.json --receipt-output VERIFY/Representative_Public_Receipt.json
```

Expected state:

```text
RESOLVED
```

Expected candidate:

```text
QUEUE_ALPHA
```

## Inspect the Result

The bundle records:

- normalized input structure;
- state and reason code;
- candidate metrics;
- minimal admission witness;
- deterministic repair requirements or blockers;
- structural commitments;
- decision, bundle, and receipt identities;
- a bound artifact-construction profile;
- `authority = NONE`.

## Run an Incomplete Case

```bash
python -B demo/ORL_AI_Reference_Kernel_v5_0_0.py --resolve examples/ORL_AI_incomplete-open-boundary_Input_v5_0_0.json
```

Expected state and reason:

```text
INCOMPLETE
BOUNDARY_INCOMPLETE
```

## Run an Abstention Case

```bash
python -B demo/ORL_AI_Reference_Kernel_v5_0_0.py --resolve examples/ORL_AI_abstain-opposition_Input_v5_0_0.json
```

Expected state:

```text
ABSTAIN
```

## Run a Denial Case

```bash
python -B demo/ORL_AI_Reference_Kernel_v5_0_0.py --resolve examples/ORL_AI_denied-forbidden-candidate_Input_v5_0_0.json
```

Expected state:

```text
DENIED
```

## Run a Refusal Case

```bash
python -B demo/ORL_AI_Reference_Kernel_v5_0_0.py --resolve examples/ORL_AI_refused-caller-authority_Input_v5_0_0.json
```

Expected state:

```text
REFUSED
```

## Build a Decision-Admission Capsule

```bash
python -B demo/ORL_AI_Decision_Admission_Capsule_v5_0_0.py --bundle examples/ORL_AI_resolved-consensus_Bundle_v5_0_0.json --output VERIFY/Representative_Capsule.json
```

Verify it against the source bundle:

```bash
python -B demo/ORL_AI_Decision_Admission_Capsule_v5_0_0.py --verify-capsule VERIFY/Representative_Capsule.json --verify-against-bundle examples/ORL_AI_resolved-consensus_Bundle_v5_0_0.json
```

## Run All Verification

```bash
python -B VERIFY_ALL.py
```

The script executes 15 functional stages covering the reference kernel, independent reconstruction, strict JavaScript intake, origin-independent SHA-256 fallback, raw-intake parity, frozen and edge cross-language parity, deterministic artifact reproduction, properties, capsules, state precedence, hostile inputs, falsification, and assurance checks.

## Verify Origin-Independent SHA-256

```bash
node verifier/ORL_AI_SHA256_Fallback_Verifier_v5_0_0.js
```

Expected final line:

```text
SHA-256 FALLBACK VERIFY: PASS
```

## Verify Raw-Intake Parity

```bash
python -B verifier/ORL_AI_Raw_Intake_Parity_Verifier_v5_0_0.py
```

Expected final line:

```text
RAW-INTAKE PARITY: PASS
```

## Verify Deterministic Reproduction

```bash
python -B verifier/ORL_AI_Determinism_Verifier_v5_0_0.py
```

Expected final line:

```text
DETERMINISM VERIFY: PASS
```

## Browser Lab

Open `demo/ORL_AI_Structural_Lab_v5_0_0.html` directly in a current browser, or serve the repository over localhost. Selecting a built-in scenario loads and resolves it immediately. After editing or pasting JSON, select **Resolve Structure**.

The browser lab performs local deterministic resolution. It does not invoke a model or remote service. When Web Crypto is unavailable, it uses the verified pure-JavaScript SHA-256 fallback.
