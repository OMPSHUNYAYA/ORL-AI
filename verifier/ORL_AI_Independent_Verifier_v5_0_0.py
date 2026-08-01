#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

PROJECT = "ORL-AI"
VERSION = "5.0.0"
INPUT_SCHEMA = "ORL-AI-INPUT-5.0.0"
BUNDLE_SCHEMA = "ORL-AI-BUNDLE-5.0.0"
RECEIPT_SCHEMA = "ORL-AI-PUBLIC-RECEIPT-5.0.0"
RULESET_ID = "ORL-AI-ADMISSION-RULESET-5-D01"
PROFILE_ID = "ORL-AI-STRICT-3CLASS-5-D01"
TEXT_PROFILE_ID = "ORL-AI-UNICODE-SCALAR-EXACT-5-D01"
ARTIFACT_PROFILE_ID = "ORL-AI-CANONICAL-SHA256-5-D01"
EXACT_MAX = 9007199254740991
MAX_CANDIDATES = 32
MAX_SOURCES = 128
MAX_EVIDENCE = 256
MAX_OBSERVATIONS = 256
MAX_CONSTRAINTS = 128
MAX_STRING_LENGTH = 512
MAX_ARRAY_LENGTH = 512
MAX_DEPTH = 16
REQUIRED_CLASSES = {"MODEL", "MODEL_REVIEW", "RULE_CHECK"}
VALID_CLASSES = REQUIRED_CLASSES | {"HUMAN_REVIEW", "TOOL_CHECK"}
IDENTIFIER_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._:-")
ROOT = Path(__file__).resolve().parents[1]


class StrictRefusal(ValueError):
    pass


