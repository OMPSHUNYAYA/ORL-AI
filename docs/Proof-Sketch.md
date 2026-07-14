# 🧩 ORL-AI Model and Invariant Sketch

## Deterministic Bounded Structural Decision Resolution

This document describes the current ORL-AI resolver model, its implemented invariants, the results established by the committed scenarios, and the limits of those results.

ORL-AI is a bounded deterministic rule resolver.

It does not train a model, predict an outcome, infer unrestricted meaning, or establish real-world decision correctness.

The current governing relation is:

`same normalized supported signal set + same embedded conflict pairs + same embedded decision rules -> same bounded decision state and current result hash`

ORL-AI is developed within the Shunyaya Framework.

---

## 1. Scope

This sketch applies to the current Python reference implementation:

`demo/orl_ai_demo_base_v4_1.py`

and its generated reference output:

`outputs/orl_ai_result_v4_1.json`

It describes:

- normalization of input signal strings;
- explicit conflict-pair evaluation;
- embedded subset-rule matching;
- `RESOLVED`, `INCOMPLETE`, and `ABSTAIN`;
- deterministic result hashing;
- committed replay and permutation checks;
- current governance records;
- current implementation boundaries.

It does not constitute:

- a formal proof;
- an independent reconstruction;
- a security proof;
- a production-safety proof;
- a universal theorem about artificial intelligence or decision systems.

---

## 2. Current Model Objects

Let:

- `S` be an iterable collection of input signal strings;
- `N(S)` be the normalized signal tuple;
- `C` be the embedded set of explicit conflict pairs;
- `R` be the embedded mapping from required signal subsets to decision labels;
- `M(S)` be the list of decision labels whose rules match `S`;
- `U(S)` be the set of unique labels in `M(S)`;
- `F(S)` be the current resolver output.

The implementation computes:

`N(S) = tuple(sorted(set(S)))`

The normalized set used for evaluation is:

`set(N(S))`

---

## 3. Normalization

The implementation removes exact duplicate strings and sorts the remaining strings.

Therefore:

`N(S) = N(P(S))`

for any permutation `P(S)` containing the same signal strings with the same multiplicities.

Because normalization uses a set:

`N(list(S) + list(S)) = N(S)`

This is exact-string duplicate absorption within the current in-memory model.

It is not:

- authenticated event deduplication;
- sender-aware replay protection;
- transport idempotency;
- nonce validation;
- message-history reconstruction.

---

## 4. Conflict Predicate

The implementation contains a finite embedded set of conflict pairs.

The conflict predicate is:

`conflict(S) = True`

when at least one pair `c ∈ C` satisfies:

`c ⊆ set(N(S))`

Example:

`{fatigue, no_fatigue} ⊆ set(N(S))`

implies:

`conflict(S) = True`

The current conflict table is project-defined and embedded in the Python source.

It is not externally versioned, independently validated, or loaded from a formal manifest.

---

## 5. Rule Matching

Each current rule has the form:

`required_signal_subset -> decision_label`

A rule matches when:

`required_signal_subset ⊆ set(N(S))`

The implementation collects the decision labels of all matching rules.

Let:

`M(S) = sorted(all matched decision labels)`

and:

`U(S) = sorted(set(M(S)))`

The resolver classifies the structure according to:

- explicit conflict presence;
- number of unique matched decision labels.

---

## 6. Exact Resolver Branch Priority

The current branch order is:

### Branch 1 — Explicit conflict

If:

`conflict(S) = True`

then:

```text
state             = ABSTAIN
decision          = None
matched_decisions = ()
```

This branch has priority over rule matching in `resolve(...)`.

### Branch 2 — Multiple incompatible decisions

If there is no explicit conflict and:

`|U(S)| > 1`

then:

```text
state             = ABSTAIN
decision          = None
matched_decisions = tuple(M(S))
```

### Branch 3 — One unique decision

If there is no explicit conflict and:

`|U(S)| = 1`

then:

```text
state             = RESOLVED
decision          = the unique label in U(S)
matched_decisions = (decision,)
```

