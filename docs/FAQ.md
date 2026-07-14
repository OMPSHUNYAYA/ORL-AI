# ⭐ FAQ — ORL-AI

## Deterministic Bounded Structural Decision Resolution

**A public reference model for resolving normalized signal sets through explicit deterministic rules**

---

ORL-AI is a bounded rule-based decision resolver.

It normalizes input signal strings, checks an embedded conflict-pair table, applies an embedded rule table, and returns one of three states:

- `RESOLVED`
- `INCOMPLETE`
- `ABSTAIN`

The current governing relation is:

`same normalized supported signal set + same embedded resolver rules -> same bounded decision state and current result hash`

ORL-AI is developed within the Shunyaya Framework.

---

# SECTION A — Purpose and Positioning

## A1. What is ORL-AI?

ORL-AI is a deterministic structural decision-rule reference model.

It evaluates a normalized set of signal labels under explicit conflict and decision rules.

It is not a trained AI model, prediction engine, or general intelligence system.

---

## A2. What problem does ORL-AI address?

ORL-AI explores how a bounded decision can be resolved from explicit structure rather than from:

- fragment arrival position;
- runtime timestamps;
- probabilistic inference;
- hidden sequencing assumptions.

The current implementation asks:

> Given this normalized signal set and these embedded rules, what bounded resolver state follows?

---

## A3. What does “orderless” mean here?

It means that, within the current model, the resolver evaluates the normalized set rather than the original input sequence.

Normalization is:

`N(S) = sorted(set(S))`

Therefore, input ordering is not used as classification authority.

This does not prove universal order independence for arbitrary systems or implementations.

---

## A4. Does ORL-AI remove all use of time?

No universal claim is made.

The current Python resolver does not use wall-clock time, timestamps, GPS, or NTP when evaluating its embedded cases.

That is a property of the current implementation, not a universal theorem about all decision systems.

---

## A5. Is ORL-AI a machine-learning system?

No.

The current implementation has:

- no model training;
- no learned weights;
- no probabilistic inference;
- no embedding model;
- no neural network;
- no generative component.

---

## A6. Does ORL-AI replace machine learning?

No.

It may be studied as a deterministic rule layer that could later sit before, after, or alongside another system.

Any such integration would require separate domain validation and engineering.

---

## A7. What is the core model?

Conceptually:

`decision_state = resolve(normalize(signal_set))`

More precisely, the current implementation evaluates:

`decision_state = F(N(S), C, R)`

where:

- `S` is the input signal collection;
- `N(S)` is normalization;
- `C` is the embedded conflict-pair table;
- `R` is the embedded rule table;
- `F` is the current bounded resolver.

---

## A8. Is ORL-AI a general decision framework?

Not yet.

The current repository is a bounded reference implementation with embedded examples.

A general framework would require:

- versioned schemas;
- versioned rule manifests;
- explicit signal validation;
- canonical serialization;
- independent reconstruction;
- broader conformance testing.

---

## A9. Is ORL-AI a production safety system?

No.

It is not production-ready and does not establish safe operation on arbitrary or hostile input.

---

## A10. What is the one-line description?

ORL-AI is a deterministic bounded reference model in which the same normalized supported signal set, evaluated under the same embedded rules, produces the same decision state and current result hash.

---

# SECTION B — Structural Decision Model

## B1. What is “structure” in ORL-AI?

In the current implementation, structure is the normalized set of input signal strings.

Example:

```text
cough
fatigue
fever
```

The resolver then evaluates explicit conflict pairs and rule subsets against that set.

---

## B2. How is the input normalized?

The implementation uses:

`sorted(set(structure))`

This:

- removes exact duplicate strings;
- discards their original order;
- sorts the remaining strings deterministically.

---

## B3. Does duplicate removal provide replay protection?

No.

It only absorbs exact duplicate signal strings inside the current set-based model.

It does not provide:

- sender authentication;
- transport replay protection;
- event identity;
- nonce checking;
- message signatures;
- duplicate-event provenance.

---

## B4. What defines a decision rule?

A rule maps a required signal subset to a decision label.

Example:

`{fever, cough, fatigue} -> Action_Isolate`

A rule matches when its required signal set is a subset of the normalized input set.

---

## B5. What defines a conflict?

The implementation contains explicit conflict pairs.

Example:

`{fatigue, no_fatigue}`

When both members of an embedded conflict pair are present, the resolver returns `ABSTAIN`.

---

## B6. What happens when no rule matches?

The resolver returns:

`INCOMPLETE`

No decision is forced.

---

## B7. What happens when exactly one unique decision matches?

The resolver returns:

```text
State    = RESOLVED
Decision = <matched decision>
```

This applies even when multiple rules match, provided every matching rule produces the same unique decision label.

