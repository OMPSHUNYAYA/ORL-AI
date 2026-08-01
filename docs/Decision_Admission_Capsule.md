# ORL-AI Decision-Admission Capsule

## Purpose

The capsule is a compact result artifact derived from an ORL-AI bundle. It supports structural comparison without carrying the normalized source, evidence, observation, or constraint arrays.

## Capsule Fields

A capsule records:

- project, version, and capsule schema;
- context, ruleset, profile, and text-profile identifiers;
- boundary state;
- result state, reason, and candidate;
- `authority = NONE`;
- structural counts;
- normalized-input, observation-set, evidence-set, constraint-set, and witness commitments;
- decision resolution identity;
- private bundle identity;
- public receipt identity;
- capsule identity.

## Capsule Identity

`capsule_id = H(capsule body without capsule_id)`

Changing any covered field invalidates the capsule identity.

## Comparison Relations

`IDENTICAL` means the capsule identities match.

`EQUIVALENT_RESOLUTION` means the context and decision resolution identity match while the capsule identities differ.

`COMPATIBLE_OUTCOME` means the same context, state, reason, and candidate are present but the structural identity differs.

`DIVERGES_STATE` means the same context has different states.

`DIVERGES_CANDIDATE` means the same context has different candidate identifiers.

`DIVERGES_STRUCTURE` means another structural difference remains.

`INCOMPARABLE_CONTEXT` means the context identifiers differ.

`UNSUPPORTED` means at least one capsule fails verification.

## Boundary

A capsule does not prove source authenticity, evidence authenticity, factual truth, decision safety, authorization, or execution. It is not a signature, notarization, encryption format, zero-knowledge proof, or formal theorem.

## Commands

Build:

```bash
python -B demo/ORL_AI_Decision_Admission_Capsule_v5_0_0.py --bundle examples/ORL_AI_resolved-consensus_Bundle_v5_0_0.json --output VERIFY/Representative_Capsule.json
```

Verify:

```bash
python -B demo/ORL_AI_Decision_Admission_Capsule_v5_0_0.py --verify-capsule VERIFY/Representative_Capsule.json --verify-against-bundle examples/ORL_AI_resolved-consensus_Bundle_v5_0_0.json
```

Compare:

```bash
python -B demo/ORL_AI_Decision_Admission_Capsule_v5_0_0.py --compare capsules/artifacts/resolved-consensus_Decision_Admission_Capsule_v5_0_0.json capsules/artifacts/incomplete-open-boundary_Decision_Admission_Capsule_v5_0_0.json
```
