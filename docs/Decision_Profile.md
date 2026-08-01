# ORL-AI Decision Profile

## Frozen Identifiers

```text
ruleset_id     = ORL-AI-ADMISSION-RULESET-5-D01
profile_id     = ORL-AI-STRICT-3CLASS-5-D01
text_profile_id = ORL-AI-UNICODE-SCALAR-EXACT-5-D01
```

Changing any identifier or its governing behavior defines a different verification boundary. The current package supports only `ORL-AI-STRICT-3CLASS-5-D01`; unknown profile identifiers are refused. An additional profile requires a new immutable identifier and its own corpus, parity vectors, and cross-implementation verification.

## Candidate Admission Predicate

For candidate `c`, let:

- `S(c)` be distinct supporting source identifiers;
- `F(c)` be distinct declared source families among `S(c)`;
- `K(c)` be source classes among `S(c)`;
- `E(c)` mean every support observation has at least one declared evidence reference;
- `O(c)` mean at least one opposition observation targets `c`;
- `M(c)` mean another candidate has support;
- `P(c)` mean an active prohibition affects `c`.

The current candidate eligibility predicate is:

`eligible(c) = |S(c)| >= 3 AND |F(c)| >= 3 AND {MODEL, MODEL_REVIEW, RULE_CHECK} subseteq K(c) AND E(c)`

Final admission requires:

`admit(c) = eligible(c) AND sealed_boundary AND NOT O(c) AND NOT M(c) AND NOT P(c) AND unique_eligible(c)`

## Source-Class Meaning

`MODEL` means a declared primary model proposal source.

`MODEL_REVIEW` means a declared model-review source.

`RULE_CHECK` means a declared deterministic rule-check source.

`HUMAN_REVIEW` and `TOOL_CHECK` are supported classes but do not replace any currently required class.

These labels are declarations. ORL-AI does not verify model architecture, training data, organizational separation, human identity, tool correctness, or actual independence.

## Observation Semantics

`SUPPORT` contributes source participation to one candidate.

`OPPOSE` blocks admission of the targeted candidate.

`ABSTAIN` records non-support without itself creating a candidate conflict.

One source can provide multiple observations for one candidate, but it counts as one distinct support source.

One source supporting multiple candidates produces `ABSTAIN / SOURCE_CONFLICT`.

One source both supporting and opposing the same candidate produces `ABSTAIN / SOURCE_CONFLICT`.

## Boundary Semantics

A `SEALED` boundary means the declared expected observation and evidence identifier sets exactly match the admitted sets.

It does not mean all real-world evidence has been disclosed or that the boundary was chosen correctly.

An `OPEN` boundary produces `INCOMPLETE` when no higher-precedence denial or conflict is already present.

## Prohibition Semantics

`FORBID_CANDIDATE` can target one candidate or `*`.

An active prohibition affecting any supported candidate produces `DENIED` before boundary completeness is evaluated. `DENIED` therefore does not imply that the remaining structure was complete.

An inactive prohibition is retained in the constraint commitment but does not block admission.

## State Precedence

When several conditions are active, the resolver applies the frozen ordering in [State Precedence](State_Precedence.md). The included verifier proves 15 combined-condition scenarios.

## Profile Change Rule

Any change to thresholds, required classes, source-count semantics, source-family semantics, evidence requirements, conflict handling, prohibition precedence, canonicalization, or text processing requires a new profile or ruleset identifier and regenerated verification artifacts.
