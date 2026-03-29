from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from hashlib import sha256
from itertools import permutations
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class ResolveResult:
    state: str
    decision: Optional[str]
    matched_decisions: Tuple[str, ...]

    def as_tuple(self) -> Tuple[str, Optional[str], Tuple[str, ...]]:
        return (self.state, self.decision, self.matched_decisions)


@dataclass(frozen=True)
class GovernanceReport:
    normalized_structure: Tuple[str, ...]
    sufficient_structure: bool
    conflict_detected: bool
    ambiguity_detected: bool
    governance_status: str
    resolution_basis: str


RULES: Dict[FrozenSet[str], str] = {
    frozenset({"fever", "cough", "fatigue"}): "Action_Isolate",
    frozenset({"fever", "cough", "travel_history"}): "Action_Monitor",
    frozenset({"headache", "nausea", "light_sensitivity"}): "Action_DarkRoomCare",
    frozenset({"fever", "rash", "joint_pain"}): "Action_Escalate",
    frozenset({"alert", "verified_source", "stable_metrics"}): "Action_Approve",
    frozenset({"verified_source", "stable_metrics", "low_risk"}): "Action_Approve",
    frozenset({"alert", "critical_signal", "verified_source"}): "Action_Escalate",
}

CONFLICT_PAIRS: Set[FrozenSet[str]] = {
    frozenset({"fatigue", "no_fatigue"}),
    frozenset({"fever", "no_fever"}),
    frozenset({"cough", "no_cough"}),
    frozenset({"headache", "no_headache"}),
    frozenset({"nausea", "no_nausea"}),
    frozenset({"light_sensitivity", "no_light_sensitivity"}),
    frozenset({"rash", "no_rash"}),
    frozenset({"joint_pain", "no_joint_pain"}),
    frozenset({"travel_history", "no_travel_history"}),
    frozenset({"alert", "no_alert"}),
    frozenset({"verified_source", "unverified_source"}),
    frozenset({"stable_metrics", "unstable_metrics"}),
    frozenset({"low_risk", "high_risk"}),
    frozenset({"critical_signal", "no_critical_signal"}),
}


def normalize(structure: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted(set(structure)))


def has_conflict(structure: Set[str]) -> bool:
    for pair in CONFLICT_PAIRS:
        if pair.issubset(structure):
            return True
    return False


def matched_decisions(structure: Set[str]) -> List[str]:
    matches: List[str] = []
    for rule_inputs, decision in RULES.items():
        if rule_inputs.issubset(structure):
            matches.append(decision)
    return sorted(matches)


def resolve(structure: Iterable[str]) -> ResolveResult:
    s = set(normalize(structure))

    if has_conflict(s):
        return ResolveResult("ABSTAIN", None, tuple())

    matches = matched_decisions(s)
    unique_decisions = sorted(set(matches))

    if len(unique_decisions) > 1:
        return ResolveResult("ABSTAIN", None, tuple(matches))

    if len(unique_decisions) == 1:
        decision = unique_decisions[0]
        return ResolveResult("RESOLVED", decision, (decision,))

    return ResolveResult("INCOMPLETE", None, tuple())


def analyze_structure(structure: Iterable[str]) -> GovernanceReport:
    s = set(normalize(structure))
    normalized = tuple(sorted(s))
    conflict_detected = has_conflict(s)
    matches = matched_decisions(s)
    unique_decisions = set(matches)
    ambiguity_detected = len(unique_decisions) > 1
    sufficient_structure = len(unique_decisions) == 1 and not conflict_detected

    if conflict_detected:
        governance_status = "REJECTED_CONFLICT"
        resolution_basis = "conflicting structure detected"
    elif ambiguity_detected:
        governance_status = "REJECTED_AMBIGUITY"
        resolution_basis = "multiple incompatible decisions detected"
    elif sufficient_structure:
        decision = sorted(unique_decisions)[0]
        governance_status = "ACCEPTED_UNIQUE_MATCH"
        resolution_basis = f"unique structural match -> {decision}"
    else:
        governance_status = "PENDING_INCOMPLETE"
        resolution_basis = "insufficient structure for unique decision"

    return GovernanceReport(
        normalized_structure=normalized,
        sufficient_structure=sufficient_structure,
        conflict_detected=conflict_detected,
        ambiguity_detected=ambiguity_detected,
        governance_status=governance_status,
        resolution_basis=resolution_basis,
    )