---

## B8. What happens when multiple incompatible decisions match?

The resolver returns:

`ABSTAIN`

Example:

```text
Action_Isolate
Action_Monitor
```

Both may be structurally matched, but because the decision labels differ, the result is `ABSTAIN`.

---

## B9. Can multiple rules match safely?

Yes.

If multiple rules match and all produce the same decision label, the resolver returns `RESOLVED`.

The committed overlap example produces:

`Action_Approve`

---

## B10. Are unknown signal strings rejected?

Not currently.

The implementation does not enforce an explicit supported-signal allowlist.

Unknown extra strings may remain in the normalized set without affecting a rule match unless they participate in a defined conflict or rule.

This is a documented technical limitation.

---

# SECTION C — Resolution States

## C1. What does RESOLVED mean?

`RESOLVED` means:

- no embedded conflict pair was detected; and
- exactly one unique decision label was matched.

It is a resolver classification, not proof of factual truth or real-world safety.

---

## C2. What does INCOMPLETE mean?

`INCOMPLETE` means:

- no embedded conflict pair was detected; and
- no decision rule matched.

It indicates insufficient structure under the current embedded rules.

---

## C3. What does ABSTAIN mean?

`ABSTAIN` means either:

- an embedded conflict pair was detected; or
- multiple incompatible decision labels were matched.

---

## C4. Does ABSTAIN guarantee safety?

No.

It is a bounded resolver state.

It does not prove system safety, adversarial robustness, legal compliance, or correct real-world action.

---

## C5. Can a RESOLVED result later change?

Yes.

Additional evidence may introduce:

- an explicit conflict;
- a second incompatible decision match.

A previously `RESOLVED` structure may therefore later become `ABSTAIN`.

The current model does not claim monotonic finality.

---

## C6. Does INCOMPLETE mean the input is wrong?

No.

It means the current signal set does not satisfy any embedded decision rule.

---

## C7. Does RESOLVED mean the decision is true?

No.

It means the current embedded resolver found one unique matching decision label.

Truth, medical validity, legal validity, and domain correctness are outside the present implementation.

---

# SECTION D — Reference Scenario

## D1. What is the main three-node scenario?

The committed reference groups are:

```text
Node-A = fever
Node-B = cough
Node-C = fatigue
```

Each local node is initially `INCOMPLETE`.

---

## D2. What happens after local set union?

The merged normalized structure is:

```text
cough
fatigue
fever
```

The embedded rule table matches:

`{fever, cough, fatigue} -> Action_Isolate`

---

## D3. What is the final reference result?

```text
State             = RESOLVED
Decision          = Action_Isolate
Governance status = ACCEPTED_UNIQUE_MATCH
```

---

## D4. What is the regrouped replay scenario?

The same signals are grouped differently:

```text
Replay-X = cough, fatigue
Replay-Y = fever
Replay-Z = empty
```

After set union and normalization, the structure is the same as the reference scenario.

---

## D5. What does the replay scenario establish?

It establishes that these two committed groupings produce:

- the same normalized signal set;
- the same resolver state;
- the same decision;
- the same current result hash.

It does not establish a networking or consensus protocol.

---

## D6. Are the nodes communicating autonomously?

No.

The demo performs local set union inside one Python process.

There is no implemented:

- message transport;
- delivery protocol;
- peer discovery;
- synchronization service;
- distributed consensus;
- reliable broadcast.

---

# SECTION E — Permutation Check

## E1. What does the demo permute?

It permutes the three committed reference node groups:

```text
{fever}
{cough}
{fatigue}
```

---

## E2. How many permutations are checked?

`3! = 6`

The generated output records:

```text
checked     = 6
independent = true
state       = RESOLVED
decision    = Action_Isolate
```

---

## E3. Is this exhaustive?

It is exhaustive for those three committed groups.

It is not exhaustive for:

- arbitrary signals;
- arbitrary node counts;
- arbitrary rules;
- arbitrary conflicts;
- malformed inputs;
- hostile inputs;
- independent implementations.

---

## E4. Does this prove universal order independence?

No.

It confirms permutation invariance for the committed three-group reference case under the current implementation.

---

# SECTION F — Other Included Scenarios

## F1. What conflict scenario is included?

```text
fever
cough
fatigue
no_fatigue
```

Because `fatigue` and `no_fatigue` form an embedded conflict pair, the result is:

```text
State             = ABSTAIN
Governance status = REJECTED_CONFLICT
```

---

## F2. What ambiguity scenario is included?

```text
fever
cough
fatigue
travel_history
```

This matches both:

```text
Action_Isolate
Action_Monitor
```

Because the unique decision count is greater than one, the result is:

