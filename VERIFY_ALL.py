#!/usr/bin/env python3

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_stage(command):
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    completed = subprocess.run(command, cwd=ROOT, env=environment)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main():
    python = sys.executable
    stages = [
        [python, "-B", "demo/ORL_AI_Reference_Kernel_v5_0_0.py", "--self-test"],
        [python, "-B", "verifier/ORL_AI_Independent_Verifier_v5_0_0.py", "--self-test"],
        [python, "-B", "verifier/ORL_AI_Independent_Verifier_v5_0_0.py", "--verify-corpus", "corpus/ORL_AI_Frozen_Corpus_Manifest_v5_0_0.json", "--strict-canonical", "--receipt-output", "VERIFY/ORL_AI_Independent_Verification_Receipt_v5_0_0.json"],
        [python, "-B", "verifier/ORL_AI_Cross_Language_Vector_Generator_v5_0_0.py", "--verify-existing"],
        ["node", "demo/ORL_AI_Strict_Json_v5_0_0.js", "--self-test"],
        ["node", "demo/ORL_AI_Browser_Resolver_v5_0_0.js", "--self-test"],
        ["node", "verifier/ORL_AI_SHA256_Fallback_Verifier_v5_0_0.js"],
        [python, "-B", "verifier/ORL_AI_Raw_Intake_Parity_Verifier_v5_0_0.py", "--receipt-output", "VERIFY/ORL_AI_Raw_Intake_Parity_Receipt_v5_0_0.json"],
        [python, "-B", "verifier/ORL_AI_Cross_Language_Cross_Check_v5_0_0.py", "--all-examples", "--receipt-output", "VERIFY/ORL_AI_Cross_Implementation_Receipt_v5_0_0.json"],
        [python, "-B", "verifier/ORL_AI_Cross_Language_Edge_Verifier_v5_0_0.py", "--receipt-output", "VERIFY/ORL_AI_Cross_Language_Edge_Receipt_v5_0_0.json"],
        [python, "-B", "verifier/ORL_AI_Determinism_Verifier_v5_0_0.py", "--receipt-output", "VERIFY/ORL_AI_Determinism_Receipt_v5_0_0.json"],
        [python, "-B", "verifier/ORL_AI_Seeded_Property_Verifier_v5_0_0.py", "--seed", "20260801", "--cases", "64", "--receipt-output", "VERIFY/ORL_AI_Seeded_Property_Receipt_v5_0_0.json"],
        [python, "-B", "demo/ORL_AI_Decision_Admission_Capsule_v5_0_0.py", "--self-test"],
        [python, "-B", "verifier/ORL_AI_State_Precedence_Test_v5_0_0.py", "--receipt-output", "VERIFY/ORL_AI_State_Precedence_Receipt_v5_0_0.json"],
        [python, "-B", "verifier/ORL_AI_Assurance_Verifier_v5_0_0.py", "--self-test", "--write-report"],
    ]
    for stage in stages:
        run_stage(stage)
    print("ORL-AI v5.0.0 functional verification: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
