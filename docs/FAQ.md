# ORL-AI — Frequently Asked Questions

This document explains the purpose, operating boundaries, resolution states, evidence model, identity structure, privacy limits, and verification scope of ORL-AI.

---

## Contents

- [1. ORL-AI Fundamentals](#1-orl-ai-fundamentals)
- [2. Admission Profile and Evidence](#2-admission-profile-and-evidence)
- [3. Resolution States and Authority](#3-resolution-states-and-authority)
- [4. Canonical Structure, Order, and Witnesses](#4-canonical-structure-order-and-witnesses)
- [5. Privacy, Execution, and Domain Boundaries](#5-privacy-execution-and-domain-boundaries)
- [6. Implementation and Version Boundaries](#6-implementation-and-version-boundaries)


---

## 1. ORL-AI Fundamentals

### Q1. What is ORL-AI?

ORL-AI is a deterministic decision-admission layer for bounded AI-assisted workflows. It decides whether declared candidate structure satisfies one frozen admission profile.

### Q2. Is ORL-AI an AI model?

No. It does not train, infer unrestricted meaning, predict, generate, or rank candidates.

### Q3. Why is it called ORL-AI?

It applies the Orderless Resolution principle to a bounded AI-assisted decision boundary: model response order and timestamps do not select the result after the same canonical structure is admitted.

### Q4. What is the main innovation?

The reference design separates proposal generation from decision admission. A model output is treated as a proposal, not authority. Admission requires corroborating source classes, evidence links, a sealed declared boundary, no blocking disagreement, and no active prohibition.


---

## 2. Admission Profile and Evidence

### Q5. Does `RESOLVED` mean the model is correct?

No. It means one candidate satisfied the frozen structural profile.

### Q6. Does the profile prove three independent sources?

No. It counts distinct declared source identifiers and source families. Actual independence requires separate evidence.

### Q7. Why require `MODEL`, `MODEL_REVIEW`, and `RULE_CHECK`?

The profile demonstrates heterogeneous corroboration: a primary model proposal, a model-review proposal, and a deterministic rule check. The labels are structural declarations, not quality guarantees.

### Q8. Why not use confidence scores?

The current profile avoids treating uncalibrated numerical confidence as authority. It uses exact source, class, family, evidence, boundary, opposition, and prohibition structure.

### Q9. Can another profile use scores?

A different profile could define bounded integer or exact rational score semantics, but it would require a new profile identifier, new rules, and new verification evidence.


---

## 3. Resolution States and Authority

### Q10. What does `INCOMPLETE` mean?

The valid structure lacks a sealed boundary or one or more admission requirements.

### Q11. What does `ABSTAIN` mean?

The valid structure contains disagreement or competition that prevents a single candidate from being admitted.

### Q12. What does `DENIED` mean?

An active declared prohibition affects a supported candidate. Denial is evaluated before boundary completeness, so `DENIED` does not imply that the remaining structure was complete.

### Q13. What does `REFUSED` mean?

The submitted structure violates the supported schema or intake contract.

### Q14. Why is authority always `NONE`?

Decision admission is not authorization. Real-world authority must be established by a separate system.


---

## 4. Canonical Structure, Order, and Witnesses

### Q15. Are duplicates ignored?

Duplicate identifiers are refused. Multiple observations from one source may be admitted, but they count as one distinct source for support thresholds.

### Q16. Is arrival order completely eliminated?

Arrival order is removed from sole decision authority after the same complete compatible structure is admitted. Operational systems may still need ordering for transport, storage, replay handling, and provenance.

### Q17. Is time completely eliminated?

No. Wall-clock time is not a resolver input in the current profile. Applications may still need time for freshness, expiry, audit, or legal obligations. A future time-sensitive profile would need explicit deterministic time evidence and a new verification boundary.

### Q18. What is the minimal witness?

It is the smallest deterministic observation subset that satisfies the current support-source, source-family, source-class, and evidence requirements for the admitted candidate. ORL-AI selects at most one representative support observation per distinct source before the bounded witness search, so relay multiplicity cannot enlarge the search space.

### Q19. Is the witness a proof?

It is bounded reconstruction evidence, not a formal theorem, signature, legal attestation, or truth proof.

### Q20. What is the difference between decision and bundle identity?

Decision identity follows canonical structure and result. Bundle identity also preserves exact submission commitment. Different orderings can therefore share a decision identity while retaining different bundle identities.


---

## 5. Privacy, Execution, and Domain Boundaries

### Q21. Does the public receipt guarantee privacy?

No. It omits direct source, observation, and evidence identifiers, but commitments and counts can still be linkable or guessable.

### Q22. Can ORL-AI execute the candidate?

No. The package contains no execution authority.

### Q23. Can it be used in medical, financial, legal, cybersecurity, or safety-critical systems?

The reference package does not establish suitability for those domains. Consequential use requires independent domain validation, governance, security, legal review, and authorization controls.


---

## 6. Implementation and Version Boundaries

### Q24. Does the JavaScript implementation have the same raw parser checks as Python?

Yes. The Python producer, independent Python verifier, standalone JavaScript parser, and JavaScript resolver CLI are tested against the same raw anomaly fixtures, including duplicate keys, nested duplicate keys, byte-order marks, invalid UTF-8, floating and non-finite numbers, out-of-range integers, trailing content, and unpaired surrogate escapes.

### Q25. Can the browser laboratory run when Web Crypto is unavailable?

Yes. The resolver uses a verified dependency-free SHA-256 implementation when browser or Node.js Web Crypto is unavailable. The fallback is tested in an isolated environment without `crypto.subtle` or `require`.

### Q26. Does a bundle claim to verify itself?

No. The `artifact_profile` describes canonicalization and the identity algorithm and is bound into the private-bundle identity. Verification is established by deterministic reconstruction and comparison, not by a static `PASS` field.

### Q27. Does v5.0.0 support multiple decision profiles?

No. It supports `ORL-AI-STRICT-3CLASS-5-D01`. Unknown profile identifiers are refused. Any additional profile requires its own immutable identifier, corpus, parity vectors, and cross-implementation verification.

### Q28. What changes require a new version boundary?

Changes to schema, profile, ruleset, text profile, artifact profile, thresholds, canonicalization, source semantics, conflict handling, prohibition handling, hashes, corpora, or verifier logic require regenerated artifacts and a distinct declared boundary.
