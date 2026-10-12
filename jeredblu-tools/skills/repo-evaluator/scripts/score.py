#!/usr/bin/env python3
"""Validate an evidence ledger and calculate rubric points. No model or network calls.

Inputs are judgments, not proof. This calculator cannot authenticate their evidence.
Exit 0: valid ledger (even an adverse/incomplete verdict); 2: invalid input.
"""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

RUBRIC = Path(__file__).resolve().parent.parent / "references" / "rubric-v1.json"
STATES = {"pass", "concern", "fail", "unknown", "not_applicable"}
SEVERITIES = ("none", "low", "medium", "high", "critical")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def template(rubric):
    return {
        "rubric_version": rubric["rubric_version"],
        "target": {"repository": "OWNER/REPO", "commit": "REPLACE_WITH_40_HEX_COMMIT",
                   "install_method": "source", "install_description": "Describe the exact path/version"},
        "checks": [{"id": c["id"], "status": "unknown", "severity": "none",
                    "reason": "Not reviewed yet", "evidence": []} for c in rubric["checks"]],
    }


def evaluate(ledger, rubric):
    require(isinstance(ledger, dict), "ledger must be an object")
    require(ledger.get("rubric_version") == rubric["rubric_version"], "rubric version mismatch")
    target = ledger.get("target")
    require(isinstance(target, dict), "target must be an object")
    require(nonempty(target.get("repository")), "target.repository is required")
    require(isinstance(target.get("commit"), str) and
            re.fullmatch(r"[0-9a-fA-F]{40}", target["commit"]), "target.commit must be a full 40-hex revision")
    require(target.get("install_method") in {"source", "release", "package_manager", "script", "other"},
            "invalid install_method")
    require(nonempty(target.get("install_description")), "install_description is required")
    submitted = ledger.get("checks")
    require(isinstance(submitted, list), "checks must be an array")
    specs = {c["id"]: c for c in rubric["checks"]}
    by_id = {}
    for item in submitted:
        require(isinstance(item, dict), "each check must be an object")
        ident = item.get("id")
        require(isinstance(ident, str) and ident in specs, "unrecognized check id: " + str(ident))
        require(ident not in by_id, "duplicate check: " + ident)
        require(not set(item) - {"id", "status", "severity", "reason", "evidence"},
                ident + ": unexpected field (points and weights cannot be overridden)")
        status, severity = item.get("status"), item.get("severity")
        require(status in STATES, ident + ": invalid status")
        require(severity in SEVERITIES, ident + ": invalid severity")
        require(nonempty(item.get("reason")), ident + ": reason required")
        evidence = item.get("evidence")
        require(isinstance(evidence, list), ident + ": evidence must be an array")
        if status != "unknown":
            require(bool(evidence), ident + ": resolved checks need evidence")
        for ev in evidence:
            require(isinstance(ev, dict) and nonempty(ev.get("source")) and nonempty(ev.get("detail")),
                    ident + ": each evidence item needs source and detail")
            if "line_start" in ev or "line_end" in ev:
                start, end = ev.get("line_start"), ev.get("line_end", ev.get("line_start"))
                require(type(start) is int and type(end) is int and 1 <= start <= end,
                        ident + ": invalid evidence line range")
        if status in {"pass", "unknown", "not_applicable"}:
            require(severity == "none", ident + ": this status requires severity=none")
        elif status == "concern":
            require(severity in {"low", "medium"}, ident + ": concern requires low/medium severity")
        else:
            require(severity in {"medium", "high", "critical"}, ident + ": fail requires medium/high/critical severity")
            require(SEVERITIES.index(severity) >= SEVERITIES.index(specs[ident]["fail_min_severity"]),
                    ident + ": failure severity is below the rubric floor")
        if status == "not_applicable":
            require(specs[ident]["allow_not_applicable"] and target["install_method"] == "source",
                    ident + ": only the artifact check for a source-only install can be N/A")
        by_id[ident] = item

    rows = []
    for spec in rubric["checks"]:
        item = by_id.get(spec["id"], {"id": spec["id"], "status": "unknown", "severity": "none",
                                     "reason": "Missing from submitted ledger", "evidence": []})
        status = item["status"]
        weight = Decimal(spec["weight"])
        credit = Decimal(str(rubric["status_credit"].get(status, 0)))
        rows.append({**item, "dimension": spec["dimension"], "title": spec["title"],
                     "weight": int(weight), "earned_points": float(weight * credit),
                     "possible_points": 0 if status == "not_applicable" else int(weight)})

    applicable = sum(r["possible_points"] for r in rows)
    earned = sum(Decimal(str(r["earned_points"])) for r in rows)
    unknown = sum(r["possible_points"] for r in rows if r["status"] == "unknown")
    worst = max((r["severity"] for r in rows), key=SEVERITIES.index)
    cap = rubric["severity_caps"][worst]
    def percent(n):
        return Decimal(n) * 100 / Decimal(applicable)
    def rounded(n):
        return float(n.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    low, high = percent(earned), percent(earned + unknown)
    capped_low, capped_high = min(low, Decimal(cap)), min(high, Decimal(cap))
    # Decide using unrounded values. A display round-up must never upgrade a verdict.
    if worst == "critical":
        verdict = "DO NOT USE"
    elif worst == "high":
        verdict = "NOT RECOMMENDED"
    elif unknown:
        verdict = "INCOMPLETE"
    elif capped_low < 30:
        verdict = "DO NOT USE"
    elif capped_low < 50:
        verdict = "NOT RECOMMENDED"
    elif capped_low < 85:
        verdict = "USE WITH CAUTION"
    else:
        verdict = "NO MAJOR RISKS IDENTIFIED"
    dimensions = {}
    for dim, label in rubric["dimensions"].items():
        subset = [r for r in rows if r["dimension"] == dim]
        dimensions[dim] = {"label": label,
                           "earned_points": sum(r["earned_points"] for r in subset),
                           "possible_points": sum(r["possible_points"] for r in subset),
                           "unknown_points": sum(r["possible_points"] for r in subset if r["status"] == "unknown")}
    return {"rubric_version": rubric["rubric_version"], "target": target, "verdict": verdict,
            "score": None if unknown else rounded(capped_low),
            "score_range": [rounded(capped_low), rounded(capped_high)],
            "raw_score_range": [rounded(low), rounded(high)],
            "earned_points": float(earned), "applicable_points": applicable,
            "coverage_percent": rounded(percent(applicable - unknown)),
            "coverage_definition": "Weighted rubric checks assessed; NOT percent of source code read",
            "status_counts": dict(Counter(r["status"] for r in rows)),
            "severity_cap": {"severity": worst, "maximum": cap,
                             "trigger_checks": [r["id"] for r in rows if r["severity"] == worst] if cap < 100 else []},
            "dimensions": dimensions, "checks": rows,
            "limitations": ["Heuristic rubric score, not a safety probability or certification.",
                            "Arithmetic is deterministic; evidence and classifications require review.",
                            "A complete rubric is not an exhaustive security audit."]}


def markdown(result):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")
    score = result["score"]
    summary = f"{score}/100" if score is not None else f"withheld; possible range {result['score_range'][0]}–{result['score_range'][1]}/100"
    lines = [f"# {result['verdict']}", "", f"Heuristic rubric score: **{summary}**.",
             f"Rubric {result['rubric_version']}; weighted check coverage: {result['coverage_percent']}% (not source-code coverage).",
             f"Revision: `{result['target']['commit']}`. Install path: {cell(result['target']['install_description'])}.",
             f"Earned: {result['earned_points']} / {result['applicable_points']} applicable points.",
             f"Uncapped rubric range: {result['raw_score_range'][0]}–{result['raw_score_range'][1]}/100 (not a statistical confidence interval).",
             f"Severity cap: {result['severity_cap']['maximum']} ({result['severity_cap']['severity']}).", "",
             "| Dimension | Earned | Applicable | Unknown points |", "|---|---:|---:|---:|"]
    for dimension in result["dimensions"].values():
        lines.append("| " + " | ".join(map(cell, [dimension["label"], dimension["earned_points"],
                                                  dimension["possible_points"], dimension["unknown_points"]])) + " |")
    lines += ["",
             "| Check | Result | Severity | Points | Reason and evidence |", "|---|---|---|---:|---|"]
    for row in result["checks"]:
        def evidence_label(ev):
            location = ev["source"]
            if "line_start" in ev:
                location += f":{ev['line_start']}"
                if "line_end" in ev:
                    location += f"–{ev['line_end']}"
            return location + ": " + ev["detail"]
        evidence = "; ".join(evidence_label(ev) for ev in row["evidence"])
        points = "unknown" if row["status"] == "unknown" else f"{row['earned_points']}/{row['possible_points']}"
        lines.append("| " + " | ".join(map(cell, [row["id"], row["status"], row["severity"], points,
                                                     row["reason"] + (" — " + evidence if evidence else "")])) + " |")
    return "\n".join(lines + ["", *["- " + x for x in result["limitations"]], ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", nargs="?")
    parser.add_argument("--template", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    try:
        rubric = load_json(RUBRIC)
        if args.template:
            print(json.dumps(template(rubric), indent=2))
        else:
            require(bool(args.ledger), "provide a ledger or --template")
            result = evaluate(load_json(args.ledger), rubric)
            print(markdown(result) if args.markdown else json.dumps(result, indent=2))
    except (ValueError, OSError, TypeError) as exc:
        print("Invalid evaluation: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