Multiple rules may match and still resolve when every matching rule produces the same decision label.

### Branch 4 — No matched decision

If there is no explicit conflict and:

`|U(S)| = 0`

then:

```text
state             = INCOMPLETE
decision          = None
matched_decisions = ()
```

---

## 7. Resolver Determinism

For unchanged:

- normalized signal strings;
- embedded conflict-pair table;
- embedded rule table;
- implementation behavior;

the resolver executes without random choice or runtime-clock input.

Therefore:

`N(S1) = N(S2) -> F(S1) = F(S2)`

within the current implementation.

This is function determinism.

It does not establish:

- independent implementation conformance;
- cross-language equality;
- platform-independent canonical bytes;
- correctness of the embedded rules.

---

## 8. Same-Evidence Equality

For two evaluated structures `S_A` and `S_B`:

`N(S_A) = N(S_B)`

implies:

`F(S_A) = F(S_B)`

under the same current implementation, embedded conflict pairs, and embedded decision rules.

This is the central current-model invariant.

It means equal normalized evidence produces equal bounded resolver output.

It does not mean that nodes with permanently different evidence must produce equal decisions.

---

## 9. Local Union Properties

The demonstration combines node signal sets using ordinary set union.

For sets `A`, `B`, and `C`:

`A ∪ B = B ∪ A`

`(A ∪ B) ∪ C = A ∪ (B ∪ C)`

`A ∪ A = A`

These algebraic properties explain why regroupings of the same committed signal sets produce the same merged set.

The implementation performs this union locally inside one Python process.

It does not implement:

- message delivery;
- peer-to-peer exchange;
- synchronization;
- replicated state;
- reliable broadcast;
- distributed consensus.

---

## 10. Reference Three-Node Scenario

The committed reference groups are:

```text
Node-A = {fever}
Node-B = {cough}
Node-C = {fatigue}
```

Their local union is:

```text
{cough, fatigue, fever}
```

The embedded rule:

`{fever, cough, fatigue} -> Action_Isolate`

matches uniquely.

Therefore the committed result is:

```text
State             = RESOLVED
Decision          = Action_Isolate
Governance status = ACCEPTED_UNIQUE_MATCH
```

---

## 11. Regrouped Replay Scenario

The committed replay grouping is:

```text
Replay-X = {cough, fatigue}
Replay-Y = {fever}
Replay-Z = {}
```

Its local union is also:

```text
{cough, fatigue, fever}
```

Therefore:

`N(reference_merge) = N(replay_merge)`

and the current implementation produces:

```text
same state
same decision
same current result hash
```

This is same-evidence equality after local regrouping.

The word “replay” here does not mean transport replay protection or authenticated event replay.

---

## 12. Committed Permutation Result

The implementation permutes the three committed reference node groups:

```text
{fever}
{cough}
{fatigue}
```

The number of checked permutations is:

`3! = 6`

For all six permutations, the current demo records:

```text
State    = RESOLVED
Decision = Action_Isolate
```

and the same current result hash.

This is exhaustive only for the three committed reference groups.

It is not a proof for:

- arbitrary signal counts;
- arbitrary node counts;
- arbitrary rules;
- arbitrary conflict definitions;
- malformed inputs;
- hostile inputs;
- independent implementations.

---

## 13. Exact Duplicate Idempotence

Because normalization uses `set(...)`:

`N(list(S) + list(S)) = N(S)`

Therefore, for exact duplicate strings:

`F(list(S) + list(S)) = F(S)`

within the current model.

This does not establish general replay safety.

A duplicate with different spelling, encoding, provenance, identifier, or semantic meaning is outside this narrow property.

---

## 14. INCOMPLETE Classification

If:

- no explicit conflict pair is present; and
- no rule matches;

then:

`F(S).state = INCOMPLETE`

This means the current embedded rules do not produce a decision for the normalized signal set.

The resolver does not synthesize missing signals.

It does not prove that the evidence is objectively incomplete in every possible domain model.

---

## 15. Explicit-Conflict ABSTAIN Classification

If an embedded conflict pair is present:

