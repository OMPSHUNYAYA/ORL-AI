# ⭐ ORL-AI — Quickstart

## Deterministic Bounded Structural Decision Resolution

This guide provides the fastest way to run and inspect the current ORL-AI Python reference implementation.

ORL-AI is a bounded deterministic rule resolver.

It normalizes input signal strings, checks an embedded conflict-pair table, applies an embedded decision-rule table, and returns one of three states:

- `RESOLVED`
- `INCOMPLETE`
- `ABSTAIN`

The current governing relation is:

`same normalized supported signal set + same embedded conflict pairs + same embedded decision rules -> same bounded decision state and current result hash`

ORL-AI is developed within the Shunyaya Framework.

---

## ⚡ Run the Reference Demo

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

## ✅ Main Reference Result

The committed three-node reference groups are:

```text
Node-A = {fever}
Node-B = {cough}
Node-C = {fatigue}
```

Each individual node is initially:

```text
State    = INCOMPLETE
Decision = None
```

After local set union and normalization:

```text
cough
fatigue
fever
```

the embedded rule:

```text
{fever, cough, fatigue} -> Action_Isolate
```

matches uniquely.

Expected result:

```text
State             = RESOLVED
Decision          = Action_Isolate
Governance status = ACCEPTED_UNIQUE_MATCH
```

---

## 🔁 Regrouped Replay Result

The same signals are grouped differently:

```text
Replay-X = {cough, fatigue}
Replay-Y = {fever}
Replay-Z = {}
```

After local set union and normalization, the structure is again:

```text
cough
fatigue
fever
```

Expected result:

```text
State    = RESOLVED
Decision = Action_Isolate
```

The reference and replay cases should produce:

```text
same state        = True
same decision     = True
same current hash = True
```

This demonstrates same-evidence equality after local regrouping.

It does not implement a networking, delivery, synchronization, or consensus protocol.

---

## 🔀 Permutation Check

The demo checks all permutations of the three committed reference node groups:

```text
{fever}
{cough}
{fatigue}
```

The number of checked permutations is:

```text
3! = 6
```

Expected output:

```text
Permutations checked        : 6
Permutation independence    : True
Resolved state              : RESOLVED
Resolved decision           : Action_Isolate
```

This result is exhaustive only for those three committed groups.

It is not a universal proof for arbitrary signals, nodes, rules, conflicts, malformed inputs, hostile inputs, or independent implementations.

---

## 🧪 Generate the Reference JSON Output

Run:

```bash
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/orl_ai_result_v4_1.json
```

Expected final console line:

```text
Wrote output JSON           : outputs/orl_ai_result_v4_1.json
```

The command writes or replaces the selected output file.

Review local changes before committing a regenerated artifact.

---

## 📦 Expected JSON Sections

The generated file should contain these top-level keys:

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

They should not be interpreted as independently verified formal proofs.

---

## ⚖️ Resolver States

### RESOLVED

Returned when:

- no embedded conflict pair is present; and
- exactly one unique decision label is matched.

Formally:

`conflict(S) = False AND |U(S)| = 1 -> RESOLVED`

Multiple rules may match and still resolve when every matching rule produces the same decision label.

---

### INCOMPLETE

Returned when:

- no embedded conflict pair is present; and
- no decision rule matches.

Formally:

`conflict(S) = False AND |U(S)| = 0 -> INCOMPLETE`

The resolver does not invent missing signals.

---

### ABSTAIN

Returned when either:

- an embedded conflict pair is present; or
- more than one incompatible decision label is matched.

Formally:

`conflict(S) = True -> ABSTAIN`

or:

`conflict(S) = False AND |U(S)| > 1 -> ABSTAIN`

`ABSTAIN` is a bounded resolver classification. It is not a general safety guarantee.

---

## 🧭 Included Scenarios

### Reference Merge

```text
{fever} + {cough} + {fatigue}
-> RESOLVED
-> Action_Isolate
```

