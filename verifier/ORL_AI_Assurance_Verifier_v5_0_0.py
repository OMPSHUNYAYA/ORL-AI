#!/usr/bin/env python3

import argparse
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kernel = load_module("orl_ai_kernel", ROOT / "demo" / "ORL_AI_Reference_Kernel_v5_0_0.py")
capsule = load_module("orl_ai_capsule", ROOT / "demo" / "ORL_AI_Decision_Admission_Capsule_v5_0_0.py")
independent = load_module("orl_ai_independent", ROOT / "verifier" / "ORL_AI_Independent_Verifier_v5_0_0.py")


def canonical(value):
    return kernel.canonical_json_bytes(value)


def verify_hostile():
    manifest = json.loads((ROOT / "hostile" / "ORL_AI_Hostile_Corpus_Manifest_v5_0_0.json").read_text(encoding="utf-8"))
    cases = []
    passed = True
    for entry in manifest["entries"]:
        path = ROOT / entry["path"]
        expected_digest = entry.get("input_sha256")
        actual_digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        digest_ok = expected_digest is None or actual_digest == expected_digest
        if "expected_parser_refusal" in entry:
            try:
                kernel.strict_json_load(path)
                ok = False
                observed = "ACCEPTED"
            except kernel.ParserRefusal as exc:
                observed = str(exc)
                ok = entry["expected_parser_refusal"] in observed
        else:
            document = kernel.strict_json_load(path)
            bundle, _ = kernel.resolve_document(document)
            observed = bundle["resolution"]["state"]
            ok = observed == entry["expected_state"] and bundle["resolution"]["reason_code"] == entry["expected_reason_code"]
            if entry.get("blockers"):
                ok = ok and bundle["resolution"]["blockers"] == entry["blockers"]
        ok = ok and digest_ok
        passed = passed and ok
        cases.append({"case_id": entry["case_id"], "observed": observed, "input_digest": actual_digest, "pass": ok})
    return passed, cases


def verify_falsification():
    manifest = json.loads((ROOT / "falsification" / "ORL_AI_Falsification_Corpus_Manifest_v5_0_0.json").read_text(encoding="utf-8"))
    cases = []
    passed = True
    for entry in manifest["entries"]:
        value = json.loads((ROOT / entry["path"]).read_text(encoding="utf-8"))
        if entry["case_id"].startswith("bundle-"):
            ok = not kernel.verify_bundle(value)[0]
        else:
            ok = not capsule.verify_capsule(value)[0]
        passed = passed and ok
        cases.append({"case_id": entry["case_id"], "pass": ok})
    return passed, cases


def verify_privacy_boundary():
    receipt_path = ROOT / "examples" / "ORL_AI_resolved-consensus_Public_Receipt_v5_0_0.json"
    text = receipt_path.read_text(encoding="utf-8")
    forbidden = ["model-primary", "model-review", "rule-checker", "e-format", "e-review", "e-policy", "obs-model", "obs-review", "obs-rule"]
    return not any(value in text for value in forbidden), forbidden


def verify_identity_separation():
    first = json.loads((ROOT / "examples" / "ORL_AI_resolved-consensus_Bundle_v5_0_0.json").read_text(encoding="utf-8"))
    second = json.loads((ROOT / "examples" / "ORL_AI_resolved-permuted-order_Bundle_v5_0_0.json").read_text(encoding="utf-8"))
    same_resolution = first["identities"]["decision_resolution_id"] == second["identities"]["decision_resolution_id"]
    same_normalized = first["commitments"]["normalized_input_commitment"] == second["commitments"]["normalized_input_commitment"]
    distinct_submitted = first["commitments"]["submitted_input_commitment"] != second["commitments"]["submitted_input_commitment"]
    distinct_bundle = first["identities"]["private_bundle_id"] != second["identities"]["private_bundle_id"]
    return same_resolution and same_normalized and distinct_submitted and distinct_bundle, {
        "same_resolution_identity": same_resolution,
        "same_normalized_commitment": same_normalized,
        "distinct_submission_commitment": distinct_submitted,
        "distinct_private_bundle_identity": distinct_bundle,
    }