def _pairs(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise StrictRefusal("DUPLICATE_JSON_KEY:" + key)
        value[key] = item
    return value


def _integer(token: str) -> int:
    result = int(token)
    if result < -EXACT_MAX or result > EXACT_MAX:
        raise StrictRefusal("INTEGER_OUTSIDE_EXACT_RANGE")
    return result


def _reject_surrogates(value: Any) -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise StrictRefusal("MALFORMED_JSON:unpaired surrogate")
        return
    if isinstance(value, list):
        for item in value:
            _reject_surrogates(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_surrogates(key)
            _reject_surrogates(item)


def load_strict(path: Path) -> Any:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise StrictRefusal("UTF8_BOM")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise StrictRefusal("INVALID_UTF8") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=_integer,
            parse_float=lambda token: (_ for _ in ()).throw(StrictRefusal("FLOATING_JSON_NUMBER")),
            parse_constant=lambda token: (_ for _ in ()).throw(StrictRefusal("NONFINITE_JSON_NUMBER:" + token)),
        )
        _reject_surrogates(value)
        return value
    except StrictRefusal:
        raise
    except json.JSONDecodeError as exc:
        raise StrictRefusal("MALFORMED_JSON:" + str(exc)) from exc


def canonical_bytes(value: Any) -> bytes:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"
    escaped = "".join("\\u" + format(ord(character), "04x") if 0xD800 <= ord(character) <= 0xDFFF else character for character in text)
    return escaped.encode("utf-8")


def identity(tag: str, value: Any) -> str:
    return "sha256:" + hashlib.sha256(tag.encode("utf-8") + b"\x00" + canonical_bytes(value)).hexdigest()


def text_issue(value: str) -> Optional[str]:
    if len(value) > MAX_STRING_LENGTH:
        return "STRING_TOO_LONG"
    for character in value:
        code = ord(character)
        if 0xD800 <= code <= 0xDFFF:
            return "SURROGATE_CODE_POINT"
        if code == 0x0D:
            return "CARRIAGE_RETURN"
        if code == 0xFEFF:
            return "ZERO_WIDTH_NO_BREAK_SPACE"
        if code < 0x20 and code not in (0x09, 0x0A):
            return "CONTROL_CODE_POINT"
        if 0x7F <= code <= 0x9F:
            return "CONTROL_CODE_POINT"
    return None


def walk_shape(value: Any, path: str, depth: int, errors: List[str]) -> None:
    if depth > MAX_DEPTH:
        errors.append("RESOURCE_DEPTH_EXCEEDED:" + path)
        return
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < -EXACT_MAX or value > EXACT_MAX:
            errors.append("INTEGER_OUTSIDE_EXACT_RANGE:" + path)
        return
    if isinstance(value, float):
        errors.append("FLOATING_NUMBER:" + path)
        return
    if isinstance(value, str):
        issue = text_issue(value)
        if issue:
            errors.append(issue + ":" + path)
        return
    if isinstance(value, list):
        if len(value) > MAX_ARRAY_LENGTH:
            errors.append("RESOURCE_ARRAY_EXCEEDED:" + path)
        for index, item in enumerate(value):
            walk_shape(item, path + "[" + str(index) + "]", depth + 1, errors)
        return
    if isinstance(value, dict):
        if len(value) > MAX_ARRAY_LENGTH:
            errors.append("RESOURCE_OBJECT_EXCEEDED:" + path)
        for key, item in value.items():
            if not isinstance(key, str):
                errors.append("NONSTRING_OBJECT_KEY:" + path)
                continue
            issue = text_issue(key)
            if issue:
                errors.append(issue + ":" + path + ".<key>")
            walk_shape(item, path + "." + key, depth + 1, errors)
        return
    errors.append("UNSUPPORTED_RUNTIME_TYPE:" + path)


def valid_id(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 128 and value[0] in IDENTIFIER_CHARS and value[0].isalnum() and all(ch in IDENTIFIER_CHARS for ch in value)


def exact_fields(value: Any, required: List[str], path: str, errors: List[str]) -> bool:
    if not isinstance(value, dict):
        errors.append("EXPECTED_OBJECT:" + path)
        return False
    wanted = set(required)
    actual = set(value)
    errors.extend("MISSING_FIELD:" + path + "." + key for key in sorted(wanted - actual))
    errors.extend("UNSUPPORTED_FIELD:" + path + "." + key for key in sorted(actual - wanted))
    return True


def normalize(document: Any) -> Tuple[Any, List[str]]:
    errors: List[str] = []
    walk_shape(document, "$", 0, errors)
    if not exact_fields(document, ["schema", "context", "sources", "evidence", "observations", "constraints", "boundary"], "$", errors):
        return None, sorted(set(errors))
    if document.get("schema") != INPUT_SCHEMA:
        errors.append("UNSUPPORTED_SCHEMA:$.schema")

    context = document.get("context")
    context_fields = ["context_id", "question_id", "domain", "candidate_ids", "ruleset_id", "profile_id", "text_profile_id", "evidence_mode", "authority_mode", "boundary_state"]
    if not exact_fields(context, context_fields, "$.context", errors):
        return None, sorted(set(errors))
    for field in ["context_id", "question_id", "domain"]:
        if not valid_id(context.get(field)):
            errors.append("INVALID_IDENTIFIER:$.context." + field)
    candidates = context.get("candidate_ids")
    if not isinstance(candidates, list):
        errors.append("EXPECTED_ARRAY:$.context.candidate_ids")
        candidates = []
    elif not candidates:
        errors.append("EMPTY_CANDIDATE_SET:$.context.candidate_ids")
    elif len(candidates) > MAX_CANDIDATES:
        errors.append("RESOURCE_CANDIDATE_LIMIT:$.context.candidate_ids")
    elif len(candidates) != len(set(candidates)):
        errors.append("DUPLICATE_ARRAY_VALUE:$.context.candidate_ids")
    for value in candidates:
        if not valid_id(value):
            errors.append("INVALID_IDENTIFIER:$.context.candidate_ids")
    if context.get("ruleset_id") != RULESET_ID:
        errors.append("UNSUPPORTED_RULESET:$.context.ruleset_id")
    if context.get("profile_id") != PROFILE_ID:
        errors.append("UNSUPPORTED_PROFILE:$.context.profile_id")
    if context.get("text_profile_id") != TEXT_PROFILE_ID:
        errors.append("UNSUPPORTED_TEXT_PROFILE:$.context.text_profile_id")
    if context.get("evidence_mode") != "DECLARED":
        errors.append("UNSUPPORTED_EVIDENCE_MODE:$.context.evidence_mode")
    if context.get("authority_mode") != "NONE":
        errors.append("CALLER_DERIVED_AUTHORITY_FORBIDDEN:$.context.authority_mode")
    if context.get("boundary_state") not in {"OPEN", "SEALED"}:
        errors.append("UNSUPPORTED_BOUNDARY_STATE:$.context.boundary_state")

    source_list = document.get("sources")
    if not isinstance(source_list, list):
        errors.append("EXPECTED_ARRAY:$.sources")
        source_list = []
    if len(source_list) > MAX_SOURCES:
        errors.append("RESOURCE_SOURCE_LIMIT:$.sources")
    sources: Dict[str, Dict[str, str]] = {}
    for index, value in enumerate(source_list):
        path = "$.sources[" + str(index) + "]"
        if not exact_fields(value, ["source_id", "source_family", "source_class"], path, errors):
            continue
        source_id = value.get("source_id")
        if not valid_id(source_id):
            errors.append("INVALID_IDENTIFIER:" + path + ".source_id")
            continue
        if source_id in sources:
            errors.append("DUPLICATE_SOURCE_ID:" + path + ".source_id")
        if not valid_id(value.get("source_family")):
            errors.append("INVALID_IDENTIFIER:" + path + ".source_family")
        if value.get("source_class") not in VALID_CLASSES:
            errors.append("UNSUPPORTED_SOURCE_CLASS:" + path + ".source_class")
        sources[source_id] = dict(value)

    evidence_list = document.get("evidence")
    if not isinstance(evidence_list, list):
        errors.append("EXPECTED_ARRAY:$.evidence")
        evidence_list = []
    if len(evidence_list) > MAX_EVIDENCE:
        errors.append("RESOURCE_EVIDENCE_LIMIT:$.evidence")
    evidence: Dict[str, Dict[str, str]] = {}
    for index, value in enumerate(evidence_list):
        path = "$.evidence[" + str(index) + "]"
        if not exact_fields(value, ["evidence_id", "kind", "digest"], path, errors):
            continue
        evidence_id = value.get("evidence_id")
        if not valid_id(evidence_id):
            errors.append("INVALID_IDENTIFIER:" + path + ".evidence_id")
            continue
        if evidence_id in evidence:
            errors.append("DUPLICATE_EVIDENCE_ID:" + path + ".evidence_id")
        if not valid_id(value.get("kind")):
            errors.append("INVALID_IDENTIFIER:" + path + ".kind")
        digest = value.get("digest")
        if not isinstance(digest, str) or len(digest) != 71 or not digest.startswith("sha256:") or any(ch not in "0123456789abcdef" for ch in digest[7:]):
            errors.append("INVALID_EVIDENCE_DIGEST:" + path + ".digest")
        evidence[evidence_id] = dict(value)

    observation_list = document.get("observations")
    if not isinstance(observation_list, list):
        errors.append("EXPECTED_ARRAY:$.observations")
        observation_list = []
    if len(observation_list) > MAX_OBSERVATIONS:
        errors.append("RESOURCE_OBSERVATION_LIMIT:$.observations")
    observations: Dict[str, Dict[str, Any]] = {}
    for index, value in enumerate(observation_list):
        path = "$.observations[" + str(index) + "]"
        if not exact_fields(value, ["observation_id", "source_id", "candidate_id", "stance", "evidence_ids"], path, errors):
            continue
        observation_id = value.get("observation_id")
        if not valid_id(observation_id):
            errors.append("INVALID_IDENTIFIER:" + path + ".observation_id")
            continue
        if observation_id in observations:
            errors.append("DUPLICATE_OBSERVATION_ID:" + path + ".observation_id")
        if value.get("source_id") not in sources:
            errors.append("UNKNOWN_SOURCE_REFERENCE:" + path + ".source_id")
        if value.get("candidate_id") not in set(candidates):
            errors.append("UNKNOWN_CANDIDATE_REFERENCE:" + path + ".candidate_id")
        if value.get("stance") not in {"SUPPORT", "OPPOSE", "ABSTAIN"}:
            errors.append("UNSUPPORTED_STANCE:" + path + ".stance")
        refs = value.get("evidence_ids")
        if not isinstance(refs, list):
            errors.append("EXPECTED_ARRAY:" + path + ".evidence_ids")
            refs = []
        if len(refs) != len(set(refs)):
            errors.append("DUPLICATE_ARRAY_VALUE:" + path + ".evidence_ids")
        if any(ref not in evidence for ref in refs):
            errors.append("UNKNOWN_EVIDENCE_REFERENCE:" + path + ".evidence_ids")
        observations[observation_id] = {
            "observation_id": observation_id,
            "source_id": value.get("source_id"),
            "candidate_id": value.get("candidate_id"),
            "stance": value.get("stance"),
            "evidence_ids": sorted(refs),
        }

    constraint_list = document.get("constraints")
    if not isinstance(constraint_list, list):
        errors.append("EXPECTED_ARRAY:$.constraints")
        constraint_list = []
    if len(constraint_list) > MAX_CONSTRAINTS:
        errors.append("RESOURCE_CONSTRAINT_LIMIT:$.constraints")
    constraints: Dict[str, Dict[str, Any]] = {}
    for index, value in enumerate(constraint_list):
        path = "$.constraints[" + str(index) + "]"
        if not exact_fields(value, ["constraint_id", "kind", "candidate_id", "active"], path, errors):
            continue
        constraint_id = value.get("constraint_id")
        if not valid_id(constraint_id):
            errors.append("INVALID_IDENTIFIER:" + path + ".constraint_id")
            continue
        if constraint_id in constraints:
            errors.append("DUPLICATE_CONSTRAINT_ID:" + path + ".constraint_id")
        if value.get("kind") != "FORBID_CANDIDATE":
            errors.append("UNSUPPORTED_CONSTRAINT_KIND:" + path + ".kind")
        if value.get("candidate_id") != "*" and value.get("candidate_id") not in set(candidates):
            errors.append("UNKNOWN_CONSTRAINT_CANDIDATE:" + path + ".candidate_id")
        if not isinstance(value.get("active"), bool):
            errors.append("EXPECTED_BOOLEAN:" + path + ".active")
        constraints[constraint_id] = dict(value)

    boundary = document.get("boundary")
    if not exact_fields(boundary, ["expected_observation_ids", "expected_evidence_ids"], "$.boundary", errors):
        boundary = {"expected_observation_ids": [], "expected_evidence_ids": []}
    expected_observations = boundary.get("expected_observation_ids")
    expected_evidence = boundary.get("expected_evidence_ids")
    if not isinstance(expected_observations, list):
        errors.append("EXPECTED_ARRAY:$.boundary.expected_observation_ids")
        expected_observations = []
    if not isinstance(expected_evidence, list):
        errors.append("EXPECTED_ARRAY:$.boundary.expected_evidence_ids")
        expected_evidence = []
    if len(expected_observations) != len(set(expected_observations)):
        errors.append("DUPLICATE_ARRAY_VALUE:$.boundary.expected_observation_ids")
    if len(expected_evidence) != len(set(expected_evidence)):
        errors.append("DUPLICATE_ARRAY_VALUE:$.boundary.expected_evidence_ids")
    extras = sorted(set(observations) - set(expected_observations))
    if extras:
        errors.append("UNDECLARED_OBSERVATION:" + ",".join(extras))
    extra_evidence = sorted(set(evidence) - set(expected_evidence))
    if extra_evidence:
        errors.append("UNDECLARED_EVIDENCE:" + ",".join(extra_evidence))

    if errors:
        return None, sorted(set(errors))

    return {
        "schema": INPUT_SCHEMA,
        "context": {
            "context_id": context["context_id"],
            "question_id": context["question_id"],
            "domain": context["domain"],
            "candidate_ids": sorted(candidates),
            "ruleset_id": context["ruleset_id"],
            "profile_id": context["profile_id"],
            "text_profile_id": context["text_profile_id"],
            "evidence_mode": context["evidence_mode"],
            "authority_mode": context["authority_mode"],
            "boundary_state": context["boundary_state"],
        },
        "sources": [sources[key] for key in sorted(sources)],
        "evidence": [evidence[key] for key in sorted(evidence)],
        "observations": [observations[key] for key in sorted(observations)],
        "constraints": [constraints[key] for key in sorted(constraints)],
        "boundary": {
            "expected_observation_ids": sorted(expected_observations),
            "expected_evidence_ids": sorted(expected_evidence),
        },
    }, []


def metrics(normalized: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    source_by_id = {item["source_id"]: item for item in normalized["sources"]}
    table: Dict[str, Dict[str, Any]] = {}
    for candidate in normalized["context"]["candidate_ids"]:
        related = [item for item in normalized["observations"] if item["candidate_id"] == candidate]
        support = [item for item in related if item["stance"] == "SUPPORT"]
        oppose = [item for item in related if item["stance"] == "OPPOSE"]
        abstain = [item for item in related if item["stance"] == "ABSTAIN"]
        source_ids = {item["source_id"] for item in support}
        families = {source_by_id[source_id]["source_family"] for source_id in source_ids}
        classes = {source_by_id[source_id]["source_class"] for source_id in source_ids}
        missing_classes = sorted(REQUIRED_CLASSES - classes)
        evidence_complete = all(len(item["evidence_ids"]) > 0 for item in support)
        table[candidate] = {
            "support_observation_ids": sorted(item["observation_id"] for item in support),
            "opposition_observation_ids": sorted(item["observation_id"] for item in oppose),
            "abstention_observation_ids": sorted(item["observation_id"] for item in abstain),
            "support_source_count": len(source_ids),
            "support_family_count": len(families),
            "support_classes": sorted(classes),
            "missing_required_classes": missing_classes,
            "missing_support_sources": max(0, 3 - len(source_ids)),
            "missing_source_families": max(0, 3 - len(families)),
            "evidence_complete": evidence_complete,
            "eligible": bool(support) and len(source_ids) >= 3 and len(families) >= 3 and not missing_classes and evidence_complete,
        }
    return table


def witness(normalized: Dict[str, Any], candidate: str) -> List[str]:
    source_by_id = {item["source_id"]: item for item in normalized["sources"]}
    first_by_source: Dict[str, Dict[str, Any]] = {}
    for item in sorted(normalized["observations"], key=lambda value: value["observation_id"]):
        if item["candidate_id"] == candidate and item["stance"] == "SUPPORT" and item["evidence_ids"]:
            first_by_source.setdefault(item["source_id"], item)

    class_order = ("MODEL", "MODEL_REVIEW", "RULE_CHECK")
    class_bit = {name: 1 << index for index, name in enumerate(class_order)}
    complete_mask = (1 << len(class_order)) - 1
    entries = sorted(
        (
            observation["observation_id"],
            source_by_id[source_id]["source_family"],
            class_bit.get(source_by_id[source_id]["source_class"], 0),
        )
        for source_id, observation in first_by_source.items()
    )

    frontier: Dict[Tuple[int, Any, int], Tuple[str, ...]] = {(0, tuple(), 0): tuple()}
    for observation_id, family, bit in entries:
        expanded = dict(frontier)
        for (mask, family_state, count_state), chosen in frontier.items():
            if family_state is None:
                next_family_state = None
            else:
                distinct = set(family_state)
                distinct.add(family)
                next_family_state = None if len(distinct) >= 3 else tuple(sorted(distinct))
            proposal = chosen + (observation_id,)
            state = (mask | bit, next_family_state, min(3, count_state + 1))
            incumbent = expanded.get(state)
            if incumbent is None or (len(proposal), proposal) < (len(incumbent), incumbent):
                expanded[state] = proposal
        frontier = expanded

    selected = frontier.get((complete_mask, None, 3))
    return list(selected) if selected is not None else []


def decision(normalized: Dict[str, Any]) -> Dict[str, Any]:
    table = metrics(normalized)
    supported = sorted(candidate for candidate, item in table.items() if item["support_observation_ids"])
    eligible = sorted(candidate for candidate, item in table.items() if item["eligible"])

    denial_blockers = []
    for constraint in normalized["constraints"]:
        if not constraint["active"]:
            continue
        affected = supported if constraint["candidate_id"] == "*" else ([constraint["candidate_id"]] if constraint["candidate_id"] in supported else [])
        if affected:
            denial_blockers.append("ACTIVE_PROHIBITION:" + constraint["constraint_id"] + ":" + ",".join(sorted(affected)))
    if denial_blockers:
        return result("DENIED", "ACTIVE_PROHIBITION", None, eligible, supported, [], sorted(denial_blockers), [], table)

    support_by_source: Dict[str, set] = {}
    oppose_by_source: Dict[str, set] = {}
    for item in normalized["observations"]:
        if item["stance"] == "SUPPORT":
            support_by_source.setdefault(item["source_id"], set()).add(item["candidate_id"])
        elif item["stance"] == "OPPOSE":
            oppose_by_source.setdefault(item["source_id"], set()).add(item["candidate_id"])
    blockers = []
    blockers.extend("SOURCE_MULTI_CANDIDATE_SUPPORT:" + source for source in sorted(source for source, candidates in support_by_source.items() if len(candidates) > 1))
    blockers.extend("SOURCE_SUPPORT_OPPOSE_CONFLICT:" + source for source in sorted(set(support_by_source) & set(oppose_by_source)) if support_by_source[source] & oppose_by_source[source])
    if blockers:
        return result("ABSTAIN", "SOURCE_CONFLICT", None, eligible, supported, [], sorted(set(blockers)), [], table)

    if len(eligible) > 1:
        return result("ABSTAIN", "MULTIPLE_ELIGIBLE_CANDIDATES", None, eligible, supported, [], ["MULTIPLE_ELIGIBLE_CANDIDATES:" + ",".join(eligible)], [], table)

    if len(eligible) == 1:
        winner = eligible[0]
        blockers = []
        if table[winner]["opposition_observation_ids"]:
            blockers.append("OPPOSITION_PRESENT:" + ",".join(table[winner]["opposition_observation_ids"]))
        minorities = sorted(candidate for candidate in supported if candidate != winner)
        if minorities:
            blockers.append("MINORITY_SUPPORT_PRESENT:" + ",".join(minorities))
        if blockers:
            return result("ABSTAIN", "BLOCKING_DISAGREEMENT", None, eligible, supported, [], sorted(blockers), [], table)

    if not eligible and len(supported) > 1:
        return result("ABSTAIN", "COMPETING_PARTIAL_SUPPORT", None, [], supported, [], ["COMPETING_PARTIAL_SUPPORT:" + ",".join(supported)], [], table)

    present_observations = {item["observation_id"] for item in normalized["observations"]}
    present_evidence = {item["evidence_id"] for item in normalized["evidence"]}
    repairs = []
    if normalized["context"]["boundary_state"] != "SEALED":
        repairs.append("SEAL_DECLARED_BOUNDARY")
    missing_observations = sorted(set(normalized["boundary"]["expected_observation_ids"]) - present_observations)
    missing_evidence = sorted(set(normalized["boundary"]["expected_evidence_ids"]) - present_evidence)
    if missing_observations:
        repairs.append("SUPPLY_OBSERVATIONS:" + ",".join(missing_observations))
    if missing_evidence:
        repairs.append("SUPPLY_EVIDENCE:" + ",".join(missing_evidence))
    if repairs:
        return result("INCOMPLETE", "BOUNDARY_INCOMPLETE", None, eligible, supported, [], [], sorted(repairs), table)

    if len(eligible) == 1:
        winner = eligible[0]
        return result("RESOLVED", "UNIQUE_ADMISSIBLE_CANDIDATE", winner, [winner], supported, witness(normalized, winner), [], [], table)

    repairs = []
    for candidate in supported or normalized["context"]["candidate_ids"]:
        item = table[candidate]
        if item["missing_support_sources"]:
            repairs.append("ADD_SUPPORT_SOURCES:" + candidate + ":" + str(item["missing_support_sources"]))
        if item["missing_source_families"]:
            repairs.append("ADD_SOURCE_FAMILIES:" + candidate + ":" + str(item["missing_source_families"]))
        if item["missing_required_classes"]:
            repairs.append("ADD_REQUIRED_CLASSES:" + candidate + ":" + ",".join(item["missing_required_classes"]))
        if not item["evidence_complete"]:
            repairs.append("ATTACH_EVIDENCE_TO_SUPPORT:" + candidate)
    return result("INCOMPLETE", "ADMISSION_REQUIREMENTS_UNMET", None, [], supported, [], [], sorted(set(repairs)), table)


def result(state: str, reason: str, candidate: Any, eligible: List[str], supported: List[str], witness_ids: List[str], blockers: List[str], repairs: List[str], table: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "state": state,
        "reason_code": reason,
        "candidate_id": candidate,
        "eligible_candidate_ids": eligible,
        "supported_candidate_ids": supported,
        "witness_observation_ids": witness_ids,
        "blockers": blockers,
        "repair_requirements": repairs,
        "candidate_metrics": table,
        "authority": "NONE",
    }


def reconstruct(document: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    submitted = identity("ORL-AI-SUBMITTED-INPUT-5", document)
    normalized, errors = normalize(document)
    if errors:
        resolution = result("REFUSED", "STRUCTURAL_INTAKE_REFUSAL", None, [], [], [], errors, [], {})
        core = {
            "schema": BUNDLE_SCHEMA,
            "project": PROJECT,
            "version": VERSION,
            "context_id": None,
            "ruleset_id": RULESET_ID,
            "profile_id": PROFILE_ID,
            "text_profile_id": TEXT_PROFILE_ID,
            "boundary_state": None,
            "normalized_input": None,
            "resolution": resolution,
            "counts": {"candidates": 0, "sources": 0, "evidence": 0, "observations": 0, "constraints": 0},
            "commitments": {
                "submitted_input_commitment": submitted,
                "normalized_input_commitment": None,
                "observation_set_commitment": None,
                "evidence_set_commitment": None,
                "constraint_set_commitment": None,
                "witness_commitment": identity("ORL-AI-WITNESS-SET-5", []),
            },
        }
    else:
        resolution = decision(normalized)
        core = {
            "schema": BUNDLE_SCHEMA,
            "project": PROJECT,
            "version": VERSION,
            "context_id": normalized["context"]["context_id"],
            "ruleset_id": normalized["context"]["ruleset_id"],
            "profile_id": normalized["context"]["profile_id"],
            "text_profile_id": normalized["context"]["text_profile_id"],
            "boundary_state": normalized["context"]["boundary_state"],
            "normalized_input": normalized,
            "resolution": resolution,
            "counts": {
                "candidates": len(normalized["context"]["candidate_ids"]),
                "sources": len(normalized["sources"]),
                "evidence": len(normalized["evidence"]),
                "observations": len(normalized["observations"]),
                "constraints": len(normalized["constraints"]),
            },
            "commitments": {
                "submitted_input_commitment": submitted,
                "normalized_input_commitment": identity("ORL-AI-NORMALIZED-INPUT-5", normalized),
                "observation_set_commitment": identity("ORL-AI-OBSERVATION-SET-5", normalized["observations"]),
                "evidence_set_commitment": identity("ORL-AI-EVIDENCE-SET-5", normalized["evidence"]),
                "constraint_set_commitment": identity("ORL-AI-CONSTRAINT-SET-5", normalized["constraints"]),
                "witness_commitment": identity("ORL-AI-WITNESS-SET-5", resolution["witness_observation_ids"]),
            },
        }
    resolution_id = identity(
        "ORL-AI-DECISION-RESOLUTION-ID-5",
        {
            "context_id": core["context_id"],
            "ruleset_id": core["ruleset_id"],
            "profile_id": core["profile_id"],
            "text_profile_id": core["text_profile_id"],
            "boundary_state": core["boundary_state"],
            "resolution": core["resolution"],
            "structural_commitments": {
                "normalized_input_commitment": core["commitments"]["normalized_input_commitment"],
                "observation_set_commitment": core["commitments"]["observation_set_commitment"],
                "evidence_set_commitment": core["commitments"]["evidence_set_commitment"],
                "constraint_set_commitment": core["commitments"]["constraint_set_commitment"],
                "witness_commitment": core["commitments"]["witness_commitment"],
            },
        },
    )
    artifact_profile = {
        "profile_id": ARTIFACT_PROFILE_ID,
        "identity_algorithm": "SHA-256",
        "canonicalization": "UTF-8 sorted-key compact JSON with LF terminator",
    }
    bundle_id = identity(
        "ORL-AI-PRIVATE-BUNDLE-ID-5",
        {**core, "decision_resolution_id": resolution_id, "artifact_profile": artifact_profile},
    )
    bundle = {
        **core,
        "artifact_profile": artifact_profile,
        "identities": {"decision_resolution_id": resolution_id, "private_bundle_id": bundle_id},
    }
    receipt_core = {
        "schema": RECEIPT_SCHEMA,
        "project": PROJECT,
        "version": VERSION,
        "context_id": bundle["context_id"],
        "ruleset_id": bundle["ruleset_id"],
        "profile_id": bundle["profile_id"],
        "text_profile_id": bundle["text_profile_id"],
        "state": bundle["resolution"]["state"],
        "reason_code": bundle["resolution"]["reason_code"],
        "candidate_id": bundle["resolution"]["candidate_id"],
        "authority": "NONE",
        "boundary_state": bundle["boundary_state"],
        "counts": bundle["counts"],
        "commitments": bundle["commitments"],
        "decision_resolution_id": resolution_id,
        "private_bundle_id": bundle_id,
    }
    receipt = {**receipt_core, "public_receipt_id": identity("ORL-AI-PUBLIC-RECEIPT-ID-5", receipt_core)}
    bundle["identities"]["public_receipt_id"] = receipt["public_receipt_id"]
    return bundle, receipt


def verify_corpus(manifest_path: Path, strict_canonical: bool) -> Tuple[bool, Dict[str, Any]]:
    manifest = load_strict(manifest_path)
    entries = manifest.get("entries", [])
    cases = []
    passed = True
    for entry in entries:
        input_path = ROOT / entry["input_path"]
        bundle_path = ROOT / entry["bundle_path"]
        receipt_path = ROOT / entry["receipt_path"]
        source = load_strict(input_path)
        expected_bundle = load_strict(bundle_path)
        expected_receipt = load_strict(receipt_path)
        actual_bundle, actual_receipt = reconstruct(source)
        bundle_equal = canonical_bytes(actual_bundle) == canonical_bytes(expected_bundle)
        receipt_equal = canonical_bytes(actual_receipt) == canonical_bytes(expected_receipt)
        canonical_ok = True
        if strict_canonical:
            canonical_ok = bundle_path.read_bytes() == canonical_bytes(expected_bundle) and receipt_path.read_bytes() == canonical_bytes(expected_receipt) and input_path.read_bytes() == canonical_bytes(source)
        state_ok = actual_bundle["resolution"]["state"] == entry["expected_state"]
        case_pass = bundle_equal and receipt_equal and canonical_ok and state_ok
        passed = passed and case_pass
        cases.append({"case_id": entry["case_id"], "bundle_equal": bundle_equal, "receipt_equal": receipt_equal, "canonical": canonical_ok, "state": actual_bundle["resolution"]["state"], "pass": case_pass})
    return passed, {"schema": "ORL-AI-INDEPENDENT-VERIFICATION-RECEIPT-5.0.0", "project": PROJECT, "version": VERSION, "cases": cases, "pass": passed}


def self_test() -> int:
    manifest = ROOT / "corpus" / "ORL_AI_Frozen_Corpus_Manifest_v5_0_0.json"
    passed, receipt = verify_corpus(manifest, True)
    for case in receipt["cases"]:
        print(("PASS" if case["pass"] else "FAIL") + "  " + case["case_id"])
    print("TOTAL " + str(sum(1 for case in receipt["cases"] if case["pass"])) + "/" + str(len(receipt["cases"])) + " PASS")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="ORL-AI independent reconstruction verifier")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verify-corpus", type=Path)
    parser.add_argument("--strict-canonical", action="store_true")
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.verify_corpus:
        passed, receipt = verify_corpus(args.verify_corpus, args.strict_canonical)
        if args.receipt_output:
            args.receipt_output.write_bytes(canonical_bytes(receipt))
        for case in receipt["cases"]:
            print(("PASS" if case["pass"] else "FAIL") + "  " + case["case_id"])
        print("INDEPENDENT CORPUS VERIFY: " + ("PASS" if passed else "FAIL"))
        return 0 if passed else 1
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
