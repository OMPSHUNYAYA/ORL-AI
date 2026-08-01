#!/usr/bin/env python3

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "corpus" / "ORL_AI_Frozen_Corpus_Manifest_v5_0_0.json"
OUTPUT = ROOT / "parity" / "ORL_AI_Cross_Language_Parity_Vectors_v5_0_0.json"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def digest(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    vectors = []
    for entry in manifest["entries"]:
        input_path = ROOT / entry["input_path"]
        bundle_path = ROOT / entry["bundle_path"]
        receipt_path = ROOT / entry["receipt_path"]
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        vectors.append({
            "case_id": entry["case_id"],
            "input_path": entry["input_path"],
            "bundle_path": entry["bundle_path"],
            "receipt_path": entry["receipt_path"],
            "expected_state": bundle["resolution"]["state"],
            "expected_reason_code": bundle["resolution"]["reason_code"],
            "expected_candidate_id": bundle["resolution"]["candidate_id"],
            "decision_resolution_id": bundle["identities"]["decision_resolution_id"],
            "private_bundle_id": bundle["identities"]["private_bundle_id"],
            "public_receipt_id": receipt["public_receipt_id"],
            "input_sha256": digest(input_path),
            "bundle_sha256": digest(bundle_path),
            "receipt_sha256": digest(receipt_path),
        })
    return {
        "schema": "ORL-AI-CROSS-LANGUAGE-PARITY-VECTORS-5.0.0",
        "project": "ORL-AI",
        "version": "5.0.0",
        "canonicalization": "UTF-8 sorted-key compact JSON with LF terminator",
        "vectors": vectors,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate or verify ORL-AI cross-language parity vectors")
    parser.add_argument("--verify-existing", action="store_true")
    args = parser.parse_args()
    expected = canonical(build())
    if args.verify_existing:
        passed = OUTPUT.is_file() and OUTPUT.read_bytes() == expected
        print("PARITY VECTOR VERIFY: " + ("PASS" if passed else "FAIL"))
        return 0 if passed else 1
    OUTPUT.write_bytes(expected)
    print("PARITY VECTORS WRITTEN: " + str(len(build()["vectors"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
