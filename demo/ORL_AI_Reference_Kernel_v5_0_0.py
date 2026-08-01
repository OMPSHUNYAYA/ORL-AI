#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

PROJECT = "ORL-AI"
VERSION = "5.0.0"
INPUT_SCHEMA = "ORL-AI-INPUT-5.0.0"
BUNDLE_SCHEMA = "ORL-AI-BUNDLE-5.0.0"
RECEIPT_SCHEMA = "ORL-AI-PUBLIC-RECEIPT-5.0.0"
RULESET_ID = "ORL-AI-ADMISSION-RULESET-5-D01"
PROFILE_ID = "ORL-AI-STRICT-3CLASS-5-D01"
TEXT_PROFILE_ID = "ORL-AI-UNICODE-SCALAR-EXACT-5-D01"
ARTIFACT_PROFILE_ID = "ORL-AI-CANONICAL-SHA256-5-D01"
MAX_EXACT_INTEGER = 9007199254740991
MAX_CANDIDATES = 32
MAX_SOURCES = 128
MAX_EVIDENCE = 256
MAX_OBSERVATIONS = 256
MAX_CONSTRAINTS = 128
MAX_STRING_LENGTH = 512
MAX_ARRAY_LENGTH = 512
MAX_DEPTH = 16
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
SOURCE_CLASSES = {"MODEL", "MODEL_REVIEW", "RULE_CHECK", "HUMAN_REVIEW", "TOOL_CHECK"}
STANCES = {"SUPPORT", "OPPOSE", "ABSTAIN"}
BOUNDARY_STATES = {"OPEN", "SEALED"}
CONSTRAINT_KINDS = {"FORBID_CANDIDATE"}
PROFILE = {
    "minimum_support_sources": 3,
    "minimum_source_families": 3,
    "required_source_classes": ["MODEL", "MODEL_REVIEW", "RULE_CHECK"],
    "opposition_mode": "BLOCK",
    "minority_support_mode": "BLOCK",
    "require_evidence_per_support": True,
}


class ParserRefusal(ValueError):
    pass


def _reject_float(value: str) -> None:
    raise ParserRefusal("FLOATING_JSON_NUMBER")


def _parse_int(value: str) -> int:
    if len(value.lstrip("-")) > 16:
        raise ParserRefusal("INTEGER_OUTSIDE_EXACT_RANGE")
    parsed = int(value)
    if parsed < -MAX_EXACT_INTEGER or parsed > MAX_EXACT_INTEGER:
        raise ParserRefusal("INTEGER_OUTSIDE_EXACT_RANGE")
    return parsed


def _pairs_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ParserRefusal("DUPLICATE_JSON_KEY:" + key)
        result[key] = value
    return result


def _reject_surrogate_values(value: Any) -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            raise ParserRefusal("MALFORMED_JSON:unpaired surrogate")
        return
    if isinstance(value, list):
        for item in value:
            _reject_surrogate_values(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_surrogate_values(key)
            _reject_surrogate_values(item)


def strict_json_loads(text: str) -> Any:
    if text.startswith("\ufeff"):
        raise ParserRefusal("UTF8_BOM")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_object,
            parse_float=_reject_float,
            parse_int=_parse_int,
            parse_constant=lambda token: (_ for _ in ()).throw(ParserRefusal("NONFINITE_JSON_NUMBER:" + token)),
        )
        _reject_surrogate_values(value)
        return value
    except ParserRefusal:
        raise
    except json.JSONDecodeError as exc:
        raise ParserRefusal("MALFORMED_JSON:" + str(exc)) from exc


def strict_json_load(path: Path) -> Any:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ParserRefusal("FILE_READ_ERROR:" + str(exc)) from exc
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ParserRefusal("INVALID_UTF8") from exc
    return strict_json_loads(text)


def canonical_json_bytes(value: Any) -> bytes:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"
    escaped = "".join("\\u" + format(ord(character), "04x") if 0xD800 <= ord(character) <= 0xDFFF else character for character in text)
    return escaped.encode("utf-8")


def canonical_json_text(value: Any) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def tagged_hash(tag: str, value: Any) -> str:
    payload = tag.encode("utf-8") + b"\x00" + canonical_json_bytes(value)
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _text_error(value: str) -> Optional[str]:
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


def _walk_shape(value: Any, path: str, depth: int, errors: List[str]) -> None:
    if depth > MAX_DEPTH:
        errors.append("RESOURCE_DEPTH_EXCEEDED:" + path)
        return
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if value < -MAX_EXACT_INTEGER or value > MAX_EXACT_INTEGER:
            errors.append("INTEGER_OUTSIDE_EXACT_RANGE:" + path)
        return
    if isinstance(value, float):
        errors.append("FLOATING_NUMBER:" + path)
        return
    if isinstance(value, str):
        issue = _text_error(value)
        if issue:
            errors.append(issue + ":" + path)
        return
    if isinstance(value, list):
        if len(value) > MAX_ARRAY_LENGTH:
            errors.append("RESOURCE_ARRAY_EXCEEDED:" + path)
        for index, item in enumerate(value):
            _walk_shape(item, path + "[" + str(index) + "]", depth + 1, errors)
        return
    if isinstance(value, dict):
        if len(value) > MAX_ARRAY_LENGTH:
            errors.append("RESOURCE_OBJECT_EXCEEDED:" + path)
        for key, item in value.items():
            if not isinstance(key, str):
                errors.append("NONSTRING_OBJECT_KEY:" + path)
                continue
            issue = _text_error(key)
            if issue:
                errors.append(issue + ":" + path + ".<key>")
            _walk_shape(item, path + "." + key, depth + 1, errors)
        return
    errors.append("UNSUPPORTED_RUNTIME_TYPE:" + path)


def _expect_object(value: Any, path: str, required: Iterable[str], errors: List[str]) -> Optional[Dict[str, Any]]:
    if not isinstance(value, dict):
        errors.append("EXPECTED_OBJECT:" + path)
        return None
    required_set = set(required)
    actual = set(value)
    for key in sorted(required_set - actual):
        errors.append("MISSING_FIELD:" + path + "." + key)
    for key in sorted(actual - required_set):
        errors.append("UNSUPPORTED_FIELD:" + path + "." + key)
    return value