`F(S).state = ABSTAIN`

The committed conflict case includes:

```text
fatigue
no_fatigue
```

and produces:

```text
State             = ABSTAIN
Governance status = REJECTED_CONFLICT
```

This is explicit conflict detection under the current conflict table.

It is not a complete contradiction detector for unrestricted data.

---

## 16. Multi-Decision ABSTAIN Classification

If:

- no explicit conflict pair is present; and
- more than one unique decision label matches;

then:

`F(S).state = ABSTAIN`

The committed ambiguity case matches:

```text
Action_Isolate
Action_Monitor
```

and produces:

```text
State             = ABSTAIN
Governance status = REJECTED_AMBIGUITY
```

The resolver does not rank, combine, or silently choose between the incompatible decision labels.

---

## 17. Same-Decision Rule Overlap

Multiple rules may match the same structure.

If:

`|M(S)| > 1`

but:

`|U(S)| = 1`

then the result is:

`RESOLVED`

The committed overlap structure is:

```text
alert
low_risk
stable_metrics
verified_source
```

Two `Action_Approve` rules match.

Because only one unique decision label remains:

```text
State    = RESOLVED
Decision = Action_Approve
```

Therefore:

`multiple matching rules != multiple incompatible decisions`

---

## 18. Governance Report

The current `GovernanceReport` contains:

- normalized structure;
- sufficient-structure flag;
- conflict flag;
- ambiguity flag;
- governance status;
- textual resolution basis.

Current statuses are:

```text
ACCEPTED_UNIQUE_MATCH
PENDING_INCOMPLETE
REJECTED_CONFLICT
REJECTED_AMBIGUITY
```

These are branch descriptions generated by the current code.

They do not establish:

- factual correctness;
- legal approval;
- policy authorization;
- medical validity;
- deployment approval;
- production safety.

---

## 19. Relationship Between Resolver and Governance Analysis

The resolver and governance analyzer use the same current:

- normalization;
- conflict predicate;
- rule matching;
- unique-decision logic.

The expected correspondence is:

```text
RESOLVED   <-> ACCEPTED_UNIQUE_MATCH
INCOMPLETE <-> PENDING_INCOMPLETE
ABSTAIN    <-> REJECTED_CONFLICT or REJECTED_AMBIGUITY
```

This correspondence is an implementation design relation.

The current script prints scenario checks but does not enforce every expected relation through a complete assertion-based failure suite.

---

## 20. Current Result Hash Construction

The function named `certificate(...)` builds a delimiter-based text payload containing:

```text
normalized structure
state
decision
matched decisions
```

It then computes:

`SHA256(payload_bytes)`

Therefore:

`same current payload bytes -> same SHA-256 hash`

The current reference and regrouped replay scenarios produce the same hash because their current payloads are equal.

---

## 21. Current Hash Boundary

The field named `certificate` should presently be interpreted as a deterministic result hash or receipt.

It is not yet:

- an independently reconstructed proof;
- a signed certificate;
- a ruleset-bound receipt;
- a schema-bound receipt;
- an authenticated attestation;
- a tamper-proof event history.

The payload does not currently bind:

- formal schema version;
- ruleset version;
- complete embedded rule table;
- complete conflict table;
- implementation identity;
- canonical serialization profile;
- digital signature.

---

## 22. Resolution Capsule

The generated output contains a structured result capsule with fields such as:

```text
case_id
proof_class
normalized_structure
state
decision
matched_decisions
governance_status
resolution_basis
decision_acceptance_rule
certificate
determinism_statement
```

The implementation currently assigns:

`proof_class = STRUCTURAL_DECISION_PROOF`

For the present release, this is a project-defined record label.

The capsule should be understood as a structured resolver-result record, not as an independently verified formal proof.

---

## 23. Additional Committed Results

### Nominal five-node case

The demo declares five node containers:

```text
{alert}
{verified_source}
{stable_metrics}
{}
{}
```

Three nodes contribute signals and two are empty.

The merged result is:

```text
RESOLVED -> Action_Approve
```

### Approval path

