from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[6]
OUT = Path(__file__).resolve().parent
ATOL = 1e-10
COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]

P = {
    "formatted": ROOT / "columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/sb_reformatted.csv",
    "dev": ROOT / "columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/count_values.csv",
    "external": ROOT / "columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2023__20260914__r01/artifacts/values.csv",
    "judgment": ROOT / "columns/001-ball-count/analysis/bcap_external_20260914__r01/comparison.csv",
    "season": ROOT / "columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_season_sensitivity.csv",
    "count": ROOT / "columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_count_results.csv",
    "event": ROOT / "columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_event_audit.csv",
    "obs_manifest": ROOT / "columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/manifest.json",
    "state_spec": ROOT / "models/bcai/state_delta/v0.1.0/specification.yaml",
    "state_actual": ROOT / "columns/001-ball-count/analysis/runs/bcai_state_delta__mlb_2024_2025__20260917__r01/artifacts/state_delta_2024_2025.csv",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


checks: list[dict[str, object]] = []


def add(name: str, expected: object, actual: object, evidence: str, tolerance: object = "exact") -> None:
    if tolerance == "exact":
        passed = expected == actual
        error = None
    else:
        error = abs(float(actual) - float(expected))
        passed = error <= float(tolerance)
    checks.append({"name": name, "expected": expected, "actual": actual,
                   "tolerance": tolerance, "absolute_error": error,
                   "evidence_type": evidence, "passed": passed})


def fcheck(name: str, expected: str | float, actual: str | float, evidence: str) -> None:
    add(name, float(expected), float(actual), evidence, ATOL)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    formatted = rows(P["formatted"])
    dev = {r["count"]: r for r in rows(P["dev"]) if r["level"] == "count" and r["region"] == "ALL" and r["pitch_group"] == "ALL"}
    ext = {r["count"]: r for r in rows(P["external"]) if r["model"] == "pitch_sb" and r["region"] == "ALL" and r["population"] == "own"}
    judgments = {r["count"]: r for r in rows(P["judgment"]) if r["year"] == "2023" and r["model"] == "pitch_sb" and r["region"] == "ALL" and r["population"] == "own"}
    add("formatted row count", 24, len(formatted), "row_count")
    for period in ("2024–2025 개발", "2023 기존 재현"):
        got = sorted(r["count"] for r in formatted if r["period"] == period)
        add(f"{period}: 12 counts", sorted(COUNTS), got, "key_set")

    fm = {(r["period"], r["count"]): r for r in formatted}
    numeric_map = {"Q_B_W": "Q0", "Q_S_W": "Q1", "ci_low_W": None, "ci_high_W": None,
                   "coverage": "coverage", "ESS_B": "ESS0", "ESS_S": "ESS1"}
    int_map = {"n_all": "n_all", "n": "n", "rows_B": "rows0", "rows_S": "rows1"}
    for period, source, low, high, family_default in (
        ("2024–2025 개발", dev, "family95_low", "family95_high", 219),
        ("2023 기존 재현", ext, "adjusted95_low", "adjusted95_high", 236),
    ):
        for count in COUNTS:
            a, s = fm[(period, count)], source[count]
            for dest, src in numeric_map.items():
                src = low if dest == "ci_low_W" else high if dest == "ci_high_W" else src
                fcheck(f"{period}/{count}/{dest}", s[src], a[dest], "source_field_copy")
            fcheck(f"{period}/{count}/delta", float(s["Q1"]) - float(s["Q0"]), a["delta_S_minus_B_W"], "independent_arithmetic")
            fcheck(f"{period}/{count}/coverage arithmetic", float(s["n"]) / float(s["n_all"]), a["coverage"], "independent_arithmetic")
            add(f"{period}/{count}/rows sum", int(s["n"]), int(a["rows_B"]) + int(a["rows_S"]), "independent_arithmetic")
            for dest, src in int_map.items():
                add(f"{period}/{count}/{dest}", int(s[src]), int(a[dest]), "source_field_copy")
            expected_family = 4 if period == "2023 기존 재현" and count in {"0-2", "1-2"} else family_default
            add(f"{period}/{count}/family", expected_family, int(a["family"]), "specified_family_rule")
            add(f"{period}/{count}/support", s["support_gate"], a["support_gate"], "source_field_copy")
            expected_class = s["evidence"] if period == "2024–2025 개발" else judgments[count]["judgment_ko"]
            add(f"{period}/{count}/classification", expected_class, a["classification"], "external_judgment_copy" if period != "2024–2025 개발" else "source_field_copy")

    season = {(int(r["year"]), r["count"]): r for r in rows(P["season"])}
    count_rows = {r["count"]: r for r in rows(P["count"])}
    events = rows(P["event"])
    manifest = json.loads(P["obs_manifest"].read_text(encoding="utf-8"))
    weights = {int(y): w for y, w in manifest["parameters"]["weights"].items()}
    fields = ["year", "count", "current_V_W", "N_reached_PA", "N_eligible_PA", "PA_reach_fraction",
              "next_ball_state", "next_ball_W", "next_ball_state_N_PA", "next_strike_state", "next_strike_W",
              "next_strike_state_N_PA", "delta_ball_W", "delta_strike_W", "ball_minus_strike_W",
              "ordinary_foul_next_W", "ordinary_foul_delta_W", "unit", "uncertainty_status", "event_frequency_status"]
    reconstructed = []
    for year in (2024, 2025):
        eligible = int(season[(year, "0-0")]["N"])
        for count in COUNTS:
            b, s = map(int, count.split("-")); cur = float(season[(year, count)]["value"])
            if b < 3:
                bs = f"{b+1}-{s}"; bv = float(season[(year, bs)]["value"]); bn: object = int(season[(year, bs)]["N"])
            else:
                bs = "BB_terminal"; bv = float(weights[year]["BB"]); bn = ""
            if s < 2:
                ss = f"{b}-{s+1}"; sv = float(season[(year, ss)]["value"]); sn: object = int(season[(year, ss)]["N"])
            else:
                ss = "K_terminal"; sv = 0.0; sn = ""
            fv = cur if s == 2 else sv
            reconstructed.append(dict(zip(fields, [year, count, cur, int(season[(year, count)]["N"]), eligible,
                int(season[(year, count)]["N"]) / eligible, bs, bv, bn, ss, sv, sn, bv-cur, sv-cur, bv-sv,
                fv, fv-cur, "W", "미산출", "미산출; PA 도달률과 별도"])))
    actual_state = {(int(r["year"]), r["count"]): r for r in rows(P["state_actual"])}
    add("state row count", 24, len(actual_state), "row_count")
    numeric_state = {"current_V_W", "PA_reach_fraction", "next_ball_W", "next_strike_W", "delta_ball_W",
                     "delta_strike_W", "ball_minus_strike_W", "ordinary_foul_next_W", "ordinary_foul_delta_W"}
    integer_state = {"year", "N_reached_PA", "N_eligible_PA", "next_ball_state_N_PA", "next_strike_state_N_PA"}
    for e in reconstructed:
        a = actual_state[(e["year"], e["count"])]
        for field in fields:
            if field in numeric_state:
                fcheck(f"state/{e['year']}/{e['count']}/{field}", e[field], a[field], "independent_reconstruction")
            elif field in integer_state:
                expected = "" if e[field] == "" else int(e[field])
                actual = "" if a[field] == "" else int(a[field])
                add(f"state/{e['year']}/{e['count']}/{field}", expected, actual, "independent_reconstruction")
            else:
                add(f"state/{e['year']}/{e['count']}/{field}", str(e[field]), a[field], "independent_reconstruction")
    for count in COUNTS:
        pooled = sum(int(season[(y, count)]["N"]) for y in (2024, 2025))
        add(f"pooled N/{count}", int(count_rows[count]["N_PA"]), pooled, "independent_sum")
    event_weight = {"single": "1B", "double": "2B", "triple": "3B", "home_run": "HR", "walk": "BB", "hit_by_pitch": "HBP"}
    for year in (2024, 2025):
        numerator = sum(int(r["PA"]) * float(weights[year][event_weight[r["event"]]])
                        for r in events if int(r["game_year"]) == year and r["exclusion"] == "included" and r["event"] in event_weight)
        derived = numerator / int(season[(year, "0-0")]["N"])
        fcheck(f"0-0 W event reconstruction/{year}", season[(year, "0-0")]["value"], derived, "event_counts_times_manifest_weights")

    source_hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in P.values()}
    payload = {"status": "PASS" if all(c["passed"] for c in checks) else "FAIL",
               "summary": {"checks": len(checks), "passed": sum(bool(c["passed"]) for c in checks),
                           "failed": sum(not bool(c["passed"]) for c in checks),
                           "max_numeric_absolute_error": max((c["absolute_error"] or 0.0) for c in checks)},
               "command": "C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -B columns/001-ball-count/analysis/runs/bcap_followup_review__mlb_2024_2025__20260918__r01/csv_review/verifier.py",
               "source_sha256": source_hashes, "checks": checks}
    (OUT / "checks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [c for c in checks if not c["passed"]]
    findings = ["# 독립 CSV 산술 검토", "", f"- 결과: **{payload['status']}**", f"- 검사: {len(checks)}건 (통과 {len(checks)-len(failed)}, 실패 {len(failed)})", f"- 최대 수치 절대오차: `{payload['summary']['max_numeric_absolute_error']}`", "- 재포맷 24행과 상태 전이 24행을 원 입력에서 독립 재구성했다.", "- 학습·부트스트랩·다운로드·원자료 전면 스캔·기존 산출물 수정은 수행하지 않았다."]
    if failed:
        findings += ["", "## 불일치", *[f"- {c['name']}: expected={c['expected']!r}, actual={c['actual']!r}" for c in failed]]
    else:
        findings += ["", "실제 불일치는 발견되지 않았다."]
    (OUT / "findings.md").write_text("\n".join(findings) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