```text
State             = ABSTAIN
Governance status = REJECTED_AMBIGUITY
```

---

## F3. What is the nominal five-node case?

The demo declares five node containers:

```text
Node-A = alert
Node-B = verified_source
Node-C = stable_metrics
Node-D = empty
Node-E = empty
```

Three nodes contribute signals and two are empty.

The merged result is:

```text
State    = RESOLVED
Decision = Action_Approve
```

---

## F4. What approval path is included?

```text
verified_source
stable_metrics
low_risk
```

Result:

```text
RESOLVED -> Action_Approve
```

---

## F5. What escalation path is included?

```text
alert
critical_signal
verified_source
```

Result:

```text
RESOLVED -> Action_Escalate
```

---

## F6. What is the same-decision overlap scenario?

The structure is:

```text
alert
verified_source
stable_metrics
low_risk
```

Two rules match, but both produce `Action_Approve`.

The unique decision count remains one, so the result is:

```text
RESOLVED -> Action_Approve
```

---

# SECTION G — Governance Report

## G1. What is a GovernanceReport?

It is a structured record created by the current implementation.

It includes:

- normalized structure;
- sufficient-structure flag;
- conflict flag;
- ambiguity flag;
- governance status;
- resolution basis.

---

## G2. What governance statuses exist?

```text
ACCEPTED_UNIQUE_MATCH
PENDING_INCOMPLETE
REJECTED_CONFLICT
REJECTED_AMBIGUITY
```

---

## G3. Does ACCEPTED_UNIQUE_MATCH mean approved for deployment?

No.

It means one unique decision label matched under the current embedded rules.

It does not establish real-world authorization, policy approval, factual correctness, or production readiness.

---

## G4. Does REJECTED_CONFLICT repair the conflict?

No.

It only classifies the current structure as conflicting under the embedded conflict-pair table.

---

## G5. Does REJECTED_AMBIGUITY select the best decision?

No.

The resolver abstains rather than ranking incompatible matched decisions.

---

# SECTION H — Current Result Hash

## H1. What is the field called certificate?

The implementation names the SHA-256 field:

`certificate`

For the current release, it should be interpreted as a deterministic result hash or receipt for the present payload construction.

---

## H2. What is included in the current hash payload?

The payload contains:

- normalized signal structure;
- state;
- selected decision;
- matched decisions.

---

## H3. What relation does the hash establish?

`same current payload bytes -> same SHA-256 hash`

---

## H4. Is it an independent proof certificate?

No.

It does not currently bind:

- a formal schema version;
- a ruleset version;
- the complete rule table;
- the complete conflict table;
- an implementation identity;
- a digital signature.

---

## H5. Is the payload formally canonical?

Not yet.

The implementation uses a deterministic delimiter-based text construction.

A future revision should define canonical byte serialization and version binding.

---

## H6. What does a matching result hash prove?

It proves that the compared current payload bytes are identical under SHA-256.

It does not by itself prove:

- decision truth;
- resolver correctness;
- message authenticity;
- ruleset validity;
- independent reconstruction;
- system security.

---

# SECTION I — Resolution Capsule

## I1. What is a resolution capsule?

It is a structured resolver-result record included in the generated output.

Fields include:

```text
case_id
normalized_structure
state
decision
matched_decisions
governance_status
resolution_basis
decision_acceptance_rule
certificate
```

---

## I2. Why does the current output say STRUCTURAL_DECISION_PROOF?

That is the label currently embedded by the implementation.

For this release, it should be read as a project-defined record label, not as an independently verified formal proof.

---

## I3. Is the capsule signed?

No.

---

## I4. Can another implementation independently reconstruct it?

There is no committed independent verifier or cross-language conformance implementation yet.

---

## I5. What would strengthen the capsule?

A stronger version should bind:

- schema version;
- ruleset version;
- conflict-manifest version;
- canonical input bytes;
- canonical output bytes;
- implementation or profile version;
- independently reconstructed result;
- optional digital signature where required.

---

# SECTION J — Determinism and Verification

## J1. Is the resolver deterministic?

Yes, for unchanged current inputs and embedded rules.

The current functions contain no random choice or runtime-clock dependency.

---

## J2. What can current verification establish?

It can establish that:

- the Python demo executes;
- the committed scenarios produce their displayed outputs;
- the JSON output can be regenerated;
- unchanged files match frozen SHA-256 values.

---

## J3. What does frozen file hashing establish?

`same file bytes -> same SHA-256 hash`

It proves byte identity of the compared files.

---

## J4. Does the workflow prove all README claims?

No.

The current workflow should be described as a reference-demo execution workflow.

It is not yet a complete conformance, proof-reconstruction, or security workflow.

---

## J5. Are the final checks enforced as assertions?