def certificate(structure: Iterable[str], result: ResolveResult) -> str:
    normalized_structure = ",".join(normalize(structure))
    matched = ",".join(result.matched_decisions)
    payload = (
        f"structure=[{normalized_structure}]|"
        f"state={result.state}|"
        f"decision={result.decision}|"
        f"matched=[{matched}]"
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def build_resolution_capsule(case_id: str, structure: Iterable[str], result: ResolveResult) -> Dict:
    s = list(normalize(structure))
    matches = list(result.matched_decisions)
    governance = analyze_structure(structure)

    return {
        "case_id": case_id,
        "proof_class": "STRUCTURAL_DECISION_PROOF",
        "normalized_structure": s,
        "state": result.state,
        "decision": result.decision,
        "matched_decisions": matches,
        "governance_status": governance.governance_status,
        "resolution_basis": governance.resolution_basis,
        "decision_acceptance_rule": "normalize(structure) satisfies: sufficient_structure AND conflict_free AND uniquely_valid",
        "certificate": certificate(structure, result),
        "determinism_statement": "same normalized structure -> same decision -> same certificate",
    }


def merge_all(*structures: Iterable[str]) -> Set[str]:
    merged: Set[str] = set()
    for structure in structures:
        merged |= set(structure)
    return merged


def print_case(name: str, structure: Iterable[str]) -> None:
    s = set(normalize(structure))
    result = resolve(s)
    governance = analyze_structure(s)
    cert = certificate(s, result)
    print(name)
    print(f"  Structure           : {sorted(s)}")
    print(f"  State               : {result.state}")
    print(f"  Decision            : {result.decision}")
    print(f"  Matched decisions   : {list(result.matched_decisions)}")
    print(f"  Governance status   : {governance.governance_status}")
    print(f"  Resolution basis    : {governance.resolution_basis}")
    print(f"  Cert                : {cert[:16]}...")
    print()


def print_capsule(title: str, capsule: Dict) -> None:
    print(title)
    print(f"  Case ID                   : {capsule['case_id']}")
    print(f"  Proof class               : {capsule['proof_class']}")
    print(f"  Structure                 : {capsule['normalized_structure']}")
    print(f"  State                     : {capsule['state']}")
    print(f"  Decision                  : {capsule['decision']}")
    print(f"  Matched decisions         : {capsule['matched_decisions']}")
    print(f"  Governance status         : {capsule['governance_status']}")
    print(f"  Resolution basis          : {capsule['resolution_basis']}")
    print(f"  Acceptance rule           : {capsule['decision_acceptance_rule']}")
    print(f"  Determinism statement     : {capsule['determinism_statement']}")
    print(f"  Cert                      : {capsule['certificate'][:16]}...")
    print()


def print_governance_summary(name: str, structure: Iterable[str]) -> None:
    governance = analyze_structure(structure)
    print(name)
    print(f"  Normalized structure : {list(governance.normalized_structure)}")
    print(f"  Sufficient structure : {governance.sufficient_structure}")
    print(f"  Conflict detected    : {governance.conflict_detected}")
    print(f"  Ambiguity detected   : {governance.ambiguity_detected}")
    print(f"  Governance status    : {governance.governance_status}")
    print(f"  Resolution basis     : {governance.resolution_basis}")
    print()


def permutation_check(parts: Tuple[Set[str], ...]) -> Tuple[bool, Optional[ResolveResult], Optional[str], int]:
    reference_result: Optional[ResolveResult] = None
    reference_cert: Optional[str] = None
    checked = 0

    for perm in permutations(parts):
        merged = merge_all(*perm)
        result = resolve(merged)
        cert = certificate(merged, result)
        checked += 1

        if reference_result is None:
            reference_result = result
            reference_cert = cert
            continue

        if result != reference_result or cert != reference_cert:
            return False, reference_result, reference_cert, checked

    return True, reference_result, reference_cert, checked


def case_payload(case_id: str, structure: Iterable[str]) -> dict:
    s = set(normalize(structure))
    result = resolve(s)
    governance = analyze_structure(s)
    capsule = build_resolution_capsule(case_id, s, result)
    return {
        "structure": sorted(s),
        "state": result.state,
        "decision": result.decision,
        "matched_decisions": list(result.matched_decisions),
        "certificate": certificate(s, result),
        "governance": {
            "normalized_structure": list(governance.normalized_structure),
            "sufficient_structure": governance.sufficient_structure,
            "conflict_detected": governance.conflict_detected,
            "ambiguity_detected": governance.ambiguity_detected,
            "governance_status": governance.governance_status,
            "resolution_basis": governance.resolution_basis,
        },
        "resolution_capsule": capsule,
    }


def build_summary_payload() -> dict:
    node_a = {"fever"}
    node_b = {"cough"}
    node_c = {"fatigue"}
    merged_abc = merge_all(node_a, node_b, node_c)

    replay_x = {"cough", "fatigue"}
    replay_y = {"fever"}
    replay_z: Set[str] = set()
    merged_xyz = merge_all(replay_x, replay_y, replay_z)

    conflict_a = {"fever"}
    conflict_b = {"cough"}
    conflict_c = {"fatigue", "no_fatigue"}
    merged_conflict = merge_all(conflict_a, conflict_b, conflict_c)

    ambiguity_a = {"fever"}
    ambiguity_b = {"cough"}
    ambiguity_c = {"fatigue", "travel_history"}
    merged_ambiguity = merge_all(ambiguity_a, ambiguity_b, ambiguity_c)

    five_a = {"alert"}
    five_b = {"verified_source"}
    five_c = {"stable_metrics"}
    five_d = set()
    five_e = set()
    merged_five = merge_all(five_a, five_b, five_c, five_d, five_e)

    replay_five_1 = {"alert", "verified_source"}
    replay_five_2 = {"stable_metrics"}
    replay_five_3 = set()
    merged_five_replay = merge_all(replay_five_1, replay_five_2, replay_five_3)

    approve_a = {"verified_source"}
    approve_b = {"stable_metrics"}
    approve_c = {"low_risk"}
    merged_approve = merge_all(approve_a, approve_b, approve_c)

    escalate_a = {"alert"}
    escalate_b = {"critical_signal"}
    escalate_c = {"verified_source"}
    merged_escalate = merge_all(escalate_a, escalate_b, escalate_c)

    conflict_replay_a = {"fatigue"}
    conflict_replay_b = {"no_fatigue"}
    conflict_replay_c = {"fever", "cough"}
    merged_conflict_replay = merge_all(conflict_replay_a, conflict_replay_b, conflict_replay_c)

    dual_approve_overlap = {"alert", "verified_source", "stable_metrics", "low_risk"}

    result_abc = resolve(merged_abc)
    result_xyz = resolve(merged_xyz)
    result_conflict = resolve(merged_conflict)
    result_ambiguity = resolve(merged_ambiguity)
    result_five = resolve(merged_five)
    result_five_replay = resolve(merged_five_replay)
    result_approve = resolve(merged_approve)
    result_escalate = resolve(merged_escalate)
    result_conflict_replay = resolve(merged_conflict_replay)
    result_dual_approve_overlap = resolve(dual_approve_overlap)

    perm_ok, perm_result, perm_cert, perm_count = permutation_check((node_a, node_b, node_c))

    return {
        "core_identity": {
            "axiom_1": "correctness != training + data_order + synchronization",
            "axiom_2": "decision = resolve(normalize(structure))",
        },
        "reference_merge": case_payload("CASE_3NODE_REFERENCE", merged_abc),
        "replay_merge": case_payload("CASE_3NODE_REPLAY", merged_xyz),
        "conflict_merge": case_payload("CASE_CONFLICT", merged_conflict),
        "ambiguity_merge": case_payload("CASE_AMBIGUITY", merged_ambiguity),
        "five_node_merge": case_payload("CASE_5NODE", merged_five),
        "five_node_replay_merge": case_payload("CASE_5NODE_REPLAY", merged_five_replay),
        "domain_portability": {
            "approve_path": case_payload("CASE_APPROVE_DOMAIN", merged_approve),
            "escalate_path": case_payload("CASE_ESCALATE_DOMAIN", merged_escalate),
            "dual_approve_overlap": case_payload("CASE_DUAL_APPROVE_OVERLAP", dual_approve_overlap),
        },
        "governance_stability": {
            "conflict_merge": case_payload("CASE_CONFLICT", merged_conflict),
            "conflict_replay_merge": case_payload("CASE_CONFLICT_REPLAY", merged_conflict_replay),
        },
        "resolution_capsules": [
            build_resolution_capsule("CASE_3NODE_REFERENCE", merged_abc, result_abc),
            build_resolution_capsule("CASE_3NODE_REPLAY", merged_xyz, result_xyz),
            build_resolution_capsule("CASE_CONFLICT", merged_conflict, result_conflict),
            build_resolution_capsule("CASE_AMBIGUITY", merged_ambiguity, result_ambiguity),
            build_resolution_capsule("CASE_5NODE", merged_five, result_five),
            build_resolution_capsule("CASE_5NODE_REPLAY", merged_five_replay, result_five_replay),
            build_resolution_capsule("CASE_APPROVE_DOMAIN", merged_approve, result_approve),
            build_resolution_capsule("CASE_ESCALATE_DOMAIN", merged_escalate, result_escalate),
            build_resolution_capsule("CASE_DUAL_APPROVE_OVERLAP", dual_approve_overlap, result_dual_approve_overlap),
            build_resolution_capsule("CASE_CONFLICT_REPLAY", merged_conflict_replay, result_conflict_replay),
        ],
        "permutation_check": {
            "checked": perm_count,
            "independent": perm_ok,
            "state": None if perm_result is None else perm_result.state,
            "decision": None if perm_result is None else perm_result.decision,
            "certificate": perm_cert,
        },
        "final_checks": {
            "converged_decision": result_abc.as_tuple() == result_xyz.as_tuple(),
            "matching_certificate": certificate(merged_abc, result_abc) == certificate(merged_xyz, result_xyz),
            "five_node_converged_decision": result_five.as_tuple() == result_five_replay.as_tuple(),
            "five_node_matching_certificate": certificate(merged_five, result_five) == certificate(merged_five_replay, result_five_replay),
            "conflict_governance_stable": analyze_structure(merged_conflict).governance_status == analyze_structure(merged_conflict_replay).governance_status,
            "conflict_capsule_stable": build_resolution_capsule("CASE_CONFLICT", merged_conflict, result_conflict)["governance_status"]
            == build_resolution_capsule("CASE_CONFLICT_REPLAY", merged_conflict_replay, result_conflict_replay)["governance_status"],
            "dual_approve_overlap_resolved": result_dual_approve_overlap.state == "RESOLVED",
            "dual_approve_overlap_decision": result_dual_approve_overlap.decision == "Action_Approve",
        },
        "theorem_block": [
            "same normalized structure -> same decision",
            "same normalized structure -> same certificate",
            "missing structure -> INCOMPLETE",
            "conflicting structure -> ABSTAIN",
            "multiple incompatible decisions -> ABSTAIN",
            "multiple matching rules with one unique decision -> RESOLVED",
            "same structural law -> portable across bounded domains",
            "governed structure -> auditable decision",
            "resolution is a deterministic function of normalized structure",
            "decision acceptance requires normalize(structure) satisfies: sufficient_structure AND conflict_free AND uniquely_valid",
            "each resolved structure produces a verifiable resolution capsule",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-output", action="store_true")
    parser.add_argument("--output", default="orl_ai_result_v4_1.json")
    args = parser.parse_args()

    node_a = {"fever"}
    node_b = {"cough"}
    node_c = {"fatigue"}
    merged_abc = merge_all(node_a, node_b, node_c)

    replay_x = {"cough", "fatigue"}
    replay_y = {"fever"}
    replay_z: Set[str] = set()
    merged_xyz = merge_all(replay_x, replay_y, replay_z)

    conflict_a = {"fever"}
    conflict_b = {"cough"}
    conflict_c = {"fatigue", "no_fatigue"}
    merged_conflict = merge_all(conflict_a, conflict_b, conflict_c)

    ambiguity_a = {"fever"}
    ambiguity_b = {"cough"}
    ambiguity_c = {"fatigue", "travel_history"}
    merged_ambiguity = merge_all(ambiguity_a, ambiguity_b, ambiguity_c)

    five_a = {"alert"}
    five_b = {"verified_source"}
    five_c = {"stable_metrics"}
    five_d = set()
    five_e = set()
    merged_five = merge_all(five_a, five_b, five_c, five_d, five_e)

    replay_five_1 = {"alert", "verified_source"}
    replay_five_2 = {"stable_metrics"}
    replay_five_3 = set()
    merged_five_replay = merge_all(replay_five_1, replay_five_2, replay_five_3)

    approve_a = {"verified_source"}
    approve_b = {"stable_metrics"}
    approve_c = {"low_risk"}
    merged_approve = merge_all(approve_a, approve_b, approve_c)

    escalate_a = {"alert"}
    escalate_b = {"critical_signal"}
    escalate_c = {"verified_source"}
    merged_escalate = merge_all(escalate_a, escalate_b, escalate_c)

    dual_approve_overlap = {"alert", "verified_source", "stable_metrics", "low_risk"}

    conflict_replay_a = {"fatigue"}
    conflict_replay_b = {"no_fatigue"}
    conflict_replay_c = {"fever", "cough"}
    merged_conflict_replay = merge_all(conflict_replay_a, conflict_replay_b, conflict_replay_c)

    result_abc = resolve(merged_abc)
    result_xyz = resolve(merged_xyz)
    result_conflict = resolve(merged_conflict)
    result_ambiguity = resolve(merged_ambiguity)
    result_five = resolve(merged_five)
    result_five_replay = resolve(merged_five_replay)
    result_approve = resolve(merged_approve)
    result_escalate = resolve(merged_escalate)
    result_dual_approve_overlap = resolve(dual_approve_overlap)
    result_conflict_replay = resolve(merged_conflict_replay)

    capsule_abc = build_resolution_capsule("CASE_3NODE_REFERENCE", merged_abc, result_abc)
    capsule_xyz = build_resolution_capsule("CASE_3NODE_REPLAY", merged_xyz, result_xyz)
    capsule_conflict = build_resolution_capsule("CASE_CONFLICT", merged_conflict, result_conflict)
    capsule_ambiguity = build_resolution_capsule("CASE_AMBIGUITY", merged_ambiguity, result_ambiguity)
    capsule_five = build_resolution_capsule("CASE_5NODE", merged_five, result_five)
    capsule_five_replay = build_resolution_capsule("CASE_5NODE_REPLAY", merged_five_replay, result_five_replay)
    capsule_approve = build_resolution_capsule("CASE_APPROVE_DOMAIN", merged_approve, result_approve)
    capsule_escalate = build_resolution_capsule("CASE_ESCALATE_DOMAIN", merged_escalate, result_escalate)
    capsule_dual_approve_overlap = build_resolution_capsule("CASE_DUAL_APPROVE_OVERLAP", dual_approve_overlap, result_dual_approve_overlap)
    capsule_conflict_replay = build_resolution_capsule("CASE_CONFLICT_REPLAY", merged_conflict_replay, result_conflict_replay)

    print("=" * 72)
    print("ORL-AI V4.1 DEMO")
    print("=" * 72)
    print("Core identity:")
    print("  correctness != training + data_order + synchronization")
    print("  decision = resolve(normalize(structure))")
    print()

    print("REFERENCE 3-NODE SCENARIO")
    print("-" * 72)
    print_case("Node A", node_a)
    print_case("Node B", node_b)
    print_case("Node C", node_c)
    print_case("Merged A+B+C", merged_abc)
    print_capsule("RESOLUTION CAPSULE — 3-NODE REFERENCE", capsule_abc)

    print("REPLAY / DIFFERENT GROUPING SCENARIO")
    print("-" * 72)
    print_case("Replay Node X", replay_x)
    print_case("Replay Node Y", replay_y)
    print_case("Replay Node Z", replay_z)
    print_case("Merged X+Y+Z", merged_xyz)
    print_capsule("RESOLUTION CAPSULE — 3-NODE REPLAY", capsule_xyz)

    print("CONFLICT-SAFETY SCENARIO")
    print("-" * 72)
    print_case("Conflict Node A", conflict_a)
    print_case("Conflict Node B", conflict_b)
    print_case("Conflict Node C", conflict_c)
    print_case("Merged Conflict", merged_conflict)
    print_capsule("RESOLUTION CAPSULE — CONFLICT", capsule_conflict)

    print("MULTI-RULE AMBIGUITY SCENARIO")
    print("-" * 72)
    print_case("Ambiguity Node A", ambiguity_a)
    print_case("Ambiguity Node B", ambiguity_b)
    print_case("Ambiguity Node C", ambiguity_c)
    print_case("Merged Ambiguity", merged_ambiguity)
    print_capsule("RESOLUTION CAPSULE — AMBIGUITY", capsule_ambiguity)

    print("5-NODE CONVERGENCE SCENARIO")
    print("-" * 72)
    print_case("Five Node A", five_a)
    print_case("Five Node B", five_b)
    print_case("Five Node C", five_c)
    print_case("Five Node D", five_d)
    print_case("Five Node E", five_e)
    print_case("Merged Five-Node", merged_five)
    print_capsule("RESOLUTION CAPSULE — 5-NODE", capsule_five)

    print("5-NODE REPLAY / DIFFERENT GROUPING")
    print("-" * 72)
    print_case("Replay Five Node 1", replay_five_1)
    print_case("Replay Five Node 2", replay_five_2)
    print_case("Replay Five Node 3", replay_five_3)
    print_case("Merged Five-Node Replay", merged_five_replay)
    print_capsule("RESOLUTION CAPSULE — 5-NODE REPLAY", capsule_five_replay)

    print("DOMAIN PORTABILITY SCENARIO")
    print("-" * 72)
    print_case("Approve Path A", approve_a)
    print_case("Approve Path B", approve_b)
    print_case("Approve Path C", approve_c)
    print_case("Merged Approve Path", merged_approve)
    print_capsule("RESOLUTION CAPSULE — APPROVE DOMAIN", capsule_approve)
    print_case("Escalate Path A", escalate_a)
    print_case("Escalate Path B", escalate_b)
    print_case("Escalate Path C", escalate_c)
    print_case("Merged Escalate Path", merged_escalate)
    print_capsule("RESOLUTION CAPSULE — ESCALATE DOMAIN", capsule_escalate)

    print("UNIQUE-DECISION OVERLAP SCENARIO")
    print("-" * 72)
    print_case("Dual Approve Overlap", dual_approve_overlap)
    print_capsule("RESOLUTION CAPSULE — DUAL APPROVE OVERLAP", capsule_dual_approve_overlap)

    print("GOVERNANCE STABILITY SCENARIO")
    print("-" * 72)
    print_case("Conflict Replay A", conflict_replay_a)
    print_case("Conflict Replay B", conflict_replay_b)
    print_case("Conflict Replay C", conflict_replay_c)
    print_case("Merged Conflict Replay", merged_conflict_replay)
    print_capsule("RESOLUTION CAPSULE — CONFLICT REPLAY", capsule_conflict_replay)

    print("PERMUTATION-INDEPENDENCE CHECK")
    print("-" * 72)
    perm_ok, perm_result, perm_cert, perm_count = permutation_check((node_a, node_b, node_c))
    print(f"Permutations checked        : {perm_count}")
    print(f"Permutation independence    : {perm_ok}")
    if perm_result is not None:
        print(f"Resolved state              : {perm_result.state}")
        print(f"Resolved decision           : {perm_result.decision}")
    if perm_cert is not None:
        print(f"Resolved cert               : {perm_cert[:16]}...")
    print()

    print("STRUCTURAL GOVERNANCE SUMMARY")
    print("-" * 72)
    print_governance_summary("Reference Merge Governance", merged_abc)
    print_governance_summary("Conflict Merge Governance", merged_conflict)
    print_governance_summary("Ambiguity Merge Governance", merged_ambiguity)
    print_governance_summary("Five-Node Governance", merged_five)
    print_governance_summary("Dual Approve Overlap Governance", dual_approve_overlap)
    print_governance_summary("Conflict Replay Governance", merged_conflict_replay)

    cert_abc = certificate(merged_abc, result_abc)
    cert_xyz = certificate(merged_xyz, result_xyz)
    cert_five = certificate(merged_five, result_five)
    cert_five_replay = certificate(merged_five_replay, result_five_replay)

    print("FINAL CHECKS")
    print("-" * 72)
    print(f"3-node converged decision   : {result_abc.as_tuple() == result_xyz.as_tuple()}")
    print(f"3-node matching cert        : {cert_abc == cert_xyz}")
    print(f"5-node converged decision   : {result_five.as_tuple() == result_five_replay.as_tuple()}")
    print(f"5-node matching cert        : {cert_five == cert_five_replay}")
    print(f"Dual approve overlap state  : {result_dual_approve_overlap.state}")
    print(f"Dual approve overlap action : {result_dual_approve_overlap.decision}")
    print(
        f"Conflict governance stable  : "
        f"{analyze_structure(merged_conflict).governance_status == analyze_structure(merged_conflict_replay).governance_status}"
    )
    print(
        f"Conflict capsule stable     : "
        f"{capsule_conflict['governance_status'] == capsule_conflict_replay['governance_status']}"
    )
    print()

    print("THEOREM BLOCK")
    print("-" * 72)
    print("same normalized structure -> same decision")
    print("same normalized structure -> same certificate")
    print("missing structure -> INCOMPLETE")
    print("conflicting structure -> ABSTAIN")
    print("multiple incompatible decisions -> ABSTAIN")
    print("multiple matching rules with one unique decision -> RESOLVED")
    print("same structural law -> portable across bounded domains")
    print("governed structure -> auditable decision")
    print("resolution is a deterministic function of normalized structure")
    print("decision acceptance requires normalize(structure) satisfies: sufficient_structure AND conflict_free AND uniquely_valid")
    print("each resolved structure produces a verifiable resolution capsule")
    print()

    print("EXPECTED INTERPRETATION")
    print("-" * 72)
    print("Independent incomplete nodes can converge through structure alone.")
    print("Different groupings of the same fragments produce the same result.")
    print("Conflict is never forced.")
    print("Ambiguity is never forced.")
    print("Five-node bounded convergence is demonstrated.")
    print("The same structural law works across more than one bounded decision domain.")
    print("Every resolution path now has an auditable governance basis.")
    print("Each major scenario now produces a portable structural resolution capsule.")
    print("Multiple matching rules with one unique decision still resolve safely.")
    print()
    print("Decision is accepted only when normalized structure is sufficient, conflict-free, and uniquely_valid.")
    print()
    print("In short:")
    print("  decision = resolve(normalize(structure))")
    print("=" * 72)

    if args.write_output:
        payload = build_summary_payload()
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"Wrote output JSON           : {args.output}")


if __name__ == "__main__":
    main()