```text
{verified_source, stable_metrics, low_risk}
-> RESOLVED
-> Action_Approve
```

### Escalation path

```text
{alert, critical_signal, verified_source}
-> RESOLVED
-> Action_Escalate
```

### Conflict regrouping

Two differently grouped conflict scenarios normalize to the same conflicting signal set and produce the same governance status and current result hash.

These are committed scenario results, not universal domain-portability proofs.

---

## 24. Implemented Capabilities Versus Established Scenario Results

The implementation contains capabilities for:

- exact duplicate string absorption;
- explicit conflict detection;
- no-match `INCOMPLETE`;
- one-unique-decision `RESOLVED`;
- multi-decision `ABSTAIN`;
- same-decision overlap resolution;
- deterministic current result hashing;
- governance-record generation.

The committed scenarios directly establish results for:

- the three-node reference merge;
- the regrouped replay merge;
- six reference-group permutations;
- one explicit conflict case;
- one multi-decision ambiguity case;
- one nominal five-node case;
- one approval path;
- one escalation path;
- one same-decision overlap case;
- one regrouped conflict comparison.

Implementation support must not be confused with exhaustive validation.

---

## 25. Arrival-Order Boundary

Within the current set-based resolver:

`N(P(S)) = N(S)`

for permutations of the same exact signal strings.

Therefore the resolver output is invariant to the discarded input ordering under unchanged current rules.

However, the committed executable permutation test covers only six permutations of three fixed node groups.

The documentation must not convert this bounded result into a universal claim about arbitrary distributed arrival histories.

---

## 26. Runtime-Time Boundary

The current resolver functions do not use:

- wall-clock time;
- timestamps;
- GPS;
- NTP;
- delays;
- timeout values;

as classification inputs.

Therefore runtime time is not classification authority in the committed implementation.

This does not prove that all future ingestion, transport, identity, expiry, or deployment systems can operate without time.

---

## 27. Synchronization Boundary

The current decision function does not require a synchronization service once the evaluated normalized signal set is supplied.

However, the demo does not solve how separate systems:

- discover evidence;
- authenticate evidence;
- exchange evidence;
- know that sharing is complete;
- recover missing evidence;
- reach consensus.

Thus the current model supports a bounded same-evidence resolver claim, not a universal synchronization-independence claim.

---

## 28. No Monotonic-Finality Guarantee

The current model is not monotonic with respect to evidence growth.

Possible transitions include:

```text
INCOMPLETE -> RESOLVED
INCOMPLETE -> ABSTAIN
RESOLVED   -> ABSTAIN
ABSTAIN    -> RESOLVED after evidence removal or correction outside the append-only model
```

Example:

```text
{fever, cough, fatigue}
-> RESOLVED
-> Action_Isolate
```

Adding:

```text
no_fatigue
```

produces an explicit conflict and changes the result to:

`ABSTAIN`

Therefore the previous claim that decisions cannot degrade is not valid for the current implementation.

The model does not provide immutable finality or structural closure.

---

## 29. No Conservative-Extension Guarantee

The current implementation does not prove:

`classical decision = ORL-AI decision`

for an independently specified classical system.

No external classical decision procedure is executed or compared.

The current demo only establishes results under its own embedded rule table.

---

## 30. Unknown-Signal Boundary

The implementation does not enforce an explicit supported-signal allowlist.

An unknown additional string may remain in the normalized set and may not affect the result when it matches no rule and no conflict pair.

Therefore the current model does not guarantee strict rejection of undeclared inputs.

A future schema should distinguish:

- valid supported signals;
- invalid signals;
- unknown extensions;
- malformed encodings.

---

## 31. Synthetic Scenario Boundary

Some embedded labels resemble health or operational terms:

```text
fever
cough
fatigue
Action_Isolate
Action_Monitor
Action_DarkRoomCare
```

They are synthetic demonstration labels.

The current rules do not constitute:

- medical advice;
- diagnosis;
- clinical decision support;
- emergency-response authority;
- autonomous safety control;
- validated operational policy.

No real-world medical, safety, financial, legal, cybersecurity, or operational decision should be made from these demonstration rules.

