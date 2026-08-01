#!/usr/bin/env python3

import argparse
import copy
import importlib.util
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


KERNEL = load_module("orl_ai_reference", ROOT / "demo" / "ORL_AI_Reference_Kernel_v5_0_0.py")
INDEPENDENT = load_module("orl_ai_independent", ROOT / "verifier" / "ORL_AI_Independent_Verifier_v5_0_0.py")
NODE_RESOLVER = ROOT / "demo" / "ORL_AI_Browser_Resolver_v5_0_0.js"


def base(case_id: str) -> Dict[str, Any]:
    return copy.deepcopy(KERNEL.example_document(case_id))


def rename_sources(document: Dict[str, Any], identifiers: List[str]) -> Dict[str, Any]:
    mapping = {}
    for source, new_id in zip(document["sources"], identifiers):
        mapping[source["source_id"]] = new_id
        source["source_id"] = new_id
    for observation in document["observations"]:
        observation["source_id"] = mapping[observation["source_id"]]
    return document


def mixed_case() -> Dict[str, Any]:
    return rename_sources(base("edge-mixed-case"), ["A", "Z", "a"])


def punctuation() -> Dict[str, Any]:
    document = rename_sources(base("edge-punctuation"), ["source.1", "source:2", "source_3"])
    for index, evidence in enumerate(document["evidence"], 1):
        old_id = evidence["evidence_id"]
        new_id = ["evidence.1", "evidence:2", "evidence_3"][index - 1]
        evidence["evidence_id"] = new_id
        for observation in document["observations"]:
            observation["evidence_ids"] = [new_id if value == old_id else value for value in observation["evidence_ids"]]
        document["boundary"]["expected_evidence_ids"] = [new_id if value == old_id else value for value in document["boundary"]["expected_evidence_ids"]]
    for index, observation in enumerate(document["observations"], 1):
        old_id = observation["observation_id"]
        new_id = ["observation.1", "observation:2", "observation_3"][index - 1]
        observation["observation_id"] = new_id
        document["boundary"]["expected_observation_ids"] = [new_id if value == old_id else value for value in document["boundary"]["expected_observation_ids"]]
    return document


def unicode_unsupported_keys() -> Dict[str, Any]:
    document = base("edge-unicode-keys")
    document["\ue000"] = "private-use"
    document["😀"] = "line\u2028separator"
    return document



def prototype_key() -> Dict[str, Any]:
    document = base("edge-prototype-key")
    document["__proto__"] = "retained-as-data"
    return document


def resource_source_limit() -> Dict[str, Any]:
    document = base("edge-source-limit")
    while len(document["sources"]) <= KERNEL.MAX_SOURCES:
        index = len(document["sources"])
        document["sources"].append({
            "source_id": "extra-" + str(index).zfill(3),
            "source_family": "family-extra-" + str(index).zfill(3),
            "source_class": "MODEL",
        })
    return document


def carriage_return() -> Dict[str, Any]:
    document = base("edge-carriage-return")
    document["context"]["context_id"] = "bad\rcontext"
    return document


def maximum_integer() -> Dict[str, Any]:
    document = base("edge-maximum-integer")
    document["numeric_marker"] = KERNEL.MAX_EXACT_INTEGER
    return document


def depth_limit() -> Dict[str, Any]:
    document = base("edge-depth-limit")
    nested: Any = "terminal"
    for _ in range(KERNEL.MAX_DEPTH + 2):
        nested = [nested]
    document["deep"] = nested
    return document


CASES: List[Tuple[str, Callable[[], Dict[str, Any]]]] = [
    ("mixed-case identifier ordering", mixed_case),
    ("punctuation identifier ordering", punctuation),
    ("Unicode unsupported-key ordering", unicode_unsupported_keys),
    ("prototype-like key retention", prototype_key),
    ("source resource limit", resource_source_limit),
    ("carriage-return text refusal", carriage_return),
    ("maximum exact integer", maximum_integer),
    ("depth resource limit", depth_limit),
]


def run() -> Tuple[bool, Dict[str, Any]]:
    results = []
    all_pass = True
    with tempfile.TemporaryDirectory(prefix="orl_ai_edge_") as temporary:
        directory = Path(temporary)
        for index, (name, builder) in enumerate(CASES):
            document = builder()
            reference_bundle, reference_receipt = KERNEL.resolve_document(document)
            independent_bundle, independent_receipt = INDEPENDENT.reconstruct(document)
            input_path = directory / (str(index) + "-input.json")
            bundle_path = directory / (str(index) + "-bundle.json")
            receipt_path = directory / (str(index) + "-receipt.json")
            input_path.write_bytes(KERNEL.canonical_json_bytes(document))
            completed = subprocess.run(
                [
                    "node", str(NODE_RESOLVER), "--resolve", str(input_path),
                    "--output", str(bundle_path), "--receipt-output", str(receipt_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            independent_ok = (
                KERNEL.canonical_json_bytes(reference_bundle) == KERNEL.canonical_json_bytes(independent_bundle)
                and KERNEL.canonical_json_bytes(reference_receipt) == KERNEL.canonical_json_bytes(independent_receipt)
            )
            javascript_ok = (
                completed.returncode == 0
                and bundle_path.is_file()
                and receipt_path.is_file()
                and bundle_path.read_bytes() == KERNEL.canonical_json_bytes(reference_bundle)
                and receipt_path.read_bytes() == KERNEL.canonical_json_bytes(reference_receipt)
            )
            case_pass = independent_ok and javascript_ok
            all_pass = all_pass and case_pass
            results.append({
                "case_id": name,
                "state": reference_bundle["resolution"]["state"],
                "reason_code": reference_bundle["resolution"]["reason_code"],
                "independent_python": independent_ok,
                "javascript": javascript_ok,
                "pass": case_pass,
            })
    return all_pass, {
        "schema": "ORL-AI-CROSS-LANGUAGE-EDGE-RECEIPT-5.0.0",
        "project": "ORL-AI",
        "version": "5.0.0",
        "cases": results,
        "pass": all_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ORL-AI cross-language edge-case parity")
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()
    passed, receipt = run()
    for case in receipt["cases"]:
        print(("PASS" if case["pass"] else "FAIL") + "  " + case["case_id"] + "  [" + case["state"] + " / " + case["reason_code"] + "]")
    passed_count = sum(1 for case in receipt["cases"] if case["pass"])
    print("TOTAL " + str(passed_count) + "/" + str(len(receipt["cases"])) + " PASS")
    print("CROSS-LANGUAGE EDGE PARITY: " + ("PASS" if passed else "FAIL"))
    if args.receipt_output:
        args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_output.write_bytes(KERNEL.canonical_json_bytes(receipt))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