def _expect_array(value: Any, path: str, errors: List[str]) -> Optional[List[Any]]:
    if not isinstance(value, list):
        errors.append("EXPECTED_ARRAY:" + path)
        return None
    return value


def _expect_string(value: Any, path: str, errors: List[str]) -> Optional[str]:
    if not isinstance(value, str):
        errors.append("EXPECTED_STRING:" + path)
        return None
    return value


def _expect_boolean(value: Any, path: str, errors: List[str]) -> Optional[bool]:
    if not isinstance(value, bool):
        errors.append("EXPECTED_BOOLEAN:" + path)
        return None
    return value


def _validate_id(value: Any, path: str, errors: List[str]) -> Optional[str]:
    text = _expect_string(value, path, errors)
    if text is not None and not ID_PATTERN.fullmatch(text):
        errors.append("INVALID_IDENTIFIER:" + path)
    return text


def _unique_string_array(value: Any, path: str, errors: List[str], id_mode: bool = True) -> Optional[List[str]]:
    array = _expect_array(value, path, errors)
    if array is None:
        return None
    result: List[str] = []
    seen = set()
    for index, item in enumerate(array):
        item_path = path + "[" + str(index) + "]"
        text = _validate_id(item, item_path, errors) if id_mode else _expect_string(item, item_path, errors)
        if text is None:
            continue
        if text in seen:
            errors.append("DUPLICATE_ARRAY_VALUE:" + item_path)
        seen.add(text)
        result.append(text)
    return result