### Regrouped Replay

```text
{cough, fatigue} + {fever} + {}
-> RESOLVED
-> Action_Isolate
```

### Explicit Conflict

```text
{fever, cough, fatigue, no_fatigue}
-> ABSTAIN
-> REJECTED_CONFLICT
```

### Multi-Decision Ambiguity

```text
{fever, cough, fatigue, travel_history}
-> Action_Isolate and Action_Monitor match
-> ABSTAIN
-> REJECTED_AMBIGUITY
```

### Nominal Five-Node Case

The demo declares five node containers, with three contributing non-empty sets and two empty sets:

```text
{alert} + {verified_source} + {stable_metrics} + {} + {}
-> RESOLVED
-> Action_Approve
```

### Five-Node Replay Grouping

```text
{alert, verified_source} + {stable_metrics} + {}
-> RESOLVED
-> Action_Approve
```

### Approval Path

```text
{verified_source, stable_metrics, low_risk}
-> RESOLVED
-> Action_Approve
```

### Escalation Path

```text
{alert, critical_signal, verified_source}
-> RESOLVED
-> Action_Escalate
```

### Same-Decision Rule Overlap

```text
{alert, verified_source, stable_metrics, low_risk}
-> multiple matching rules
-> one unique decision
-> RESOLVED
-> Action_Approve
```

### Conflict Regrouping

Two differently grouped conflict cases normalize to the same conflicting set and produce:

```text
State             = ABSTAIN
Governance status = REJECTED_CONFLICT
```

---

## 🔐 Current Result Hash

The function named `certificate(...)` builds a delimiter-based text payload containing:

```text
normalized structure
state
decision
matched decisions
```

It then computes SHA-256.

The current relation is:

`same current payload bytes -> same SHA-256 hash`

For the reference and replay scenarios, the expected current result hash is:

```text
7f763b91b0ed88ecae869feba2d872ee7bcfcc6afdd666eb35bf989ca10a89fb
```

The current field named `certificate` should be interpreted as a deterministic result hash or receipt for the present payload construction.

It is not yet:

- an independently reconstructed proof;
- a signed certificate;
- a schema-bound receipt;
- a ruleset-bound receipt;
- a conflict-manifest-bound receipt;
- an authenticated attestation.

---

## 📦 Resolution Capsule Boundary

The generated output includes structured result records containing fields such as:

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

For the current release, these capsules are structured resolver-result records.

Independent reconstruction, canonical serialization, schema binding, ruleset binding, conflict-manifest binding, and signature verification are future technical targets.

---

## 🔁 Repeatability Check

Generate two temporary outputs:

```bash
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/run_1.json
python demo/orl_ai_demo_base_v4_1.py --write-output --output outputs/run_2.json
```

### Windows Command Prompt

```bat
fc /b outputs\run_1.json outputs\run_2.json
```

Expected:

```text
FC: no differences encountered
```

### PowerShell

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

### Linux or macOS

```bash
cmp outputs/run_1.json outputs/run_2.json
sha256sum outputs/run_1.json outputs/run_2.json
```

Expected:

- `cmp` produces no difference output;
- both SHA-256 values are identical.

Delete temporary outputs after review when they are not intended for the repository.

---

## ✅ Final Checks to Review

The console should display six Boolean comparison checks as `True`, together with:

```text
Dual approve overlap state  : RESOLVED
Dual approve overlap action : Action_Approve
```

The generated JSON should contain all eight `final_checks` values as `true`:

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

The current script prints checks but does not enforce every failed condition through a non-zero process exit.

A zero exit code alone is therefore not sufficient.

Review the printed checks and generated JSON.

---

## 📁 Repository Structure

```text
ORL-AI/
├── README.md
├── LICENSE
├── demo/
│   └── orl_ai_demo_base_v4_1.py
├── docs/
│   ├── ORL-AI-Structural-Decision-Overview-v1.png
│   ├── FAQ.md
│   ├── Quickstart.md
│   ├── Test-Guide.md
│   └── Proof-Sketch.md
├── outputs/
│   └── orl_ai_result_v4_1.json
└── VERIFY/
    ├── VERIFY.txt
    └── FREEZE_DEMO_SHA256.txt
```

