"""Small-summary-only BCAI state arithmetic; no raw data, fitting, or resampling."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import platform
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def file_record(path):
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_rows(season, weights, years):
    lookup = {(int(r["year"]), r["count"]): r for r in season}
    rows = []
    for year in years:
        base_n = int(lookup[year, "0-0"]["N"])
        for count in COUNTS:
            b, s = map(int, count.split("-"))
            current = lookup[year, count]
            v = float(current["value"])
            ball = lookup.get((year, f"{b+1}-{s}")) if b < 3 else None
            strike = lookup.get((year, f"{b}-{s+1}")) if s < 2 else None
            vb = float(ball["value"]) if ball else float(weights[str(year)]["BB"])
            vs = float(strike["value"]) if strike else 0.0
            vf = v if s == 2 else vs
            rows.append({
                "year": year, "count": count, "current_V_W": v,
                "N_reached_PA": int(current["N"]), "N_eligible_PA": base_n,
                "PA_reach_fraction": int(current["N"])/base_n,
                "next_ball_state": f"{b+1}-{s}" if b < 3 else "BB_terminal",
                "next_ball_W": vb, "next_ball_state_N_PA": int(ball["N"]) if ball else None,
                "next_strike_state": f"{b}-{s+1}" if s < 2 else "K_terminal",
                "next_strike_W": vs, "next_strike_state_N_PA": int(strike["N"]) if strike else None,
                "delta_ball_W": vb-v, "delta_strike_W": vs-v,
                "ball_minus_strike_W": vb-vs,
                "ordinary_foul_next_W": vf, "ordinary_foul_delta_W": vf-v,
                "unit": "W", "uncertainty_status": "미산출",
                "event_frequency_status": "미산출; PA 도달률과 별도"
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"bcai_state_delta__mlb_2024_2025__\d{8}__r\d{2,}", args.run_id):
        raise ValueError("실행 ID 형식이 맞지 않습니다.")
    out = ROOT / "columns/001-ball-count/analysis/runs" / args.run_id
    if out.exists():
        raise FileExistsError(f"완료/기존 실행을 보존합니다. 새 ID를 사용하세요: {out}")
    spec_path = HERE / "specification.yaml"
    spec = read_json(spec_path)
    source = ROOT / spec["source_directory"]
    paths = [source / "manifest.json", source / spec["source_season_table"],
             source / spec["source_count_table"], source / spec["source_event_table"],
             ROOT / spec["source_definition"], ROOT / spec["source_calculation"]]
    manifest, season, pooled, events = read_json(paths[0]), read_csv(paths[1]), read_csv(paths[2]), read_csv(paths[3])
    obs = read_json(paths[4])
    weights = manifest["parameters"]["weights"]
    rows = make_rows(season, weights, spec["years"])
    checks = []

    def check(name, passed, detail=None):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    expected = {(y, c) for y in spec["years"] for c in COUNTS}
    check("시즌별 12카운트 및 중복 없음", len(season) == 24 and
          {(int(r["year"]), r["count"]) for r in season} == expected)
    recorded = {r["path"]: r["sha256"] for r in manifest["artifacts"]}
    for path in paths[1:4]:
        rec = file_record(path)
        check("기존 manifest 해시 일치: " + path.name, rec["sha256"] == recorded[rec["path"]])
    event_map = {event: kind for kind, labels in obs["result_classification"].items() for event in labels}
    for year in spec["years"]:
        selected = [r for r in events if int(r["game_year"]) == year and r["exclusion"] == "included"]
        denom = sum(int(r["PA"]) for r in selected)
        observed0 = next(r for r in rows if r["year"] == year and r["count"] == "0-0")
        mean = sum(int(r["PA"]) * float(weights[str(year)].get(event_map[r["event"]], 0))
                   for r in selected) / denom
        check(f"{year} 0-0 분모=기존 적격 event 합", denom == observed0["N_reached_PA"], denom)
        check(f"{year} 0-0 W 독립 가중합", abs(mean-observed0["current_V_W"]) < 1e-12,
              {"recalculated_W": mean, "absolute_error": abs(mean-observed0["current_V_W"])})
        check(f"{year} manifest 기준 W 일치", abs(mean-manifest["parameters"]["baseline_value"][str(year)]) < 1e-12)
    for count in COUNTS:
        n = sum(r["N_reached_PA"] for r in rows if r["count"] == count)
        original = next(r for r in pooled if r["count"] == count)
        check(f"{count} 시즌 분모 합=기존 OBS 분모", n == int(original["N_PA"]), n)
    for row in rows:
        b, s = map(int, row["count"].split("-"))
        key = f"{row['year']} {row['count']}"
        check(key + " 유한값·도달률", all(math.isfinite(row[k]) for k in
              ["current_V_W", "next_ball_W", "next_strike_W", "delta_ball_W", "delta_strike_W", "ball_minus_strike_W"])
              and 0 < row["PA_reach_fraction"] <= 1)
        check(key + " 차이 항등식", abs(row["delta_ball_W"]-row["delta_strike_W"]-row["ball_minus_strike_W"]) < 1e-12)
        if b == 3:
            check(key + " 볼넷 종료", row["next_ball_W"] == weights[str(row["year"])]["BB"] and row["next_ball_state_N_PA"] is None)
        if s == 2:
            check(key + " 삼진 종료·일반 파울 자기유지", row["next_strike_W"] == 0 and row["ordinary_foul_delta_W"] == 0 and row["next_strike_state_N_PA"] is None)
    if not all(c["passed"] for c in checks):
        raise AssertionError(json.dumps([c for c in checks if not c["passed"]], ensure_ascii=False))

    artifacts = out / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=False)
    with (artifacts / "state_delta_2024_2025.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_json(artifacts / "quick_checks.json", {"status": "PASS", "checks_n": len(checks), "checks": checks,
               "scope": "저장 소형 요약·기존 정의의 산술 일치 확인. 원자료 재감사·불확실성·인과 검증 아님"})
    write_json(artifacts / "exception_handling.json", spec["exceptions"])
    report = ["# BCAI 볼·스트라이크 상태 평균 차이", "", "2026-09-17 · BCAI-STATE-DELTA-v0.1.0 · EXPERIMENTAL", "",
        "기존 시즌별 원 W 요약 24행으로 새 산술 차이를 계산했다. 신규 학습·부트스트랩·원자료 처리는 없다. 기존 BCAI의 VALIDATED 상태를 이 모듈에 전용하지 않는다.", "",
        "V는 그 카운트에 도달한 유효 PA의 최종 W 평균이다. 각 카운트는 PA마다 한 번 세며 같은 PA가 여러 카운트에 포함될 수 있다. 도달률은 시즌 유효 PA 대비 비율이며 실제 볼·스트라이크 사건 발생률이나 투구 비율이 아니다. 다음 상태 평균의 분모는 해당 다음 카운트 전체 도달 집단이므로 현재 상태에서 실제로 전이한 집단과 다르다.", "",
        "볼 뒤 값은 3볼에서 BB 종료 가중치(2024 0.689, 2025 0.691), 스트라이크 뒤 값은 2스트라이크에서 일반 삼진 종료 W=0이다. 이 종료 값은 표본평균이 아니므로 해당 분모는 CSV에서 빈칸으로 둔다. 일반 2스트라이크 파울은 현재 카운트를 유지해 상태 차이가 0이다. 번트·파울팁은 이 일반 파울 규칙에 포함하지 않는다.", "",
        "양수 차이는 타자 공격가치 증가 방향이다. 각 상태를 구성하는 선수·경로가 다르므로 볼이나 스트라이크 하나의 인과 효과가 아니다. W는 득점·확률·상대지수와 다르며 시즌 가중치 차이도 남는다. 이 차이를 기존 최종 PA W에 다시 더하지 않는다. 새 구간은 계산하지 않았으며 기존 상대지수 구간을 옮겨 쓰지 않았다.", ""]
    for year in spec["years"]:
        report += [f"## {year}년", "", "| 카운트 | 도달 PA | 도달률 | 현재 V | 볼 뒤 V | 스트라이크 뒤 V | 볼 차이 | 스트라이크 차이 | 볼−스트라이크 |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for row in (r for r in rows if r["year"] == year):
            report.append(f"| {row['count']} | {row['N_reached_PA']:,} | {row['PA_reach_fraction']:.2%} | " + " | ".join(f"{row[k]:.6f}" for k in ["current_V_W", "next_ball_W", "next_strike_W", "delta_ball_W", "delta_strike_W", "ball_minus_strike_W"]) + " |")
        report.append("")
    report += ["## 예외와 미실행", ""] + [f"- **{r['case']}**: {r['handling']}" for r in spec["exceptions"]]
    report += ["", "실제 투구별 사건 빈도와 해당 사건 뒤 최종 W 표는 필요한 투구 행 연결을 이번 빠른 작업에서 수행하지 않아 미산출했다. 현재 표로 이를 대신하지 않는다. 사건별 작업에는 실제 투구·PA 키, 최종 W, 이벤트 분류·모순 점검, 중복 파울과 자동 판정의 별도 분모가 필요하다.", "",
        f"빠른 확인 {len(checks)}항목 PASS: 기존 요약 해시, 24행 카운트 완전성, 시즌·통합 도달 분모, 0-0의 독립 event 가중합, 차이 항등식·유한값·종료 및 파울 처리. 기존 집계 코드의 PA×count 중복 제거는 읽어 확인했으며 원자료에서 재집계하지 않았다. 추가적인 분모·선택집단 검토와 새 차이의 불확실성 평가는 미실시다.", "",
        "## 입력과 재현", ""] + [f"- `{p.relative_to(ROOT).as_posix()}`" for p in paths] + ["",
        "프로젝트 루트에서 `python -B models/bcai/state_delta/v0.1.0/run.py --run-id bcai_state_delta__mlb_2024_2025__YYYYMMDD__r02` 형태로 실제 실행일·미사용 번호를 지정한다. 기존 ID는 오류로 중단한다.", ""]
    (out / "report.md").write_text("\n".join(report), encoding="utf-8")
    write_json(out / "manifest.json", {
        "run_id": args.run_id, "model_id": spec["model_id"], "version": spec["version"],
        "model_status": "EXPERIMENTAL", "execution_status": "COMPLETED_QUICK_CHECK_ONLY",
        "executed_at": datetime.now().astimezone().isoformat(), "source_run": spec["source_run"],
        "paths_relative_to": "project_root", "input": [file_record(p) for p in paths],
        "configuration": file_record(spec_path), "code": file_record(Path(__file__).resolve()),
        "environment": {"python": platform.python_version(), "dependencies": "stdlib only"},
        "sample": {"summary_rows": len(rows), "eligible_PA_by_year": {str(y): next(r["N_eligible_PA"] for r in rows if r["year"] == y) for y in spec["years"]}},
        "uncertainty": "미산출", "full_data_execution": False, "training": False,
        "checks_status": "PASS", "checks_n": len(checks),
        "outputs": [file_record(p) for p in sorted(artifacts.glob("*"))] + [file_record(out / "report.md")]
    })
    print(json.dumps({"run_id": args.run_id, "status": "PASS", "checks": len(checks), "rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