def validate_and_normalize(document: Any) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    _walk_shape(document, "$", 0, errors)
    root = _expect_object(document, "$", ["schema", "context", "sources", "evidence", "observations", "constraints", "boundary"], errors)
    if root is None:
        return None, sorted(set(errors))

    schema = _expect_string(root.get("schema"), "$.schema", errors)
    if schema is not None and schema != INPUT_SCHEMA:
        errors.append("UNSUPPORTED_SCHEMA:$.schema")

    context = _expect_object(
        root.get("context"),
        "$.context",
        ["context_id", "question_id", "domain", "candidate_ids", "ruleset_id", "profile_id", "text_profile_id", "evidence_mode", "authority_mode", "boundary_state"],
        errors,
    )
    context_id = question_id = domain = ruleset_id = profile_id = text_profile_id = evidence_mode = authority_mode = boundary_state = None
    candidate_ids: Optional[List[str]] = None
    if context is not None:
        context_id = _validate_id(context.get("context_id"), "$.context.context_id", errors)
        question_id = _validate_id(context.get("question_id"), "$.context.question_id", errors)
        domain = _validate_id(context.get("domain"), "$.context.domain", errors)
        candidate_ids = _unique_string_array(context.get("candidate_ids"), "$.context.candidate_ids", errors)
        ruleset_id = _expect_string(context.get("ruleset_id"), "$.context.ruleset_id", errors)
        profile_id = _expect_string(context.get("profile_id"), "$.context.profile_id", errors)
        text_profile_id = _expect_string(context.get("text_profile_id"), "$.context.text_profile_id", errors)
        evidence_mode = _expect_string(context.get("evidence_mode"), "$.context.evidence_mode", errors)
        authority_mode = _expect_string(context.get("authority_mode"), "$.context.authority_mode", errors)
        boundary_state = _expect_string(context.get("boundary_state"), "$.context.boundary_state", errors)
        if ruleset_id is not None and ruleset_id != RULESET_ID:
            errors.append("UNSUPPORTED_RULESET:$.context.ruleset_id")
        if profile_id is not None and profile_id != PROFILE_ID:
            errors.append("UNSUPPORTED_PROFILE:$.context.profile_id")
        if text_profile_id is not None and text_profile_id != TEXT_PROFILE_ID:
            errors.append("UNSUPPORTED_TEXT_PROFILE:$.context.text_profile_id")
        if evidence_mode is not None and evidence_mode != "DECLARED":
            errors.append("UNSUPPORTED_EVIDENCE_MODE:$.context.evidence_mode")
        if authority_mode is not None and authority_mode != "NONE":
            errors.append("CALLER_DERIVED_AUTHORITY_FORBIDDEN:$.context.authority_mode")
        if boundary_state is not None and boundary_state not in BOUNDARY_STATES:
            errors.append("UNSUPPORTED_BOUNDARY_STATE:$.context.boundary_state")
        if candidate_ids is not None:
            if not candidate_ids:
                errors.append("EMPTY_CANDIDATE_SET:$.context.candidate_ids")
            if len(candidate_ids) > MAX_CANDIDATES:
                errors.append("RESOURCE_CANDIDATE_LIMIT:$.context.candidate_ids")

    sources_array = _expect_array(root.get("sources"), "$.sources", errors)
    normalized_sources: List[Dict[str, str]] = []
    source_map: Dict[str, Dict[str, str]] = {}
    if sources_array is not None:
        if len(sources_array) > MAX_SOURCES:
            errors.append("RESOURCE_SOURCE_LIMIT:$.sources")
        for index, source_value in enumerate(sources_array):
            path = "$.sources[" + str(index) + "]"
            source = _expect_object(source_value, path, ["source_id", "source_family", "source_class"], errors)
            if source is None:
                continue
            source_id = _validate_id(source.get("source_id"), path + ".source_id", errors)
            source_family = _validate_id(source.get("source_family"), path + ".source_family", errors)
            source_class = _expect_string(source.get("source_class"), path + ".source_class", errors)
            if source_class is not None and source_class not in SOURCE_CLASSES:
                errors.append("UNSUPPORTED_SOURCE_CLASS:" + path + ".source_class")
            if source_id and source_family and source_class:
                if source_id in source_map:
                    errors.append("DUPLICATE_SOURCE_ID:" + path + ".source_id")
                item = {"source_id": source_id, "source_family": source_family, "source_class": source_class}
                source_map[source_id] = item
                normalized_sources.append(item)

    evidence_array = _expect_array(root.get("evidence"), "$.evidence", errors)
    normalized_evidence: List[Dict[str, str]] = []
    evidence_map: Dict[str, Dict[str, str]] = {}
    if evidence_array is not None:
        if len(evidence_array) > MAX_EVIDENCE:
            errors.append("RESOURCE_EVIDENCE_LIMIT:$.evidence")
        for index, evidence_value in enumerate(evidence_array):
            path = "$.evidence[" + str(index) + "]"
            evidence_item = _expect_object(evidence_value, path, ["evidence_id", "kind", "digest"], errors)
            if evidence_item is None:
                continue
            evidence_id = _validate_id(evidence_item.get("evidence_id"), path + ".evidence_id", errors)
            kind = _validate_id(evidence_item.get("kind"), path + ".kind", errors)
            digest = _expect_string(evidence_item.get("digest"), path + ".digest", errors)
            if digest is not None and not DIGEST_PATTERN.fullmatch(digest):
                errors.append("INVALID_EVIDENCE_DIGEST:" + path + ".digest")
            if evidence_id and kind and digest:
                if evidence_id in evidence_map:
                    errors.append("DUPLICATE_EVIDENCE_ID:" + path + ".evidence_id")
                item = {"evidence_id": evidence_id, "kind": kind, "digest": digest}
                evidence_map[evidence_id] = item
                normalized_evidence.append(item)

    observations_array = _expect_array(root.get("observations"), "$.observations", errors)
    normalized_observations: List[Dict[str, Any]] = []
    observation_map: Dict[str, Dict[str, Any]] = {}
    if observations_array is not None:
        if len(observations_array) > MAX_OBSERVATIONS:
            errors.append("RESOURCE_OBSERVATION_LIMIT:$.observations")
        for index, observation_value in enumerate(observations_array):
            path = "$.observations[" + str(index) + "]"
            observation = _expect_object(observation_value, path, ["observation_id", "source_id", "candidate_id", "stance", "evidence_ids"], errors)
            if observation is None:
                continue
            observation_id = _validate_id(observation.get("observation_id"), path + ".observation_id", errors)
            source_id = _validate_id(observation.get("source_id"), path + ".source_id", errors)
            candidate_id = _validate_id(observation.get("candidate_id"), path + ".candidate_id", errors)
            stance = _expect_string(observation.get("stance"), path + ".stance", errors)
            evidence_ids = _unique_string_array(observation.get("evidence_ids"), path + ".evidence_ids", errors)
            if stance is not None and stance not in STANCES:
                errors.append("UNSUPPORTED_STANCE:" + path + ".stance")
            if source_id is not None and source_id not in source_map:
                errors.append("UNKNOWN_SOURCE_REFERENCE:" + path + ".source_id")
            if candidate_ids is not None and candidate_id is not None and candidate_id not in set(candidate_ids):
                errors.append("UNKNOWN_CANDIDATE_REFERENCE:" + path + ".candidate_id")
            if evidence_ids is not None:
                for evidence_id in evidence_ids:
                    if evidence_id not in evidence_map:
                        errors.append("UNKNOWN_EVIDENCE_REFERENCE:" + path + ".evidence_ids")
            if observation_id and source_id and candidate_id and stance and evidence_ids is not None:
                if observation_id in observation_map:
                    errors.append("DUPLICATE_OBSERVATION_ID:" + path + ".observation_id")
                item = {
                    "observation_id": observation_id,
                    "source_id": source_id,
                    "candidate_id": candidate_id,
                    "stance": stance,
                    "evidence_ids": sorted(evidence_ids),
                }
                observation_map[observation_id] = item
                normalized_observations.append(item)

    constraints_array = _expect_array(root.get("constraints"), "$.constraints", errors)
    normalized_constraints: List[Dict[str, Any]] = []
    constraint_ids = set()
    if constraints_array is not None:
        if len(constraints_array) > MAX_CONSTRAINTS:
            errors.append("RESOURCE_CONSTRAINT_LIMIT:$.constraints")
        for index, constraint_value in enumerate(constraints_array):
            path = "$.constraints[" + str(index) + "]"
            constraint = _expect_object(constraint_value, path, ["constraint_id", "kind", "candidate_id", "active"], errors)
            if constraint is None:
                continue
            constraint_id = _validate_id(constraint.get("constraint_id"), path + ".constraint_id", errors)
            kind = _expect_string(constraint.get("kind"), path + ".kind", errors)
            candidate_id = _expect_string(constraint.get("candidate_id"), path + ".candidate_id", errors)
            active = _expect_boolean(constraint.get("active"), path + ".active", errors)
            if kind is not None and kind not in CONSTRAINT_KINDS:
                errors.append("UNSUPPORTED_CONSTRAINT_KIND:" + path + ".kind")
            if candidate_id is not None:
                if candidate_id != "*" and not ID_PATTERN.fullmatch(candidate_id):
                    errors.append("INVALID_IDENTIFIER:" + path + ".candidate_id")
                if candidate_ids is not None and candidate_id != "*" and candidate_id not in set(candidate_ids):
                    errors.append("UNKNOWN_CONSTRAINT_CANDIDATE:" + path + ".candidate_id")
            if constraint_id and kind and candidate_id is not None and active is not None:
                if constraint_id in constraint_ids:
                    errors.append("DUPLICATE_CONSTRAINT_ID:" + path + ".constraint_id")
                constraint_ids.add(constraint_id)
                normalized_constraints.append({"constraint_id": constraint_id, "kind": kind, "candidate_id": candidate_id, "active": active})

    boundary = _expect_object(root.get("boundary"), "$.boundary", ["expected_observation_ids", "expected_evidence_ids"], errors)
    expected_observation_ids: Optional[List[str]] = None
    expected_evidence_ids: Optional[List[str]] = None
    if boundary is not None:
        expected_observation_ids = _unique_string_array(boundary.get("expected_observation_ids"), "$.boundary.expected_observation_ids", errors)
        expected_evidence_ids = _unique_string_array(boundary.get("expected_evidence_ids"), "$.boundary.expected_evidence_ids", errors)

    if errors:
        return None, sorted(set(errors))

    actual_observation_ids = set(observation_map)
    actual_evidence_ids = set(evidence_map)
    expected_observation_set = set(expected_observation_ids or [])
    expected_evidence_set = set(expected_evidence_ids or [])
    undeclared_observations = sorted(actual_observation_ids - expected_observation_set)
    undeclared_evidence = sorted(actual_evidence_ids - expected_evidence_set)
    if undeclared_observations:
        errors.append("UNDECLARED_OBSERVATION:" + ",".join(undeclared_observations))
    if undeclared_evidence:
        errors.append("UNDECLARED_EVIDENCE:" + ",".join(undeclared_evidence))
    if errors:
        return None, sorted(set(errors))

    normalized = {
        "schema": INPUT_SCHEMA,
        "context": {
            "context_id": context_id,
            "question_id": question_id,
            "domain": domain,
            "candidate_ids": sorted(candidate_ids or []),
            "ruleset_id": ruleset_id,
            "profile_id": profile_id,
            "text_profile_id": text_profile_id,
            "evidence_mode": evidence_mode,
            "authority_mode": authority_mode,
            "boundary_state": boundary_state,
        },
        "sources": sorted(normalized_sources, key=lambda item: item["source_id"]),
        "evidence": sorted(normalized_evidence, key=lambda item: item["evidence_id"]),
        "observations": sorted(normalized_observations, key=lambda item: item["observation_id"]),
        "constraints": sorted(normalized_constraints, key=lambda item: item["constraint_id"]),
        "boundary": {
            "expected_observation_ids": sorted(expected_observation_ids or []),
            "expected_evidence_ids": sorted(expected_evidence_ids or []),
        },
    }
    return normalized, []


