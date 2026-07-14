# ⭐ ORL-AI — Test Guide

## Deterministic Bounded Structural Decision Resolution

This guide defines the recommended procedure for executing and reviewing the current ORL-AI Python reference implementation.

ORL-AI is a bounded deterministic rule resolver.

It normalizes input signal strings, checks an embedded conflict-pair table, applies an embedded decision-rule table, and returns one of three states:

- `RESOLVED`
- `INCOMPLETE`
- `ABSTAIN`

The current governing relation is:

`same normalized supported signal set + same embedded conflict pairs + same embedded decision rules -> same bounded decision state and current result hash`

ORL-AI is developed within the Shunyaya Framework.

---

# 1. Test Scope

This guide applies to:

```text
demo/orl_ai_demo_base_v4_1.py
outputs/orl_ai_result_v4_1.json
VERIFY/VERIFY.txt
VERIFY/FREEZE_DEMO_SHA256.txt
```

The current tests may establish:

- successful Python execution;
- deterministic normalization of the committed signal strings;
- current conflict and rule evaluation;
- expected `RESOLVED`, `INCOMPLETE`, and `ABSTAIN` outputs;
- equality between committed reference and replay groupings;
- six permutations of the three committed reference node groups;
- regeneration of the reference JSON output;
- repeatability of the current result hashes;
- byte identity of frozen artifacts when hashes match.

The current tests do not establish:

- general artificial intelligence;
- machine learning correctness;
- unrestricted decision correctness;
- universal order independence;
- universal time independence;
- universal synchronization independence;
- autonomous networking or evidence delivery;
- independent proof reconstruction;
- cross-language conformance;
- security;
- production readiness;
- medical, legal, financial, cybersecurity, or operational validity.

---

# 2. Required Environment

Use:

```text
Python 3.9 or later
```

The current demo uses only Python standard-library modules.

No runtime installation of third-party packages is required.

The resolver does not use:

- GPS;
- NTP;
- a database;
- a live server;
- a runtime clock;
- internet access.

Internet access may still be needed to download the repository initially.

---

# 3. Repository Layout Expected by This Guide

From the repository root:

```text
demo/
  orl_ai_demo_base_v4_1.py

docs/
  Quickstart.md
  FAQ.md
  Test-Guide.md
  Proof-Sketch.md
  ORL-AI-Structural-Decision-Overview-v1.png

outputs/
  orl_ai_result_v4_1.json

VERIFY/
  VERIFY.txt
  FREEZE_DEMO_SHA256.txt

LICENSE
README.md
```

---

# 4. Start Here — Run the Reference Demo

Open Command Prompt, PowerShell, Terminal, or another shell in the repository root.

Run:

```bash
python demo/orl_ai_demo_base_v4_1.py
```

On systems where `python` does not select Python 3, use:

```bash
python3 demo/orl_ai_demo_base_v4_1.py
```

The process should complete without an unhandled exception.

---

# 5. Generate the Reference JSON Output

Run:

```bash
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/orl_ai_result_v4_1.json
```

Expected final console line:

```text
Wrote output JSON           : outputs/orl_ai_result_v4_1.json
```

The command rewrites the selected output path.

Review any local changes before committing the regenerated file.

---

# 6. Overall Pass Criteria

The current reference-demo execution passes when all of the following are true:

- the Python process exits normally;
- the expected scenarios are printed;
- the three-node reference merge resolves to `Action_Isolate`;
- the regrouped replay merge produces the same state, decision, and current result hash;
- the explicit conflict case returns `ABSTAIN`;
- the multi-decision ambiguity case returns `ABSTAIN`;
- the nominal five-node case resolves to `Action_Approve`;
- the five-node replay resolves to the same result;
- the approval path resolves to `Action_Approve`;
- the escalation path resolves to `Action_Escalate`;
- the dual-approve overlap resolves to one unique decision;
- the conflict regrouping preserves the conflict governance status;
- all six permutations of the three committed reference node groups match;
- all displayed Boolean comparison checks are True;
- the dual-approve overlap state is RESOLVED;
- the dual-approve overlap action is Action_Approve;
- the generated JSON parses successfully;
- the generated JSON contains the expected bounded results.

The current script prints boolean checks but does not enforce every false result through a non-zero exit code.

Therefore, a zero process exit alone is not sufficient.

