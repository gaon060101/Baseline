"""Create reviewable BCAP tables and Korean prose from completed aggregate outputs.

No model engine imports, fitting, row-level reads, collection or network calls.
Inputs are explicit run IDs/directories. Existing report artifacts are never
overwritten. External runs must cite an existing matching seal. The report's
provenance manifest records every aggregate file actually read.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
COL = ROOT / "columns/001-ball-count"
ANAL = COL / "analysis"
RUNS = ANAL / "runs"
sys.path.insert(0, str(ANAL / "runtime_ridge_v02"))
import pandas as pd

COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]
UNIT = "season-weighted final PA W per selected current decision; no summed PA policy gain"
READS: dict[str, dict] = {}
MODEL_NAMES = {"pitch": "BCAP-PITCH-v0.1.0", "swing": "BCAP-SWING-v0.1.0"}
TABLE_NAMES = [
    (1, "bcai_state_values", "카운트별 BCAI 상태 가치"),
    (2, "pitch_observed_rates", "카운트별 FB/NFB 실제 선택 비율"),
    (3, "pitch_standardized_values", "카운트별 FB/NFB 보정 기대 공격가치"),
    (4, "pitch_differences", "투수 행동가치 차이와 구간"),
    (5, "pitch_grades", "투수 판정 등급·추천 보류"),
    (6, "swing_observed_rates", "카운트·존·구종군별 번트 포함 Swing/Take 비율"),
    (7, "swing_standardized_values", "번트 포함 Swing/Take 보정 기대 공격가치"),
    (8, "swing_differences", "타자 행동가치 차이와 구간"),
    (9, "swing_grades", "타자 판정 등급·추천 보류"),
    (10, "policy_values", "동일 평가집단의 실제·고정·학습·보수 정책 가치"),
    (11, "propensity_overlap_diagnostics", "표본·propensity·calibration·가중치·공통 지지 진단"),
    (12, "known_unseen", "개발 선수 사전 기준 known/unseen 결과"),
    (13, "external_2023", "2023 외부 재현"),
    (14, "external_2026", "2026-09-07까지 외부 평가·SWING 측정 보류"),
    (15, "sensitivity", "trimming/clipping·반복 도달·군집·전체 재학습 민감도"),
    (16, "unavailable_states", "판정 불가 상태와 필요한 증거"),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def rel(path):
    path = Path(path).resolve()
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    path = Path(path).resolve()
    value = path.read_bytes()
    record = {"path": rel(path), "sha256": digest(value), "bytes": len(value)}
    if str(path) in READS and READS[str(path)] != record:
        raise RuntimeError("Input changed during report generation: " + str(path))
    READS[str(path)] = record
    return value


def read_json(path):
    return json.loads(read_bytes(path).decode("utf-8-sig"))


def read_csv(path):
    try:
        return pd.read_csv(io.BytesIO(read_bytes(path)), encoding="utf-8-sig")
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


def artifact_meta(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": rel(path), "sha256": digest(data), "bytes": len(data)}


def run_path(value):
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    if len(path.parts) == 1:
        return (RUNS / path).resolve()
    return (ROOT / path).resolve()


def require_in_analysis(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ANAL.resolve()):
        raise ValueError("Reports must stay under this column's analysis directory: " + str(path))
    return path


def load_run(value, variant, period):
    path = run_path(value)
    manifest = read_json(path / "manifest.json")
    if manifest.get("model_id") != MODEL_NAMES[variant]:
        raise ValueError("Wrong model in " + str(path))
    allowed = {"COMPLETE", "WITHHELD"} if period != "2024_2025" else {"COMPLETE"}
    if manifest.get("status") not in allowed:
        raise ValueError("Report requires a completed or explicitly withheld run: " + str(path))
    expected_role = "development_2024_2025" if period == "2024_2025" else "external_" + period
    if manifest.get("role") != expected_role:
        raise ValueError("Unexpected role in " + str(path))
    if period != "2024_2025":
        seal = manifest.get("seal")
        if not seal or "path" not in seal or "sha256" not in seal:
            raise ValueError("External run lacks its pre-evaluation seal")
        if digest(read_bytes(ROOT / seal["path"])) != seal["sha256"]:
            raise ValueError("External seal hash changed")
    if manifest.get("status") == "WITHHELD" and (variant, period) != ("swing", "2026"):
        raise ValueError("Unexpected withholding; review instead of silently labeling it")
    run = {"path": path, "manifest": manifest, "variant": variant, "period": period,
           "run_id": manifest["run_id"], "model_id": manifest["model_id"],
           "execution_status": manifest["status"], "artifacts": {}}
    if manifest["status"] == "COMPLETE":
        for name in ["action_values", "policy_values", "propensity_overlap", "calibration",
                     "known_unseen", "sensitivity", "support_exclusions", "fit_diagnostics"]:
            run["artifacts"][name] = read_csv(path / "artifacts" / (name + ".csv"))
        run["metrics"] = read_json(path / "artifacts/metrics.json")
        validate_aggregates(run)
        if period == "2024_2025":
            run["final_policy"] = read_json(path / "artifacts/final_policy.json")
        if period != "2024_2025":
            fixed = path / "artifacts/fixed_prediction_diagnostics"
            run["fixed_metrics"] = read_json(fixed / "metrics.json")
            run["fixed_calibration"] = read_csv(fixed / "calibration.csv")
            run["fixed_known_unseen"] = read_csv(fixed / "known_unseen.csv")
            run["access_log"] = read_json(path / "artifacts/external_access_log.json")
    return run


def validate_aggregates(run):
    action = run["artifacts"]["action_values"]
    required = {"level", "state", "n_all", "n", "coverage", "grade", "reason"}
    if not required.issubset(action):
        raise ValueError("Action summary schema mismatch: " + run["run_id"])
    if action.duplicated(["level", "state"]).any():
        raise ValueError("Duplicate action-summary key")
    count = action[action.level.eq("count")]
    if set(count.state.astype(str)) != set(COUNTS):
        raise ValueError("Expected exactly twelve count rows")
    overall = action[action.level.eq("overall")]
    if len(overall) != 1 or int(count.n_all.sum()) != int(overall.iloc[0].n_all):
        raise ValueError("Count all-row denominators do not sum to overall")
    if int(count.n.sum()) != int(overall.iloc[0].n):
        raise ValueError("Count support-row denominators do not sum to overall")
    if not action.grade.isin(["UNCERTAIN", "NO_SUPPORT"]).all():
        raise ValueError("v0.1.0 reporting refuses unsupported recommendation grades")
    if "suggested_action" in action and action.suggested_action.notna().any():
        raise ValueError("No v0.1.0 action recommendation is authorized by its gates")
    valid = action.n.gt(0)
    if not ((action.n >= 0) & (action.n <= action.n_all)).all():
        raise ValueError("Invalid support denominator")
    if valid.any():
        delta_error = (action.loc[valid, "Q1"] - action.loc[valid, "Q0"] - action.loc[valid, "delta"]).abs().max()
        if delta_error > 1e-9:
            raise ValueError("AIPW delta is not Q1 minus Q0")
    policies = run["artifacts"]["policy_values"]
    if policies.duplicated(["level", "state", "policy"]).any():
        raise ValueError("Duplicate policy key")
    checked = policies.merge(action[["level", "state", "n"]], on=["level", "state"],
                             how="left", suffixes=("_policy", "_action"), validate="many_to_one")
    if not checked.n_policy.eq(checked.n_action).all():
        raise ValueError("Policy and action values use different denominators")
    for (level, state), group in policies.groupby(["level", "state"], observed=True):
        observed = group[group.policy.eq("observed")]
        if len(observed) != 1:
            raise ValueError("Missing observed-policy baseline")
        sign = -1 if run["variant"] == "pitch" else 1
        err = (group.gain - sign * (group.value - float(observed.iloc[0].value))).abs().max()
        if err > 1e-9:
            raise ValueError("Policy gain sign or baseline mismatch")
    if run["variant"] == "swing":
        cells = action[action.level.eq("cell")]
        if int(cells.n_all.sum()) != int(overall.iloc[0].n_all) or int(cells.n.sum()) != int(overall.iloc[0].n):
            raise ValueError("Swing-cell denominators do not sum to overall")


def tagged(frame, run, evaluation_method=None):
    frame = frame.copy()
    for name in ["run_id", "model_id", "variant", "period", "execution_status"]:
        frame[name] = run[name]
    frame["evaluation_method"] = evaluation_method or (
        "outer_game_nested_procedure_OPE" if run["period"] == "2024_2025"
        else "fixed_development_policy_external_crossfit_nuisance_OPE")
    frame["unit"] = UNIT
    frame["column_units"] = "Q/value/delta/gain: raw W; outcome MSE: W^2; probabilities/coverage: fraction; sample counts: explicit rows/PA/games"
    frame["action0_label"] = "NFB" if run["variant"] == "pitch" else "Take_adjudicated"
    frame["action1_label"] = "FB" if run["variant"] == "pitch" else "Swing_offer_including_bunts"
    return frame


def decode_cells(frame):
    frame = frame.copy()
    frame["count"] = frame["state"]
    frame["zone"] = pd.NA
    frame["pitch_group"] = pd.NA
    mask = frame.level.eq("cell")
    if mask.any():
        pieces = frame.loc[mask, "state"].astype(str).str.split("|", regex=False, expand=True)
        if pieces.shape[1] != 3:
            raise ValueError("Unexpected swing-cell key")
        frame.loc[mask, ["count", "zone", "pitch_group"]] = pieces.to_numpy()
    return frame


def add_saved_policy(frame, run):
    """Saved whole-development policy differs from outer-fold candidate policies."""
    frame = frame.copy()
    policy = run["saved_development_policy"]
    applicable = frame.level.eq("count" if run["variant"] == "pitch" else "cell")
    frame["saved_development_policy_p1"] = pd.NA
    frame["saved_development_policy_role"] = "Frozen diagnostic candidate; never a recommended action"
    for idx, row in frame[applicable].iterrows():
        entry = policy["states"].get(str(row["state"]))
        frame.at[idx, "saved_development_policy_p1"] = entry["p1"] if entry else policy["fallback_p1"]
    if "candidate_direction" in frame:
        frame = frame.rename(columns={"candidate_direction": "evaluation_contrast_direction"})
    return frame


def project(frame, columns):
    # Unavailable statistics remain blank, never filled with invented zeroes.
    frame = frame.copy()
    for column in columns:
        if column not in frame:
            frame[column] = pd.NA
    provenance = ["run_id", "model_id", "variant", "period", "execution_status",
                  "evaluation_method", "unit", "action0_label", "action1_label"]
    return frame[list(dict.fromkeys(columns + [c for c in provenance if c in frame]))]


def concat(frames):
    frames = [f for f in frames if f is not None and len(f)]
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def status_record(run):
    return tagged(pd.DataFrame([{
        "record_type": "evaluation_status", "evaluation_status": run["manifest"].get("evaluation_status", "WITHHELD"),
        "reason": run["manifest"].get("reason"), "grade": pd.NA,
        "numeric_estimate_available": False,
    }]), run, "not_evaluated_measurement_noncomparability")


def bcai_table():
    obs_path = RUNS / "bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_count_results.csv"
    ridge_path = RUNS / "bcai_ridge__mlb_2024_2025__20260908__r02/artifacts/count_indices.csv"
    obs = read_csv(obs_path)
    ridge = read_csv(ridge_path)
    ridge = ridge[ridge.period.eq("combined")].copy()
    obs = obs[["count", "index", "CI95_low", "CI95_high", "simultaneous95_low", "simultaneous95_high",
               "confirmed_grade", "N_PA"]].rename(columns={
                   "index": "OBS_I", "CI95_low": "OBS_CI95_low", "CI95_high": "OBS_CI95_high",
                   "simultaneous95_low": "OBS_simultaneous95_low", "simultaneous95_high": "OBS_simultaneous95_high",
                   "confirmed_grade": "OBS_confirmed_grade", "N_PA": "OBS_N_PA"})
    ridge = ridge[["count", "N", "J", "shift"]].rename(columns={"N": "Ridge_N_PA", "J": "Ridge_v02_J", "shift": "Ridge_J_minus_I"})
    result = obs.merge(ridge, on="count", how="outer", validate="one_to_one")
    if set(result["count"]) != set(COUNTS) or result[["OBS_I", "Ridge_v02_J"]].isna().any().any():
        raise ValueError("Legacy BCAI count values missing")
    result["OBS_source"] = rel(obs_path)
    result["Ridge_source"] = rel(ridge_path)
    result["unit"] = "BCAI relative index; 0-0=100; not BCAP raw W"
    result["interval_scope"] = "OBS intervals belong only to OBS; no Ridge or BCAP interval inheritance"
    return result


def external_table(runs, period):
    frames = []
    for run in runs:
        if run["period"] != period:
            continue
        if run["execution_status"] == "WITHHELD":
            frames.append(status_record(run))
            continue
        action = add_saved_policy(decode_cells(tagged(run["artifacts"]["action_values"], run)), run)
        action["record_type"] = "action_and_policy_value"
        action["evaluation_status"] = "EVALUATED"
        action["numeric_estimate_available"] = True
        for name in ["observed", "learned", "conservative", "always_0", "always_1", "stochastic_half"]:
            pol = run["artifacts"]["policy_values"]
            pol = pol[pol.policy.eq(name)][["level", "state", "value", "gain", "gain_low", "gain_high"]]
            pol = pol.rename(columns={column: name + "_" + column for column in ["value", "gain", "gain_low", "gain_high"]})
            action = action.merge(pol, on=["level", "state"], how="left", validate="one_to_one")
        for name, value in run["fixed_metrics"].items():
            action["fixed_development_prediction_" + name] = pd.NA
            action.loc[action.level.eq("overall"), "fixed_development_prediction_" + name] = value
        for name, value in run["metrics"].items():
            action["external_CF_nuisance_" + name] = pd.NA
            action.loc[action.level.eq("overall"), "external_CF_nuisance_" + name] = value
        action["access_log_source"] = rel(run["path"] / "artifacts/external_access_log.json")
        action["first_external_row_access_utc"] = run["access_log"].get("first_current_task_BCAP_external_row_access_utc")
        frames.append(action)
    return concat(frames)


def bootstrap_tables(value, development):
    if not value:
        return None, {"variant": development["variant"], "status": "NOT_PROVIDED",
                      "full_learning_interval_available": False}
    path = run_path(value)
    manifest = read_json(path / "manifest.json")
    if manifest.get("role") != "full_pipeline_game_bootstrap_stability" or manifest.get("source_development_run") != development["run_id"]:
        raise ValueError("Bootstrap diagnostic has a different procedure or source development run")
    record = {"variant": development["variant"], "status": manifest.get("status"),
              "run_id": manifest.get("run_id"), "planned_replicates": manifest.get("planned_replicates"),
              "completed_replicates": manifest.get("completed_replicates"), "full_learning_interval_available": False,
              "source": rel(path / "manifest.json")}
    if manifest.get("status") != "COMPLETE":
        raise ValueError("Only completed bootstrap diagnostics may enter the final report")
    frame = read_csv(path / "artifacts/stability_summary.csv")
    frame["variant"] = development["variant"]
    frame["model_id"] = development["model_id"]
    frame["period"] = "2024_2025"
    frame["run_id"] = manifest["run_id"]
    frame["record_type"] = "whole_pipeline_bootstrap_stability"
    frame["setting"] = "refit_preprocessing_nuisance_tuning_calibration_policy"
    frame["unit"] = "metric-dependent; finite diagnostic range is not 95% interval"
    return frame, record


def build_tables(runs, bootstrap_inputs):
    pitch = runs[0]
    swing = runs[1]
    pa = add_saved_policy(decode_cells(tagged(pitch["artifacts"]["action_values"], pitch)), pitch)
    sa = add_saved_policy(decode_cells(tagged(swing["artifacts"]["action_values"], swing)), swing)
    pa = pa[pa.level.eq("count")].copy()
    sa = sa[sa.level.isin(["count", "cell"])].copy()
    counts = ["level", "state", "count", "zone", "pitch_group", "n_all", "n", "coverage", "games", "PA", "pitchers", "batters"]
    rates = counts + ["action0_rate_all", "action1_rate_all", "action0_rate_support", "action1_rate"]
    for frame in [pa, sa]:
        frame["action0_rate_all"] = 1 - frame.action1_rate_all
        frame["action0_rate_support"] = 1 - frame.action1_rate
    values = counts + ["Q0", "Q1", "gcomp0", "gcomp1"]
    differences = counts + ["delta", "se", "CI95_low", "CI95_high", "simultaneous95_low", "simultaneous95_high", "ESS0", "ESS1", "arm_games0", "arm_games1", "max_game_share0", "max_game_share1"]
    grades = counts + ["grade", "reason", "suggested_action", "evaluation_contrast_direction", "saved_development_policy_p1", "saved_development_policy_role", "ESS0", "ESS1", "arm_games0", "arm_games1"]
    tables = {
        1: bcai_table(), 2: project(pa, rates), 3: project(pa, values), 4: project(pa, differences), 5: project(pa, grades),
        6: project(sa[sa.level.eq("cell")], rates), 7: project(sa, values), 8: project(sa, differences), 9: project(sa, grades),
    }
    policies, diag, known, sensitivity, unavailable = [], [], [], [], []
    for run in runs:
        if run["execution_status"] == "WITHHELD":
            record = status_record(run)
            for target in [policies, diag, known, sensitivity, unavailable]:
                target.append(record)
            continue
        policies.append(decode_cells(tagged(run["artifacts"]["policy_values"], run)))
        for name in ["propensity_overlap", "calibration", "support_exclusions", "fit_diagnostics"]:
            frame = tagged(run["artifacts"][name], run)
            frame["record_type"] = name
            frame["source"] = rel(run["path"] / "artifacts" / (name + ".csv"))
            diag.append(frame)
        metrics = tagged(pd.DataFrame([run["metrics"]]), run)
        metrics["record_type"] = "aggregate_nuisance_prediction_metrics"
        diag.append(metrics)
        known.append(tagged(run["artifacts"]["known_unseen"], run))
        if run["period"] != "2024_2025":
            fixed = tagged(pd.DataFrame([run["fixed_metrics"]]), run, "fixed_development_prediction_only")
            fixed["record_type"] = "aggregate_fixed_development_prediction_metrics"
            diag.append(fixed)
            fixedcal = tagged(run["fixed_calibration"], run, "fixed_development_prediction_only")
            fixedcal["record_type"] = "fixed_development_calibration"
            diag.append(fixedcal)
            fixedknown = tagged(run["fixed_known_unseen"][["group", "n", "games", "coverage", "MSE", "Brier"]], run, "fixed_development_prediction_only")
            fixedknown["note"] = "Prediction errors only; fixed development propensity is not assumed correct for external OPE"
            known.append(fixedknown)
        sens = decode_cells(tagged(run["artifacts"]["sensitivity"], run))
        sens["record_type"] = "fixed_score_sensitivity"
        sensitivity.append(sens)
        un = decode_cells(tagged(run["artifacts"]["action_values"], run))
        un = un[un.grade.isin(["UNCERTAIN", "NO_SUPPORT"])].copy()
        un["record_type"] = "evaluated_but_no_recommendation"
        un["evaluation_status"] = "EVALUATED"
        un["needed_evidence"] = un.grade.map({
            "UNCERTAIN": "Causal/measurement identification and adequate nuisance+policy relearning uncertainty; reproducible fixed policy value",
            "NO_SUPPORT": "Both-action overlap, adequate rows/arm-games/ESS, coverage and lower game concentration; then identification and uncertainty"})
        unavailable.append(project(un, ["record_type", "evaluation_status", "level", "state", "count", "zone", "pitch_group", "n_all", "n", "coverage", "grade", "reason", "needed_evidence", "suggested_action"]))
    bootstrap_records = []
    for development, value in [(pitch, bootstrap_inputs[0]), (swing, bootstrap_inputs[1])]:
        frame, record = bootstrap_tables(value, development)
        sensitivity.append(frame)
        bootstrap_records.append(record)
        unavailable.append(pd.DataFrame([{
            "record_type": "uncertainty_scope", "model_id": development["model_id"], "variant": development["variant"],
            "period": "2024_2025", "evaluation_status": "FULL_LEARNING_95_INTERVAL_UNAVAILABLE", "grade": pd.NA,
            "reason": "No adequate full nuisance+policy-relearning 95% interval; small diagnostic resample count is not a CI",
            "needed_evidence": "Larger valid relearning design, tie-sensitive policy inference and cross-game player-dependence treatment",
        }]))
    unavailable.append(pd.DataFrame([{
        "record_type": "joint_model_not_designed", "model_id": "BCAP-JOINT", "evaluation_status": "NOT_DESIGNED",
        "grade": pd.NA, "reason": "Prerequisite identification, sequential information and external SWING evidence insufficient",
        "needed_evidence": "Validated component models and sequential payoff identification with response/adaptation assumptions",
    }]))
    tables.update({10: concat(policies), 11: concat(diag), 12: concat(known), 13: external_table(runs, "2023"),
                   14: external_table(runs, "2026"), 15: concat(sensitivity), 16: concat(unavailable)})
    return tables, bootstrap_records


def missing(value):
    return value is None or (not isinstance(value, (list, dict)) and bool(pd.isna(value)))


def fmt(value, digits=4):
    if missing(value):
        return "미산출"
    try:
        x = float(value)
        return f"{x:,.{digits}f}" if math.isfinite(x) else "미산출"
    except (TypeError, ValueError):
        return str(value)


def pct(value):
    return "미산출" if missing(value) else f"{100 * float(value):.1f}%"


def interval(row, low="simultaneous95_low", high="simultaneous95_high"):
    return f"[{fmt(row.get(low))}, {fmt(row.get(high))}]"


def clean(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(headers, rows):
    return "\n".join(["| " + " | ".join(map(clean, headers)) + " |",
                      "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(map(clean, row)) + " |" for row in rows])


def link(path, label, report):
    relative = Path(os.path.relpath(Path(path).resolve(), report.parent.resolve())).as_posix()
    return f"[{label}]({relative})"


def summary_row(run, level="overall", state="ALL"):
    if run["execution_status"] != "COMPLETE":
        return None
    frame = run["artifacts"]["action_values"]
    found = frame[frame.level.eq(level) & frame.state.astype(str).eq(state)]
    return found.iloc[0].to_dict() if len(found) == 1 else None


def policy_row(run, name="learned", level="overall", state="ALL"):
    if run["execution_status"] != "COMPLETE":
        return None
    frame = run["artifacts"]["policy_values"]
    found = frame[frame.level.eq(level) & frame.state.astype(str).eq(state) & frame.policy.eq(name)]
    return found.iloc[0].to_dict() if len(found) == 1 else None


def external_count_text(run, count):
    if run["execution_status"] == "WITHHELD":
        return "2026 SWING: 위치 기준면·존 정의 정합성이 확보되지 않아 전체 평가 보류. 수치·표본 기반 등급 없음."
    row = summary_row(run, "count", count)
    if row is None:
        return run["period"] + ": 해당 카운트 결과 미산출."
    value = policy_row(run, "learned", "count", count)
    policy_text = (f" 고정 개발 후보 정책의 개선량 {fmt(value['gain'])} W, 동시 구간 {interval(value, 'gain_low', 'gain_high')}."
                   if value else " 정책가치는 공통 지지 없어 미산출.")
    return (f"{run['period']}: Δ {fmt(row.get('delta'))} W, 동시 구간 {interval(row)}, "
            f"지지 {fmt(row.get('n'), 0)}/{fmt(row.get('n_all'), 0)}행({pct(row.get('coverage'))}), {row.get('grade')}." + policy_text)


def report_text(runs, tables, catalog, bootstrap_records, report):
    pitch, swing, p23, s23, p26, s26 = runs
    lines = ["# BCAP v0.1.0 실제 개발·외부 평가 보고서", "",
             f"작성 시각: {now()}. 대상: 001-ball-count. 이 문서는 저장된 실행 집계만 읽은 후처리 결과다.", "",
             "두 모델의 실행 상태는 아래와 같다. 모든 실행된 행동 비교는 **UNCERTAIN 또는 NO_SUPPORT**이며 행동 추천은 없다. "
             "학습한 후보 정책의 값과 실제 적용 권고를 구분한다. 2026 SWING은 측정 정의가 달라 전체 평가를 보류했다.", ""]
    overview = []
    for run in runs:
        r = summary_row(run)
        p = policy_row(run)
        overview.append([run["variant"].upper(), run["period"], run["execution_status"],
                         fmt(r.get("n_all"), 0) if r else "미평가", fmt(r.get("n"), 0) if r else "미평가",
                         pct(r.get("coverage")) if r else "미평가", fmt(p.get("gain")) if p else "미산출",
                         interval(p, "gain_low", "gain_high") if p else "미산출",
                         r.get("grade") if r else "등급 없음"])
    lines += [markdown_table(["모델", "기간", "실행", "전체 적격 행", "지지 행", "지지 비율", "후보 개선량 W", "조건부 동시95% 구간", "전체 판정"], overview), "",
              "PITCH 개선량은 관찰 가치−후보 가치, SWING 개선량은 후보 가치−관찰 가치다. 양수는 점추정상 개선 방향이다. "
              "이 표의 ‘전체’는 의사결정 행의 빈도로 가중한 집단이며 PA당 효과를 더한 값이 아니다. 보수 정책은 전 영역에서 실제 행동 메커니즘을 유지하므로 개선량 0은 정의상 결과다.", "",
              "## 1. 정의와 해석 범위", "",
              "결과 W는 기존 OBS의 시즌별 선형 가중치를 최종 PA 결과에 부여한 원 단위다. 2026에는 2025 가중치를 고정했다. "
              "BCAI의 0-0=100 지수나 즉시 득점과 단위가 다르며 상태 가치·전이 보상을 추가하지 않았다. "
              "기준 집단은 완료 PA·최종 사건 자격·실투구/행동 라벨·측정·공통 지지 조건으로 선택된 현재 의사결정 행이다. "
              "완료 PA·IBB·결측 제외는 미래 결과에 따른 선택을 포함하므로 사전 자격 표본과 같지 않다.", "",
              "PITCH는 FB=FF/SI/FC와 명시된 나머지 구종군 NFB를 비교한다. 현재 공 구속·위치·타자 반응 및 직전 위치를 입력하지 않는다. "
              "SWING은 번트·번트 인플레이를 포함한 기록상 공격 시도와 판정상 Take의 비교다. 명시적 scored HBP는 Take로 분류하며 미분류를 Take로 채우지 않는다. "
              "체크스윙·번트·일반 스윙의 행동 버전 차이와 심판 판정 오차가 남는다. 현재 공 특성은 타자의 정확한 실시간 지각이 아니라 사후 측정 대리값이므로 실시간 지침이 아니다.", "",
              "양 nuisance에 축소된 투수·타자 효과를 넣고 같은 실제 선수·상황 행에 양 행동을 적용해 평균화했다. "
              "개인 절편으로 구종 품질·당일 컨디션·투구 의도·타자 예상·미측정 교란이 제거됐다고 해석하지 않는다. "
              "현재 한 구만 바꾸는 평가이며 이후 전체 타석의 행동을 바꾼 순차 정책이나 상대 적응·Nash 균형을 추정하지 않는다.", "",
              link(ROOT / "models/bcap/design_decisions.md", "원 요구 대비 설계 결정", report) + " · " +
              link(ROOT / "models/bcap/measurement_review.md", "측정·규칙·방법론 일차 출처", report), "",
              "## 2. 자료 분리·예측 성능과 OPE", "",
              "개발 outer 3개 경기 fold의 평가 경기는 그 정책의 nuisance 튜닝·전처리·범주 사전·calibration·정책 학습에서 제외됐다. "
              "outer 훈련 내부의 inner 2개 경기 fold 점수로 제한 정책을 학습했다. PITCH 정책 상태는 카운트, SWING은 카운트×존×FB/NFB다. "
              "행동별 Ridge 결과 회귀와 Ridge score+별도 훈련 경기 Platt calibration propensity를 사용했다. "
              "외부 OPE는 개발 정책·최종 hyperparameter를 고정한 채 외부 경기 교차 적합 nuisance를 썼다. "
              "고정 개발 nuisance의 외부 예측 성능은 아래에서 별도 표시하며 이를 외부 OPE로 대체하지 않는다.", ""]
    predictive = []
    for run in runs:
        if run["execution_status"] != "COMPLETE":
            continue
        for source, values in [("개발 outer OOF" if run["period"] == "2024_2025" else "외부 교차 적합 nuisance", run["metrics"]),
                               ("고정 개발 nuisance 예측", run.get("fixed_metrics"))]:
            if values is None:
                continue
            predictive.append([run["variant"].upper(), run["period"], source, fmt(values.get("outcome_MSE")),
                               fmt(values.get("Brier")), fmt(values.get("log_loss")), pct(values.get("coverage"))])
    lines += [markdown_table(["모델", "기간", "역할", "결과 MSE", "propensity Brier", "log loss", "지지 비율"], predictive), "",
              "calibration 세부 구간, 확률 분위수, 역확률 가중치, ESS, 경기 집중도와 known/unseen은 표 11·12에 있다. "
              "외부의 known/unseen은 최종 개발 선수 사전에 대한 구분이다. 미관측 선수의 중심 효과 0은 해당 행동의 자료 근거 확보를 뜻하지 않는다.", "",
              "## 3. 불확실성과 등급", "",
              "출력의 CI95는 고정 OOF 점수의 경기 군집 sandwich 구간이며, simultaneous95 및 정책 gain 구간은 사전 비교 가족의 Bonferroni 동시 범위를 사용한다. "
              "사전 가족 상한 1,536은 주 action contrast와 여섯 정책 gain 비교를 위한 것이다. 고정 개발 예측 진단의 AIPW 값, "
              "민감도·known/unseen 추가 구간과 정책 학습용 구간은 이 주 동시 추론 가족의 권고 근거로 사용하지 않는다. "
              "이는 nuisance·정책 재학습까지 포함하는 95% 구간이 아니다. 경기 간 같은 선수·시리즈의 종속성, 양 행동의 선택 교란, 동률 근처 정책 선택 불안정성도 남는다. "
              "12개 카운트·여러 셀·여러 정책을 비교하므로 점추정 순위나 개별95% 구간만으로 방향을 확정하지 않는다.", ""]
    for record in bootstrap_records:
        if record["status"] == "COMPLETE":
            lines.append(f"- {record['variant'].upper()} 전체 재학습 민감도: {record.get('completed_replicates')}회 완료. "
                         "경기 재표본마다 전처리·튜닝·calibration·nuisance·정책을 다시 학습한 유한 반복 진단이다. "
                         "범위·SD·부호 빈도는 95% 구간이나 권고 근거가 아니다. " + link(ROOT / record["source"], "실행 기록", report))
        else:
            lines.append(f"- {record['variant'].upper()} 전체 재학습 민감도: 이 보고서 입력으로 제공되지 않았다. 이를 실행 완료로 간주하지 않는다.")
    lines += ["", "NO_SUPPORT는 실행된 비교의 표본·ESS·행동별 경기 수·지지 비율·경기 집중도 조건 미충족이다. "
              "UNCERTAIN은 지원된 비교에도 식별·완전한 학습 불확실성 근거가 부족해 추천을 보류한다는 뜻이다. "
              "2026 SWING의 측정 보류와 전체 학습95% 구간 미산출은 별도 실행 상태이며 NO_SUPPORT라는 실증 결과가 아니다. "
              "미측정 교란에 대한 효과 크기 한계가 확보되지 않았으므로 좁은 통계 구간이 나와도 추천하지 않는다.", "",
              "## 4. 주요 결과표 16종", ""]
    lines.append(markdown_table(["번호", "표", "행 수", "해석"], [
        [record["number"], link(ROOT / record["path"], record["title"], report), record["rows"], record["note"]]
        for record in catalog]))
    lines += ["", "표 6–9는 카운트·존·구종군 셀 및 명시된 카운트 평균이다. 비율의 전체 적격 분모와 보정 가치의 공통 지지 분모를 구분한다. "
              "table 11은 record_type별 진단을 합친 긴 표다. table 12의 fixed_development_prediction_only는 고정 모델 예측 진단이고, "
              "그 값들을 외부 교차 적합 OPE와 합치지 않는다. table 14의 WITHHELD 한 행은 미실행 사유 기록이며 가상 표본·효과 행이 아니다. "
              "table 15의 trimming 비교는 대상 집단이 달라지고 같은 대상 clipping은 가중치 편향을 바꾸므로 동일 효과의 반복 측정으로 읽지 않는다. "
              "evaluation_contrast_direction은 해당 평가자료의 AIPW 점추정 방향이며 실제 저장된 정책의 행동과 다를 수 있다. "
              "saved_development_policy_p1은 개발 전체로 학습해 고정한 후보 정책의 행동1 확률이다. "
              "개발 outer OPE에서는 각 outer 훈련 부분에서 학습한 정책을 평가하므로 이 최종 정책의 개발 OPE라고 읽지 않는다. "
              "외부 점추정 방향을 ‘외부 최적 행동’ 정답으로 부르지 않는다.", "",
              "## 5. 카운트별 해석", ""]
    bca = tables[1].set_index("count")
    swing_cells = swing["artifacts"]["action_values"]
    external_swing_cells = s23["artifacts"]["action_values"] if s23["execution_status"] == "COMPLETE" else pd.DataFrame()
    for count in COUNTS:
        base = bca.loc[count]
        pr, sr = summary_row(pitch, "count", count), summary_row(swing, "count", count)
        lines += [f"### {count}", "",
                  f"현재 상태: BCAI-OBS I={fmt(base.OBS_I, 2)}, 기존 판정 ‘{base.OBS_confirmed_grade}’. "
                  f"BCAI-RIDGE v0.2 J={fmt(base.Ridge_v02_J, 2)}. 두 값은 카운트에 도달한 PA의 상태 진단이며 행동 선택의 이익을 뜻하지 않는다.", ""]
        for run, row, label in [(pitch, pr, "투수"), (swing, sr, "타자")]:
            if row is None:
                lines += [label + ": 이 카운트 집계가 없어 미산출.", ""]
                continue
            action0, action1 = ("NFB", "FB") if run["variant"] == "pitch" else ("Take", "번트 포함 Swing")
            lines += [f"{label} 개발: 전체 적격 행의 {action1} 비율 {pct(row.get('action1_rate_all'))}; "
                      f"보정 공통 지지 {fmt(row.get('n'), 0)}/{fmt(row.get('n_all'), 0)}행({pct(row.get('coverage'))}), "
                      f"{fmt(row.get('games'), 0)}경기·{fmt(row.get('PA'), 0)}PA. "
                      f"{action0} Q={fmt(row.get('Q0'))}, {action1} Q={fmt(row.get('Q1'))}, "
                      f"Δ({action1}−{action0})={fmt(row.get('delta'))} W, 조건부 동시95% {interval(row)}. "
                      f"행동별 ESS={fmt(row.get('ESS0'), 0)}/{fmt(row.get('ESS1'), 0)}, 판정 {row.get('grade')}. "
                      "이 방향은 추천이 아니다.", ""]
        lines += ["투수 외부: " + external_count_text(p23, count) + " " + external_count_text(p26, count), "",
                  "타자 외부: " + external_count_text(s23, count) + " " + external_count_text(s26, count), ""]
        cells = swing_cells[swing_cells.level.eq("cell") & swing_cells.state.astype(str).str.startswith(count + "|")]
        cell_rows = []
        for _, cell in cells.sort_values("state").iterrows():
            _, zone, group = str(cell.state).split("|")
            ext = external_swing_cells[external_swing_cells.state.eq(cell.state) & external_swing_cells.level.eq("cell")] if len(external_swing_cells) else pd.DataFrame()
            extdelta = fmt(ext.iloc[0].get("delta")) if len(ext) == 1 else "미산출"
            cell_rows.append([zone, group, f"{fmt(cell.get('n'), 0)}/{fmt(cell.get('n_all'), 0)}", pct(cell.get("action1_rate_all")),
                              fmt(cell.get("Q0")), fmt(cell.get("Q1")), fmt(cell.get("delta")), interval(cell), cell.get("grade"), extdelta])
        if cell_rows:
            lines += ["타자 공 특성별 진단(비율은 전체 적격 행, Q·Δ는 해당 셀 공통 지지 행):", "",
                      markdown_table(["존", "구종군", "지지/전체 행", "Swing 비율", "Q Take", "Q Swing", "Δ W", "동시95%", "등급", "2023 Δ W"], cell_rows), ""]
        lines += [f"{count} 결론: 투수·타자 행동 추천을 모두 보류한다. 집단 평균·셀의 반사실 보정은 관찰된 선택 집단과 공통 지지에 한정된다. "
                  "이 카운트의 유불리 상태만으로 매 공의 최적 행동이나 전체 PA 개선을 정할 수 없다.", ""]
    lines += ["## 6. 외부 봉인·실행·검수 연결", "",
              "2023·2026은 기존 BCAI/Ridge에서 이미 사용한 자료다. 이번 BCAP에서는 개발 정책·정의·평가 절차 해시를 먼저 고정하고 "
              "외부 자료 최초 접근 시각을 별도로 기록했다. 이것은 완전히 미노출인 데이터나 공개 사전등록을 뜻하지 않는다. "
              "2026은 9월7일까지의 진행 시즌이며 시즌 최종 검증이 아니다. KBO 수집·분석, Drive 업로드, 외부 게시·전송은 수행하지 않았다.", ""]
    for run in runs:
        lines.append("- " + run["run_id"] + ": " + link(run["path"] / "manifest.json", "실행 manifest", report))
        if run["execution_status"] == "COMPLETE" and run["period"] != "2024_2025":
            lines.append("  외부 최초 접근: " + str(run["access_log"].get("first_current_task_BCAP_external_row_access_utc")) +
                         "; " + link(ROOT / run["manifest"]["seal"]["path"], "봉인 기록", report))
    lines += ["", "별도 검수자는 먼저 (1) 입력·코드·최종 정책 해시, (2) 경기/PA 키와 outer·inner·calibration 분리, "
              "(3) 독립 AIPW/OPE 검산의 부호·단위·동일 분모, (4) 현재 사후 변수 금지 및 행동 매핑, "
              "(5) 외부 고정 예측과 외부 nuisance OPE의 분리, (6) 실제 지지와 판정 보류 이유, "
              "(7) 전체 재학습 진단의 실행 범위와 구간 제한을 확인한다. "
              "이 후처리 코드는 집계 수준의 합계·차이·정책 분모·gain 부호를 재검사한다. row-level 독립 검산을 대신하지 않는다.", "",
              "보고서와 16개 CSV의 입력·출력 해시 및 재현 명령은 " + link(report.parent / "PLACEHOLDER_MANIFEST", "후처리 manifest", report) + "에 저장한다.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ["pitch-dev", "swing-dev", "pitch-2023", "swing-2023", "pitch-2026", "swing-2026"]:
        parser.add_argument("--" + arg, required=True, help="Explicit run ID or run directory")
    parser.add_argument("--pitch-bootstrap")
    parser.add_argument("--swing-bootstrap")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    out = require_in_analysis(args.output_dir)
    report = require_in_analysis(args.report)
    if out.exists() or report.exists():
        raise FileExistsError("Preserve existing report outputs; use a new output directory and report filename")
    if report.is_relative_to(out):
        raise ValueError("Keep the report outside its table directory to avoid circular artifact ownership")
    runs = [load_run(args.pitch_dev, "pitch", "2024_2025"), load_run(args.swing_dev, "swing", "2024_2025"),
            load_run(args.pitch_2023, "pitch", "2023"), load_run(args.swing_2023, "swing", "2023"),
            load_run(args.pitch_2026, "pitch", "2026"), load_run(args.swing_2026, "swing", "2026")]
    for run in runs[2:]:
        seal = read_json(ROOT / run["manifest"]["seal"]["path"])
        if seal.get("pitch_run") != runs[0]["run_id"] or seal.get("swing_run") != runs[1]["run_id"]:
            raise ValueError("External evaluation policy seal does not match report's development runs")
    for run in runs:
        run["saved_development_policy"] = runs[0 if run["variant"] == "pitch" else 1]["final_policy"]
    tables, bootstrap_records = build_tables(runs, (args.pitch_bootstrap, args.swing_bootstrap))
    catalog = []
    for number, basename, title in TABLE_NAMES:
        frame = tables[number]
        if frame.empty:
            raise ValueError("Required table has no result or explicit unavailable record: " + str(number))
        file = out / f"{number:02d}_{basename}.csv"
        note = ("OBS 구간은 OBS에만 적용" if number == 1 else
                "고정 점수 조건부 구간; 권고 없음" if number in [4, 8, 10] else
                "평가됨·지지 부족·미실행 구분" if number in [5, 9, 14, 16] else
                "전처리 재학습 진단은 95% 구간 아님" if number == 15 else
                "원 실행의 단위·분모·역할 보존")
        catalog.append({"number": number, "title": title, "path": rel(file), "rows": len(frame), "columns": list(frame.columns), "note": note})
    content = report_text(runs, tables, catalog, bootstrap_records, report)
    placeholder = link(report.parent / "PLACEHOLDER_MANIFEST", "후처리 manifest", report)
    content = content.replace(placeholder, link(out / "report_manifest.json", "후처리 manifest", report))
    out.mkdir(parents=True, exist_ok=False)
    report.parent.mkdir(parents=True, exist_ok=True)
    for record in catalog:
        tables[record["number"]].to_csv(ROOT / record["path"], index=False, encoding="utf-8-sig")
    with report.open("x", encoding="utf-8") as handle:
        handle.write(content)
    manifest = {
        "status": "COMPLETE", "generated_at_utc": now(), "role": "postprocessing_only_no_fitting_or_row_access",
        "command": [sys.executable] + sys.argv, "generator": artifact_meta(__file__),
        "inputs": sorted(READS.values(), key=lambda value: value["path"]),
        "source_runs": [{key: run[key] for key in ["run_id", "model_id", "variant", "period", "execution_status"]} for run in runs],
        "bootstrap_diagnostics": bootstrap_records, "tables": catalog,
        "validation": {"exactly_16_tables": len(catalog) == 16, "count_sections": len(COUNTS),
                       "completed_inputs_required": True, "summary_keys_and_denominators_checked": True,
                       "gain_sign_and_Q1_minus_Q0_checked": True, "no_recommendations": True,
                       "external_seal_reference_hashes_checked": True, "row_level_independent_verification": "separate verifier required"},
        "outputs": [artifact_meta(ROOT / record["path"]) for record in catalog] + [artifact_meta(report)],
    }
    with (out / "report_manifest.json").open("x", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"status": "COMPLETE", "report": rel(report), "tables": len(catalog),
                      "provenance": rel(out / "report_manifest.json"), "inputs_read": len(READS)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