Not currently.

The script prints boolean checks but does not convert every failed check into a non-zero exit code.

Assertion-based failure gates are a future improvement.

---

## J6. Is there an independent verifier?

No.

---

# SECTION K — Safety and Domain Boundaries

## K1. Are the health-like examples medical advice?

No.

Labels such as:

```text
fever
cough
fatigue
Action_Isolate
Action_Monitor
Action_DarkRoomCare
```

are synthetic demonstration labels only.

---

## K2. Is ORL-AI a diagnostic system?

No.

---

## K3. Is ORL-AI clinical decision support?

No.

---

## K4. Can the embedded rules be used for real health decisions?

No.

No real-world medical or safety decision should be based on the demonstration rules.

---

## K5. Does ORL-AI establish safe cybersecurity actions?

No.

Cybersecurity is only a possible future domain direction after separate rule validation, threat modeling, authorization design, and operational testing.

---

## K6. Does ORL-AI establish safe financial decisions?

No.

---

## K7. Is ORL-AI a legal decision engine?

No.

---

## K8. Does ABSTAIN make the system adversarially secure?

No.

---

# SECTION L — What ORL-AI Is and Is Not

## L1. What is ORL-AI?

ORL-AI is:

- a deterministic bounded decision-rule model;
- a public Python reference implementation;
- an explicit three-state resolver;
- a demonstration of equal results from equal normalized signal sets;
- a basis for later conformance work.

---

## L2. What is ORL-AI not?

ORL-AI is not:

- a full AI system;
- a trained model;
- a prediction engine;
- a generative AI system;
- a chatbot;
- a consensus protocol;
- a communication protocol;
- a production decision authority;
- a universal safety layer.

---

## L3. Does ORL-AI prove correctness equals structure?

No universal theorem is claimed.

The bounded current relation is:

`same normalized supported signal set + same embedded resolver rules -> same bounded decision state and current result hash`

---

## L4. Does it prove training is unnecessary for all intelligence?

No.

The current resolver is rule-based and does not train.

That does not establish a universal claim about all intelligence or all AI systems.

---

## L5. Does it eliminate ambiguity?

No.

It detects one defined form of decision ambiguity and returns `ABSTAIN`.

It does not eliminate ambiguity in unrestricted real-world systems.

---

# SECTION M — Potential Application Direction

## M1. Where might this pattern later be explored?

With substantial additional engineering and domain validation, possible directions include:

- deterministic policy-rule evaluation;
- AI output validation gates;
- sensor-state classification;
- cybersecurity response gating;
- multi-agent proposal checks;
- financial workflow controls;
- operational readiness checks;
- human-reviewed safety interlocks.

---

## M2. Are these current capabilities?

No.

They are future application directions.

---

## M3. What would a real deployment require?

At minimum:

- validated ingestion;
- identity and provenance controls;
- authorization;
- versioned rules;
- versioned conflict definitions;
- formal schemas;
- canonical serialization;
- threat modeling;
- independent verification;
- domain safety review;
- audit and rollback procedures.

---

# SECTION N — Future Technical Direction

## N1. What are the main next technical steps?

A stronger revision should add:

- formal versioned input schemas;
- an explicit supported-signal vocabulary;
- validated versioned rule manifests;
- validated versioned conflict manifests;
- canonical byte serialization;
- deterministic byte-wise ordering;
- schema and ruleset hashes;
- assertion-based failure gates;
- malformed-input vectors;
- unknown-signal vectors;
- duplicate-insertion vectors;
- conflict vectors;
- ambiguity vectors;
- overlap vectors;
- regrouping vectors;
- metamorphic testing;
- independent reconstruction;
- cross-language conformance;
- structural-closure rules.

---

## N2. What is the future target relation?

`same validated canonical signals + same ruleset version -> same independently reconstructed bounded decision result and receipt`

This target is not part of the current implementation.

---

## N3. Will the demo be revised later?

Yes.

The present documentation intentionally distinguishes current behavior from future technical hardening.

---

# SECTION O — License

## O1. Where are the license terms?

See:

[LICENSE](../LICENSE)

---

## O2. How should the repository be described?

It is a publicly available ORL-AI reference implementation under its stated license terms.

---

## O3. How is architecture documentation licensed?

Architecture documentation is subject to the licensing terms declared in the repository, including CC BY-NC 4.0 where stated.

---

# ⭐ Final One-Line Summary

ORL-AI is a deterministic bounded reference model in which the same normalized supported signal set, evaluated under the same embedded rules, produces the same decision state and current result hash.

For the committed three-node reference groups, the Python demo resolves:

`fever + cough + fatigue -> RESOLVED -> Action_Isolate`

and confirms the same bounded result across all six group permutations.