The displayed results and generated JSON must also be reviewed.

---

# 7. Resolver-State Rules to Verify

## 7.1 RESOLVED

Expected when:

- no embedded conflict pair is present; and
- exactly one unique decision label is matched.

Formally:

`conflict(S) = False AND |U(S)| = 1 -> RESOLVED`

Multiple rules may match when all matching rules produce the same decision label.

---

## 7.2 INCOMPLETE

Expected when:

- no embedded conflict pair is present; and
- no decision rule matches.

Formally:

`conflict(S) = False AND |U(S)| = 0 -> INCOMPLETE`

The resolver does not invent missing signals.

---

## 7.3 ABSTAIN — Explicit Conflict

Expected when an embedded conflict pair is present.

Formally:

`conflict(S) = True -> ABSTAIN`

This branch has priority in the current `resolve(...)` function.

---

## 7.4 ABSTAIN — Multiple Incompatible Decisions

Expected when:

- no explicit conflict pair is present; and
- more than one unique decision label is matched.

Formally:

`conflict(S) = False AND |U(S)| > 1 -> ABSTAIN`

---

# 8. Scenario 1 — Individual Reference Nodes

The reference node sets are:

```text
Node A = {fever}
Node B = {cough}
Node C = {fatigue}
```

Expected local state for each node:

```text
State    = INCOMPLETE
Decision = None
```

Expected governance status:

```text
PENDING_INCOMPLETE
```

Reason:

No single local set satisfies a complete embedded decision rule.

---

# 9. Scenario 2 — Three-Node Reference Merge

The local union is:

```text
{fever} ∪ {cough} ∪ {fatigue}
```

Normalized structure:

```text
cough
fatigue
fever
```

Matching rule:

```text
{fever, cough, fatigue} -> Action_Isolate
```

Expected result:

```text
State             = RESOLVED
Decision          = Action_Isolate
Matched decisions = Action_Isolate
Governance status = ACCEPTED_UNIQUE_MATCH
Resolution basis  = unique structural match -> Action_Isolate
```

Expected current result hash:

```text
7f763b91b0ed88ecae869feba2d872ee7bcfcc6afdd666eb35bf989ca10a89fb
```

This hash is a deterministic result hash for the current delimiter-based payload construction.

It is not an independent proof certificate.

---

# 10. Scenario 3 — Regrouped Replay Merge

The replay grouping is:

```text
Replay Node X = {cough, fatigue}
Replay Node Y = {fever}
Replay Node Z = {}
```

Normalized merged structure:

```text
cough
fatigue
fever
```

Expected result:

```text
State             = RESOLVED
Decision          = Action_Isolate
Governance status = ACCEPTED_UNIQUE_MATCH
```

Expected current result hash:

```text
7f763b91b0ed88ecae869feba2d872ee7bcfcc6afdd666eb35bf989ca10a89fb
```

Expected comparison with the reference merge:

```text
same state        = True
same decision     = True
same current hash = True
```

This demonstrates same-evidence equality after local regrouping.

It does not demonstrate transport replay protection or autonomous distributed convergence.

---

# 11. Scenario 4 — Explicit Conflict

The committed conflicting structure is:

```text
cough
fatigue
fever
no_fatigue
```

Embedded conflict pair:

```text
fatigue
no_fatigue
```

Expected result:

```text
State             = ABSTAIN
Decision          = None
Governance status = REJECTED_CONFLICT
Resolution basis  = conflicting structure detected
```

Expected current result hash:

```text
81f7404130a2a7a44d4528186d47bef8f6711a7f5a4c7bf27a47e390082e70cf
```

The resolver does not repair, rank, or override the conflict.

---

# 12. Scenario 5 — Multi-Decision Ambiguity

The committed ambiguity structure is:

```text
cough
fatigue
fever
travel_history
```

Matching decisions:

```text
Action_Isolate
Action_Monitor
```

Expected result:

```text
State             = ABSTAIN
Decision          = None
Governance status = REJECTED_AMBIGUITY
Resolution basis  = multiple incompatible decisions detected
```

Expected current result hash:

```text
45394162f33a9650ca8a456d8969296b5e68ece6ec64b7c2690af787517e3d8b
```

The resolver does not silently select one of the incompatible decision labels.

---

# 13. Scenario 6 — Nominal Five-Node Merge

The demo declares five node containers:

