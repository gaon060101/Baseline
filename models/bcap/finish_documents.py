"""Finalize BCAP documentation after every required run/report has completed.

Documentation/provenance only: never imports a model engine, reads row-level
data, changes frozen definitions/code/policies, fits models, or uses a network.
All prerequisites and literal source-text replacements are checked before any
writes. Existing evidence and originals are immutable; output audit/backups
must not already exist. Run once only after the parent has completed validation.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "models/bcap"
COL = ROOT / "columns/001-ball-count"
ANAL = COL / "analysis"
RUNS = ANAL / "runs"
SEAL = MODEL / "external_seal_20260909_r01.json"
REPORT = ANAL / "bcap_v010_report_20260909.md"
TABLEDIR = ANAL / "bcap_report_20260909_r01"
REVIEW = ANAL / "bcap_implementation_review_20260909"
BEHAVIOR = REVIEW / "behavior_comparison.md"
ORIGINAL = ANAL / "bcap_original_handoff_20260909"
UPDATE = ANAL / "bcap_document_update_20260909.json"
EVIDENCE = ANAL / "bcap_execution_evidence_20260909.json"
INVOCATIONS = ANAL / "bcap_execution_commands_20260909.json"
FINAL_AUDIT_DIR = ANAL / "bcap_final_validation_20260909"
FINAL_AUDIT = FINAL_AUDIT_DIR / "validation.json"
BACKUPS = ANAL / "bcap_document_backups_20260909_r01"
MARKER = "BCAP 실제 구현·평가 반영 — 2026-09-09"
RUN_DEFS = [
    ("pitch_dev", "bcap_pitch__mlb_2024_2025__20260909__r02", "COMPLETE", "development_2024_2025", "pitch"),
    ("swing_dev", "bcap_swing__mlb_2024_2025__20260909__r01", "COMPLETE", "development_2024_2025", "swing"),
    ("pitch_boot", "bcap_pitch__mlb_2024_2025__20260909__r03", "COMPLETE", "full_pipeline_game_bootstrap_stability", "pitch"),
    ("swing_boot", "bcap_swing__mlb_2024_2025__20260909__r02", "COMPLETE", "full_pipeline_game_bootstrap_stability", "swing"),
    ("pitch_2023", "bcap_pitch__mlb_2023__20260909__r01", "COMPLETE", "external_2023", "pitch"),
    ("swing_2023", "bcap_swing__mlb_2023__20260909__r01", "COMPLETE", "external_2023", "swing"),
    ("pitch_2026", "bcap_pitch__mlb_2026_ytd_20260907__20260909__r01", "COMPLETE", "external_2026", "pitch"),
    ("swing_2026", "bcap_swing__mlb_2026_ytd_20260907__20260909__r01", "WITHHELD", "external_2026", "swing"),
    ("pitch_failed", "bcap_pitch__mlb_2024_2025__20260909__r01", "FAILED", "development_2024_2025", "pitch"),
]
INPUTS = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def relative(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def meta(path):
    path = Path(path).resolve()
    return {"path": relative(path), "sha256": sha(path), "bytes": path.stat().st_size}


def read_bytes(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    item = {"path": relative(path), "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
    key = str(path)
    if key in INPUTS and INPUTS[key] != item:
        raise RuntimeError("Input changed during documentation generation: " + str(path))
    INPUTS[key] = item
    return data


def read_json(path):
    return json.loads(read_bytes(path).decode("utf-8-sig"))


def read_text(path):
    return read_bytes(path).decode("utf-8-sig").replace("\r\n", "\n")


def read_csv(path):
    return list(csv.DictReader(io.StringIO(read_bytes(path).decode("utf-8-sig"))))


def write_json_exclusive(path, value):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def fmt(value, digits=4):
    if value in (None, "", "nan", "NaN"):
        return "미산출"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def pct(value):
    return "미산출" if value in (None, "") else f"{float(value) * 100:.1f}%"


def link(source_doc, dest, title):
    value = Path(os.path.relpath(Path(dest).resolve(), Path(source_doc).parent.resolve())).as_posix()
    return f"[{title}]({value})"


def table(headers, rows):
    def clean(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    return "\n".join(["| " + " | ".join(map(clean, headers)) + " |",
                      "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(map(clean, row)) + " |" for row in rows])


def replace_once(text, old, new, label):
    if text.count(old) != 1:
        raise ValueError(f"Source text changed or repeated for {label}; inspect before editing")
    return text.replace(old, new, 1)


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def ps_command(argv):
    return "& " + " ".join(ps_quote(x) for x in argv)


def check_entry(item):
    path = ROOT / item["path"]
    if not path.is_file() or sha(path) != item["sha256"]:
        raise ValueError("Hash mismatch: " + item["path"])


def historical_command(record):
    m, alias = record["manifest"], record["alias"]
    if record.get("task_invocation"):
        captured = record["task_invocation"]
        return {"kind": "recorded_actual_task_invocation_after_execution", "argv": captured["argv"],
                "source": relative(INVOCATIONS), "attribution": captured["source"],
                "warning": "Task invocation record is not independently recovered shell history. Original IDs cannot be overwritten."}
    if m.get("command"):
        return {"kind": "captured_manifest_command", "argv": m["command"], "source": relative(record["path"] / "manifest.json")}
    executable = m.get("environment", {}).get("executable", sys.executable)
    if m["role"].startswith("external_"):
        argv = [executable, str(MODEL / "run.py"), "external", "--model", record["variant"],
                "--year", m["role"].split("_")[-1], "--run-id", m["run_id"], "--seal", str(SEAL)]
    elif m["role"] == "development_2024_2025":
        data = [x for x in m.get("inputs", []) if x["path"].endswith(".pkl")]
        if not data:
            return {"kind": "not_recorded_before_failure", "argv": None,
                    "reason": "No input path in failed prefit manifest; do not invent the command"}
        argv = [executable, str(MODEL / "run.py"), "develop", "--model", record["variant"],
                "--data", str(ROOT / data[0]["path"]), "--run-id", m["run_id"]]
    else:
        return {"kind": "unavailable", "argv": None}
    return {"kind": "reconstructed_from_manifest_not_captured_runtime_command", "argv": argv,
            "source": relative(record["path"] / "manifest.json"),
            "warning": "Historical ID is immutable; direct rerun refuses overwrite. Use a new run ID. Reused external data is no longer first independent validation."}


def validate_bootstrap_audit(result):
    expected = {x[1]: "BCAP-" + x[4].upper() + "-v0.1.0" for x in RUN_DEFS if x[0].endswith("_boot")}
    if (result.get("status") != "PASS" or result.get("both_completed_8") is not True
            or result.get("full_learning_interval_validated") is not False
            or result.get("recommendation_gate_upgrade") is not False):
        raise ValueError("Final independent bootstrap audit must validate both eight-refit runs without a full-CI or grade claim")
    runs = result.get("runs", [])
    if len(runs) != 2 or {x.get("run_id") for x in runs} != set(expected):
        raise ValueError("Final bootstrap audit does not cover the exact two completed diagnostic runs")
    for record in runs:
        if (record.get("model_id") != expected[record["run_id"]] or record.get("run_status") != "COMPLETE"
                or record.get("status") != "PASS" or record.get("planned_replicates") != 8
                or record.get("checked_replicates") != 8 or record.get("stability_summary_checked") is not True
                or len(record.get("replicate_checks", [])) != 8):
            raise ValueError("Incomplete independent bootstrap replication/summary audit: " + record["run_id"])


def validate_legacy_audit(result):
    if result.get("status") not in {"PASS", "PASS_WITH_COVERAGE_LIMITATIONS"}:
        raise ValueError("Legacy preservation audit has not passed its stated evidence coverage")
    summary = result.get("summary", {})
    fields = ["verified_files", "unverified_no_prior_hash", "unverified_historical_hash_only", "historical_reference_differences",
              "missing_files", "baseline_mismatches",
              "processed_total", "processed_verified", "bcai_run_total", "bcai_run_verified", "bcai_model_total", "bcai_model_verified"]
    if any(not isinstance(summary.get(key), int) or summary[key] < 0 for key in fields):
        raise ValueError("Legacy preservation audit must state numeric verified and unverified coverage")
    if summary["missing_files"] or summary["baseline_mismatches"]:
        raise ValueError("Legacy preservation audit reports missing files or prior-baseline hash mismatch")
    for group in ["processed", "bcai_run", "bcai_model"]:
        if summary[group + "_verified"] > summary[group + "_total"]:
            raise ValueError("Legacy verified count exceeds the inventoried coverage")


def validate_behavior_presentation(result):
    if (result.get("status") != "COMPLETE" or result.get("role") != "postseal_presentation_only"
            or result.get("new_analysis") is not False or result.get("policy_changed") is not False
            or result.get("recommendations") is not False or result.get("stage") != "evaluation_nuisance"
            or result.get("same_support_population") is not True or result.get("total_count_rows") != 60):
        raise ValueError("Behavior comparison must preserve the completed same-support, presentation-only scope")
    if len(result.get("tables", [])) != 5 or any(x.get("rows") != 12 for x in result["tables"]):
        raise ValueError("Behavior presentation must cover all five evaluated runs' twelve counts")
    if not result.get("development_policy_role") or not result.get("external_policy_role"):
        raise ValueError("Development outer policy and fixed final external policy roles must be distinguished")


def load_all():
    for path in [UPDATE, EVIDENCE, BACKUPS]:
        if path.exists():
            raise FileExistsError("Documentation finalization already attempted; preserve output: " + str(path))
    seal = read_json(SEAL)
    if seal.get("pitch_run") != RUN_DEFS[0][1] or seal.get("swing_run") != RUN_DEFS[1][1]:
        raise ValueError("Unexpected development sources in final seal")
    sealed_before = {}
    for item in seal["files"]:
        check_entry(item)
        sealed_before[item["path"]] = item["sha256"]
    protected = [ANAL / "handoff_bcap_review_evidence.json", ANAL / "handoff_bcap_review_validation.json",
                 ORIGINAL / "handoff_bcap_review.md", ORIGINAL / "README.md", ORIGINAL / "column.md",
                 ORIGINAL / "sources.md", ORIGINAL / "registry.md"]
    immutable = {relative(p): sha(p) for p in protected}
    original_evidence = read_json(protected[0])
    for item in original_evidence["files"]:
        if item["path"] == "columns/001-ball-count/analysis/handoff_bcap_review.md":
            if sha(ORIGINAL / "handoff_bcap_review.md") != item["sha256"]:
                raise ValueError("Original handoff snapshot differs from original evidence")
    current_handoff = read_text(ANAL / "handoff_bcap_review.md")
    preserved_handoff = read_text(ORIGINAL / "handoff_bcap_review.md")
    if current_handoff != preserved_handoff:
        # The parent explicitly added this one progress paragraph. Preserve its
        # complete bytes in the documentation backup, then retire stale status.
        without_progress = re.sub(r"\n> \*\*2026-09-09 구현 진행 업데이트:\*\*[^\n]*\n", "", current_handoff, count=1)
        if without_progress != preserved_handoff:
            raise ValueError("Current handoff changed beyond the inspected parent progress block")
    records = []
    # Only read terminal status manifests before proceeding to any results.
    for alias, run_id, status, role, variant in RUN_DEFS:
        path = RUNS / run_id
        m = read_json(path / "manifest.json")
        if m.get("status") != status or m.get("role") != role or m.get("model_id") != "BCAP-" + variant.upper() + "-v0.1.0":
            raise ValueError(f"Prerequisite incomplete/mismatched: {run_id}; expected {status}/{role}")
        if status == "COMPLETE" and not m.get("all_fits_converged", False):
            raise ValueError("Completed run lacks all-fits-converged evidence: " + run_id)
        if alias.endswith("_boot") and (m.get("completed_replicates") != 8 or not m.get("no_full_learning_confidence_interval")):
            raise ValueError("Eight completed diagnostic refits and no-full-CI distinction required")
        records.append({"alias": alias, "path": path, "manifest": m, "variant": variant,
                        "overall": None, "learned": None, "counts": [], "fits": [], "folds": []})
    report_meta = read_json(TABLEDIR / "report_manifest.json")
    if report_meta.get("status") != "COMPLETE" or len(report_meta.get("tables", [])) != 16:
        raise ValueError("Completed report with all sixteen tables required")
    report_sources = {x["run_id"] for x in report_meta["source_runs"]}
    expected_sources = {x[1] for x in RUN_DEFS if not x[0].endswith("_boot") and not x[0].endswith("_failed")}
    if report_sources != expected_sources:
        raise ValueError("Report runs differ from expected final runs")
    for item in report_meta["outputs"]:
        check_entry(item)
    boots = report_meta.get("bootstrap_diagnostics", [])
    if len(boots) != 2 or any(x.get("status") != "COMPLETE" or x.get("completed_replicates") != 8 for x in boots):
        raise ValueError("Final report must include both completed eight-refit diagnostics")
    if not REPORT.is_file():
        raise FileNotFoundError(REPORT)
    captured = read_json(INVOCATIONS)
    command_by_run = {x["run_id"]: x for x in captured["commands"]}
    if set(command_by_run) != {x[1] for x in RUN_DEFS}:
        raise ValueError("Actual invocation record must cover all nine expected runs")
    for record in records:
        m, art = record["manifest"], record["path"] / "artifacts"
        record["task_invocation"] = command_by_run[m["run_id"]]
        check_entry(record["task_invocation"]["manifest"])
        record["extensions"] = []
        for extension in sorted(record["path"].glob("*extension*.json")):
            record["extensions"].append({"metadata": meta(extension), "content": read_json(extension)})
        if m["status"] == "COMPLETE" and not record["alias"].endswith("_boot"):
            actions, policies = read_csv(art / "action_values.csv"), read_csv(art / "policy_values.csv")
            record["overall"] = next(x for x in actions if x["level"] == "overall")
            record["learned"] = next(x for x in policies if x["level"] == "overall" and x["policy"] == "learned")
            record["counts"] = [x for x in actions if x["level"] == "count"]
            if len(record["counts"]) != 12 or any(x["grade"] not in {"UNCERTAIN", "NO_SUPPORT"} for x in actions):
                raise ValueError("Unexpected counts or unsupported recommendation grade")
            if any(x.get("suggested_action") for x in actions):
                raise ValueError("A recommended action appeared despite frozen gates")
            record["fits"] = read_csv(art / "fit_diagnostics.csv")
            record["folds"] = read_json(art / "fold_records.json")
            if any(int(x.get("intersection_n", -1)) != 0 for x in record["folds"]):
                raise ValueError("Train/evaluation game overlap in recorded split")
        if m["role"].startswith("external_") and m["status"] == "COMPLETE":
            record["access"] = read_json(art / "external_access_log.json")
            if m.get("seal", {}).get("sha256") != sha(SEAL):
                raise ValueError("External run cites another seal")
            access = record["access"]["first_current_task_BCAP_external_row_access_utc"]
            if datetime.fromisoformat(access) < datetime.fromisoformat(seal["sealed_at_utc"]):
                raise ValueError("External row access predates final seal")
        record["command"] = historical_command(record)
    verification_files = ["pitch_development_complete_validation.json", "swing_development_complete_validation.json",
                          "pitch_2023_external_validation.json", "swing_2023_external_validation.json", "pitch_2026_external_validation.json"]
    verifications = []
    for name in verification_files:
        path = REVIEW / name
        result = read_json(path)
        if result.get("status") != "PASS":
            raise ValueError("Independent verification has not passed: " + name)
        verifications.append({"file": meta(path), "status": result["status"],
                              "checked_at_utc": result.get("checked_at_utc"), "rows": result.get("rows"),
                              "supported_rows": result.get("supported_rows")})
    preparations = [ANAL / "bcap_preparation_20260909_r01/preparation_audit.json"]
    preparations += [x["path"] / "artifacts/preparation/preparation_audit.json" for x in records
                     if x["manifest"]["role"].startswith("external_") and x["manifest"]["status"] == "COMPLETE"]
    prep = [{"file": meta(path), "content": read_json(path)} for path in preparations]
    supplements = [{"file": meta(path), "content": read_json(path)} for path in sorted(REVIEW.glob("*_supplement/supplement_manifest.json"))]
    auxiliary = []
    for name in ["action_lineage_validation.json", "score_timing_validation.json"]:
        path = REVIEW / name
        result = read_json(path)
        if not (result.get("status") == "PASS" or result.get("all_pass") is True):
            raise ValueError("Independent source/feature lineage validation has not passed: " + name)
        auxiliary.append({"file": meta(path), "content": result})
    comparison_path = REVIEW / "postseal_descriptive_comparison/comparison_manifest.json"
    comparison = read_json(comparison_path)
    if comparison.get("status") != "COMPLETE_DESCRIPTIVE_ONLY" or comparison.get("post_seal_recipe") is not True:
        raise ValueError("Post-seal comparison must remain explicitly descriptive")
    for item in comparison.get("outputs", []):
        check_entry(item)
    bootstrap_path = REVIEW / "bootstrap_final_validation.json"
    bootstrap_validation = read_json(bootstrap_path)
    validate_bootstrap_audit(bootstrap_validation)
    legacy_path = REVIEW / "legacy_asset_preservation.json"
    legacy_validation = read_json(legacy_path)
    validate_legacy_audit(legacy_validation)
    behavior_path = REVIEW / "behavior_comparison_manifest.json"
    behavior_comparison = read_json(behavior_path)
    validate_behavior_presentation(behavior_comparison)
    for item in behavior_comparison.get("inputs", []) + behavior_comparison.get("outputs", []):
        check_entry(item)
    if {x["path"] for x in behavior_comparison.get("outputs", [])} != {relative(BEHAVIOR)}:
        raise ValueError("Behavior presentation output does not match the linked document")
    return {"seal": seal, "records": records, "report_meta": report_meta, "immutable": immutable,
            "sealed_before": sealed_before, "verifications": verifications, "preparations": prep, "supplements": supplements,
            "auxiliary_validations": auxiliary, "postseal_comparison": {"file": meta(comparison_path), "content": comparison},
            "bootstrap_validation": {"file": meta(bootstrap_path), "content": bootstrap_validation},
            "legacy_preservation": {"file": meta(legacy_path), "content": legacy_validation},
            "behavior_comparison": {"file": meta(behavior_path), "content": behavior_comparison}}


def summary_table(doc, records, detailed=False):
    rows = []
    for record in records:
        m, value = record["manifest"], record["overall"]
        role = {"development_2024_2025": "2024·2025 개발", "external_2023": "2023 재현", "external_2026": "2026-09-07까지",
                "full_pipeline_game_bootstrap_stability": "개발 전체 재학습 8회"}[m["role"]]
        if m["status"] == "FAILED":
            role = "개발 최초 호출 실패 보존"
        row = [record["variant"].upper(), role, m["status"],
               fmt(value.get("n_all"), 0) if value else "해당 없음",
               fmt(value.get("n"), 0) if value else "해당 없음",
               value.get("grade") if value else "등급 없음",
               link(doc, record["path"] / "manifest.json", m["run_id"])]
        if detailed:
            row.insert(-1, m.get("finished_at_utc", "미기록"))
        rows.append(row)
    headers = ["모델", "범위", "실행 상태", "적격 행", "공통 지지 행", "전체 판정"]
    if detailed:
        headers.append("완료 UTC")
    return table(headers + ["실행"], rows)


def numeric_summary(doc, records):
    rows = []
    for record in records:
        if record["overall"] is None:
            continue
        m, v, p = record["manifest"], record["overall"], record["learned"]
        rows.append([record["variant"].upper(), m["role"], fmt(v.get("Q0")), fmt(v.get("Q1")), fmt(v.get("delta")),
                     f"[{fmt(v.get('simultaneous95_low'))}, {fmt(v.get('simultaneous95_high'))}]",
                     fmt(p.get("gain")), f"[{fmt(p.get('gain_low'))}, {fmt(p.get('gain_high'))}]", pct(v.get("coverage"))])
    return table(["모델", "평가", "Q0", "Q1", "Δ=Q1−Q0 W", "Δ 조건부 동시95%", "후보 정책 개선량 W", "개선량 조건부 동시95%", "지지 비율"], rows)


def main_limits():
    return ("PITCH는 현재 한 구 FB/NFB의 최종 PA 공격가치 비교이며 현재·직전 좌표를 입력하지 않는다. "
            "SWING은 번트 포함 기록상 공격 시도/판정상 Take의 사후 공 특성 조건부 진단이다. 명시적 scored HBP는 Take로 포함하지만 "
            "불명 라벨을 Take로 대치하지 않는다. 타자의 실시간 지각·구종 품질·컨디션·의도·미측정 교란은 식별되지 않았다. "
            "같은 실제 선수·상황 행에 양 행동을 적용했으며 가상 평균 선수 예측으로 대체하지 않았다. "
            "완료 PA·IBB·최종 결과 결측 제외는 사후 선택을 포함한다. 행별 차이를 합쳐 PA 전체 정책의 개선량으로 보고하지 않는다.")


def inference_limits():
    return ("주 구간은 고정 OOF 점수의 경기 군집 조건부 구간과 Bonferroni 1,536 가족 범위다. "
            "각 모델의 8회 전체 재학습은 매 반복의 전처리·튜닝·calibration·nuisance·정책 선택을 다시 수행한 안정성 진단이며 "
            "최종 개발 정책의 완전한 95% 신뢰구간이 아니다. 경기 간 선수·시리즈 의존성과 동률 근처 선택도 남는다. "
            "known/unseen·IPW·Hájek·g-computation·추가 calibration·민감도와 보조 구간은 별도 진단이다. "
            "NO_SUPPORT는 실행된 비교의 표본·공통 지지 부족, UNCERTAIN은 지원된 비교에도 식별·학습 불확실성 근거 부족을 뜻한다. "
            "미실행·측정 보류에는 표본 판정 등급을 부여하지 않는다. 모든 추천 행동은 비어 있고 보수 정책은 전 영역에서 실제 행동을 유지한다.")


def legacy_scope(doc, context):
    record = context["legacy_preservation"]
    summary = record["content"]["summary"]
    return (link(doc, ROOT / record["file"]["path"], "기존 자산 보존 검사") + "의 기존 증거 SHA 대조 범위는 "
            + fmt(summary["verified_files"], 0) + "개 파일이다. 대상 정제본 "
            + fmt(summary["processed_verified"], 0) + "/" + fmt(summary["processed_total"], 0)
            + ", BCAI 실행 파일 " + fmt(summary["bcai_run_verified"], 0) + "/" + fmt(summary["bcai_run_total"], 0)
            + ", BCAI 모델 파일 " + fmt(summary["bcai_model_verified"], 0) + "/" + fmt(summary["bcai_model_total"], 0)
            + "에서 과거 기준 해시와 일치했다. 기준 증거가 없는 " + fmt(summary["unverified_no_prior_hash"], 0)
            + "개와 과거 마이그레이션 이전 참조만 있는 " + fmt(summary["unverified_historical_hash_only"], 0)
            + "개 파일은 이번 현재 해시만으로 BCAP 직전부터의 무변경을 확인할 수 없다. 오래된 역사적 참조와 현재 파일의 차이 "
            + fmt(summary["historical_reference_differences"], 0) + "개를 이번 BCAP의 변경으로 간주하지 않는다. 누락 " + fmt(summary["missing_files"], 0)
            + "개·선택한 과거 기준 해시 불일치 " + fmt(summary["baseline_mismatches"], 0)
            + "개이며 상세 파일·기준 선택·이전 참조의 차이는 원 JSON을 따른다. 원본 150 CSV는 이 기존 자산 검사에서 제외했고 "
            "별도 원본/봉인 해시 검사와 구분한다. 기존 트리 전체에 과거 무변경 증명이 있다고 주장하지 않는다.")


def model_card(doc, variant, context):
    records = [x for x in context["records"] if x["variant"] == variant]
    title = "BCAP-" + variant.upper() + "-v0.1.0"
    purpose = "같은 투구 전 상태·공통 실제 기준 집단의 FB/NFB 비교" if variant == "pitch" else "같은 상태·사후 공 특성의 번트 포함 Swing/판정상 Take 비교"
    external = "2023 외부 재현 및 2026-09-07까지 시간 순방향 진단 완료" if variant == "pitch" else "2023 외부 재현 완료; 2026 위치·존 측정 정합성 부족으로 전체 평가 보류"
    return (f"# {title}\n\n상태: **EXPERIMENTAL**. 갱신 시각 {context['at']}. 실제 구현·적합·검산·명시 범위 외부 진단 완료. 행동 추천 없음.\n\n"
            f"목적: {purpose}. 개발 2024·2025. {external}. 기존 OBS/Ridge의 검증 상태를 전용하지 않는다.\n\n"
            "모델은 DRAFT에서 시작했다. 봉인된 specification.yaml의 status_at_definition=DRAFT는 최초 정의 시점의 역사이며 "
            "현재 카드·레지스트리의 EXPERIMENTAL과 충돌하지 않는다. 명세·코드·정책 해시는 이 문서 갱신으로 바꾸지 않았다.\n\n"
            + main_limits() + "\n\n" + inference_limits() + "\n\n"
            "X는 양 nuisance 보정 입력, Z는 정책 허용 상태다. PITCH Z는 count, SWING Z는 count×zone×FB/NFB다. "
            "양 nuisance의 투수·타자 효과를 Ridge로 축소하며 행동별 outcome T learner와 별도 훈련 경기에서 Platt 보정한 propensity를 썼다. "
            "경기 outer3/inner2에서 정책 학습과 평가를 분리했다. 외부 고정 개발 nuisance의 예측 성능과 외부 교차 적합 nuisance를 이용한 "
            "고정 개발 정책 OPE는 별도 산출물이다.\n\n"
            + link(doc, doc.parent / "specification.yaml", "봉인된 기계 명세") + " · "
            + link(doc, doc.parent / "validation.md", "실제 검증 범위") + " · "
            + link(doc, MODEL / "design_decisions.md", "설계 변경 근거") + " · "
            + link(doc, MODEL / "measurement_review.md", "측정 근거") + " · "
            + link(doc, REPORT, "16종 표·카운트별 보고서") + "\n\n"
            + summary_table(doc, records) + "\n\n"
            "새 입력 적용은 새 실행 ID를 사용한다. 결과에 영향을 주는 설계 변경은 새 버전을 만들고, 이미 본 2023·2026을 "
            "최초 독립 검증이라고 부르지 않는다. KBO·Drive·외부 게시 범위는 이번 실행에 없다.\n")


def model_validation(doc, variant, context):
    records = [x for x in context["records"] if x["variant"] == variant]
    rows = []
    for r in records:
        if r["fits"]:
            rows.append([r["manifest"]["run_id"], len(r["fits"]), len(r["folds"]), "0",
                         r["manifest"].get("all_fits_converged"), link(doc, r["path"] / "artifacts/fit_diagnostics.csv", "수렴")])
    verification = [x for x in context["verifications"] if Path(x["file"]["path"]).name.startswith(variant)]
    text = (f"# BCAP-{variant.upper()}-v0.1.0 검증\n\n상태: **EXPERIMENTAL**. 실제 기록 기준 {context['at']}. "
            "적합·독립 수치 검산과 명시한 외부 진단을 완료했다. 인과 효과·실시간 정책·행동 추천은 검증되지 않았다.\n\n"
            + summary_table(doc, records, True) + "\n\n## 수치·자료 분리 검사\n\n"
            + table(["실행", "적합/보정 기록 수", "분할 기록 수", "자기 훈련/평가 교집합", "전부 수렴", "기록"], rows) + "\n\n"
            "독립 검산은 주 실행기의 AIPW 행 점수를 가져다 평균하는 데 그치지 않고 별도 OPE 식을 통해 부호·분모·단위·키·fold 및 "
            "개발 정책 학습과 상위 holdout 분리를 대조한다. 상세 허용오차·최대 차이는 다음 원 기록을 따른다.\n\n")
    text += "\n".join("- " + link(doc, ROOT / x["file"]["path"], Path(x["file"]["path"]).name) + ": " + x["status"] for x in verification)
    text += ("\n\n전체 재학습 8회에서 저장 복제 키·집계·최종 안정성 요약의 독립 대조는 "
             + link(doc, ROOT / context["bootstrap_validation"]["file"]["path"], "bootstrap 최종 독립 검산") + "에서 PASS를 확인했다. "
             "이는 저장 산출물 재구성 검산이며 완전한 학습 신뢰구간이나 추천 승격의 근거가 아니다.")
    text += "\n\n## 불확실성·정책 판정\n\n" + inference_limits() + "\n\n" + main_limits() + "\n\n"
    text += ("SWING의 2026 위치·존 정합성이 확보되지 않았으므로 대리 분석으로 채우지 않고 WITHHELD로 남겼다. "
             "이것은 외부 성과가 나빠 실패한 결과나 표본 NO_SUPPORT 판정이 아니다.\n\n" if variant == "swing" else
             "2026 PITCH에는 현재·직전 위치·존 파생 입력이 없으며 2025 공격가치 가중치를 고정했다. 진행 시즌의 9월7일까지 평가로 한정한다.\n\n")
    text += link(doc, REVIEW / "review.md", "독립 검수 의견·보조 진단") + " · " + link(doc, EVIDENCE, "실행·코드·입출력 해시·명령 증거") + " · " + link(doc, REPORT, "주 결과 보고서") + "\n"
    return text


def model_readme(doc, context):
    return ("# BCAP 모델과 재현 안내\n\n" + MARKER + f". {context['at']}.\n\n"
            "BCAP-PITCH-v0.1.0과 BCAP-SWING-v0.1.0은 모두 **EXPERIMENTAL**이다. 실제 개발·외부 진단과 독립 검산을 완료했으나 "
            "행동 추천은 없다. BCAP-JOINT는 두 모델의 식별·외부 근거가 충분하지 않아 설계하지 않았다.\n\n"
            + link(doc, MODEL / "pitch/v0.1.0/model_card.md", "PITCH 카드") + " · "
            + link(doc, MODEL / "swing/v0.1.0/model_card.md", "SWING 카드") + " · "
            + link(doc, REPORT, "주 보고서·16종 표·12카운트 해석") + " · "
            + link(doc, BEHAVIOR, "카운트별 실제·후보 행동 비율 비교") + " · "
            + link(doc, ANAL / "handoff_bcap_review.md", "별도 검수 인계") + "\n\n"
            "행동 비율 비교는 이미 저장된 같은 공통 지지 집단의 실제·후보 비율·%p 차이·불일치율을 읽기 쉽게 제시한 "
            "봉인 뒤 표현 보완이다. 새 분석·주 검증 변경·행동 추천은 없으며 개발 outer 평가 정책과 외부에 적용한 최종 개발 정책의 역할을 구분한다.\n\n"
            "문서 갱신 뒤 실행하는 최종 보존·해시·내부 링크 검사의 실제 결과는 "
            + link(doc, FINAL_AUDIT_DIR, "최종 보존·해시·링크 검사 폴더") + "의 `validation.json`에서 확인한다. "
            "이 문서 생성 시점에는 예정 출력이며 PASS를 선제적으로 단정하지 않는다.\n\n"
            "## 역할과 추정 대상\n\n" + main_limits() + "\n\n" + inference_limits() + "\n\n"
            "## 파일 역할\n\n"
            "- pitch/v0.1.0, swing/v0.1.0: 모델 카드·불변 기계 명세·검증 범위. 명세의 최초 DRAFT 상태는 역사적 값이다.\n"
            "- data.py: 기존 로컬 원본에서 새 정제본과 행동·PA·측정 감사를 생성. run.py: 중첩 개발·최종 정책·봉인·외부 평가.\n"
            "- verify_bcap.py: 주 실행기와 분리한 AIPW/OPE 검산. refit_stability.py: 전체 재학습 경기 bootstrap 안정성 진단.\n"
            "- supplement_diagnostics.py: IPW/Hájek/회귀 표준화·known/unseen·정책 비율·calibration 보조 표.\n"
            "- finalize_seal.py: 보조 분석 및 보고 코드·기존 외부 입력 해시까지 포함한 최종 봉인. check_artifacts.py: 보존·해시·링크 점검.\n"
            "- build_report.py: 완료 집계의 보고서·16종 CSV·후처리 manifest. finish_documents.py: 완료 후 문서·새 증거 인덱스만 갱신.\n"
            "- record_invocations.py: 실제 작업에서 호출한 명령을 출처와 함께 사후 기록. 독립 shell history 회수와 구분한다.\n\n"
            + summary_table(doc, context["records"]) + "\n\n## 재현\n\n"
            "프로젝트 루트에서 실행한다. 기존 run ID·정제본·보고 파일은 재사용하지 않는다. 정확한 환경·입력 경로·해시와 "
            "실제 작업 호출을 실행 후 기록한 " + link(doc, INVOCATIONS, "명령 기록") + "과 " + link(doc, EVIDENCE, "실행 증거 인덱스") + "에 있다. "
            "작업의 도구 호출에서 사후 기록한 명령이며 독립적으로 복구한 shell history라고 주장하지 않는다. "
            "완료된 수치의 독립 검산·보고서 후처리는 원본 재수집이나 모델 재적합을 필요로 하지 않는다. "
            "새 모델 재적합 후 같은 2023·2026에 적용하면 이미 노출된 외부 자료의 반복 평가로 기록해야 한다.\n\n"
            + context["reproduction_text"] + "\n\n"
            "정제·적합·외부 평가 명령의 --help는 각 실행기의 역할과 필요한 인수를 확인하는 데 쓴다. "
            "해시 봉인은 공개 사전등록이나 모든 과거 미노출을 증명하지 않는다.\n")


def make_handoff(doc, context):
    records = context["records"]
    lines = ["# BCAP 별도 검수 인계 — 실제 구현·평가 완료 범위", "", f"갱신: {context['at']}. Baseline 001-ball-count.", "",
             "## 1. 현재 상태", "",
             "BCAP-PITCH-v0.1.0 / BCAP-SWING-v0.1.0은 실제 제작·개발·독립 검산 후 **EXPERIMENTAL**이다. "
             "PITCH는 2023·2026-09-07까지 외부 진단, SWING은 2023 외부 진단을 완료했다. "
             "SWING 2026은 plate 기준면과 존 정의의 정합성을 확보하지 못해 전체 평가를 보류했다. 두 모델의 행동 추천은 모두 비어 있다. "
             "실행된 비교는 UNCERTAIN/NO_SUPPORT로 구분한다. BCAP-JOINT는 전제 근거 부족으로 설계하지 않았다.", "",
             link(doc, REPORT, "실제 수치·16종 주요 표·카운트별 해석") + " · " + link(doc, BEHAVIOR, "카운트별 실제·후보 행동 비율 비교") + " · "
             + link(doc, MODEL / "README.md", "모델·실행 안내") + " · " +
             link(doc, REVIEW / "review.md", "독립 구현 검수") + " · " + link(doc, EVIDENCE, "새 실행 증거 목록") + " · " + link(doc, UPDATE, "MD 변경 감사"), "",
             "## 2. 원래 인계 보존", "",
             "이전 ‘구현 미착수’ 인계는 " + link(doc, ORIGINAL / "handoff_bcap_review.md", "원래 인계 스냅샷") + "으로 보존했다. "
             + link(doc, ANAL / "handoff_bcap_review_evidence.json", "원래 증거 JSON") + "과 " + link(doc, ANAL / "handoff_bcap_review_validation.json", "원래 검증 JSON") +
             "은 바이트를 변경하지 않았다. 기존 문서 해시가 가리키는 시점과 현재 실행 완료 시점을 구분한다. "
             "새 기록은 새 증거 인덱스에 추가했으며 이전 인계 해시를 외부 사전 봉인이라고 재해석하지 않는다.", "",
             legacy_scope(doc, context), "",
             "진행 중 만든 " + link(doc, ANAL / "bcap_execution_progress_20260909.md", "진행 기록") + "과 "
             + link(doc, ANAL / "bcap_v010_primary_report_20260909.md", "재학습 완료 전 주 분석 1차 보고서") + "도 중간 기록으로 보존했다. "
             "현재 인계의 최종 상태·8회 재학습 포함 결과는 본 문서와 최종 보고서가 기준이다.", "",
             "원문 요구는 " + link(doc, ANAL / "bcap_request_original.txt", "보관 원문") + ", 원 요구·문제·채택 수정·근거·추정 대상 영향은 "
             + link(doc, MODEL / "design_decisions.md", "설계 결정") + ", 행동 라벨·2026 측정 근거는 " + link(doc, MODEL / "measurement_review.md", "측정 검토") + "에 있다.", "",
             "## 3. 구현한 추정 대상·상태·정책", "", main_limits(), "",
             "Y는 기존 OBS 계열의 시즌별 가중 최종 PA 공격가치 W이며 BCAI 상태 가치나 전이 보상을 더하지 않았다. "
             "PITCH의 Δ는 Q(FB)−Q(NFB), SWING의 Δ는 Q(번트 포함 Swing)−Q(Take)다. 투수는 작을수록, 타자는 클수록 점추정 방향이 유리하다. "
             "개선량 부호는 PITCH=관찰−후보, SWING=후보−관찰이다. 단위는 W/선택된 현재 의사결정 행이며 공식 wOBA·득점·PA 전체 누적 개선과 다르다.", "",
             "X에는 실제 투수·타자 및 허용한 상황을 넣고 양 nuisance에 작은 표본 효과 축소를 적용한다. Z는 PITCH count, "
             "SWING count×zone×FB/NFB다. 카운트 평균 AIPW Q, 행별 조건부 회귀 μ, 실제 학습한 후보 정책 d(Z)는 별개다. "
             "평가 action_values의 방향은 평가자료 점추정이며 저장된 정책 행동과 다를 수 있다. 외부 승자를 정답 ‘최적 행동’으로 부르지 않는다.", "",
             "카운트별 실제·후보 행동 비율 비교는 기존 보조 산출물의 같은 공통 지지 집단에서 실제 비율·후보 비율·%p 차이·불일치율을 "
             "문서로 옮긴 봉인 뒤 표현 보완이다. 새 추정·주 검증 변경·추천 승격은 없다. "
             "개발 행에는 해당 outer 훈련에서 학습한 정책, 외부 행에는 고정된 최종 개발 정책을 적용한 기록을 구분해 제시한다.", "",
             "Ridge T learner 결과 회귀와 Ridge score·별도 20% 훈련 경기 Platt propensity를 사용했다. α 후보 100·1000의 선택·범주 사전·calibration은 "
             "해당 훈련 자료 안에서 이루어진다. 경기 outer3/inner2 구조로 정책 점수 생성과 outer OPE를 분리했다. "
             "일반 deterministic 후보와 fallback Bernoulli(.5)를 기록하고, 보수 정책은 H(Z)=0으로 실제 메커니즘을 전 영역에서 유지한다. "
             "보수 정책 개선량 0은 정의상 결과다.", "",
             "## 4. 실행 목록·실제 수치", "", summary_table(doc, records, True), "", numeric_summary(doc, records), "",
             "카운트와 셀의 분모·가치·구간·등급·external 비교는 주 보고서와 16종 CSV를 따른다. "
             "최초 PITCH r01은 입력 경로 처리 오류로 적합 전 실패한 기록을 FAILED로 보존했고 새 r02에서 수행했다. "
             "실패 당시 manifest의 코드 해시와 일치하는 "
             + link(doc, RUNS / "bcap_pitch__mlb_2024_2025__20260909__r01/artifacts/run_failed_source.py", "실패 실행 원 코드 사본") + "과 "
             + link(doc, RUNS / "bcap_pitch__mlb_2024_2025__20260909__r01/provenance_extension_20260909.json", "추가 provenance")
             + "에 현재 코드와의 경로 보정·스냅샷 보존 차이를 기록했다. 원 실패 manifest는 바꾸지 않았다. "
             "r03(PITCH)과 r02(SWING)는 버전 교체가 아닌 8회 전체 재학습 민감도 실행이다.", "",
             "## 5. 외부 봉인과 열람 이력", "",
             "최종 봉인: " + link(doc, SEAL, "external_seal_20260909_r01.json") + f". UTC {context['seal']['sealed_at_utc']}, SHA256 `{sha(SEAL)}`. "
             "정의·코드·최종 개발 nuisance/정책·hyperparameter와 사전 보조 범위를 고정했다. "
             "기존 외부 원본의 파일 해시는 최종 봉인에 기록했다. 문서 갱신 시 모든 sealed files 해시를 재확인하며 원본 전체 재해시는 별도 check_artifacts 검사의 역할이다.", "",
             "2023·2026은 기존 BCAI/Ridge에서 이미 사용했다. 이번 BCAP 결과 접근 시각만 별도 남기며 완전히 미관측 데이터라고 주장하지 않는다. "
             "외부 고정 개발 nuisance의 예측 성능과 외부 경기 교차 적합 nuisance로 평가한 고정 개발 정책가치를 구분한다. "
             "외부 propensity를 개발에서 그대로 맞다고 가정하지 않고, 외부 nuisance의 알고리즘·α는 개발 고정값을 사용했다. "
             "외부 정책 학습·외부 튜닝·외부 결과에 따른 모델 재설계는 하지 않았다.", ""]
    access_rows = []
    for r in records:
        if r["manifest"]["role"].startswith("external_"):
            access_rows.append([r["manifest"]["run_id"], r.get("access", {}).get("first_current_task_BCAP_external_row_access_utc", "모델 평가 접근 없음; WITHHELD"),
                                r["manifest"].get("finished_at_utc"), r["manifest"].get("outcome_evaluations", "미기록")])
    lines += [table(["실행", "이번 작업 최초 BCAP 외부 행 접근 UTC", "완료 UTC", "모델 결과 평가 횟수"], access_rows), "",
              "2026은 2025 결과 가중치를 고정했다. PITCH 입력은 위치를 쓰지 않는다. SWING은 front/middle plate와 operator/ABS zone 간 "
              "검증된 교량 자료가 없어 전체 평가를 보류했으며 위치를 뺀 대리 분석으로 주 검증을 대체하지 않았다. "
              "외부 결과 뒤 설계를 바꾸면 새 버전·새 실행과 재노출 이력을 남겨야 한다.", "",
              "## 6. 검증과 남은 한계", "", inference_limits(), "",
              "독립 검산 기록:", ""]
    lines += ["- " + link(doc, ROOT / v["file"]["path"], Path(v["file"]["path"]).name) + ": PASS; " + str(v.get("checked_at_utc")) for v in context["verifications"]]
    lines += ["- " + link(doc, ROOT / v["file"]["path"], Path(v["file"]["path"]).name) + ": PASS (원자료 행동·입력 계보 또는 투구 전 점수 시점 검사)" for v in context["auxiliary_validations"]]
    lines += ["- " + link(doc, ROOT / context["bootstrap_validation"]["file"]["path"], "bootstrap_final_validation.json")
              + ": PASS; 두 모델 각각 완료 8회 저장 복제 키·집계·안정성 요약을 독립 대조. 전체 학습 신뢰구간 검증·추천 승격 없음."]
    lines += ["", "독립 검산은 AIPW/OPE 부호·W 단위·같은 분모·키·fold 교집합·금지 입력·학습 정책을 검사했다. "
              "행동·입력 계보 재구성과 투구 전 점수 시점을 별도 검사했으며 행동 선택의 인과 식별·실시간 유용성 검증을 대신하지 않는다. "
              "투타 개인 효과를 두 nuisance에 포함해도 선수×행동 품질과 목표 위치·예상·컨디션 교란이 남는다.", "",
              "외부 방향 일치·상관의 " + link(doc, REVIEW / "postseal_descriptive_comparison/comparison_manifest.json", "사후 기술 비교") + "와 "
              + link(doc, REVIEW / "postseal_descriptive_comparison/direction_and_correlation_summary.csv", "요약 CSV") + "는 봉인 뒤 기존 결과를 본 상태에서 작성한 집계다. "
              "주 명세·추정 대상·정책·등급은 변경하지 않았고, 각 시즌의 서로 다른 실제 지지 집단을 비교한다. "
              "사전 고정 주 검증 또는 최적 정책의 정답 일치로 해석하지 않으며, 추천 등급을 올리지 않는다.", "",
              "해결되지 않은 항목과 필요한 증거:", "",
              "1. 인과적 행동 추천: 선수별 실행 가능한 구종군, 의도·구종 품질·상태·타자 지각의 측정 및 교환가능성/선택 식별 근거가 필요하다.",
              "2. SWING 실시간 정책: 결정을 내릴 때 실제 가용했던 시간별 지각 대리값과 측정 지연·오차 검증이 필요하다.",
              "3. 2026 SWING: 같은 투구 구·신 좌표와 두 존 정의의 짝지은 교량 자료 및 사전 오차 기준이 필요하다.",
              "4. 전체 학습95% 구간: 충분한 재학습 반복과 동률 민감 정책 추론, 경기 간 선수·시리즈 의존성을 다루는 별도 설계가 필요하다. 8회 범위는 대체 증거가 아니다.",
              "5. NO_SUPPORT 셀: 해당 행동별 표본·경기·ESS·공통 지지 확보가 먼저이며 일반 선수군 외삽으로 메우지 않는다.",
              "6. 전체 PA·JOINT: 바뀐 행동의 미래 상태 분포·상대 반응을 포함한 순차 식별·평가를 별도 설계해야 한다.", "",
              "## 7. 파일·입출력·명령·다음 검수", "",
              "모델 정의는 models/bcap/<variant>/v0.1.0, 실제 실행은 해당 run manifest/artifacts, 새 정제본은 기존 data/processed의 "
              "bcap 이름 파일이다. 이전 원본·정제본·BCAI 모델·실행은 보존했다. 정제 감사의 사유별 제외·문자열·구종 맵·키·측정 검사와 "
              "raw/input/code/config/output 해시를 " + link(doc, EVIDENCE, "새 실행 증거 JSON") + "에서 모두 연결한다. "
              "실제 작업의 도구 호출 명령은 " + link(doc, INVOCATIONS, "사후 명령 기록") + "에서 출처·UTC·manifest 해시와 함께 확인한다. "
              "독립 shell history 회수와 구분하며, 명령이 누락되어 manifest에서 복원한 경우에는 별도 kind로 표시한다. "
             "각 run에 후속 provenance/manifest extension이 있으면 새 증거 목록에 함께 보존한다.", "",
              "문서 갱신 뒤 실행하는 최종 보존·해시·내부 링크 검사의 실제 결과는 "
              + link(doc, FINAL_AUDIT_DIR, "최종 보존·해시·링크 검사 폴더") + "의 `validation.json`에서 확인한다. "
              "이 문서 생성 시점에는 예정 출력이며 PASS를 선제적으로 단정하지 않는다. 최종 감사 이후 문서를 바꾸면 새로운 감사가 필요하다.", "",
              context["reproduction_text"], "",
              "검수 순서: (1) 원 인계 증거 보존과 최종 봉인 해시, (2) 실제 실행·정제 입력/출력 해시, "
              "(3) 시간 순서와 행동 라벨·사후 선택, (4) outer/inner/tuning/calibration/정책 평가 경기 분리, "
              "(5) 독립 수치 검산과 16종 표의 분모·부호, (6) 외부 고정 예측/OPE 분리와 열람 시각, "
              "(7) 실제 지지 등급·전체 학습 불확실성·2026 측정 보류, (8) 카운트 해석과 문서 상태의 일치.", "",
              "KBO 수집·분석, Drive 업로드, 공동 Docs 수정, 외부 게시·전송은 이번 작업에서 하지 않았다. "
              "로컬 MD 갱신이 기존 드라이브 공유 사본에 자동 반영되지 않는다. 기존 자료를 다시 수집하지 않았다.", ""]
    return "\n".join(lines)


def reproduction(context):
    exe = context["records"][0]["manifest"]["environment"]["executable"]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ANAL / ("bcap_report_recheck_" + stamp)
    report = ANAL / ("bcap_report_recheck_" + stamp + ".md")
    argv = [exe, str(MODEL / "build_report.py")]
    keys = ["pitch-dev", "swing-dev", "pitch-2023", "swing-2023", "pitch-2026", "swing-2026", "pitch-bootstrap", "swing-bootstrap"]
    by_alias = {x["alias"]: x for x in context["records"]}
    for name in keys:
        alias = name.replace("-", "_").replace("_bootstrap", "_boot")
        argv += ["--" + name, by_alias[alias]["manifest"]["run_id"]]
    argv += ["--output-dir", str(out), "--report", str(report)]
    text = ("후처리 재현 예시(모델 적합·데이터 수집 없이 기존 완료 집계에서 새 보고 사본 생성; 아래 목적지가 이미 있으면 새 이름 사용):\n\n"
            "```powershell\n" + ps_command(argv) + "\n```\n\n"
            "행별 독립 검산을 다시 수행할 때는 verify_bcap.py의 --rows/--model/--summary/--folds/--config에 해당 실행 artifacts를 "
            "지정하고 --output에 새 JSON 경로를 쓴다. 기존 명령의 run ID로 다시 적합하면 보존 규칙에 따라 중단되므로 "
            "새 분석 실행은 반드시 새 ID를 사용한다.")
    return text, argv


def build_documents(context):
    docs = {}
    rootdoc, coldoc, sourcedoc, regdoc = ROOT / "README.md", COL / "column.md", COL / "sources.md", ROOT / "models/registry.md"
    readme, column, sources, registry = [read_text(x) for x in [rootdoc, coldoc, sourcedoc, regdoc]]
    if any(MARKER in x for x in [readme, column, sources, registry]):
        raise ValueError("BCAP finalization marker already exists")
    status_old = "MLB OBS·Ridge v0.2 외부 검증 완료 · BCAP 검수 인계 작성·구현 미착수 · KBO 미착수"
    status_new = "MLB OBS·Ridge v0.2 외부 검증 완료 · BCAP 실제 개발·외부 진단 완료·추천 보류(2026 SWING 보류) · KBO 미착수"
    readme = replace_once(readme, status_old, status_new, "README current status")
    column = replace_once(column, status_old, status_new, "column current status")
    old_next = "2026-09-09: [BCAP 별도 검수 인계](columns/001-ball-count/analysis/handoff_bcap_review.md)에 첨부 프롬프트, 방법론 수정안, 한 구 정책의 추정 대상, 자료 분리·외부 봉인 요구와 미완료 항목을 기록했다. BCAP 모델·실행·결과는 아직 없으며 기존 BCAI 검증과 구분한다."
    new_next = ("2026-09-09: [BCAP 실제 보고서](columns/001-ball-count/analysis/bcap_v010_report_20260909.md)와 "
                "[갱신 인계](columns/001-ball-count/analysis/handoff_bcap_review.md)에 모델 구현·개발·외부 진단·독립 검산·8회 전체 재학습 안정성을 연결했다. "
                "두 모델은 EXPERIMENTAL이며 모든 행동 추천을 보류한다. 2026 SWING은 측정 정합성 부족으로 전체 평가를 보류했다. "
                "이어서 검수할 항목은 인과 식별·실시간 지각 자료·측정 교량·완전한 학습 불확실성이다.")
    readme = replace_once(readme, old_next, new_next, "README next BCAP paragraph")
    old_col = "BCAP 후속 검수: [별도 인계 문서](analysis/handoff_bcap_review.md)에 사용자 원문·기존 자산 근거·설계 수정안·추정 대상·개인 효과 보정 한계·학습/평가 분리·외부 봉인 및 미완료 상태를 저장했다. BCAP-PITCH/SWING은 설계 검토 단계로 정식 등록·구현·분석 결과가 없으며 모든 행동 추천은 판정 보류다. 아래 OBS/Ridge 완료 상태를 BCAP에 전용하지 않는다. KBO·Drive 작업은 수행하지 않았다."
    new_col = ("BCAP 실제 제작·검증: [16종 표·카운트별 보고서](analysis/bcap_v010_report_20260909.md), "
               "[갱신 인계](analysis/handoff_bcap_review.md), [모델 안내](../../models/bcap/README.md). "
               "BCAP-PITCH/SWING은 실제 구현·2024·2025 개발·독립 검산 후 EXPERIMENTAL이다. "
               "PITCH 2023·2026-09-07 외부, SWING 2023 외부 진단을 완료했고 SWING 2026은 측정 정합성 부족으로 보류했다. "
               "각 모델 8회 전체 재학습은 안정성 진단이며 완전한 95% 구간이 아니다. 모든 행동 추천을 보류하며 OBS/Ridge의 상태 검증과 구분한다. "
               "KBO·Drive·외부 게시 작업은 하지 않았다.")
    column = replace_once(column, old_col, new_col, "column latest BCAP paragraph")
    old_tree = """├─ models/
