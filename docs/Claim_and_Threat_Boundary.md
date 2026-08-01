# ORL-AI Claim and Threat Boundary

## Bounded Claim

ORL-AI demonstrates deterministic decision admission from declared canonical structure under one frozen profile and ruleset.

It establishes within the committed boundary that:

- array arrival order does not select the decision resolution identity;
- observation relay multiplicity from one source does not create additional source participation;
- profile requirements can produce explicit incomplete states;
- conflict can produce deterministic abstention;
- active prohibitions can produce deterministic denial;
- unsupported structure can produce deterministic refusal;
- the same supported structure is reconstructed by separate Python and JavaScript implementations for the frozen corpus;
- the pure-JavaScript SHA-256 fallback reproduces the frozen artifacts without Web Crypto or Node.js module access;
- committed example artifacts reproduce byte-for-byte across repeated runs.

## Not Claimed

ORL-AI does not establish:

- general artificial intelligence;
- factual truth;
- model accuracy;
- source authenticity;
- real independence between declared source families;
- safety, legality, morality, usefulness, or optimality of a candidate;
- authorization or execution authority;
- distributed consensus;
- Byzantine fault tolerance;
- secure communication;
- complete privacy;
- immutable finality;
- regulatory compliance;
- production qualification;
- third-party certification;
- universal order independence for arbitrary schemas or profiles.

## Threats Addressed Within the Model

- arrival-order dependence for set-like declared arrays;
- duplicate source identifiers;
- duplicate observation identifiers;
- duplicate evidence identifiers;
- duplicate constraint identifiers;
- unsupported fields and profiles;
- unknown source, candidate, and evidence references;
- undeclared observations and evidence;
- caller-derived authority;
- explicit source contradiction;
- competing candidate support;
- active candidate prohibitions;
- floating and non-finite JSON numbers;
- duplicate JSON keys across the Python and JavaScript strict intake paths;
- integers outside the exact interoperable range;
- invalid UTF-8, UTF-8 byte-order marks, trailing content, and unpaired surrogate escapes;
- locale-sensitive ordering drift for canonical keys and identifiers;
- selected resource-limit violations;
- bundle and capsule tampering represented in the falsification corpus.

## Threats Outside the Model

- forged source identifiers or family labels;
- compromised models, reviewers, rule checkers, hosts, runtimes, cryptographic implementations, or storage;
- malicious but schema-valid declarations;
- false evidence digests or false claims about what a digest represents;
- cryptographic key theft;
- side-channel leakage;
- network interception;
- denial of service outside declared limits;
- prompt injection in upstream extraction systems;
- unsafe downstream authorization or execution;
- incorrect domain policy;
- human misunderstanding.

## State Boundary

`RESOLVED` is structural admission, not truth or authorization.

`INCOMPLETE` is missing profile or boundary structure, not a claim that the candidate is false.

`ABSTAIN` is bounded disagreement, not a safety guarantee.

`DENIED` is application of a declared prohibition, not proof of harm.

`REFUSED` is intake-contract failure, not a domain judgment.

## Source-Family Boundary

Source-family diversity is measured from declared labels. The resolver cannot determine whether two models share training data, architecture, fine-tuning, prompts, tools, operators, or failure modes.

`declared distinct family != proven independent source`

## Evidence Boundary

Evidence objects contain identifiers, kinds, and digests. ORL-AI verifies reference consistency and digest syntax, not the authenticity or meaning of the underlying evidence.

`valid digest syntax != authentic evidence`

## Public Receipt Boundary

The public receipt omits direct source, observation, and evidence identifiers, but its deterministic commitments may still reveal equality and may permit guessing when the underlying structure is low entropy.

`commitment != encryption`

## Cross-Language Intake Boundary

The Python producer, independent Python verifier, standalone JavaScript parser, and JavaScript resolver CLI are tested against the same raw anomaly fixtures. The committed parity set covers duplicate keys, nested duplicate keys, escaped-equivalent duplicate keys, UTF-8 byte-order marks, invalid UTF-8, floating numbers, non-finite numbers, out-of-range integers, trailing content, and unpaired surrogate escapes.

A raw parser refusal occurs before a supported ORL-AI document exists and therefore does not produce a canonical `REFUSED` bundle.

## Artifact-Profile Boundary

Each private bundle contains a bound `artifact_profile` descriptor. It declares the canonicalization profile and identity algorithm. Verification status is not asserted by a static field; it is established by reconstruction and comparison.

## Modification Boundary

Modified files, profiles, rules, corpora, examples, manifests, text handling, canonicalization, or verification logic create a new evidence boundary. Existing verification results must not be represented as applying to changed materials unless the declared checks are rerun and pass.