```text
Five Node A = {alert}
Five Node B = {verified_source}
Five Node C = {stable_metrics}
Five Node D = {}
Five Node E = {}
```

Three nodes contribute signals and two are empty.

Normalized merged structure:

```text
alert
stable_metrics
verified_source
```

Expected result:

```text
State             = RESOLVED
Decision          = Action_Approve
Governance status = ACCEPTED_UNIQUE_MATCH
```

Expected current result hash:

```text
eaa36a8427d43a6cf0e89e0d38e7ed744c4246637173bc31a6a733d7bbdeb0be
```

This is a nominal five-container scenario.

It is not evidence of a five-process distributed protocol.

---

# 14. Scenario 7 — Five-Node Replay Grouping

The replay grouping is:

```text
Replay Five Node 1 = {alert, verified_source}
Replay Five Node 2 = {stable_metrics}
Replay Five Node 3 = {}
```

Normalized merged structure:

```text
alert
stable_metrics
verified_source
```

Expected result:

```text
State    = RESOLVED
Decision = Action_Approve
```

Expected current result hash:

```text
eaa36a8427d43a6cf0e89e0d38e7ed744c4246637173bc31a6a733d7bbdeb0be
```

Expected comparisons:

```text
five_node_converged_decision   = True
five_node_matching_certificate = True
```

---

# 15. Scenario 8 — Approval Path

Input structure:

```text
low_risk
stable_metrics
verified_source
```

Expected result:

```text
State             = RESOLVED
Decision          = Action_Approve
Governance status = ACCEPTED_UNIQUE_MATCH
```

Expected current result hash:

```text
3b05a4c5e2726b43cd1a41197decd753a61d10674c8cdfa7e7fa84e332ed9bb4
```

This is a bounded embedded rule example.

It does not establish real-world approval authority.

---

# 16. Scenario 9 — Escalation Path

Input structure:

```text
alert
critical_signal
verified_source
```

Expected result:

```text
State             = RESOLVED
Decision          = Action_Escalate
Governance status = ACCEPTED_UNIQUE_MATCH
```

Expected current result hash:

```text
d2d82cb52e4c82f8620e14f08b0982877e892d28f0c7202217220c8ac05b44e8
```

This is a bounded embedded rule example.

It does not authorize real-world escalation.

---

# 17. Scenario 10 — Same-Decision Rule Overlap

Input structure:

```text
alert
low_risk
stable_metrics
verified_source
```

Two embedded rules match:

```text
{alert, verified_source, stable_metrics} -> Action_Approve
{verified_source, stable_metrics, low_risk} -> Action_Approve
```

Both matching rules produce the same decision label.

Expected result:

```text
State             = RESOLVED
Decision          = Action_Approve
Governance status = ACCEPTED_UNIQUE_MATCH
```

Expected current result hash:

```text
50b5996a28f3c4211d3f8d0b02e48f85889518f0104c674bf6d3144416ff344c
```

Expected final checks:

```text
dual_approve_overlap_resolved = True
dual_approve_overlap_decision = True
```

This verifies:

`multiple matching rules != multiple incompatible decisions`

---

# 18. Scenario 11 — Conflict Regrouping

The conflict replay groups the same conflicting signal set differently:

```text
Conflict Replay A = {fatigue}
Conflict Replay B = {no_fatigue}
Conflict Replay C = {fever, cough}
```

Normalized merged structure:

```text
cough
fatigue
fever
no_fatigue
```

Expected result:

```text
State             = ABSTAIN
Decision          = None
Governance status = REJECTED_CONFLICT
```

Expected current result hash:

```text
81f7404130a2a7a44d4528186d47bef8f6711a7f5a4c7bf27a47e390082e70cf
```

Expected final checks:

```text
conflict_governance_stable = True
conflict_capsule_stable    = True
```

---

# 19. Permutation Check

The current executable permutation test uses:

```text
{fever}
{cough}
{fatigue}
```

The number of group permutations is:

`3! = 6`

Expected output:

```text
Permutations checked        : 6
Permutation independence    : True
Resolved state              : RESOLVED
Resolved decision           : Action_Isolate
```

Expected JSON block:

```json
{
  "checked": 6,
  "independent": true,
  "state": "RESOLVED",
  "decision": "Action_Isolate"
}
```

This check is exhaustive only for the three committed reference groups.

