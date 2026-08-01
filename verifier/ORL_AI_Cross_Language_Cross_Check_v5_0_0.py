#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VECTORS = ROOT / "parity" / "ORL_AI_Cross_Language_Parity_Vectors_v5_0_0.json"
JS = ROOT / "demo" / "ORL_AI_Browser_Resolver_v5_0_0.js"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def run_all():
    vectors = json.loads(VECTORS.read_text(encoding="utf-8"))["vectors"]
    cases = []
    passed = True
    with tempfile.TemporaryDirectory(prefix="orl_ai_cross_") as tmp:
        tmp_path = Path(tmp)
        for vector in vectors:
            bundle_out = tmp_path / (vector["case_id"] + "_bundle.json")
            receipt_out = tmp_path / (vector["case_id"] + "_receipt.json")
            command = [
                "node", str(JS), "--resolve", str(ROOT / vector["input_path"]),
                "--output", str(bundle_out), "--receipt-output", str(receipt_out),
            ]
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env={**os.environ, "NODE_NO_WARNINGS": "1"})
            expected_bundle = (ROOT / vector["bundle_path"]).read_bytes()
            expected_receipt = (ROOT / vector["receipt_path"]).read_bytes()
            bundle_equal = completed.returncode == 0 and bundle_out.is_file() and bundle_out.read_bytes() == expected_bundle
            receipt_equal = completed.returncode == 0 and receipt_out.is_file() and receipt_out.read_bytes() == expected_receipt
            case_pass = bundle_equal and receipt_equal
            passed = passed and case_pass
            cases.append({
                "case_id": vector["case_id"],
                "node_exit_code": completed.returncode,
                "bundle_equal": bundle_equal,
                "receipt_equal": receipt_equal,
                "pass": case_pass,
            })
    receipt = {
        "schema": "ORL-AI-CROSS-IMPLEMENTATION-RECEIPT-5.0.0",
        "project": "ORL-AI",
        "version": "5.0.0",
        "implementations": ["Python reference kernel", "JavaScript resolver"],
        "cases": cases,
        "pass": passed,
    }
    return passed, receipt


def main():
    parser = argparse.ArgumentParser(description="Cross-check Python-produced ORL-AI artifacts with the JavaScript resolver")
    parser.add_argument("--all-examples", action="store_true")
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()
    if not args.all_examples:
        parser.print_help()
        return 0
    passed, receipt = run_all()
    for case in receipt["cases"]:
        print(("PASS" if case["pass"] else "FAIL") + "  " + case["case_id"])
    if args.receipt_output:
        args.receipt_output.write_bytes(canonical(receipt))
    print("CROSS-IMPLEMENTATION VERIFY: " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