│  ├─ registry.md
│  ├─ migration_20260908.md / migration_20260908.json
│  └─ bcai/
│     ├─ README.md
│     ├─ observed/v1.0.0/  # model_card.md, specification.yaml, validation.md
│     └─ ridge/
│        ├─ v0.1.0/      # 기존 모델 정의 보존
│        └─ v0.2.0/      # 정의·사전 계획·고정 코드·검증 문서"""
    new_tree = """├─ models/
│  ├─ registry.md
│  ├─ migration_20260908.md / migration_20260908.json
│  ├─ bcai/
│  │  ├─ README.md
│  │  ├─ observed/v1.0.0/  # model_card.md, specification.yaml, validation.md
│  │  └─ ridge/
│  │     ├─ v0.1.0/      # 기존 모델 정의 보존
│  │     └─ v0.2.0/      # 정의·사전 계획·고정 코드·검증 문서
│  └─ bcap/
│     ├─ README.md / design_decisions.md / measurement_review.md
│     ├─ pitch/v0.1.0/ / swing/v0.1.0/  # 카드·불변 명세·검증
│     ├─ run.py / data.py / verify_bcap.py
│     ├─ refit_stability.py / supplement_diagnostics.py
│     ├─ build_report.py / finish_documents.py / record_invocations.py
│     └─ check_artifacts.py / finalize_seal.py"""
    readme = replace_once(readme, old_tree, new_tree, "README model structure")
    tree_anchor = "│     │  ├─ bcai_paths.py\n│     │  └─ runs/"
    tree_new = ("│     │  ├─ bcai_paths.py\n│     │  ├─ bcap_original_handoff_20260909/  # 원 인계·문서 스냅샷 보존\n"
                "│     │  ├─ bcap_implementation_review_20260909/  # 독립 검산·보조 표\n"
                "│     │  ├─ bcap_report_20260909_r01/  # 16종 CSV·보고 manifest\n"
                "│     │  ├─ bcap_document_backups_20260909_r01/  # MD 갱신 전 보존\n"
                "│     │  └─ runs/             # BCAI 및 BCAP 개발·외부·재학습·실패 실행 보존")
    readme = replace_once(readme, tree_anchor, tree_new, "README analysis structure")
    readme += ("\n\n## " + MARKER + "\n\n두 BCAP 모델은 EXPERIMENTAL이다. 실제 개발과 외부 진단·독립 검산을 수행했지만 "
               "행동 추천은 없으며 SWING의 2026 검증은 측정 정의 불일치로 보류했다. "
               + link(rootdoc, MODEL / "README.md", "모델 안내") + " · " + link(rootdoc, REPORT, "주 보고서") + " · "
               + link(rootdoc, UPDATE, "수정 MD와 변경 이력") + ". 기존 BCAI 자산·원본·실행은 보존하고 KBO·Drive·외부 게시에는 반영하지 않았다.\n")
    column += ("\n\n## " + MARKER + f"\n\n갱신 {context['at']}.\n\n" + summary_table(coldoc, context["records"]) + "\n\n"
               "BCAP의 현재 한 구 행동 진단은 이전 카운트 상태 지수와 별개다. 원 단위 W·선택된 의사결정 행 분모·공통 지지를 사용하며 "
               "조건부 구간과 8회 재학습 안정성의 범위를 구분한다. 자세한 해석은 " + link(coldoc, REPORT, "카운트별 보고서") + "를 따른다. "
               "다음 BCAP 검수는 식별·지각 측정·2026 좌표/존 교량·완전한 학습 구간의 증거 확보다. "
               "아래에 보존된 KBO·경로·협업 계획을 자동으로 시작하지 않는다. " + link(coldoc, UPDATE, "로컬 MD 반영 기록") + ".\n")
    src_lines = ["\n\n## " + MARKER, "", f"기록 {context['at']}. 신규 원본 수집 없이 기존 2024·2025 및 BCAI/Ridge용 2023·2026 스냅샷을 재사용했다. "
                 "기존 원본·정제본·실행은 덮어쓰지 않고 새 BCAP 정제본과 실행 디렉터리를 만들었다. 기존 MLB 이용 조건과 원본 재배포 권한 미확인 범위는 그대로다.", ""]
    src_rows = []
    for p in context["preparations"]:
        c = p["content"]
        src_rows.append(["·".join(map(str, c.get("years", []))), fmt(c.get("raw_rows"), 0), fmt(c.get("eligible_PA"), 0),
                         fmt(c.get("eligible_pitch_rows"), 0), fmt(c.get("eligible_swing_rows"), 0),
                         link(sourcedoc, ROOT / p["file"]["path"], "정제 감사"), link(sourcedoc, ROOT / c["output"]["path"], "새 정제본")])
    src_lines += [table(["시즌", "원본 행", "유효 PA", "PITCH 적격 행", "SWING 라벨 적격 행", "출처·제외·키·해시", "출력"], src_rows), "",
                  "정제 감사의 SWING 라벨 적격 수와 실제 위치 기반 모형 평가 완료는 다르다. 2026 SWING 모델 평가 자체는 보류했으며 "
                  "PITCH 정제 과정에서 행동 라벨을 만들었다고 SWING 외부 검증을 수행한 것으로 세지 않는다.", "",
                  "2026 결과 가중치는 기존 2025값 고정이다. 최종 봉인 " + link(sourcedoc, SEAL, "모델·코드·정책·입력 SHA256") +
                  " 이후 이번 BCAP 외부 결과에 접근한 시각은 " + link(sourcedoc, EVIDENCE, "실행 증거") + "를 따른다. "
                  "2023·2026은 앞선 BCAI/Ridge에서 이미 사용한 자료라는 노출 이력을 유지한다.", "",
                  "일차 공개 근거는 " + link(sourcedoc, MODEL / "measurement_review.md", "BCAP 측정·규칙 검토") + "에 저장했다. "
                  "[MLB Savant CSV 설명](https://baseballsavant.mlb.com/csv-docs)의 2026 plate 앞면→중간면 및 운영자→ABS 존 변경을 확인했고, "
                  "[MLB 공식 2026 ABS 안내](https://img.mlbstatic.com/opprops-images/image/upload/opprops/jgdgj1bak2bgiskwpdnm.pdf)와 "
                  "[2023 공식 규칙](https://img.mlbstatic.com/mlb-images/image/upload/mlb/wqn5ah4c3qtivwx3jatm.pdf)의 HBP·번트 정의를 참조했다. "
                  "열람일 2026-09-09. 미분류 행동을 Take로 채우지 않으며 번트 포함 공격 시도와 순수 full swing을 구분한다.", "",
                  "이 변경은 로컬 기록에만 적용했다. KBO 수집·분석, Drive/Docs 업로드, 외부 전송·게시·원본 재배포는 하지 않았다.", ""]
    sources += "\n".join(src_lines)
    registry += ("\n\n## " + MARKER + "\n\n"
                 + table(["모델", "현재 상태", "추정 대상", "개발·외부 범위", "정의·검증"], [
                     ["BCAP-PITCH-v0.1.0", "EXPERIMENTAL · 추천 없음", "같은 실제 상태에서 현재 한 구 FB/NFB 최종 PA W 비교", "2024·2025 개발; 2023·2026-09-07 진단; 8회 재학습 안정성",
                      link(regdoc, MODEL / "pitch/v0.1.0/model_card.md", "카드") + " · " + link(regdoc, MODEL / "pitch/v0.1.0/specification.yaml", "명세") + " · " + link(regdoc, MODEL / "pitch/v0.1.0/validation.md", "검증")],
                     ["BCAP-SWING-v0.1.0", "EXPERIMENTAL · 추천 없음", "사후 공 특성 조건부 번트 포함 Swing/판정상 Take의 현재 한 구 W 비교", "2024·2025 개발; 2023 진단; 2026 전체 보류; 8회 재학습 안정성",
                      link(regdoc, MODEL / "swing/v0.1.0/model_card.md", "카드") + " · " + link(regdoc, MODEL / "swing/v0.1.0/specification.yaml", "명세") + " · " + link(regdoc, MODEL / "swing/v0.1.0/validation.md", "검증")]])
                 + "\n\nBCAP-JOINT는 식별·순차 정보·SWING 외부 근거가 충분하지 않아 설계하지 않았다. "
                 "봉인 명세의 status_at_definition=DRAFT는 최초 등록 이력이며 현재 카드의 EXPERIMENTAL이 실행 후 상태다. "
                 "이 상태는 인과 추천·실시간 배포·전체 PA 개선의 검증을 뜻하지 않는다. " + link(regdoc, MODEL / "README.md", "모델/실행 목록") + " · "
                 + link(regdoc, REPORT, "실제 보고서") + " · " + link(regdoc, EVIDENCE, "입출력·명령·열람 증거") + ".\n")
    docs[rootdoc] = (readme, "BCAP 현재 상태·다음 검수와 실제 폴더/도구 구조를 갱신; BCAI·Drive 기존 내용 유지")
    docs[coldoc] = (column, "BCAP 미착수 문단을 실제 EXPERIMENTAL 범위로 교체하고 실행별 완료/보류·해석 연결 추가")
    docs[sourcedoc] = (sources, "기존 원본 재사용·새 정제본 감사·2026 정의와 가중치·공개 일차 출처·업로드 미실시 추가")
    docs[regdoc] = (registry, "기존 BCAI 등록 유지하며 BCAP 두 버전의 현재 상태·정의·실행 범위 등록")
    for variant in ["pitch", "swing"]:
        card = MODEL / variant / "v0.1.0/model_card.md"
        validation = card.with_name("validation.md")
        if "상태: DRAFT. 실제 데이터 개발 실행 전 등록." not in read_text(card):
            raise ValueError("Model card already changed; inspect before replacing")
        if "DRAFT. 아직 적합·외부 평가하지 않았다." not in read_text(validation):
            raise ValueError("Validation doc already changed; inspect before replacing")
        docs[card] = (model_card(card, variant, context), "최초 DRAFT 역사와 실제 EXPERIMENTAL 상태·추정 대상·외부/권고 한계·실행 링크 기록")
        docs[validation] = (model_validation(validation, variant, context), "실제 수렴·분할·독립 PASS·외부 평가와 8회 재학습 한계에 맞춰 검증 범위 갱신")
    model_doc = MODEL / "README.md"
    if model_doc.exists():
        raise FileExistsError("Do not overwrite an existing BCAP README without inspection")
    docs[model_doc] = (model_readme(model_doc, context), "BCAP 모델 역할·실행 ID·코드 위치·재현과 보존 규칙을 새 안내로 생성")
    handoff = ANAL / "handoff_bcap_review.md"
    docs[handoff] = (make_handoff(handoff, context), "원 인계 별도 보존 후 실제 실행·수치·정책·외부 열람·검산·미완료 증거를 자급식 인계로 갱신")
    return docs


