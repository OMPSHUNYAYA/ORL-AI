#!/usr/bin/env python3

import argparse
import copy
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL_PATH = ROOT / "demo" / "ORL_AI_Reference_Kernel_v5_0_0.py"
spec = importlib.util.spec_from_file_location("orl_ai_reference", KERNEL_PATH)
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)


def canonical(value):
    return k.canonical_json_bytes(value)


def shuffled(rng, values):
    result = list(values)
    rng.shuffle(result)
    return result


def run(seed, case_count):
    rng = random.Random(seed)
    results = []
    passed = True
    for index in range(case_count):
        mode = index % 8
        name = [
            "permutation-invariance", "relay-multiplicity", "family-collapse", "opposition-block", "prohibition-precedence", "missing-boundary-item", "minority-support", "unsupported-field-refusal"
        ][mode]
        document = k.example_document("property-" + str(index))
        base_bundle, _ = k.resolve_document(copy.deepcopy(document))
        expected = None
        observed = None
        detail = None

        if mode == 0:
            candidate = copy.deepcopy(document)
            candidate["sources"] = shuffled(rng, candidate["sources"])
            candidate["evidence"] = shuffled(rng, candidate["evidence"])
            candidate["observations"] = shuffled(rng, candidate["observations"])
            candidate["context"]["candidate_ids"] = shuffled(rng, candidate["context"]["candidate_ids"])
            candidate["boundary"]["expected_observation_ids"] = shuffled(rng, candidate["boundary"]["expected_observation_ids"])
            candidate["boundary"]["expected_evidence_ids"] = shuffled(rng, candidate["boundary"]["expected_evidence_ids"])
            bundle, _ = k.resolve_document(candidate)
            expected = base_bundle["identities"]["decision_resolution_id"]
            observed = bundle["identities"]["decision_resolution_id"]
            ok = observed == expected and bundle["commitments"]["normalized_input_commitment"] == base_bundle["commitments"]["normalized_input_commitment"]
            detail = "resolution identity and normalized structure remain equal"
        elif mode == 1:
            candidate = copy.deepcopy(document)
            relay_count = rng.randint(1, 5)
            for relay_index in range(relay_count):
                observation_id = "obs-relay-" + str(relay_index)
                candidate["observations"].append({"observation_id":observation_id,"source_id":"model-primary","candidate_id":"QUEUE_ALPHA","stance":"SUPPORT","evidence_ids":["e-format"]})
                candidate["boundary"]["expected_observation_ids"].append(observation_id)
            bundle, _ = k.resolve_document(candidate)
            expected = "RESOLVED with three distinct support sources"
            observed = bundle["resolution"]["state"] + " with " + str(bundle["resolution"]["candidate_metrics"]["QUEUE_ALPHA"]["support_source_count"]) + " distinct support sources"
            ok = bundle["resolution"]["state"] == "RESOLVED" and bundle["resolution"]["candidate_metrics"]["QUEUE_ALPHA"]["support_source_count"] == 3
            detail = "multiple observations from one source do not create new source participation"
        elif mode == 2:
            candidate = copy.deepcopy(document)
            for source in candidate["sources"]:
                source["source_family"] = "shared-family"
            bundle, _ = k.resolve_document(candidate)
            expected = "INCOMPLETE"
            observed = bundle["resolution"]["state"]
            ok = observed == expected
            detail = "declared family diversity is required"
        elif mode == 3:
            candidate = copy.deepcopy(document)
            candidate["sources"].append({"source_id":"tool-opposition","source_family":"family-delta","source_class":"TOOL_CHECK"})
            candidate["observations"].append({"observation_id":"obs-opposition","source_id":"tool-opposition","candidate_id":"QUEUE_ALPHA","stance":"OPPOSE","evidence_ids":["e-policy"]})
            candidate["boundary"]["expected_observation_ids"].append("obs-opposition")
            bundle, _ = k.resolve_document(candidate)
            expected = "ABSTAIN"
            observed = bundle["resolution"]["state"]
            ok = observed == expected
            detail = "opposition blocks admission"
        elif mode == 4:
            candidate = copy.deepcopy(document)
            candidate["constraints"] = [{"constraint_id":"deny-alpha","kind":"FORBID_CANDIDATE","candidate_id":"QUEUE_ALPHA","active":True}]
            bundle, _ = k.resolve_document(candidate)
            expected = "DENIED"
            observed = bundle["resolution"]["state"]
            ok = observed == expected
            detail = "active prohibition precedes candidate admission"
        elif mode == 5:
            candidate = copy.deepcopy(document)
            removed = rng.choice(candidate["observations"])
            candidate["observations"] = [item for item in candidate["observations"] if item["observation_id"] != removed["observation_id"]]
            bundle, _ = k.resolve_document(candidate)
            expected = "INCOMPLETE"
            observed = bundle["resolution"]["state"]
            ok = observed == expected and bundle["resolution"]["reason_code"] == "BOUNDARY_INCOMPLETE"
            detail = "missing expected observation prevents admission"
        elif mode == 6:
            candidate = copy.deepcopy(document)
            candidate["observations"][0]["candidate_id"] = "QUEUE_BETA"
            bundle, _ = k.resolve_document(candidate)
            expected = "ABSTAIN"
            observed = bundle["resolution"]["state"]
            ok = observed == expected
            detail = "competing partial support does not force a winner"
        else:
            candidate = copy.deepcopy(document)
            candidate["unsupported"] = "value"
            bundle, _ = k.resolve_document(candidate)
            expected = "REFUSED"
            observed = bundle["resolution"]["state"]
            ok = observed == expected
            detail = "unsupported structure is refused"

        passed = passed and ok
        results.append({"case_index":index,"property":name,"expected":expected,"observed":observed,"detail":detail,"pass":ok})

    receipt = {
        "schema":"ORL-AI-SEEDED-PROPERTY-RECEIPT-5.0.0",
        "project":"ORL-AI",
        "version":"5.0.0",
        "seed":seed,
        "case_count":case_count,
        "passed_count":sum(1 for item in results if item["pass"]),
        "properties":sorted({item["property"] for item in results}),
        "cases":results,
        "pass":passed,
    }
    return passed, receipt


def main():
    parser = argparse.ArgumentParser(description="Run seeded ORL-AI property checks")
    parser.add_argument("--seed", type=int, default=20260801)
    parser.add_argument("--cases", type=int, default=64)
    parser.add_argument("--receipt-output", type=Path)
    args = parser.parse_args()
    passed, receipt = run(args.seed, args.cases)
    if args.receipt_output:
        args.receipt_output.write_bytes(canonical(receipt))
    for name in receipt["properties"]:
        total = sum(1 for item in receipt["cases"] if item["property"] == name)
        count = sum(1 for item in receipt["cases"] if item["property"] == name and item["pass"])
        print(("PASS" if count == total else "FAIL") + "  " + name + " " + str(count) + "/" + str(total))
    print("TOTAL " + str(receipt["passed_count"]) + "/" + str(receipt["case_count"]) + " PASS")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