def relay_stress_document():
    document = kernel.example_document("relay-heavy-witness")
    document["sources"] = [
        {"source_id":"model-primary","source_family":"family-alpha","source_class":"MODEL"},
        {"source_id":"model-review","source_family":"family-alpha","source_class":"MODEL_REVIEW"},
        {"source_id":"rule-checker","source_family":"family-alpha","source_class":"RULE_CHECK"},
        {"source_id":"tool-family-beta","source_family":"family-beta","source_class":"TOOL_CHECK"},
        {"source_id":"human-family-gamma","source_family":"family-gamma","source_class":"HUMAN_REVIEW"},
    ]
    document["evidence"] = [
        {"evidence_id":"e-model","kind":"DECLARED_FACT","digest":kernel._digest("relay-heavy:model")},
        {"evidence_id":"e-review","kind":"REVIEW_RESULT","digest":kernel._digest("relay-heavy:review")},
        {"evidence_id":"e-rule","kind":"RULE_RESULT","digest":kernel._digest("relay-heavy:rule")},
        {"evidence_id":"e-tool","kind":"RULE_RESULT","digest":kernel._digest("relay-heavy:tool")},
        {"evidence_id":"e-human","kind":"REVIEW_RESULT","digest":kernel._digest("relay-heavy:human")},
    ]
    observations = [{"observation_id":"obs-000-model","source_id":"model-primary","candidate_id":"QUEUE_ALPHA","stance":"SUPPORT","evidence_ids":["e-model"]}]
    for index in range(1, 252):
        observations.append({"observation_id":"obs-" + str(index).zfill(3) + "-relay","source_id":"model-primary","candidate_id":"QUEUE_ALPHA","stance":"SUPPORT","evidence_ids":["e-model"]})
    observations.extend([
        {"observation_id":"obs-252-review","source_id":"model-review","candidate_id":"QUEUE_ALPHA","stance":"SUPPORT","evidence_ids":["e-review"]},
        {"observation_id":"obs-253-rule","source_id":"rule-checker","candidate_id":"QUEUE_ALPHA","stance":"SUPPORT","evidence_ids":["e-rule"]},
        {"observation_id":"obs-254-tool","source_id":"tool-family-beta","candidate_id":"QUEUE_ALPHA","stance":"SUPPORT","evidence_ids":["e-tool"]},
        {"observation_id":"obs-255-human","source_id":"human-family-gamma","candidate_id":"QUEUE_ALPHA","stance":"SUPPORT","evidence_ids":["e-human"]},
    ])
    document["observations"] = observations
    document["boundary"] = {
        "expected_observation_ids":[item["observation_id"] for item in observations],
        "expected_evidence_ids":[item["evidence_id"] for item in document["evidence"]],
    }
    return document


def verify_bounded_witness_construction():
    document = relay_stress_document()
    expected_witness = ["obs-000-model","obs-252-review","obs-253-rule","obs-254-tool","obs-255-human"]
    reference_bundle, reference_receipt = kernel.resolve_document(document)
    independent_bundle, independent_receipt = independent.reconstruct(document)
    reference_ok = reference_bundle["resolution"]["state"] == "RESOLVED" and reference_bundle["resolution"]["witness_observation_ids"] == expected_witness
    independent_ok = canonical(reference_bundle) == canonical(independent_bundle) and canonical(reference_receipt) == canonical(independent_receipt)
    with tempfile.TemporaryDirectory(prefix="orl_ai_witness_") as temporary:
        temporary_path = Path(temporary)
        input_path = temporary_path / "input.json"
        bundle_path = temporary_path / "bundle.json"
        receipt_path = temporary_path / "receipt.json"
        input_path.write_bytes(canonical(document))
        completed = subprocess.run([
            "node", str(ROOT / "demo" / "ORL_AI_Browser_Resolver_v5_0_0.js"),
            "--resolve", str(input_path), "--output", str(bundle_path), "--receipt-output", str(receipt_path),
        ], cwd=ROOT, capture_output=True, text=True)
        javascript_ok = completed.returncode == 0 and bundle_path.is_file() and receipt_path.is_file() and bundle_path.read_bytes() == canonical(reference_bundle) and receipt_path.read_bytes() == canonical(reference_receipt)
    return reference_ok and independent_ok and javascript_ok, {
        "observations":len(document["observations"]),
        "distinct_sources":len(document["sources"]),
        "witness_size":len(reference_bundle["resolution"]["witness_observation_ids"]),
        "reference":reference_ok,
        "independent":independent_ok,
        "javascript":javascript_ok,
    }