def evidence(context):
    records = []
    for r in context["records"]:
        m = r["manifest"]
        records.append({"alias": r["alias"], "manifest": meta(r["path"] / "manifest.json"),
                        "run_id": m["run_id"], "model_id": m["model_id"], "status": m["status"], "role": m["role"],
                        "started_at_utc": m.get("started_at_utc"), "finished_at_utc": m.get("finished_at_utc"),
                        "environment": m.get("environment"), "configuration": m.get("configuration"),
                        "inputs": m.get("inputs", []), "raw_inputs": m.get("raw_inputs", []),
                        "code": m.get("code", []), "definition": m.get("definition"), "outputs": m.get("outputs", []),
                        "policy_source": m.get("policy_source"), "external_access": r.get("access"),
                        "external_seal": m.get("seal"), "all_fits_converged": m.get("all_fits_converged"),
                        "fit_records": len(r["fits"]), "split_records": len(r["folds"]),
                        "all_recorded_self_intersections_zero": all(x.get("intersection_n") == 0 for x in r["folds"]) if r["folds"] else None,
                        "bootstrap_completed_replicates": m.get("completed_replicates"),
                        "no_full_learning_confidence_interval": m.get("no_full_learning_confidence_interval"),
                        "overall_action_values": r["overall"], "overall_candidate_policy": r["learned"],
                        "command": r["command"], "existing_manifest_extensions": r["extensions"]})
    return {"created_at_utc": context["at"], "scope": "Append-only execution/document evidence; original handoff evidence is unchanged",
            "generator": meta(__file__), "document_update": relative(UPDATE), "original_evidence": meta(ANAL / "handoff_bcap_review_evidence.json"),
            "actual_task_invocations_recorded_after_execution": meta(INVOCATIONS),
            "original_validation": meta(ANAL / "handoff_bcap_review_validation.json"), "original_snapshots": context["immutable"],
            "final_seal": meta(SEAL), "sealed_at_utc": context["seal"]["sealed_at_utc"],
            "external_inputs_hashed_before_access": context["seal"].get("external_input_hashes_before_action_result_access", []),
            "runs": records, "preparation_audits": context["preparations"], "independent_verifications": context["verifications"],
            "supplemental_manifests": context["supplements"], "additional_source_feature_validations": context["auxiliary_validations"],
            "independent_final_bootstrap_validation": context["bootstrap_validation"],
            "legacy_asset_preservation_audit": context["legacy_preservation"],
            "postseal_behavior_presentation_existing_input_output_hashes": context["behavior_comparison"],
            "postseal_descriptive_comparison": context["postseal_comparison"], "report_manifest": meta(TABLEDIR / "report_manifest.json"),
            "report": meta(REPORT), "reproduction_report_command": context["reproduction_argv"],
            "final_preservation_hash_link_audit_after_document_update": {"path": relative(FINAL_AUDIT), "status_at_document_generation": "PLANNED_OUTPUT_NOT_YET_VALIDATED"},
            "limits": {"no_recommended_actions": True, "no_causal_identification": True,
                       "swing_2026_measurement_withheld": True, "full_learning_95_interval_available": False,
                       "relearning_replicates_per_model": 8, "KBO_Drive_external_posts": "not performed"}}


