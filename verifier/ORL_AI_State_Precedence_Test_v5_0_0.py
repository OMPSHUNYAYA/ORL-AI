#!/usr/bin/env python3

"""
ORL-AI v5.0.0 state-precedence test.

The resolver evaluates admission conditions in a fixed order. When a single
input satisfies more than one condition, exactly one must win, and it must
always be the same one. This test freezes that order and asserts it by
constructing inputs that deliberately co-activate two or more conditions, then
checking that the higher-precedence condition governs the result.

Frozen precedence (highest wins), by (state, reason_code):

  0  REFUSED     STRUCTURAL_INTAKE_REFUSAL        (strict intake failure)
  1  DENIED      ACTIVE_PROHIBITION               (prohibition before admission)
  2  ABSTAIN     SOURCE_CONFLICT                  (one source, conflicting stances)
  3  ABSTAIN     MULTIPLE_ELIGIBLE_CANDIDATES     (more than one admissible candidate)
  4  ABSTAIN     BLOCKING_DISAGREEMENT            (opposition or minority on the sole eligible)
  5  ABSTAIN     COMPETING_PARTIAL_SUPPORT        (no eligible, several partially supported)
  6  INCOMPLETE  BOUNDARY_INCOMPLETE              (unsealed or missing declared structure)
  7  RESOLVED    UNIQUE_ADMISSIBLE_CANDIDATE      (exactly one admissible candidate)
  8  INCOMPLETE  ADMISSION_REQUIREMENTS_UNMET     (single under-supported candidate)

Each scenario records the reason codes whose *conditions it injects* and the
reason code it *expects to win*. The test asserts both that the expected code is
observed and that the observed code is the minimum-rank injected code, so no
lower-precedence condition can ever override a higher one.

Usage:
  python -B verifier/ORL_AI_State_Precedence_Test_v5_0_0.py
  python -B verifier/ORL_AI_State_Precedence_Test_v5_0_0.py --receipt-output VERIFY/ORL_AI_State_Precedence_Receipt_v5_0_0.json
"""

import argparse
import copy
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
KERNEL_PATH = ROOT / "demo" / "ORL_AI_Reference_Kernel_v5_0_0.py"