---

## ⚙️ Requirements

- Python 3.9 or later
- Python standard library only
- no third-party runtime dependency
- no runtime GPS or NTP
- no runtime database
- no live server required
- no runtime internet connection required after download

---

## 🚫 What This Quickstart Does Not Establish

The current demo does not establish:

- general artificial intelligence;
- machine learning correctness;
- model training;
- prediction;
- unrestricted decision correctness;
- factual truth;
- universal order independence;
- universal time independence;
- universal synchronization independence;
- autonomous evidence delivery;
- distributed consensus;
- reliable broadcast;
- sender identity or authenticity;
- authorization;
- encryption;
- replay-attack prevention;
- independent proof reconstruction;
- cross-language conformance;
- immutable finality;
- production safety;
- regulatory compliance.

---

## ⚠️ Synthetic Scenario Notice

Some demonstration labels resemble medical or operational terms:

```text
fever
cough
fatigue
Action_Isolate
Action_Monitor
Action_DarkRoomCare
```

These are synthetic demonstration labels only.

ORL-AI is not:

- medical advice;
- a diagnostic system;
- clinical decision support;
- an emergency-response authority;
- an autonomous medical system;
- a production operational authority.

No real-world medical, safety, financial, legal, cybersecurity, or operational decision should be based on the embedded demonstration rules.

---

## 🛡 Current Technical Limitations

The current implementation has:

- embedded rule and conflict tables;
- no formal input schema;
- no enforced supported-signal allowlist;
- no canonical byte-serialization specification;
- no schema, ruleset, or conflict-manifest version binding;
- no independent verifier;
- no cross-language implementation;
- printed checks rather than complete assertion-enforced failure gates;
- six committed reference-group permutations rather than a broad conformance corpus;
- local set union rather than a communication protocol;
- no structural-closure or immutable-finality layer;
- no production threat model.

Additional evidence may change a previously `RESOLVED` state to `ABSTAIN`.

The current implementation does not claim monotonic finality.

---

## 🧪 Verification Boundary

Use:

```text
VERIFY/VERIFY.txt
```

for platform-specific verification commands.

Compare files against:

```text
VERIFY/FREEZE_DEMO_SHA256.txt
```

Frozen file hashing establishes:

`same file bytes -> same SHA-256 hash`

It does not by itself prove behavioral correctness, decision truth, schema validity, independent reconstruction, security, or production readiness.

Do not regenerate frozen hashes until the later coordinated technical revision is complete.

---

## 🧭 Future Technical Direction

A stronger revision should add:

- formal versioned input schemas;
- an explicit supported-signal vocabulary;
- validated versioned decision-rule manifests;
- validated versioned conflict manifests;
- canonical byte serialization;
- deterministic byte-wise ordering;
- schema, ruleset, and conflict-manifest hashes;
- assertion-enforced failure gates;
- malformed-input vectors;
- unknown-signal vectors;
- duplicate-insertion vectors;
- conflict vectors;
- multi-decision ambiguity vectors;
- same-decision overlap vectors;
- regrouping vectors;
- metamorphic tests;
- independent reconstruction;
- cross-language conformance;
- explicit structural-closure rules.

Future target relation:

`same validated canonical signals + same ruleset and conflict-manifest versions -> same independently reconstructed bounded decision result and receipt`

This target is not part of the current implementation.

---

## ⭐ One-Line Summary

ORL-AI is a deterministic bounded reference model in which the same normalized supported signal set, evaluated under the same embedded conflict pairs and decision rules, produces the same bounded decision state and current result hash.

For the committed three-node reference groups:

```text
6 permutations checked
State    = RESOLVED
Decision = Action_Isolate
```