It is not a universal order-independence proof.

---

# 20. Expected Final Checks

The generated JSON should contain:

```json
{
  "converged_decision": true,
  "matching_certificate": true,
  "five_node_converged_decision": true,
  "five_node_matching_certificate": true,
  "conflict_governance_stable": true,
  "conflict_capsule_stable": true,
  "dual_approve_overlap_resolved": true,
  "dual_approve_overlap_decision": true
}
```

The console should display six Boolean comparison checks as True, together with:

Dual approve overlap state  : RESOLVED
Dual approve overlap action : Action_Approve

The generated JSON should contain all eight final_checks values as true.

Because the script currently prints rather than asserts every condition, manually confirm both the Boolean checks and the two overlap values.

---

# 21. Generated JSON Review

After running:

```bash
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/orl_ai_result_v4_1.json
```

confirm that the file contains these top-level keys:

```text
core_identity
reference_merge
replay_merge
conflict_merge
ambiguity_merge
five_node_merge
five_node_replay_merge
domain_portability
governance_stability
resolution_capsules
permutation_check
final_checks
theorem_block
```

The labels `proof_class`, `certificate`, and `theorem_block` are current project-defined field names.

They should not be interpreted as independent formal proof verification.

---

# 22. Repeatability Test

Run the JSON-generation command twice without changing the code:

```bash
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/run_1.json
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/run_2.json
```

Compare the two files.

## Windows Command Prompt

```bat
fc /b outputs\run_1.json outputs\run_2.json
```

Expected result:

```text
FC: no differences encountered
```

## PowerShell

```powershell
$h1 = (Get-FileHash outputs\run_1.json -Algorithm SHA256).Hash
$h2 = (Get-FileHash outputs\run_2.json -Algorithm SHA256).Hash
$h1
$h2
$h1 -eq $h2
```

Expected final value:

```text
True
```

## Linux or macOS

```bash
cmp outputs/run_1.json outputs/run_2.json
sha256sum outputs/run_1.json outputs/run_2.json
```

Expected:

- `cmp` produces no difference output;
- both SHA-256 values are identical.

Delete temporary files after review if they are not intended for the repository.

---

# 23. Current Result-Hash Review

The function named `certificate(...)` hashes a delimiter-based text payload containing:

```text
normalized structure
state
decision
matched decisions
```

The relation tested is:

`same current payload bytes -> same SHA-256 hash`

A matching current result hash does not by itself prove:

- correct rule design;
- factual decision truth;
- schema validity;
- signal authenticity;
- independent reconstruction;
- security;
- production safety.

---

# 24. Frozen Artifact Verification

Use:

```text
VERIFY/VERIFY.txt
```

for the repository’s platform-specific verification commands.

Compare files against:

```text
VERIFY/FREEZE_DEMO_SHA256.txt
```

Frozen artifact hashing tests:

`same file bytes -> same SHA-256 hash`

It does not test behavioral correctness by itself.

Do not update frozen hashes until all intended demo, output, workflow, and documentation changes for the technical revision are complete.

---

# 25. Suggested One-Minute Review Flow

1. Run the Python demo.
2. Confirm each individual reference node is `INCOMPLETE`.
3. Confirm the reference merge is `RESOLVED -> Action_Isolate`.
4. Confirm the regrouped replay produces the same result and current hash.
5. Confirm the explicit conflict returns `ABSTAIN`.
6. Confirm the multi-decision ambiguity returns `ABSTAIN`.
7. Confirm the nominal five-node and replay cases resolve to `Action_Approve`.
8. Confirm the approval and escalation paths.
9. Confirm the same-decision overlap resolves to `Action_Approve`.
10. Confirm the conflict regrouping remains `REJECTED_CONFLICT`.
11. Confirm six group permutations pass.
12. Confirm all printed Boolean comparison checks are True, and confirm the dual-approve overlap state and action match the expected values.
13. Regenerate and review the JSON output.
14. Verify frozen artifact hashes separately.

---

# 26. Pass/Fail Checklist

## Execution

- [ ] Python process completes without an unhandled exception.
- [ ] JSON-generation command completes.
- [ ] Output file is created at the requested path.

## Reference and Replay

- [ ] Reference merge state is `RESOLVED`.
- [ ] Reference decision is `Action_Isolate`.
- [ ] Replay merge state is `RESOLVED`.
- [ ] Replay decision is `Action_Isolate`.
- [ ] Reference and replay current hashes match.