---

## 32. Verification Boundary

Current repository checks may establish:

- Python execution;
- displayed committed scenario results;
- JSON-output regeneration;
- current six-permutation result;
- unchanged artifact byte identity through frozen hashes.

Frozen file hashing establishes:

`same file bytes -> same SHA-256 hash`

It does not independently establish:

- resolver correctness;
- rule validity;
- schema validity;
- decision truth;
- independent reconstruction;
- security;
- production readiness.

The current workflow should be described as a reference-demo execution workflow.

---

## 33. Current Invariants

Within the current Python implementation, under unchanged embedded rules:

### Normalization idempotence

`N(N(S)) = N(S)`

### Exact duplicate absorption

`N(list(S) + list(S)) = N(S)`

### Permutation invariance of normalized strings

`N(P(S)) = N(S)`

### Same-normalized-input resolver equality

`N(S1) = N(S2) -> F(S1) = F(S2)`

### Explicit conflict precedence

`conflict(S) = True -> F(S).state = ABSTAIN`

### No-match incompleteness

`conflict(S) = False AND |U(S)| = 0 -> INCOMPLETE`

### Unique-decision resolution

`conflict(S) = False AND |U(S)| = 1 -> RESOLVED`

### Multi-decision abstention

`conflict(S) = False AND |U(S)| > 1 -> ABSTAIN`

### Current payload-hash equality

`same current payload bytes -> same SHA-256 hash`

These are model and implementation invariants.

They are not universal real-world correctness guarantees.

---

## 34. Properties Not Established

The current repository does not establish:

- unrestricted decision correctness;
- universal order independence;
- universal time independence;
- universal synchronization independence;
- monotonic evidence growth;
- immutable finality;
- safe arbitrary-input handling;
- sender authenticity;
- authorization;
- encryption;
- replay-attack prevention;
- Byzantine fault tolerance;
- distributed consensus;
- reliable broadcast;
- canonical cross-language serialization;
- independent receipt reconstruction;
- regulatory compliance;
- production safety.

---

## 35. Future Proof Obligations

A stronger technical revision should define and test:

### Input validity

- formal versioned schema;
- supported-signal vocabulary;
- explicit refusal of malformed and unknown inputs;
- deterministic Unicode and encoding rules.

### Rule authority

- versioned rule manifest;
- versioned conflict manifest;
- canonical ordering;
- manifest hashes;
- declared resolver profile.

### Canonical serialization

- exact byte format;
- exact character encoding;
- exact separators;
- byte-wise ordering;
- refusal of non-canonical forms.

### Verification

- assertion-based expected outputs;
- independent result reconstruction;
- cross-language implementation;
- positive and negative vectors;
- mutation and metamorphic tests;
- deterministic non-zero failure behavior.

### Receipt strengthening

- schema hash;
- ruleset hash;
- conflict-manifest hash;
- canonical input root;
- canonical result root;
- implementation or profile version;
- optional digital signature where appropriate.

### Finality

- explicit closure state;
- rules for later evidence;
- revocation or supersession model;
- distinction between provisional resolution and sealed resolution.

---

## 36. Future Target Relation

A stronger target is:

`same validated canonical signals + same ruleset and conflict-manifest versions -> same independently reconstructed bounded decision result and receipt`

This target requires validation, canonicalization, version binding, and independent reconstruction.

It is not part of the current implementation.

---

## 37. Final Statement

Within its current bounded model, ORL-AI deterministically:

- normalizes exact signal strings;
- evaluates embedded conflict pairs;
- evaluates embedded subset rules;
- returns `RESOLVED`, `INCOMPLETE`, or `ABSTAIN`;
- produces equal results for equal normalized signal sets;
- produces a deterministic current result hash.

For the committed three-node reference groups, the Python demo confirms:

```text
6 permutations checked
State    = RESOLVED
Decision = Action_Isolate
```

The current evidence supports a bounded deterministic structural decision-rule claim.

It does not support a universal claim that structure alone guarantees correct decisions in unrestricted systems.
