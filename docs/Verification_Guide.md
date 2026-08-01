# ORL-AI Verification Guide

## Complete Functional Verification

Run from the repository root:

```text
python -B VERIFY_ALL.py
```

Windows:

```text
VERIFY_ALL.bat
```

Linux or macOS:

```text
sh verify_all.sh
```

The shared runner stops at the first failing stage and prints:

```text
ORL-AI v5.0.0 functional verification: PASS
```

when all included stages succeed.

## Verification Sequence

1. Python reference-kernel self-test;
2. independent Python reconstruction self-test;
3. frozen-corpus reconstruction with strict canonical bytes;
4. frozen parity-vector reproducibility;
5. standalone JavaScript strict-JSON self-test;
6. JavaScript resolver frozen-corpus parity;
7. origin-independent SHA-256 fallback verification;
8. raw-intake parity across both Python paths and both JavaScript paths;
9. live Python-JavaScript example cross-check;
10. cross-language edge-case parity;
11. committed artifact reproduction and second-run idempotence;
12. seeded structural properties;
13. Decision-Admission Capsule self-test;
14. frozen state-precedence scenarios;
15. assurance, hostile, falsification, privacy, identity, resource, tamper, and bounded-witness checks.

## Individual Commands

Reference kernel:

```text
python -B demo/ORL_AI_Reference_Kernel_v5_0_0.py --self-test
```

Independent reconstruction:

```text
python -B verifier/ORL_AI_Independent_Verifier_v5_0_0.py --self-test
```

Frozen corpus:

```text
python -B verifier/ORL_AI_Independent_Verifier_v5_0_0.py --verify-corpus corpus/ORL_AI_Frozen_Corpus_Manifest_v5_0_0.json --strict-canonical --receipt-output VERIFY/ORL_AI_Independent_Verification_Receipt_v5_0_0.json
```

Strict JavaScript intake:

```text
node demo/ORL_AI_Strict_Json_v5_0_0.js --self-test
```

JavaScript resolver:

```text
node demo/ORL_AI_Browser_Resolver_v5_0_0.js --self-test
```

Origin-independent SHA-256 fallback:

```text
node verifier/ORL_AI_SHA256_Fallback_Verifier_v5_0_0.js
```

Raw-intake parity:

```text
python -B verifier/ORL_AI_Raw_Intake_Parity_Verifier_v5_0_0.py --receipt-output VERIFY/ORL_AI_Raw_Intake_Parity_Receipt_v5_0_0.json
```

Frozen example cross-check:

```text
python -B verifier/ORL_AI_Cross_Language_Cross_Check_v5_0_0.py --all-examples --receipt-output VERIFY/ORL_AI_Cross_Implementation_Receipt_v5_0_0.json
```

Cross-language edge parity:

```text
python -B verifier/ORL_AI_Cross_Language_Edge_Verifier_v5_0_0.py --receipt-output VERIFY/ORL_AI_Cross_Language_Edge_Receipt_v5_0_0.json
```

Deterministic reproduction:

```text
python -B verifier/ORL_AI_Determinism_Verifier_v5_0_0.py --receipt-output VERIFY/ORL_AI_Determinism_Receipt_v5_0_0.json
```

Properties:

```text
python -B verifier/ORL_AI_Seeded_Property_Verifier_v5_0_0.py --seed 20260801 --cases 64 --receipt-output VERIFY/ORL_AI_Seeded_Property_Receipt_v5_0_0.json
```

Capsules:

```text
python -B demo/ORL_AI_Decision_Admission_Capsule_v5_0_0.py --self-test
```

State precedence:

```text
python -B verifier/ORL_AI_State_Precedence_Test_v5_0_0.py --receipt-output VERIFY/ORL_AI_State_Precedence_Receipt_v5_0_0.json
```

Assurance:

```text
python -B verifier/ORL_AI_Assurance_Verifier_v5_0_0.py --self-test --write-report
```

## Expected Counts

```text
Reference self-test             26/26
Independent corpus              10/10
Strict JavaScript parser        19/19
JavaScript frozen parity        10/10
SHA-256 fallback verification   18/18
Raw-intake parity               11/11
Live example cross-check        10/10
Cross-language edge parity       8/8
Deterministic reproduction       10/10
Seeded properties               64/64
Capsule self-test                6/6
State precedence                15/15
Hostile corpus                  20/20
Falsification corpus            11/11
```

## Raw-Intake Boundary

Raw parser checks compare the Python producer, independent Python verifier, standalone JavaScript parser, and JavaScript resolver CLI. They cover:

- duplicate keys, nested duplicate keys, and escaped-equivalent duplicate keys;
- UTF-8 byte-order marks;
- invalid UTF-8;
- floating and non-finite numbers;
- integers outside the exact interoperable range;
- trailing content;
- unpaired surrogate escapes.

`raw parser refusal != canonical REFUSED bundle`

## Structural Parity Boundary

Accepted documents are checked for byte-identical bundles and public receipts. Edge cases include mixed-case and punctuation identifiers, Unicode unsupported-key ordering, prototype-like key retention, exact integer handling, text controls, resource limits, and depth limits.

## Runtime Boundary

The workflow tests:

- Python 3.9 with Node.js 18;
- Python 3.12 with Node.js 20.

Other successful runtime combinations are additional evidence but do not replace the declared minimum-runtime checks.

## What the Checks Establish

The checks establish deterministic behavior for the committed profile, examples, corpora, implementations, and artifacts. They test raw intake, canonical ordering, source-count semantics, family-count semantics, conflict handling, state precedence, prohibitions, refusals, identity separation, public-receipt identifier omission, resource controls, text controls, direct bundle-tamper rejection, and bounded relay-heavy witness construction.

## What the Checks Do Not Establish

The checks do not establish factual truth, actual model independence, source authenticity, evidence authenticity, security against compromised hosts, formal verification, domain safety, legal validity, authorization, or third-party certification.

## Checksum Boundary

Functional verification does not depend on a checksum manifest. A selected-file checksum manifest may be generated after the final file set is frozen. The GitHub Actions integrity job verifies `hashes/SHA256SUMS.txt` whenever the manifest is present.