def _candidate_metrics(normalized: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    source_map = {item["source_id"]: item for item in normalized["sources"]}
    result: Dict[str, Dict[str, Any]] = {}
    for candidate_id in normalized["context"]["candidate_ids"]:
        candidate_observations = [item for item in normalized["observations"] if item["candidate_id"] == candidate_id]
        support = [item for item in candidate_observations if item["stance"] == "SUPPORT"]
        oppose = [item for item in candidate_observations if item["stance"] == "OPPOSE"]
        abstain = [item for item in candidate_observations if item["stance"] == "ABSTAIN"]
        support_sources = sorted({item["source_id"] for item in support})
        support_families = sorted({source_map[item["source_id"]]["source_family"] for item in support})
        support_classes = sorted({source_map[item["source_id"]]["source_class"] for item in support})
        evidence_complete = all(bool(item["evidence_ids"]) for item in support)
        missing_classes = sorted(set(PROFILE["required_source_classes"]) - set(support_classes))
        missing_support_sources = max(0, PROFILE["minimum_support_sources"] - len(support_sources))
        missing_source_families = max(0, PROFILE["minimum_source_families"] - len(support_families))
        eligible = bool(support) and not missing_classes and missing_support_sources == 0 and missing_source_families == 0 and evidence_complete
        result[candidate_id] = {
            "support_observation_ids": sorted(item["observation_id"] for item in support),
            "opposition_observation_ids": sorted(item["observation_id"] for item in oppose),
            "abstention_observation_ids": sorted(item["observation_id"] for item in abstain),
            "support_source_count": len(support_sources),
            "support_family_count": len(support_families),
            "support_classes": support_classes,
            "missing_required_classes": missing_classes,
            "missing_support_sources": missing_support_sources,
            "missing_source_families": missing_source_families,
            "evidence_complete": evidence_complete,
            "eligible": eligible,
        }
    return result


def _minimal_witness(normalized: Dict[str, Any], candidate_id: str) -> List[str]:
    source_map = {item["source_id"]: item for item in normalized["sources"]}
    representatives: Dict[str, Dict[str, Any]] = {}
    for observation in sorted(normalized["observations"], key=lambda item: item["observation_id"]):
        if observation["candidate_id"] != candidate_id or observation["stance"] != "SUPPORT" or not observation["evidence_ids"]:
            continue
        representatives.setdefault(observation["source_id"], observation)

    required_classes = tuple(PROFILE["required_source_classes"])
    class_bits = {source_class: 1 << index for index, source_class in enumerate(required_classes)}
    target_mask = (1 << len(required_classes)) - 1
    minimum_sources = PROFILE["minimum_support_sources"]
    minimum_families = PROFILE["minimum_source_families"]
    items = []
    for source_id, observation in representatives.items():
        source = source_map[source_id]
        items.append((observation["observation_id"], source["source_family"], class_bits.get(source["source_class"], 0)))
    items.sort()

    states: Dict[Tuple[int, Optional[Tuple[str, ...]], int], Tuple[str, ...]] = {(0, tuple(), 0): tuple()}
    for observation_id, family, class_bit in items:
        next_states = dict(states)
        for (mask, families, source_count), selected in states.items():
            if families is None:
                next_families: Optional[Tuple[str, ...]] = None
            else:
                family_set = set(families)
                family_set.add(family)
                next_families = None if len(family_set) >= minimum_families else tuple(sorted(family_set))
            candidate = selected + (observation_id,)
            key = (mask | class_bit, next_families, min(minimum_sources, source_count + 1))
            current = next_states.get(key)
            if current is None or (len(candidate), candidate) < (len(current), current):
                next_states[key] = candidate
        states = next_states

    witness = states.get((target_mask, None, minimum_sources))
    return list(witness) if witness is not None else []


def resolve_normalized(normalized: Dict[str, Any]) -> Dict[str, Any]:
    context = normalized["context"]
    observations = normalized["observations"]
    metrics = _candidate_metrics(normalized)
    supported_candidates = sorted(candidate_id for candidate_id, item in metrics.items() if item["support_observation_ids"])
    eligible_candidates = sorted(candidate_id for candidate_id, item in metrics.items() if item["eligible"])
    blockers: List[str] = []
    repairs: List[str] = []

    active_denials = []
    for constraint in normalized["constraints"]:
        if not constraint["active"]:
            continue
        if constraint["kind"] != "FORBID_CANDIDATE":
            continue
        target = constraint["candidate_id"]
        affected = supported_candidates if target == "*" else ([target] if target in supported_candidates else [])
        if affected:
            active_denials.append({"constraint_id": constraint["constraint_id"], "candidate_ids": sorted(affected)})
    if active_denials:
        for item in active_denials:
            blockers.append("ACTIVE_PROHIBITION:" + item["constraint_id"] + ":" + ",".join(item["candidate_ids"]))
        return {
            "state": "DENIED",
            "reason_code": "ACTIVE_PROHIBITION",
            "candidate_id": None,
            "eligible_candidate_ids": eligible_candidates,
            "supported_candidate_ids": supported_candidates,
            "witness_observation_ids": [],
            "blockers": sorted(blockers),
            "repair_requirements": [],
            "candidate_metrics": metrics,
            "authority": "NONE",
        }

    source_supports: Dict[str, set] = {}
    source_opposes: Dict[str, set] = {}
    for observation in observations:
        if observation["stance"] == "SUPPORT":
            source_supports.setdefault(observation["source_id"], set()).add(observation["candidate_id"])
        if observation["stance"] == "OPPOSE":
            source_opposes.setdefault(observation["source_id"], set()).add(observation["candidate_id"])
    conflicting_sources = sorted(source_id for source_id, candidates in source_supports.items() if len(candidates) > 1)
    self_conflicting_sources = sorted(source_id for source_id in set(source_supports) & set(source_opposes) if source_supports[source_id] & source_opposes[source_id])
    if conflicting_sources or self_conflicting_sources:
        blockers.extend("SOURCE_MULTI_CANDIDATE_SUPPORT:" + source_id for source_id in conflicting_sources)
        blockers.extend("SOURCE_SUPPORT_OPPOSE_CONFLICT:" + source_id for source_id in self_conflicting_sources)
        return {
            "state": "ABSTAIN",
            "reason_code": "SOURCE_CONFLICT",
            "candidate_id": None,
            "eligible_candidate_ids": eligible_candidates,
            "supported_candidate_ids": supported_candidates,
            "witness_observation_ids": [],
            "blockers": sorted(set(blockers)),
            "repair_requirements": [],
            "candidate_metrics": metrics,
            "authority": "NONE",
        }

    if len(eligible_candidates) > 1:
        blockers.append("MULTIPLE_ELIGIBLE_CANDIDATES:" + ",".join(eligible_candidates))
        return {
            "state": "ABSTAIN",
            "reason_code": "MULTIPLE_ELIGIBLE_CANDIDATES",
            "candidate_id": None,
            "eligible_candidate_ids": eligible_candidates,
            "supported_candidate_ids": supported_candidates,
            "witness_observation_ids": [],
            "blockers": blockers,
            "repair_requirements": [],
            "candidate_metrics": metrics,
            "authority": "NONE",
        }

    if len(eligible_candidates) == 1:
        winner = eligible_candidates[0]
        opposition = metrics[winner]["opposition_observation_ids"]
        minority = sorted(candidate_id for candidate_id in supported_candidates if candidate_id != winner)
        if opposition:
            blockers.append("OPPOSITION_PRESENT:" + ",".join(opposition))
        if minority:
            blockers.append("MINORITY_SUPPORT_PRESENT:" + ",".join(minority))
        if blockers:
            return {
                "state": "ABSTAIN",
                "reason_code": "BLOCKING_DISAGREEMENT",
                "candidate_id": None,
                "eligible_candidate_ids": eligible_candidates,
                "supported_candidate_ids": supported_candidates,
                "witness_observation_ids": [],
                "blockers": sorted(blockers),
                "repair_requirements": [],
                "candidate_metrics": metrics,
                "authority": "NONE",
            }

    if len(eligible_candidates) == 0 and len(supported_candidates) > 1:
        blockers.append("COMPETING_PARTIAL_SUPPORT:" + ",".join(supported_candidates))
        return {
            "state": "ABSTAIN",
            "reason_code": "COMPETING_PARTIAL_SUPPORT",
            "candidate_id": None,
            "eligible_candidate_ids": [],
            "supported_candidate_ids": supported_candidates,
            "witness_observation_ids": [],
            "blockers": blockers,
            "repair_requirements": [],
            "candidate_metrics": metrics,
            "authority": "NONE",
        }

    actual_observation_ids = {item["observation_id"] for item in observations}
    actual_evidence_ids = {item["evidence_id"] for item in normalized["evidence"]}
    expected_observation_ids = set(normalized["boundary"]["expected_observation_ids"])
    expected_evidence_ids = set(normalized["boundary"]["expected_evidence_ids"])
    missing_observations = sorted(expected_observation_ids - actual_observation_ids)
    missing_evidence = sorted(expected_evidence_ids - actual_evidence_ids)
    if context["boundary_state"] != "SEALED":
        repairs.append("SEAL_DECLARED_BOUNDARY")
    if missing_observations:
        repairs.append("SUPPLY_OBSERVATIONS:" + ",".join(missing_observations))
    if missing_evidence:
        repairs.append("SUPPLY_EVIDENCE:" + ",".join(missing_evidence))
    if repairs:
        return {
            "state": "INCOMPLETE",
            "reason_code": "BOUNDARY_INCOMPLETE",
            "candidate_id": None,
            "eligible_candidate_ids": eligible_candidates,
            "supported_candidate_ids": supported_candidates,
            "witness_observation_ids": [],
            "blockers": [],
            "repair_requirements": sorted(repairs),
            "candidate_metrics": metrics,
            "authority": "NONE",
        }

    if len(eligible_candidates) == 1:
        winner = eligible_candidates[0]
        witness = _minimal_witness(normalized, winner)
        return {
            "state": "RESOLVED",
            "reason_code": "UNIQUE_ADMISSIBLE_CANDIDATE",
            "candidate_id": winner,
            "eligible_candidate_ids": [winner],
            "supported_candidate_ids": supported_candidates,
            "witness_observation_ids": witness,
            "blockers": [],
            "repair_requirements": [],
            "candidate_metrics": metrics,
            "authority": "NONE",
        }

    target_candidates = supported_candidates or context["candidate_ids"]
    for candidate_id in target_candidates:
        item = metrics[candidate_id]
        if item["missing_support_sources"]:
            repairs.append("ADD_SUPPORT_SOURCES:" + candidate_id + ":" + str(item["missing_support_sources"]))
        if item["missing_source_families"]:
            repairs.append("ADD_SOURCE_FAMILIES:" + candidate_id + ":" + str(item["missing_source_families"]))
        if item["missing_required_classes"]:
            repairs.append("ADD_REQUIRED_CLASSES:" + candidate_id + ":" + ",".join(item["missing_required_classes"]))
        if not item["evidence_complete"]:
            repairs.append("ATTACH_EVIDENCE_TO_SUPPORT:" + candidate_id)
    return {
        "state": "INCOMPLETE",
        "reason_code": "ADMISSION_REQUIREMENTS_UNMET",
        "candidate_id": None,
        "eligible_candidate_ids": [],
        "supported_candidate_ids": supported_candidates,
        "witness_observation_ids": [],
        "blockers": [],
        "repair_requirements": sorted(set(repairs)),
        "candidate_metrics": metrics,
        "authority": "NONE",
    }


def build_public_receipt(bundle: Dict[str, Any]) -> Dict[str, Any]:
    resolution = bundle["resolution"]
    commitments = bundle["commitments"]
    core = {
        "schema": RECEIPT_SCHEMA,
        "project": PROJECT,
        "version": VERSION,
        "context_id": bundle["context_id"],
        "ruleset_id": bundle["ruleset_id"],
        "profile_id": bundle["profile_id"],
        "text_profile_id": bundle["text_profile_id"],
        "state": resolution["state"],
        "reason_code": resolution["reason_code"],
        "candidate_id": resolution["candidate_id"],
        "authority": "NONE",
        "boundary_state": bundle["boundary_state"],
        "counts": bundle["counts"],
        "commitments": commitments,
        "decision_resolution_id": bundle["identities"]["decision_resolution_id"],
        "private_bundle_id": bundle["identities"]["private_bundle_id"],
    }
    receipt_id = tagged_hash("ORL-AI-PUBLIC-RECEIPT-ID-5", core)
    return {**core, "public_receipt_id": receipt_id}


def resolve_document(document: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    submitted_commitment = tagged_hash("ORL-AI-SUBMITTED-INPUT-5", document)
    normalized, errors = validate_and_normalize(document)
    if errors:
        resolution = {
            "state": "REFUSED",
            "reason_code": "STRUCTURAL_INTAKE_REFUSAL",
            "candidate_id": None,
            "eligible_candidate_ids": [],
            "supported_candidate_ids": [],
            "witness_observation_ids": [],
            "blockers": errors,
            "repair_requirements": [],
            "candidate_metrics": {},
            "authority": "NONE",
        }
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
                "submitted_input_commitment": submitted_commitment,
                "normalized_input_commitment": None,
                "observation_set_commitment": None,
                "evidence_set_commitment": None,
                "constraint_set_commitment": None,
                "witness_commitment": tagged_hash("ORL-AI-WITNESS-SET-5", []),
            },
        }
    else:
        assert normalized is not None
        resolution = resolve_normalized(normalized)
        normalized_commitment = tagged_hash("ORL-AI-NORMALIZED-INPUT-5", normalized)
        observation_commitment = tagged_hash("ORL-AI-OBSERVATION-SET-5", normalized["observations"])
        evidence_commitment = tagged_hash("ORL-AI-EVIDENCE-SET-5", normalized["evidence"])
        constraint_commitment = tagged_hash("ORL-AI-CONSTRAINT-SET-5", normalized["constraints"])
        witness_commitment = tagged_hash("ORL-AI-WITNESS-SET-5", resolution["witness_observation_ids"])
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
                "submitted_input_commitment": submitted_commitment,
                "normalized_input_commitment": normalized_commitment,
                "observation_set_commitment": observation_commitment,
                "evidence_set_commitment": evidence_commitment,
                "constraint_set_commitment": constraint_commitment,
                "witness_commitment": witness_commitment,
            },
        }
    resolution_id = tagged_hash(
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
    private_bundle_id = tagged_hash(
        "ORL-AI-PRIVATE-BUNDLE-ID-5",
        {**core, "decision_resolution_id": resolution_id, "artifact_profile": artifact_profile},
    )
    bundle = {
        **core,
        "artifact_profile": artifact_profile,
        "identities": {
            "decision_resolution_id": resolution_id,
            "private_bundle_id": private_bundle_id,
        },
    }
    receipt = build_public_receipt(bundle)
    bundle["identities"]["public_receipt_id"] = receipt["public_receipt_id"]
    return bundle, receipt


def verify_bundle(bundle: Any) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(bundle, dict):
        return False, ["BUNDLE_NOT_OBJECT"]
    normalized = bundle.get("normalized_input")
    if normalized is None:
        errors.append("REFUSED_BUNDLE_REQUIRES_SUBMITTED_INPUT_FOR_RECONSTRUCTION")
        return False, errors
    reconstructed, receipt = resolve_document(normalized)
    if canonical_json_bytes(reconstructed) != canonical_json_bytes(bundle):
        errors.append("BUNDLE_RECONSTRUCTION_MISMATCH")
    if bundle.get("identities", {}).get("public_receipt_id") != receipt.get("public_receipt_id"):
        errors.append("PUBLIC_RECEIPT_ID_MISMATCH")
    return not errors, errors


def _digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def example_document(case_id: str = "resolved-consensus") -> Dict[str, Any]:
    candidates = ["QUEUE_ALPHA", "QUEUE_BETA"]
    sources = [
        {"source_id": "model-primary", "source_family": "family-alpha", "source_class": "MODEL"},
        {"source_id": "model-review", "source_family": "family-beta", "source_class": "MODEL_REVIEW"},
        {"source_id": "rule-checker", "source_family": "family-gamma", "source_class": "RULE_CHECK"},
    ]
    evidence = [
        {"evidence_id": "e-format", "kind": "DECLARED_FACT", "digest": _digest(case_id + ":format")},
        {"evidence_id": "e-policy", "kind": "RULE_RESULT", "digest": _digest(case_id + ":policy")},
        {"evidence_id": "e-review", "kind": "REVIEW_RESULT", "digest": _digest(case_id + ":review")},
    ]
    observations = [
        {"observation_id": "obs-model", "source_id": "model-primary", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-format"]},
        {"observation_id": "obs-review", "source_id": "model-review", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-review"]},
        {"observation_id": "obs-rule", "source_id": "rule-checker", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-policy"]},
    ]
    return {
        "schema": INPUT_SCHEMA,
        "context": {
            "context_id": case_id,
            "question_id": "route-synthetic-record",
            "domain": "synthetic-routing",
            "candidate_ids": candidates,
            "ruleset_id": RULESET_ID,
            "profile_id": PROFILE_ID,
            "text_profile_id": TEXT_PROFILE_ID,
            "evidence_mode": "DECLARED",
            "authority_mode": "NONE",
            "boundary_state": "SEALED",
        },
        "sources": sources,
        "evidence": evidence,
        "observations": observations,
        "constraints": [],
        "boundary": {
            "expected_observation_ids": [item["observation_id"] for item in observations],
            "expected_evidence_ids": [item["evidence_id"] for item in evidence],
        },
    }


def self_test() -> int:
    checks: List[Tuple[str, bool]] = []

    resolved = example_document()
    bundle, receipt = resolve_document(resolved)
    checks.append(("resolved state", bundle["resolution"]["state"] == "RESOLVED"))
    checks.append(("resolved candidate", bundle["resolution"]["candidate_id"] == "QUEUE_ALPHA"))
    checks.append(("minimal witness", len(bundle["resolution"]["witness_observation_ids"]) == 3))
    checks.append(("authority none", bundle["resolution"]["authority"] == "NONE"))
    checks.append(("receipt binding", bundle["identities"]["public_receipt_id"] == receipt["public_receipt_id"]))
    expected_artifact_profile = {
        "profile_id": ARTIFACT_PROFILE_ID,
        "identity_algorithm": "SHA-256",
        "canonicalization": "UTF-8 sorted-key compact JSON with LF terminator",
    }
    checks.append(("artifact profile declared", bundle.get("artifact_profile") == expected_artifact_profile))
    checks.append(("static verification status absent", "self_verification" not in bundle))
    identity_core = {key: value for key, value in bundle.items() if key not in {"artifact_profile", "identities"}}
    expected_private_id = tagged_hash(
        "ORL-AI-PRIVATE-BUNDLE-ID-5",
        {
            **identity_core,
            "decision_resolution_id": bundle["identities"]["decision_resolution_id"],
            "artifact_profile": bundle["artifact_profile"],
        },
    )
    checks.append(("artifact profile identity binding", bundle["identities"]["private_bundle_id"] == expected_private_id))
    altered_profile_bundle = json.loads(json.dumps(bundle))
    altered_profile_bundle["artifact_profile"]["canonicalization"] = "ALTERED"
    checks.append(("artifact profile tamper detected", not verify_bundle(altered_profile_bundle)[0]))

    permuted = json.loads(json.dumps(resolved))
    permuted["sources"] = list(reversed(permuted["sources"]))
    permuted["evidence"] = [permuted["evidence"][1], permuted["evidence"][2], permuted["evidence"][0]]
    permuted["observations"] = [permuted["observations"][2], permuted["observations"][0], permuted["observations"][1]]
    permuted["context"]["candidate_ids"] = list(reversed(permuted["context"]["candidate_ids"]))
    permuted["boundary"]["expected_observation_ids"] = list(reversed(permuted["boundary"]["expected_observation_ids"]))
    permuted_bundle, _ = resolve_document(permuted)
    checks.append(("order-independent resolution identity", bundle["identities"]["decision_resolution_id"] == permuted_bundle["identities"]["decision_resolution_id"]))
    checks.append(("normalized structure equality", bundle["commitments"]["normalized_input_commitment"] == permuted_bundle["commitments"]["normalized_input_commitment"]))

    open_boundary = json.loads(json.dumps(resolved))
    open_boundary["context"]["context_id"] = "open-boundary"
    open_boundary["context"]["boundary_state"] = "OPEN"
    open_bundle, _ = resolve_document(open_boundary)
    checks.append(("open boundary incomplete", open_bundle["resolution"]["state"] == "INCOMPLETE"))

    competing = json.loads(json.dumps(resolved))
    competing["context"]["context_id"] = "competing"
    competing["observations"][0]["candidate_id"] = "QUEUE_BETA"
    competing_bundle, _ = resolve_document(competing)
    checks.append(("minority support abstain", competing_bundle["resolution"]["state"] == "ABSTAIN"))

    opposition = json.loads(json.dumps(resolved))
    opposition["context"]["context_id"] = "opposition"
    opposition["observations"].append({"observation_id": "obs-opposition", "source_id": "model-primary", "candidate_id": "QUEUE_ALPHA", "stance": "OPPOSE", "evidence_ids": ["e-format"]})
    opposition["boundary"]["expected_observation_ids"].append("obs-opposition")
    opposition_bundle, _ = resolve_document(opposition)
    checks.append(("support oppose conflict", opposition_bundle["resolution"]["state"] == "ABSTAIN"))

    denied = json.loads(json.dumps(resolved))
    denied["context"]["context_id"] = "denied"
    denied["constraints"] = [{"constraint_id": "deny-alpha", "kind": "FORBID_CANDIDATE", "candidate_id": "QUEUE_ALPHA", "active": True}]
    denied_bundle, _ = resolve_document(denied)
    checks.append(("active prohibition denied", denied_bundle["resolution"]["state"] == "DENIED"))

    correlated = json.loads(json.dumps(resolved))
    correlated["context"]["context_id"] = "correlated"
    for source in correlated["sources"]:
        source["source_family"] = "shared-family"
    correlated_bundle, _ = resolve_document(correlated)
    checks.append(("correlated sources incomplete", correlated_bundle["resolution"]["state"] == "INCOMPLETE"))

    malformed = json.loads(json.dumps(resolved))
    malformed["context"]["authority_mode"] = "CALLER"
    malformed_bundle, _ = resolve_document(malformed)
    checks.append(("caller authority refused", malformed_bundle["resolution"]["state"] == "REFUSED"))

    relay = json.loads(json.dumps(resolved))
    relay["context"]["context_id"] = "relay"
    relay["observations"].append({"observation_id": "obs-model-relay", "source_id": "model-primary", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-format"]})
    relay["boundary"]["expected_observation_ids"].append("obs-model-relay")
    relay_bundle, _ = resolve_document(relay)
    checks.append(("relay multiplicity does not raise source count", relay_bundle["resolution"]["candidate_metrics"]["QUEUE_ALPHA"]["support_source_count"] == 3))

    stress = example_document("relay-heavy-witness")
    stress["sources"] = [
        {"source_id": "model-primary", "source_family": "family-alpha", "source_class": "MODEL"},
        {"source_id": "model-review", "source_family": "family-alpha", "source_class": "MODEL_REVIEW"},
        {"source_id": "rule-checker", "source_family": "family-alpha", "source_class": "RULE_CHECK"},
        {"source_id": "tool-family-beta", "source_family": "family-beta", "source_class": "TOOL_CHECK"},
        {"source_id": "human-family-gamma", "source_family": "family-gamma", "source_class": "HUMAN_REVIEW"},
    ]
    stress["evidence"] = [
        {"evidence_id": "e-model", "kind": "DECLARED_FACT", "digest": _digest("relay-heavy:model")},
        {"evidence_id": "e-review", "kind": "REVIEW_RESULT", "digest": _digest("relay-heavy:review")},
        {"evidence_id": "e-rule", "kind": "RULE_RESULT", "digest": _digest("relay-heavy:rule")},
        {"evidence_id": "e-tool", "kind": "RULE_RESULT", "digest": _digest("relay-heavy:tool")},
        {"evidence_id": "e-human", "kind": "REVIEW_RESULT", "digest": _digest("relay-heavy:human")},
    ]
    stress_observations = [
        {"observation_id": "obs-000-model", "source_id": "model-primary", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-model"]}
    ]
    for index in range(1, 252):
        stress_observations.append({"observation_id": "obs-" + str(index).zfill(3) + "-relay", "source_id": "model-primary", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-model"]})
    stress_observations.extend([
        {"observation_id": "obs-252-review", "source_id": "model-review", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-review"]},
        {"observation_id": "obs-253-rule", "source_id": "rule-checker", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-rule"]},
        {"observation_id": "obs-254-tool", "source_id": "tool-family-beta", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-tool"]},
        {"observation_id": "obs-255-human", "source_id": "human-family-gamma", "candidate_id": "QUEUE_ALPHA", "stance": "SUPPORT", "evidence_ids": ["e-human"]},
    ])
    stress["observations"] = stress_observations
    stress["boundary"] = {
        "expected_observation_ids": [item["observation_id"] for item in stress_observations],
        "expected_evidence_ids": [item["evidence_id"] for item in stress["evidence"]],
    }
    stress_bundle, _ = resolve_document(stress)
    expected_stress_witness = ["obs-000-model", "obs-252-review", "obs-253-rule", "obs-254-tool", "obs-255-human"]
    checks.append(("relay-heavy bounded witness", stress_bundle["resolution"]["state"] == "RESOLVED" and stress_bundle["resolution"]["witness_observation_ids"] == expected_stress_witness))

    strict_cases = [
        ("duplicate key parser refusal", '{"a":1,"a":2}', "DUPLICATE_JSON_KEY"),
        ("float parser refusal", '{"a":1.0}', "FLOATING_JSON_NUMBER"),
        ("non-finite parser refusal", '{"a":NaN}', "NONFINITE_JSON_NUMBER"),
        ("large integer parser refusal", '{"a":9007199254740992}', "INTEGER_OUTSIDE_EXACT_RANGE"),
        ("trailing content parser refusal", '{}{}', "MALFORMED_JSON"),
        ("bom parser refusal", '\ufeff{}', "UTF8_BOM"),
        ("unpaired surrogate parser refusal", '{"a":"\\ud800"}', "MALFORMED_JSON"),
    ]
    for name, text, expected in strict_cases:
        try:
            strict_json_loads(text)
            checks.append((name, False))
        except ParserRefusal as exc:
            checks.append((name, expected in str(exc)))

    passed = sum(1 for _, status in checks if status)
    for name, status in checks:
        print(("PASS" if status else "FAIL") + "  " + name)
    print("TOTAL " + str(passed) + "/" + str(len(checks)) + " PASS")
    return 0 if passed == len(checks) else 1


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def main() -> int:
    parser = argparse.ArgumentParser(description="ORL-AI deterministic decision-admission reference kernel")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--resolve", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--receipt-output", type=Path)
    parser.add_argument("--verify-bundle", type=Path)
    parser.add_argument("--print-example", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.print_example:
        sys.stdout.write(canonical_json_text(example_document()))
        return 0
    if args.verify_bundle:
        bundle = strict_json_load(args.verify_bundle)
        passed, errors = verify_bundle(bundle)
        print("BUNDLE VERIFY: " + ("PASS" if passed else "FAIL"))
        for error in errors:
            print(error)
        return 0 if passed else 1
    if args.resolve:
        try:
            document = strict_json_load(args.resolve)
        except ParserRefusal as exc:
            print("PARSER REFUSAL: " + str(exc), file=sys.stderr)
            return 2
        bundle, receipt = resolve_document(document)
        if args.output:
            write_json(args.output, bundle)
        else:
            sys.stdout.write(canonical_json_text(bundle))
        if args.receipt_output:
            write_json(args.receipt_output, receipt)
        return 0
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