def verify_resource_and_text_controls():
    base = kernel.example_document("resource-check")
    oversized = json.loads(json.dumps(base))
    oversized["sources"] = []
    for index in range(kernel.MAX_SOURCES + 1):
        oversized["sources"].append({"source_id":"s" + str(index),"source_family":"f" + str(index),"source_class":"MODEL"})
    bundle, _ = kernel.resolve_document(oversized)
    resource_ok = bundle["resolution"]["state"] == "REFUSED" and any("RESOURCE_SOURCE_LIMIT" in item for item in bundle["resolution"]["blockers"])
    control = json.loads(json.dumps(base))
    control["context"]["context_id"] = "bad\rcontext"
    control_bundle, _ = kernel.resolve_document(control)
    text_ok = control_bundle["resolution"]["state"] == "REFUSED" and any("CARRIAGE_RETURN" in item for item in control_bundle["resolution"]["blockers"])
    return resource_ok and text_ok, {"resource_limit":resource_ok,"text_profile":text_ok}


def run_all():
    independent_pass, independent_receipt = independent.verify_corpus(ROOT / "corpus" / "ORL_AI_Frozen_Corpus_Manifest_v5_0_0.json", True)
    hostile_pass, hostile_cases = verify_hostile()
    falsification_pass, falsification_cases = verify_falsification()
    privacy_pass, forbidden = verify_privacy_boundary()
    identity_pass, identity_detail = verify_identity_separation()
    controls_pass, controls_detail = verify_resource_and_text_controls()
    witness_pass, witness_detail = verify_bounded_witness_construction()
    checks = {
        "independent_corpus": independent_pass,
        "hostile_corpus": hostile_pass,
        "falsification_corpus": falsification_pass,
        "public_receipt_boundary": privacy_pass,
        "identity_separation": identity_pass,
        "resource_and_text_controls": controls_pass,
        "bounded_witness_construction": witness_pass,
    }
    passed = all(checks.values())
    receipt = {
        "schema":"ORL-AI-ASSURANCE-RECEIPT-5.0.0",
        "project":"ORL-AI",
        "version":"5.0.0",
        "checks":checks,
        "independent_cases":independent_receipt["cases"],
        "hostile_cases":hostile_cases,
        "falsification_cases":falsification_cases,
        "receipt_forbidden_identifiers_tested":forbidden,
        "identity_detail":identity_detail,
        "control_detail":controls_detail,
        "witness_detail":witness_detail,
        "pass":passed,
    }
    return passed, receipt


def main():
    parser = argparse.ArgumentParser(description="Run ORL-AI assurance and falsification checks")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.print_help()
        return 0
    passed, receipt = run_all()
    for name, status in receipt["checks"].items():
        print(("PASS" if status else "FAIL") + "  " + name)
    print("HOSTILE " + str(sum(1 for item in receipt["hostile_cases"] if item["pass"])) + "/" + str(len(receipt["hostile_cases"])))
    print("FALSIFICATION " + str(sum(1 for item in receipt["falsification_cases"] if item["pass"])) + "/" + str(len(receipt["falsification_cases"])))
    if args.write_report:
        (ROOT / "VERIFY" / "ORL_AI_Assurance_Receipt_v5_0_0.json").write_bytes(canonical(receipt))
        lines = [
            "ORL-AI v5.0.0 Assurance Verification",
            "",
            *[("PASS" if status else "FAIL") + "  " + name for name, status in receipt["checks"].items()],
            "",
            "Hostile cases: " + str(sum(1 for item in receipt["hostile_cases"] if item["pass"])) + "/" + str(len(receipt["hostile_cases"])),
            "Falsification cases: " + str(sum(1 for item in receipt["falsification_cases"] if item["pass"])) + "/" + str(len(receipt["falsification_cases"])),
            "Overall: " + ("PASS" if passed else "FAIL"),
        ]
        report_payload = ("\n".join(lines) + "\n").encode("utf-8")
        (ROOT / "VERIFY" / "ORL_AI_Assurance_Verification_Report_v5_0_0.txt").write_bytes(report_payload)
    print("ASSURANCE VERIFY: " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
