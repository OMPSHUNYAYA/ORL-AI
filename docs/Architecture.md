# ORL-AI Architecture

## Purpose

ORL-AI is a deterministic decision-admission layer placed after proposal generation and before any execution authority.

`proposal generation -> structural admission -> separate authorization -> separate execution`

The reference package implements only structural admission.

## Layer 1: Strict Intake

The Python producer, independent Python verifier, and JavaScript CLI intake reject:

- duplicate JSON keys;
- floating JSON numbers;
- non-finite numbers;
- integers outside `-9007199254740991` to `9007199254740991`;
- UTF-8 byte-order marks;
- malformed JSON and trailing content;
- invalid UTF-8;
- unpaired surrogate escapes.

Structural and text-profile validation then rejects unsupported fields, profiles, references, identifiers, source classes, constraints, caller-derived authority, control characters, and resource-limit violations.

`strict parser refusal != canonical REFUSED bundle`

A raw parser refusal occurs before a supported input object exists. A parsed but unsupported object produces a canonical `REFUSED` bundle.

## Layer 2: Canonical Structure

Set-like arrays are sorted by stable identifiers. Exact duplicate identifiers are refused rather than silently collapsed.

Canonical JSON uses:

`UTF-8 + sorted object keys + compact separators + LF terminator`

The resolver preserves exact string code-point sequences under the frozen text profile. It does not apply Unicode normalization.

## Layer 3: Frozen Decision Profile

The profile `ORL-AI-STRICT-3CLASS-5-D01` requires:

- `minimum_support_sources = 3`;
- `minimum_source_families = 3`;
- required classes `MODEL`, `MODEL_REVIEW`, and `RULE_CHECK`;
- evidence on each support observation;
- blocking opposition;
- blocking minority support.

Profile parameters are not caller-controlled fields.

## Layer 4: Prohibition

Active `FORBID_CANDIDATE` constraints are evaluated before candidate admission.

`active prohibition + support for affected candidate -> DENIED`

The constraint does not prove that the candidate is dangerous. It enforces a declared prohibition within the profile.

## Layer 5: Conflict and Admission

The resolver computes candidate metrics from distinct source identifiers rather than observation count. Multiple relay observations from one source do not create new support participation.

It applies the frozen nine-tier precedence documented in [State Precedence](State_Precedence.md). Active prohibition precedes boundary completeness, so `DENIED` does not imply that the remaining structure was complete.

## Layer 6: Minimal Witness

For `RESOLVED`, the kernel first selects the lexicographically earliest evidence-bearing support observation from each distinct source. It then performs a bounded source-level state search and selects the smallest observation subset satisfying:

- three distinct source identifiers;
- three distinct declared source families;
- all required source classes;
- evidence on every selected observation.

Repeated observations from one source cannot expand the witness search. Minimum size is the primary selection rule, followed by lexicographic observation-identifier order. The same witness rule is reconstructed independently in Python and implemented separately in JavaScript.

## Layer 7: Structural Identities

The architecture separates submission identity from resolution identity.

`submitted_input_commitment = H(exact parsed submission)`

`normalized_input_commitment = H(canonical admitted structure)`

`decision_resolution_id = H(context + result + structural commitments)`

`private_bundle_id = H(bundle body + decision_resolution_id + artifact profile)`

`public_receipt_id = H(reduced public receipt body)`

The decision identity excludes the submission commitment. Therefore, arrival-order changes that normalize to the same structure preserve the decision identity. The private-bundle identity binds the frozen `artifact_profile`, which declares the canonicalization profile and identity algorithm without embedding a literal verification-status claim.

## Layer 8: Browser Hashing

The JavaScript resolver selects Web Crypto when available, Node.js Web Crypto in Node environments, and a dependency-free pure-JavaScript SHA-256 implementation otherwise. The fallback is verified against standard vectors, padding boundaries, deterministic fuzz cases, and all frozen bundles and receipts in an isolated environment without `crypto.subtle` or `require`.

## Layer 9: Receipt and Capsule

The private bundle retains normalized sources, evidence, observations, constraints, and candidate metrics.

The public receipt omits source, observation, and evidence identifiers. It retains counts and commitments.

The capsule provides a compact comparison artifact linked to the private bundle and public receipt.

## Operational Boundary

ORL-AI does not collect evidence, authenticate sources, call models, deliver messages, authorize actions, or execute decisions. Those are separate systems with separate security and governance requirements.
