#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT = "ORL-AI"
VERSION = "5.0.0"
CAPSULE_SCHEMA = "ORL-AI-DECISION-ADMISSION-CAPSULE-5.0.0"
COMPARISON_SCHEMA = "ORL-AI-CAPSULE-COMPARISON-5.0.0"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def tagged_hash(tag: str, value: Any) -> str:
    return "sha256:" + hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))


def build_capsule(bundle: Dict[str, Any]) -> Dict[str, Any]:
    resolution = bundle["resolution"]
    commitments = bundle["commitments"]
    identities = bundle["identities"]
    core = {
        "schema": CAPSULE_SCHEMA,
        "project": PROJECT,
        "version": VERSION,
        "context_id": bundle["context_id"],
        "ruleset_id": bundle["ruleset_id"],
        "profile_id": bundle["profile_id"],
        "text_profile_id": bundle["text_profile_id"],
        "boundary_state": bundle["boundary_state"],
        "state": resolution["state"],
        "reason_code": resolution["reason_code"],
        "candidate_id": resolution["candidate_id"],
        "authority": "NONE",
        "counts": bundle["counts"],
        "structural_commitments": {
            "normalized_input_commitment": commitments["normalized_input_commitment"],
            "observation_set_commitment": commitments["observation_set_commitment"],
            "evidence_set_commitment": commitments["evidence_set_commitment"],
            "constraint_set_commitment": commitments["constraint_set_commitment"],
            "witness_commitment": commitments["witness_commitment"],
        },
        "decision_resolution_id": identities["decision_resolution_id"],
        "private_bundle_id": identities["private_bundle_id"],
        "public_receipt_id": identities["public_receipt_id"],
    }
    return {**core, "capsule_id": tagged_hash("ORL-AI-DECISION-CAPSULE-ID-5", core)}


def verify_capsule(capsule: Any) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(capsule, dict):
        return False, ["CAPSULE_NOT_OBJECT"]
    expected_fields = {
        "schema", "project", "version", "context_id", "ruleset_id", "profile_id", "text_profile_id", "boundary_state", "state", "reason_code", "candidate_id", "authority", "counts", "structural_commitments", "decision_resolution_id", "private_bundle_id", "public_receipt_id", "capsule_id"
    }
    if set(capsule) != expected_fields:
        errors.append("CAPSULE_FIELD_SET_MISMATCH")
    if capsule.get("schema") != CAPSULE_SCHEMA:
        errors.append("CAPSULE_SCHEMA_MISMATCH")
    if capsule.get("project") != PROJECT or capsule.get("version") != VERSION:
        errors.append("CAPSULE_PROJECT_VERSION_MISMATCH")
    if capsule.get("authority") != "NONE":
        errors.append("CAPSULE_AUTHORITY_MISMATCH")
    core = {key: value for key, value in capsule.items() if key != "capsule_id"}
    expected_id = tagged_hash("ORL-AI-DECISION-CAPSULE-ID-5", core)
    if capsule.get("capsule_id") != expected_id:
        errors.append("CAPSULE_ID_MISMATCH")
    return not errors, errors


def verify_capsule_against_bundle(capsule: Dict[str, Any], bundle: Dict[str, Any]) -> Tuple[bool, List[str]]:
    valid, errors = verify_capsule(capsule)
    expected = build_capsule(bundle)
    if canonical_bytes(capsule) != canonical_bytes(expected):
        errors.append("CAPSULE_BUNDLE_RECONSTRUCTION_MISMATCH")
    return valid and len(errors) == 0, sorted(set(errors))


