#!/usr/bin/env python3

import argparse
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


KERNEL = load_module("orl_ai_reference", ROOT / "demo" / "ORL_AI_Reference_Kernel_v5_0_0.py")
INDEPENDENT = load_module("orl_ai_independent", ROOT / "verifier" / "ORL_AI_Independent_Verifier_v5_0_0.py")
NODE_PARSER = ROOT / "demo" / "ORL_AI_Strict_Json_v5_0_0.js"
NODE_RESOLVER = ROOT / "demo" / "ORL_AI_Browser_Resolver_v5_0_0.js"
MANIFEST = ROOT / "hostile" / "ORL_AI_Hostile_Corpus_Manifest_v5_0_0.json"


def classify_python(loader, path: Path) -> str:
    try:
        loader(path)
        return "ACCEPTED"
    except Exception as exc:
        return str(exc)


def classify_node_parser(path: Path) -> Tuple[int, str]:
    completed = subprocess.run(
        ["node", str(NODE_PARSER), "--classify", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.returncode, (completed.stdout or completed.stderr).strip()


def classify_node_resolver(path: Path) -> Tuple[int, str]:
    completed = subprocess.run(
        ["node", str(NODE_RESOLVER), "--resolve", str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.returncode, (completed.stderr or completed.stdout).strip()


def run() -> Tuple[bool, Dict[str, Any]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases: List[Dict[str, Any]] = []
    all_pass = True

    raw_entries = [entry for entry in manifest["entries"] if "expected_parser_refusal" in entry]
    for entry in raw_entries:
        path = ROOT / entry["path"]
        expected = entry["expected_parser_refusal"]
        producer = classify_python(KERNEL.strict_json_load, path)
        independent = classify_python(INDEPENDENT.load_strict, path)
        parser_code, parser_output = classify_node_parser(path)
        resolver_code, resolver_output = classify_node_resolver(path)
        case_pass = (
            expected in producer
            and expected in independent
            and parser_code == 2
            and expected in parser_output
            and resolver_code == 2
            and expected in resolver_output
        )
        all_pass = all_pass and case_pass
        cases.append({
            "case_id": entry["case_id"],
            "expected": expected,
            "python_reference": producer,
            "python_independent": independent,
            "javascript_parser": parser_output,
            "javascript_resolver": resolver_output,
            "pass": case_pass,
        })

    valid_path = ROOT / "examples" / "ORL_AI_resolved-consensus_Input_v5_0_0.json"
    producer = classify_python(KERNEL.strict_json_load, valid_path)
    independent = classify_python(INDEPENDENT.load_strict, valid_path)
    parser_code, parser_output = classify_node_parser(valid_path)
    resolver_code, resolver_output = classify_node_resolver(valid_path)
    valid_pass = (
        producer == "ACCEPTED"
        and independent == "ACCEPTED"
        and parser_code == 0
        and parser_output == "ACCEPTED"
        and resolver_code == 0
        and '"state":"RESOLVED"' in resolver_output
    )
    all_pass = all_pass and valid_pass
    cases.append({
        "case_id": "well-formed-control",
        "expected": "ACCEPTED",
        "python_reference": producer,
        "python_independent": independent,
        "javascript_parser": parser_output,
        "javascript_resolver": "RESOLVED" if '"state":"RESOLVED"' in resolver_output else resolver_output,
        "pass": valid_pass,
    })

    receipt = {
        "schema": "ORL-AI-RAW-INTAKE-PARITY-RECEIPT-5.0.0",
        "project": "ORL-AI",
        "version": "5.0.0",
        "cases": cases,
        "pass": all_pass,
    }
    return all_pass, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ORL-AI raw-intake parity across Python and JavaScript")
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()

    passed, receipt = run()
    for case in receipt["cases"]:
        print(("PASS" if case["pass"] else "FAIL") + "  " + case["case_id"])
    passed_count = sum(1 for case in receipt["cases"] if case["pass"])
    print("TOTAL " + str(passed_count) + "/" + str(len(receipt["cases"])) + " PASS")
    print("RAW-INTAKE PARITY: " + ("PASS" if passed else "FAIL"))

    if args.receipt_output:
        args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_output.write_bytes(KERNEL.canonical_json_bytes(receipt))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