def load_kernel():
    spec = importlib.util.spec_from_file_location("orl_ai_reference_kernel", KERNEL_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


KERNEL = load_kernel()

# Frozen precedence order. Index is the rank; lower rank wins.
PRECEDENCE: List[Tuple[str, str]] = [
    ("REFUSED", "STRUCTURAL_INTAKE_REFUSAL"),
    ("DENIED", "ACTIVE_PROHIBITION"),
    ("ABSTAIN", "SOURCE_CONFLICT"),
    ("ABSTAIN", "MULTIPLE_ELIGIBLE_CANDIDATES"),
    ("ABSTAIN", "BLOCKING_DISAGREEMENT"),
    ("ABSTAIN", "COMPETING_PARTIAL_SUPPORT"),
    ("INCOMPLETE", "BOUNDARY_INCOMPLETE"),
    ("RESOLVED", "UNIQUE_ADMISSIBLE_CANDIDATE"),
    ("INCOMPLETE", "ADMISSION_REQUIREMENTS_UNMET"),
]
RANK = {reason: index for index, (_, reason) in enumerate(PRECEDENCE)}
STATE_OF = {reason: state for state, reason in PRECEDENCE}


def digest(label: str) -> str:
    return KERNEL._digest(label)


def base_document() -> Dict[str, Any]:
    """A clean input that resolves to RESOLVED / QUEUE_ALPHA."""
    return copy.deepcopy(KERNEL.example_document("precedence-base"))


def reseal(document: Dict[str, Any]) -> Dict[str, Any]:
    """Make the declared boundary exactly match the present observations and evidence."""
    document["boundary"] = {
        "expected_observation_ids": sorted(item["observation_id"] for item in document["observations"]),
        "expected_evidence_ids": sorted(item["evidence_id"] for item in document["evidence"]),
    }
    return document


def make_beta_eligible(document: Dict[str, Any]) -> Dict[str, Any]:
    """Add three distinct sources across three families and the three required
    classes, all supporting QUEUE_BETA, so BETA becomes independently eligible."""
    document["sources"].extend([
        {"source_id": "beta-model", "source_family": "family-delta", "source_class": "MODEL"},
        {"source_id": "beta-review", "source_family": "family-epsilon", "source_class": "MODEL_REVIEW"},
        {"source_id": "beta-rule", "source_family": "family-zeta", "source_class": "RULE_CHECK"},
    ])
    document["evidence"].extend([
        {"evidence_id": "e-beta-model", "kind": "DECLARED_FACT", "digest": digest("beta:model")},
        {"evidence_id": "e-beta-review", "kind": "REVIEW_RESULT", "digest": digest("beta:review")},
        {"evidence_id": "e-beta-rule", "kind": "RULE_RESULT", "digest": digest("beta:rule")},
    ])
    document["observations"].extend([
        {"observation_id": "obs-beta-model", "source_id": "beta-model", "candidate_id": "QUEUE_BETA", "stance": "SUPPORT", "evidence_ids": ["e-beta-model"]},
        {"observation_id": "obs-beta-review", "source_id": "beta-review", "candidate_id": "QUEUE_BETA", "stance": "SUPPORT", "evidence_ids": ["e-beta-review"]},
        {"observation_id": "obs-beta-rule", "source_id": "beta-rule", "candidate_id": "QUEUE_BETA", "stance": "SUPPORT", "evidence_ids": ["e-beta-rule"]},
    ])
    return reseal(document)


def forbid_alpha(document: Dict[str, Any]) -> Dict[str, Any]:
    document["constraints"] = [{"constraint_id": "deny-alpha", "kind": "FORBID_CANDIDATE", "candidate_id": "QUEUE_ALPHA", "active": True}]
    return document


def source_supports_beta_too(document: Dict[str, Any]) -> Dict[str, Any]:
    """model-primary already supports ALPHA; also make it support BETA -> source conflict."""
    document["observations"].append(
        {"observation_id": "obs-model-beta", "source_id": "model-primary", "candidate_id": "QUEUE_BETA", "stance": "SUPPORT", "evidence_ids": ["e-format"]}
    )
    return reseal(document)


def oppose_alpha(document: Dict[str, Any]) -> Dict[str, Any]:
    """Add opposition to ALPHA from a fresh, non-conflicting source."""
    document["sources"].append({"source_id": "human-opp", "source_family": "family-omega", "source_class": "HUMAN_REVIEW"})
    document["evidence"].append({"evidence_id": "e-opp", "kind": "REVIEW_RESULT", "digest": digest("opp:alpha")})
    document["observations"].append(
        {"observation_id": "obs-opp", "source_id": "human-opp", "candidate_id": "QUEUE_ALPHA", "stance": "OPPOSE", "evidence_ids": ["e-opp"]}
    )
    return reseal(document)


def open_boundary(document: Dict[str, Any]) -> Dict[str, Any]:
    document["context"]["boundary_state"] = "OPEN"
    return document


def caller_authority(document: Dict[str, Any]) -> Dict[str, Any]:
    document["context"]["authority_mode"] = "CALLER"
    return document


def two_partial_candidates(document: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce to one supporter each for ALPHA and BETA: no eligible, two supported."""
    document["sources"] = [
        {"source_id": "model-primary", "source_family": "family-alpha", "source_class": "MODEL"},
        {"source_id": "model-review", "source_family": "family-beta", "source_class": "MODEL_REVIEW"},
    ]
    document["evidence"] = [
        {"evidence_id": "e-format", "kind": "DECLARED_FACT", "digest": digest("partial:format")},
        {"evidence_id": "e-review", "kind": "REVIEW_RESULT", "digest": digest("partial:review")},
    ]
    document["observations"] = [
        {"observation_id": "obs-alpha", "source_id": "model-primary", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-format"]},
        {"observation_id": "obs-beta", "source_id": "model-review", "candidate_id": "QUEUE_BETA", "stance": "SUPPORT", "evidence_ids": ["e-review"]},
    ]
    return reseal(document)


# Each scenario: name, builder, set of injected reason codes, expected winning reason code.
def build_scenarios() -> List[Dict[str, Any]]:
    scenarios: List[Dict[str, Any]] = []

    def add(name, builder, injected, expected):
        scenarios.append({"name": name, "builder": builder, "injected": injected, "expected": expected})

    # Anchors: single-condition canonical states.
    add("anchor_resolved", lambda: base_document(),
        ["UNIQUE_ADMISSIBLE_CANDIDATE"], "UNIQUE_ADMISSIBLE_CANDIDATE")
    add("anchor_incomplete_open", lambda: open_boundary(base_document()),
        ["BOUNDARY_INCOMPLETE"], "BOUNDARY_INCOMPLETE")
    add("anchor_denied", lambda: forbid_alpha(base_document()),
        ["ACTIVE_PROHIBITION"], "ACTIVE_PROHIBITION")
    add("anchor_refused", lambda: caller_authority(base_document()),
        ["STRUCTURAL_INTAKE_REFUSAL"], "STRUCTURAL_INTAKE_REFUSAL")

    # Adjacent and critical precedence contests (two or more conditions co-active).
    add("refused_over_denied", lambda: forbid_alpha(caller_authority(base_document())),
        ["STRUCTURAL_INTAKE_REFUSAL", "ACTIVE_PROHIBITION"], "STRUCTURAL_INTAKE_REFUSAL")

    add("denied_over_source_conflict", lambda: forbid_alpha(source_supports_beta_too(base_document())),
        ["ACTIVE_PROHIBITION", "SOURCE_CONFLICT"], "ACTIVE_PROHIBITION")

    add("denied_over_incomplete", lambda: forbid_alpha(open_boundary(base_document())),
        ["ACTIVE_PROHIBITION", "BOUNDARY_INCOMPLETE"], "ACTIVE_PROHIBITION")

    add("denied_over_resolved", lambda: forbid_alpha(base_document()),
        ["ACTIVE_PROHIBITION", "UNIQUE_ADMISSIBLE_CANDIDATE"], "ACTIVE_PROHIBITION")

    add("source_conflict_over_multiple_eligible",
        lambda: source_supports_beta_too(make_beta_eligible(base_document())),
        ["SOURCE_CONFLICT", "MULTIPLE_ELIGIBLE_CANDIDATES"], "SOURCE_CONFLICT")

    add("source_conflict_over_incomplete",
        lambda: open_boundary(source_supports_beta_too(base_document())),
        ["SOURCE_CONFLICT", "BOUNDARY_INCOMPLETE"], "SOURCE_CONFLICT")

    add("multiple_eligible_over_disagreement",
        lambda: oppose_alpha(make_beta_eligible(base_document())),
        ["MULTIPLE_ELIGIBLE_CANDIDATES", "BLOCKING_DISAGREEMENT"], "MULTIPLE_ELIGIBLE_CANDIDATES")

    add("multiple_eligible_over_incomplete",
        lambda: open_boundary(make_beta_eligible(base_document())),
        ["MULTIPLE_ELIGIBLE_CANDIDATES", "BOUNDARY_INCOMPLETE"], "MULTIPLE_ELIGIBLE_CANDIDATES")

    add("blocking_disagreement_over_incomplete",
        lambda: open_boundary(oppose_alpha(base_document())),
        ["BLOCKING_DISAGREEMENT", "BOUNDARY_INCOMPLETE"], "BLOCKING_DISAGREEMENT")

    add("competing_partial_over_incomplete",
        lambda: open_boundary(two_partial_candidates(base_document())),
        ["COMPETING_PARTIAL_SUPPORT", "BOUNDARY_INCOMPLETE"], "COMPETING_PARTIAL_SUPPORT")

    add("incomplete_over_resolved", lambda: open_boundary(base_document()),
        ["BOUNDARY_INCOMPLETE", "UNIQUE_ADMISSIBLE_CANDIDATE"], "BOUNDARY_INCOMPLETE")

    return scenarios


def run() -> Tuple[bool, Dict[str, Any]]:
    scenarios = build_scenarios()
    cases: List[Dict[str, Any]] = []
    all_pass = True

    for scenario in scenarios:
        document = scenario["builder"]()
        bundle, _ = KERNEL.resolve_document(document)
        observed_state = bundle["resolution"]["state"]
        observed_reason = bundle["resolution"]["reason_code"]

        expected_reason = scenario["expected"]
        injected = scenario["injected"]

        # 1) The observed winner is the expected one.
        expected_ok = observed_reason == expected_reason and observed_state == STATE_OF.get(expected_reason)

        # 2) Every injected reason is a known precedence tier.
        known_ok = all(reason in RANK for reason in injected)

        # 3) The observed winner is the minimum-rank injected condition:
        #    no lower-precedence condition overrode a higher-precedence one.
        min_rank_injected = min((RANK[reason] for reason in injected), default=None)
        precedence_ok = known_ok and observed_reason in RANK and RANK[observed_reason] == min_rank_injected

        case_pass = expected_ok and precedence_ok
        all_pass = all_pass and case_pass
        cases.append({
            "name": scenario["name"],
            "injected": injected,
            "expected_reason_code": expected_reason,
            "observed_state": observed_state,
            "observed_reason_code": observed_reason,
            "pass": case_pass,
        })

    receipt = {
        "schema": "ORL-AI-STATE-PRECEDENCE-RECEIPT-5.0.0",
        "project": "ORL-AI",
        "version": "5.0.0",
        "precedence": [{"rank": index, "state": state, "reason_code": reason} for index, (state, reason) in enumerate(PRECEDENCE)],
        "cases": cases,
        "pass": all_pass,
    }
    return all_pass, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="ORL-AI deterministic state-precedence test")
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()

    passed, receipt = run()
    for case in receipt["cases"]:
        print(("PASS" if case["pass"] else "FAIL") + "  " + case["name"]
              + "  [" + case["observed_state"] + " / " + case["observed_reason_code"] + "]")
    print("TOTAL " + str(sum(1 for case in receipt["cases"] if case["pass"])) + "/" + str(len(receipt["cases"])) + " PASS")
    print("STATE-PRECEDENCE VERIFY: " + ("PASS" if passed else "FAIL"))

    if args.receipt_output:
        payload = (json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
        args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_output.write_bytes(payload)

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