def compare_capsules(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    left_valid, left_errors = verify_capsule(left)
    right_valid, right_errors = verify_capsule(right)
    if not left_valid or not right_valid:
        relation = "UNSUPPORTED"
    elif left["capsule_id"] == right["capsule_id"]:
        relation = "IDENTICAL"
    elif left["context_id"] != right["context_id"]:
        relation = "INCOMPARABLE_CONTEXT"
    elif left["decision_resolution_id"] == right["decision_resolution_id"]:
        relation = "EQUIVALENT_RESOLUTION"
    elif left["state"] == right["state"] and left["candidate_id"] == right["candidate_id"] and left["reason_code"] == right["reason_code"]:
        relation = "COMPATIBLE_OUTCOME"
    elif left["state"] != right["state"]:
        relation = "DIVERGES_STATE"
    elif left["candidate_id"] != right["candidate_id"]:
        relation = "DIVERGES_CANDIDATE"
    else:
        relation = "DIVERGES_STRUCTURE"
    core = {
        "schema": COMPARISON_SCHEMA,
        "project": PROJECT,
        "version": VERSION,
        "left_capsule_id": left.get("capsule_id"),
        "right_capsule_id": right.get("capsule_id"),
        "left_valid": left_valid,
        "right_valid": right_valid,
        "left_errors": left_errors,
        "right_errors": right_errors,
        "relation": relation,
    }
    return {**core, "comparison_id": tagged_hash("ORL-AI-CAPSULE-COMPARISON-ID-5", core)}


def self_test(root: Path) -> int:
    resolved_bundle = load(root / "examples" / "ORL_AI_resolved-consensus_Bundle_v5_0_0.json")
    incomplete_bundle = load(root / "examples" / "ORL_AI_incomplete-open-boundary_Bundle_v5_0_0.json")
    resolved = build_capsule(resolved_bundle)
    incomplete = build_capsule(incomplete_bundle)
    checks = []
    checks.append(("capsule verifies", verify_capsule(resolved)[0]))
    checks.append(("capsule reconstructs", verify_capsule_against_bundle(resolved, resolved_bundle)[0]))
    checks.append(("identical relation", compare_capsules(resolved, resolved)["relation"] == "IDENTICAL"))
    checks.append(("different contexts are incomparable", compare_capsules(resolved, incomplete)["relation"] == "INCOMPARABLE_CONTEXT"))
    same_context = dict(incomplete)
    same_context["context_id"] = resolved["context_id"]
    same_context["capsule_id"] = tagged_hash("ORL-AI-DECISION-CAPSULE-ID-5", {key: value for key, value in same_context.items() if key != "capsule_id"})
    checks.append(("same-context state divergence", compare_capsules(resolved, same_context)["relation"] == "DIVERGES_STATE"))
    tampered = dict(resolved)
    tampered["candidate_id"] = "QUEUE_BETA"
    checks.append(("tamper detected", not verify_capsule(tampered)[0]))
    passed = sum(1 for _, status in checks if status)
    for name, status in checks:
        print(("PASS" if status else "FAIL") + "  " + name)
    print("TOTAL " + str(passed) + "/" + str(len(checks)) + " PASS")
    return 0 if passed == len(checks) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and compare ORL-AI decision-admission capsules")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify-capsule", type=Path)
    parser.add_argument("--verify-against-bundle", type=Path)
    parser.add_argument("--compare", nargs=2, type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if args.self_test:
        return self_test(root)
    if args.bundle:
        capsule = build_capsule(load(args.bundle))
        if args.output:
            write(args.output, capsule)
        else:
            print(canonical_bytes(capsule).decode("utf-8"), end="")
        return 0
    if args.verify_capsule:
        capsule = load(args.verify_capsule)
        if args.verify_against_bundle:
            passed, errors = verify_capsule_against_bundle(capsule, load(args.verify_against_bundle))
        else:
            passed, errors = verify_capsule(capsule)
        print("CAPSULE VERIFY: " + ("PASS" if passed else "FAIL"))
        for error in errors:
            print(error)
        return 0 if passed else 1
    if args.compare:
        comparison = compare_capsules(load(args.compare[0]), load(args.compare[1]))
        if args.output:
            write(args.output, comparison)
        else:
            print(canonical_bytes(comparison).decode("utf-8"), end="")
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