## Abstention

- [ ] Explicit conflict state is `ABSTAIN`.
- [ ] Explicit conflict governance is `REJECTED_CONFLICT`.
- [ ] Ambiguity state is `ABSTAIN`.
- [ ] Ambiguity governance is `REJECTED_AMBIGUITY`.

## Additional Scenarios

- [ ] Nominal five-node decision is `Action_Approve`.
- [ ] Five-node replay decision is `Action_Approve`.
- [ ] Approval path decision is `Action_Approve`.
- [ ] Escalation path decision is `Action_Escalate`.
- [ ] Same-decision overlap is `RESOLVED`.
- [ ] Conflict regrouping remains `REJECTED_CONFLICT`.

## Permutation and Final Checks

- [ ] Exactly six reference-group permutations are checked.
- [ ] `Permutation independence` is `True`.
- [ ] All eight generated `final_checks` values are `true`.

## Verification

- [ ] Repeated unchanged JSON generation is byte-identical.
- [ ] Frozen repository hashes match when tested.
- [ ] Behavioral results and file identity are reviewed separately.

---

# 27. Failure Conditions

Treat the current execution as failed when any of the following occurs:

- the script raises an unhandled exception;
- the expected output file is not created;
- the reference merge does not resolve to `Action_Isolate`;
- the reference and replay results differ;
- the explicit conflict does not return `ABSTAIN`;
- the ambiguity case does not return `ABSTAIN`;
- the same-decision overlap does not resolve to `Action_Approve`;
- the permutation count is not six;
- permutation independence is not `True`;
- any expected final check is `False`;
- repeated unchanged JSON generation differs;
- frozen hashes differ unexpectedly.

A frozen-hash mismatch may indicate an intentional local modification.

Review the repository diff before treating it as corruption.

---

# 28. Tests Not Yet Included

The current repository does not contain a complete test corpus for:

- malformed input types;
- invalid Unicode handling;
- unknown signal refusal;
- empty-string signal refusal;
- conflicting identifier reuse;
- schema-version mismatch;
- ruleset-version mismatch;
- conflict-manifest-version mismatch;
- canonical byte serialization;
- cross-language reconstruction;
- independent verifier agreement;
- mutation testing;
- hostile-input testing;
- denial-of-service resistance;
- signed receipt verification;
- closure and later-evidence handling.

---

# 29. Recommended Future Test Expansion

A stronger technical revision should add:

- formal versioned input vectors;
- valid and invalid signal-vocabulary vectors;
- duplicate-insertion vectors;
- unknown-signal vectors;
- malformed-input vectors;
- direct `INCOMPLETE` vectors;
- every embedded conflict-pair vector;
- multi-decision ambiguity vectors;
- same-decision overlap vectors;
- irrelevant-extra-signal vectors;
- regrouping vectors;
- larger permutation samples;
- metamorphic tests;
- assertion-enforced pass/fail gates;
- non-zero exit codes on failure;
- canonical serialization vectors;
- ruleset and conflict-manifest hashes;
- independent reconstruction;
- cross-language conformance;
- structural-closure vectors.

Future target relation:

`same validated canonical signals + same ruleset and conflict-manifest versions -> same independently reconstructed bounded decision result and receipt`

This target is not part of the current implementation.

---

# 30. Synthetic Scenario Notice

Some committed labels resemble medical or operational terms:

```text
fever
cough
fatigue
Action_Isolate
Action_Monitor
Action_DarkRoomCare
```

They are synthetic demonstration labels only.

The tests do not validate:

- medical advice;
- diagnosis;
- clinical decision support;
- emergency-response policy;
- operational authorization;
- financial decisions;
- legal decisions;
- cybersecurity actions.

No real-world decision should be based on the embedded demonstration rules.

---

# 31. Final Verification Statement

A successful current test run supports this bounded statement:

> Under the current Python implementation, the same normalized committed signal set, evaluated with the same embedded conflict pairs and decision rules, produces the same bounded decision state and current result hash.

For the committed three-node reference groups:

```text
6 permutations checked
State    = RESOLVED
Decision = Action_Isolate
```

This does not establish universal decision correctness, general artificial intelligence, distributed consensus, independent proof reconstruction, or production safety.
