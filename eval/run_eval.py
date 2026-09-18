import json
from collections import Counter
from pathlib import Path


EXPECTED_COUNTS = {
    "single_concept": 5,
    "ambiguous": 5,
    "insufficient_evidence": 5,
    "prerequisite_order": 5,
}


def evaluate_case(case):
    checks = {
        "verdict_present": case.get("verdict") in {"accept", "reject"},
        "concept_mapping": case.get("proposed_concept") == case.get("correct_concept")
        or case.get("verdict") == "reject",
        "source_pages": case.get("source_pages") == case.get("expected_source_pages")
        or case.get("verdict") == "reject",
        "material_present": bool(str(case.get("material", "")).strip())
        or case.get("verdict") == "reject",
    }
    if case.get("category") == "prerequisite_order":
        checks["prerequisite_order"] = (
            case.get("proposed_order") == case.get("expected_order")
        )
    return all(checks.values()), checks


def main():
    dataset_path = Path(__file__).with_name("golden_set.json")
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = dataset.get("cases", [])
    counts = Counter(case.get("category") for case in cases)
    assert len(cases) >= 20, "Golden set must contain at least 20 cases"
    assert dict(counts) == EXPECTED_COUNTS, f"Unexpected category counts: {counts}"

    results = []
    for case in cases:
        passed, checks = evaluate_case(case)
        results.append({"id": case["id"], "passed": passed, "checks": checks})

    passed_count = sum(result["passed"] for result in results)
    report = {
        "total": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "pass_rate": passed_count / len(results),
        "results": results,
    }
    report_path = Path(__file__).with_name("latest_results.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if passed_count == len(results) else 1)


if __name__ == "__main__":
    main()