def validate_links(docs):
    future = set(docs) | {EVIDENCE, UPDATE}
    errors = []
    for doc, (text, _) in docs.items():
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            path = (doc.parent / target.split("#")[0].strip("<>")).resolve()
            if not path.exists() and path not in future:
                errors.append(relative(doc) + " -> " + target)
    if errors:
        raise ValueError("Proposed documentation contains broken local links: " + "; ".join(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Required to apply after all prerequisite runs/reports have completed")
    args = parser.parse_args()
    if not args.apply:
        parser.error("--apply is required; this is a final documentation step, not a background watcher")
    context = load_all()
    context["at"] = now()
    context["reproduction_text"], context["reproduction_argv"] = reproduction(context)
    documents = build_documents(context)
    validate_links(documents)
    for doc in documents:
        if relative(doc) in context["sealed_before"]:
            raise ValueError("Refusing to change a sealed file: " + relative(doc))
    updates = []
    original_bytes = {doc: doc.read_bytes() if doc.exists() else None for doc in documents}
    execution_evidence = evidence(context)
    # Everything above is read-only. Preserve original MD bytes before mutation.
    BACKUPS.mkdir(parents=True, exist_ok=False)
    for doc, before in original_bytes.items():
        if before is not None:
            backup = BACKUPS / doc.relative_to(ROOT)
            backup.parent.mkdir(parents=True, exist_ok=True)
            with backup.open("xb") as f:
                f.write(before)
    for doc, (text, reason) in documents.items():
        before = original_bytes[doc]
        after = text.encode("utf-8")
        with doc.open("wb") as f:
            f.write(after)
        updates.append({"path": relative(doc), "change": reason,
                        "before_sha256": hashlib.sha256(before).hexdigest() if before is not None else None,
                        "after_sha256": hashlib.sha256(after).hexdigest(), "before_bytes": len(before) if before is not None else None,
                        "after_bytes": len(after), "backup": relative(BACKUPS / doc.relative_to(ROOT)) if before is not None else None})
    write_json_exclusive(EVIDENCE, execution_evidence)
    for name, expected in context["immutable"].items():
        if sha(ROOT / name) != expected:
            raise RuntimeError("Protected original changed during documentation update: " + name)
    for name, expected in context["sealed_before"].items():
        if sha(ROOT / name) != expected:
            raise RuntimeError("Sealed artifact changed during documentation update: " + name)
    write_json_exclusive(UPDATE, {"status": "COMPLETE", "updated_at_utc": now(), "generator": meta(__file__),
                                "command": [sys.executable] + sys.argv, "modified_MD": updates,
                                "execution_evidence": meta(EVIDENCE), "immutable_originals_preserved": context["immutable"],
                                "sealed_files_preserved": context["sealed_before"],
                                "inputs_read": sorted(INPUTS.values(), key=lambda x: x["path"]),
                                "verification": {"all_9_expected_run_statuses_checked": True,
                                                 "5_complete_action_evaluations_1_measurement_withheld": True,
                                                 "both_8_replicate_bootstraps_complete": True,
                                                 "both_8_replicate_bootstrap_independent_audits_PASS": True,
                                                 "legacy_prior_hash_scope_checked_missing_or_mismatch_zero": True,
                                                 "five_independent_validations_PASS": True,
                                                 "six_run_report_16_tables_hash_checked": True,
                                                 "proposed_local_links_checked": True,
                                                 "no_sealed_model_or_specification_changed": True,
                                                 "original_handoff_evidence_validation_untouched": True,
                                                 "raw_data_rehash": "Not part of this document generator; use check_artifacts.py"}})
    print(json.dumps({"status": "COMPLETE", "modified_MD": [x["path"] for x in updates],
                      "audit": relative(UPDATE), "evidence": relative(EVIDENCE)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
