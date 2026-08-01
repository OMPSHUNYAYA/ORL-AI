#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "demo" / "ORL_AI_Reference_Kernel_v5_0_0.py"
JAVASCRIPT_RESOLVER = ROOT / "demo" / "ORL_AI_Browser_Resolver_v5_0_0.js"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def run_command(command: List[str]) -> None:
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    completed = subprocess.run(command, cwd=ROOT, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if completed.returncode != 0:
        raise RuntimeError("COMMAND_FAILED:" + " ".join(command) + "\n" + completed.stdout + completed.stderr)


def expected_paths(input_path: Path) -> Tuple[Path, Path]:
    base = input_path.name
    bundle_name = base.replace("_Input_", "_Bundle_")
    receipt_name = base.replace("_Input_", "_Public_Receipt_")
    return input_path.parent / bundle_name, input_path.parent / receipt_name


def run() -> Tuple[bool, Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="orl_ai_determinism_") as temporary:
        temp = Path(temporary)
        for input_path in sorted((ROOT / "examples").glob("*_Input_v5_0_0.json")):
            case_id = input_path.name[len("ORL_AI_"):-len("_Input_v5_0_0.json")]
            committed_bundle, committed_receipt = expected_paths(input_path)
            a_bundle = temp / (case_id + "_a_bundle.json")
            a_receipt = temp / (case_id + "_a_receipt.json")
            b_bundle = temp / (case_id + "_b_bundle.json")
            b_receipt = temp / (case_id + "_b_receipt.json")
            js_bundle = temp / (case_id + "_js_bundle.json")
            js_receipt = temp / (case_id + "_js_receipt.json")

            run_command([sys.executable, "-B", str(KERNEL), "--resolve", str(input_path), "--output", str(a_bundle), "--receipt-output", str(a_receipt)])
            run_command([sys.executable, "-B", str(KERNEL), "--resolve", str(input_path), "--output", str(b_bundle), "--receipt-output", str(b_receipt)])
            run_command(["node", str(JAVASCRIPT_RESOLVER), "--resolve", str(input_path), "--output", str(js_bundle), "--receipt-output", str(js_receipt)])

            checks = {
                "committed_bundle_reproduced": a_bundle.read_bytes() == committed_bundle.read_bytes(),
                "committed_receipt_reproduced": a_receipt.read_bytes() == committed_receipt.read_bytes(),
                "python_bundle_idempotent": a_bundle.read_bytes() == b_bundle.read_bytes(),
                "python_receipt_idempotent": a_receipt.read_bytes() == b_receipt.read_bytes(),
                "javascript_bundle_equal": a_bundle.read_bytes() == js_bundle.read_bytes(),
                "javascript_receipt_equal": a_receipt.read_bytes() == js_receipt.read_bytes(),
            }
            case_pass = all(checks.values())
            cases.append({"case_id": case_id, "checks": checks, "pass": case_pass})

    passed = all(case["pass"] for case in cases)
    receipt = {
        "schema": "ORL-AI-DETERMINISM-RECEIPT-5.0.0",
        "project": "ORL-AI",
        "version": "5.0.0",
        "cases": cases,
        "pass": passed,
    }
    return passed, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify ORL-AI regeneration parity and idempotence")
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()

    passed, receipt = run()
    for case in receipt["cases"]:
        print(("PASS" if case["pass"] else "FAIL") + "  " + case["case_id"])
    count = sum(1 for case in receipt["cases"] if case["pass"])
    print("TOTAL " + str(count) + "/" + str(len(receipt["cases"])) + " PASS")
    print("DETERMINISM VERIFY: " + ("PASS" if passed else "FAIL"))

    if args.receipt_output:
        args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
        args.receipt_output.write_bytes(canonical_bytes(receipt))

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
