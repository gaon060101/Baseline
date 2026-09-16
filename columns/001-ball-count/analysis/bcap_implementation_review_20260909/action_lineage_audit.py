"""Independent read-only audit of BCAP preparation, actions and feature lineage.

Run after external sealing/preparation. Does not fit models, alter action labels,
or evaluate a 2026 SWING policy. Sources already hashed by preparation are not
reread wholesale; raw retained fields, schedules and preserved OBS/Ridge audits
provide the independent reconstruction inputs.
"""
from pathlib import Path
import argparse
import ast
import datetime as dt
import hashlib
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
COL = ROOT / "columns/001-ball-count"
ANAL = COL / "analysis"
KEYS = ["game_pk", "at_bat_number", "pitch_number"]
PA = KEYS[:2]
BASE = ["pitcher", "batter", "game_year", "venue", "matchup", "count", "base_state", "outs_when_up",
        "inning_bin", "score_bin", "pitch_number_bin", "prev_pitch_type", "prev_description", "prev_release_speed_bin"]
SWING_FEATURES = ["pitch_type", "release_speed_bin", "pfx_x_bin", "pfx_z_bin", "plate_x_bin", "relative_z_bin", "swing_cell"]
FORBIDDEN = {"description", "events", "final_event", "result", "Y", "launch_speed", "launch_angle", "des", "inplay_bunt_text_flag", "A_swing", "A_pitch"}
FB = {"FF", "SI", "FC"}
NFB = {"SL", "CH", "ST", "CU", "FS", "KC", "SV", "FA", "EP", "KN", "FO", "CS", "SC"}
OFFERS = {"swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "hit_into_play", "foul_bunt", "missed_bunt", "bunt_foul_tip"}
TAKES = {"ball", "blocked_ball", "called_strike", "hit_by_pitch"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def meta(path):
    path = Path(path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path), "bytes": path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def text_mismatch(actual, expected):
    return int((actual.astype("string").fillna("__NA__") != pd.Series(expected, index=actual.index).astype("string").fillna("__NA__")).sum())


def number_mismatch(actual, expected):
    a, b = np.asarray(actual, dtype=float), np.asarray(expected, dtype=float)
    return int((~np.isclose(a, b, rtol=0, atol=1e-12, equal_nan=True)).sum())


def target_sources():
    return [
        ("development", COL / "data/processed/bcap_dev_v010_20260909_r01.pkl", ANAL / "bcap_preparation_20260909_r01/preparation_audit.json", None),
        ("2023", COL / "data/processed/bcap_2023_v010_bcap_pitch__mlb_2023__20260909__r01.pkl", ANAL / "runs/bcap_pitch__mlb_2023__20260909__r01/artifacts/preparation/preparation_audit.json", ANAL / "runs/bcai_ridge__mlb_2023__20260908__r01/artifacts/sample_audit.json"),
        ("2026_pitch_preparation_only", COL / "data/processed/bcap_2026_v010_bcap_pitch__mlb_2026_ytd_20260907__20260909__r01.pkl", ANAL / "runs/bcap_pitch__mlb_2026_ytd_20260907__20260909__r01/artifacts/preparation/preparation_audit.json", ANAL / "runs/bcai_ridge__mlb_2026_ytd_20260907__20260909__r01/artifacts/sample_audit.json"),
    ]


def feature_function():
    # Execute only the sealed engine's pure feature function, without importing
    # its solver/runtime. Independent reconstruction formulas below are separate.
    tree = ast.parse((ROOT / "models/bcap/run.py").read_text(encoding="utf-8"))
    function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "features")
    namespace = {"np": np, "pd": pd}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "sealed_features_only", "exec"), namespace)
    return namespace["features"]


def audit_one(label, path, audit_path, reference_path, feature_builder):
    prep = read(audit_path)
    if "completed_at" not in prep:
        raise RuntimeError("Preparation has not completed: " + str(audit_path))
    input_meta = meta(path)
    assert input_meta["sha256"] == prep["output"]["sha256"]
    d = pd.read_pickle(path).sort_values(KEYS).reset_index(drop=True)
    checks = {"duplicate_pitch_keys": int(d.duplicated(KEYS).sum()), "invalid_count_rows": int((~d.balls.between(0, 3) | ~d.strikes.between(0, 2)).sum())}
    g = d.groupby(PA, sort=False, observed=True)
    first = ~d.duplicated(PA)
    last = d.drop_duplicates(PA, keep="last").set_index(PA)
    begin = d.drop_duplicates(PA).set_index(PA)
    event_map = {v: k for k, vs in read(ROOT / "models/bcai/observed/v1.0.0/specification.yaml")["result_classification"].items() for v in vs}
    terminal = last.events.astype("string")
    result = terminal.map(event_map)
    start_count = begin.balls.astype(str) + "-" + begin.strikes.astype(str)
    reason = np.select([terminal.isna(), terminal.eq("intent_walk").fillna(False), terminal.eq("catcher_interf").fillna(False),
                        terminal.eq("truncated_pa").fillna(False), result.isna(), start_count.ne("0-0")],
                       ["missing_final", "intentional_walk", "catcher_interference", "truncated", "unknown_event", "no_observed_0_0"], default="included")
    reconstructed = pd.DataFrame({"final_event": terminal, "result": result, "pa_exclusion": reason})
    weights = read(ROOT / "models/bcai/ridge/v0.2.0/specification.yaml")["weights"]
    reconstructed["Y"] = [weights[str(2025 if y == 2026 else y)].get(r, 0.0) if ok == "included" else np.nan
                            for y, r, ok in zip(begin.game_year, reconstructed.result, reconstructed.pa_exclusion)]
    linked = d[PA].join(reconstructed, on=PA)
    for column in ["final_event", "result", "pa_exclusion"]:
        checks[column + "_mismatch"] = text_mismatch(d[column], linked[column])
    checks["Y_mismatch"] = number_mismatch(d.Y, linked.Y)
    checks["eligible_pa_mismatch"] = int(d.eligible_pa.ne(linked.pa_exclusion.eq("included")).sum())
    checks["count_mismatch"] = text_mismatch(d["count"], d.balls.astype(str) + "-" + d.strikes.astype(str))
    checks["base_state_mismatch"] = number_mismatch(d.base_state, sum(d[f"on_{b}b"].notna().astype(int) * 2 ** (b - 1) for b in (1, 2, 3)))
    checks["matchup_mismatch"] = text_mismatch(d.matchup, d.stand.astype("string").fillna("?") + d.p_throws.astype("string").fillna("?"))
    checks["inning_bin_mismatch"] = number_mismatch(d.inning_bin, np.minimum(d.inning, 10))
    checks["pitch_number_bin_mismatch"] = number_mismatch(d.pitch_number_bin, np.minimum(d.pitch_number, 8))
    expected_score = pd.cut(d.bat_score_diff, [-np.inf, -4, -1, 0, 3, np.inf], labels=["trailing4+", "trailing1-3", "tie", "leading1-3", "leading4+"]).astype(str)
    checks["score_bin_mismatch"] = text_mismatch(d.score_bin, expected_score)
    for current, previous in [("pitch_type", "prev_pitch_type"), ("description", "prev_description")]:
        lag = g[current].shift().astype("string").fillna("MISSING_PREVIOUS")
        lag.loc[first] = "START"
        checks[previous + "_mismatch"] = text_mismatch(d[previous], lag)
    lag_speed = g.release_speed.shift()
    checks["prev_release_speed_mismatch"] = number_mismatch(d.prev_release_speed, lag_speed)
    speed_bins = np.floor(lag_speed / 5).astype("Int64").astype(str)
    speed_bins.loc[first] = "START"
    checks["prev_release_speed_bin_mismatch"] = text_mismatch(d.prev_release_speed_bin, speed_bins)
    checks["prev_pitch_number_mismatch"] = number_mismatch(d.prev_pitch_number, g.pitch_number.shift())
    auto = d.description.isin(["automatic_ball", "automatic_strike"])
    pitchout = d.pitch_type.eq("PO") | d.description.isin(["pitchout", "swinging_pitchout", "foul_pitchout"])
    expected_pitch = d.pitch_type.astype("string").map({**dict.fromkeys(FB, 1), **dict.fromkeys(NFB, 0)}).astype("Int8").mask(auto | pitchout)
    expected_swing = d.description.astype("string").map({**dict.fromkeys(OFFERS, 1), **dict.fromkeys(TAKES, 0)}).astype("Int8").mask(auto | pitchout)
    checks["A_pitch_mismatch"] = text_mismatch(d.A_pitch, expected_pitch)
    checks["A_swing_mismatch"] = text_mismatch(d.A_swing, expected_swing)
    expected_pitch_reason = np.select([~d.eligible_pa, auto, pitchout, d.pitch_type.isna(), ~d.pitch_type.isin(FB | NFB)],
                                      ["PA_EXCLUDED", "automatic_record", "pitchout", "missing_pitch_type", "unmapped_pitch_type"], default="included")
    expected_swing_reason = np.select([~d.eligible_pa, auto, pitchout, d.description.isna(), ~d.description.isin(OFFERS | TAKES)],
                                      ["PA_EXCLUDED", "automatic_record", "pitchout", "missing_description", "unmapped_description"], default="included")
    checks["reason_pitch_mismatch"] = text_mismatch(d.reason_pitch, expected_pitch_reason)
    checks["reason_swing_mismatch"] = text_mismatch(d.reason_swing, expected_swing_reason)
    checks["unknown_description_assigned_take"] = int((~d.description.isin(OFFERS | TAKES) & d.A_swing.eq(0).fillna(False)).sum())
    hbp = d.description.eq("hit_by_pitch")
    offers = d.description.isin(OFFERS) & ~pitchout
    checks["hbp_not_take"] = int((hbp & d.A_swing.ne(0).fillna(True)).sum())
    checks["hbp_final_event_not_HBP"] = int((hbp & d.final_event.ne("hit_by_pitch").fillna(True)).sum())
    checks["hbp_current_events_not_HBP"] = int((hbp & d.events.ne("hit_by_pitch").fillna(True)).sum())
    checks["hbp_not_last_record"] = int((hbp & d.duplicated(PA, keep="last")).sum())
    checks["explicit_offers_not_Swing"] = int((offers & d.A_swing.ne(1).fillna(True)).sum())
    for model in ["pitch", "swing"]:
        checks[f"{model}_eligibility_reason_mismatch"] = int(d[f"eligible_{model}"].ne(d[f"reason_{model}"].eq("included")).sum())
        checks[f"{model}_eligible_with_bad_PA_or_missing_action"] = int((d[f"eligible_{model}"] & (~d.eligible_pa | d[f"A_{model}"].isna())).sum())
        checks[f"{model}_exclusion_partition_difference"] = int(d[f"reason_{model}"].value_counts(dropna=False).sum() - len(d))
    z = (d.plate_z - d.sz_bot) / (d.sz_top - d.sz_bot).where((d.sz_top - d.sz_bot).gt(0))
    valid = d[["plate_x", "plate_z", "sz_top", "sz_bot"]].notna().all(axis=1) & d.sz_top.gt(d.sz_bot)
    zones = np.select([~valid, d.plate_x.abs().le(17 / 24 - .15) & z.between(.1, .9), d.plate_x.abs().gt(17 / 24 + .15) | z.lt(-.1) | z.gt(1.1)], ["MISSING", "INNER", "OUT"], default="BOUNDARY")
    checks["zone_mismatch"] = text_mismatch(d.zone, zones)
    checks["zone_normalized_z_mismatch"] = number_mismatch(d.zone_z_normalized, z)
    feature_input = d[BASE + ["pitch_type", "release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "sz_top", "sz_bot", "zone", "pitch_group"]].copy()
    built = feature_builder(feature_input, {"variant": "swing"})
    for column in feature_input:
        checks["feature_preserves_" + column] = text_mismatch(built[column], feature_input[column])
    for col, divisor in [("release_speed", 5), ("pfx_x", .5), ("pfx_z", .5), ("plate_x", .35)]:
        expected = np.floor(pd.to_numeric(d[col], errors="coerce") / divisor).fillna(-999).astype(int).astype(str)
        checks[col + "_model_bin_mismatch"] = text_mismatch(built[col + "_bin"], expected)
    model_z = (d.plate_z - d.sz_bot) / (d.sz_top - d.sz_bot)
    checks["relative_z_model_bin_mismatch"] = text_mismatch(built.relative_z_bin, np.floor(model_z / .2).replace([np.inf, -np.inf], np.nan).fillna(-999).astype(int).astype(str))
    checks["swing_cell_mismatch"] = text_mismatch(built.swing_cell, d["count"].astype(str) + "|" + d.zone.astype(str) + "|" + d.pitch_group.astype(str))
    schedule_checks = []
    for item in prep["inputs"]:
        if not Path(item["path"]).name.startswith("schedule_"):
            continue
        schedule_path = ROOT / item["path"]
        year = int(schedule_path.stem.split("_")[-1])
        cutoff = "2026-09-07" if year == 2026 else f"{year}-12-31"
        games = [game for date in read(schedule_path)["dates"] for game in date["games"] if game["gameType"] == "R" and game["status"]["abstractGameState"] == "Final" and game["status"].get("detailedState") != "Cancelled" and game["officialDate"] <= cutoff]
        expected = {game["gamePk"] for game in games}
        sy = d[d.game_year.eq(year)]
        check = {"year": year, "original_schedule_hash_matches": sha(schedule_path) == item["sha256"],
                 "expected_games": len(expected), "actual_games": int(sy.game_pk.nunique()), "missing_games": sorted(expected - set(sy.game_pk)), "extra_games": sorted(set(sy.game_pk) - expected),
                 "venue_mismatch": number_mismatch(sy.venue, sy.game_pk.map({game["gamePk"]: game["venue"]["id"] for game in games})),
                 "official_date_mismatch": text_mismatch(sy.official_date, sy.game_pk.map({game["gamePk"]: game["officialDate"] for game in games}))}
        schedule_checks.append(check)
    pa_counts = pd.Series(reason).value_counts().to_dict()
    if reference_path:
        ref = read(reference_path)
        reference = {"path": str(reference_path.relative_to(ROOT)), "PA_counts_identical": pa_counts == ref["exclusions"], "raw_rows_match": len(d) == ref["rows"], "games_match": d.game_pk.nunique() == ref["games"], "eligible_PA_match": pa_counts.get("included") == ref["eligible_PA"]}
    else:
        old = pd.read_csv(ANAL / "runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_event_audit.csv")
        new = reconstructed.assign(game_year=begin.game_year).groupby(["game_year", "final_event", "pa_exclusion"], dropna=False, observed=True).size().rename("new_n").reset_index()
        merged = old.merge(new, left_on=["game_year", "event", "exclusion"], right_on=["game_year", "final_event", "pa_exclusion"], how="outer")
        reference = {"path": "preserved OBS advantage_event_audit.csv", "all_46_event_exclusion_cells_identical": bool(merged.PA.eq(merged.new_n).all()), "compared_cells": len(merged), "eligible_PA_match": pa_counts.get("included") == 364124}
    measurement_composition = []
    if 2026 not in set(d.game_year):
        e = d[d.eligible_swing].copy()
        e["measurement_support"] = e.zone.ne("MISSING") & e[["release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "sz_top", "sz_bot"]].notna().all(axis=1) & e.pitch_group.isin(["FB", "NFB"])
        for (year, action, supported), cell in e.groupby(["game_year", "A_swing", "measurement_support"], observed=True):
            measurement_composition.append({"year": int(year), "A_swing": int(action), "measurement_support": bool(supported), "rows": len(cell), "mean_Y_descriptive_only": float(cell.Y.mean()), "HBP_rows": int(cell.description.eq("hit_by_pitch").sum()), "HBP_share": float(cell.description.eq("hit_by_pitch").mean()), "missing_current_group": int((~cell.pitch_group.isin(["FB", "NFB"])).sum())})
    mismatch_samples = d.loc[hbp & (d.final_event.ne("hit_by_pitch").fillna(True) | d.A_swing.ne(0).fillna(True)), KEYS + ["description", "events", "final_event", "A_swing"]].head(30).to_dict("records")
    transitions = {"PA_multiple_pitchers": int(g.pitcher.nunique().gt(1).sum()), "PA_multiple_batters": int(g.batter.nunique().gt(1).sum()),
                   "rows_previous_pitcher_differs": int((~first & d.pitcher.ne(g.pitcher.shift())).sum()), "rows_previous_batter_differs": int((~first & d.batter.ne(g.batter.shift())).sum()),
                   "interpretation": "Lag records may belong to a substituted pitcher/batter; current row IDs remain actual current IDs. No future/current action was silently used as the lag."}
    reference_pass = all(value for value in reference.values() if isinstance(value, (bool, np.bool_)))
    ok = all(value == 0 for value in checks.values()) and reference_pass and all(not s["missing_games"] and not s["extra_games"] and s["venue_mismatch"] == 0 and s["official_date_mismatch"] == 0 and s["original_schedule_hash_matches"] for s in schedule_checks)
    return {"label": label, "input": input_meta, "preparation_audit": meta(audit_path), "raw_rows": len(d), "PA": len(begin), "PA_exclusions": pa_counts,
            "all_numeric_mismatch_checks_zero": ok, "checks": checks, "hbp_rows": int(hbp.sum()), "explicit_offer_rows": int(offers.sum()),
            "explicit_bunt_rows": int(d.description.isin(["foul_bunt", "missed_bunt", "bunt_foul_tip"]).sum()), "inplay_rows": int(d.description.eq("hit_into_play").sum()),
            "hbp_mismatch_examples": mismatch_samples, "schedule": schedule_checks, "preserved_reference": reference, "within_PA_player_change": transitions,
            "measurement_selection_composition": measurement_composition,
            "measurement_selection_interpretation": "Descriptive composition only; measurement completeness is selection related to observed action/outcome, not pretreatment eligibility. No action-effect estimate was changed.",
            "2026_swing_policy_evaluation_rows": 0, "2026_swing_measurement_Y_stratification": "NOT_COMPUTED" if 2026 in set(d.game_year) else "not applicable"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(HERE / "action_lineage_validation.json"))
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError("Audit output exists; supply a fresh --output")
    configs = {name: read(ROOT / f"models/bcap/{name}/v0.1.0/specification.yaml") for name in ["pitch", "swing"]}
    allowlists = {"pitch_features_exact_precontext_allowlist": configs["pitch"]["features"] == BASE,
                  "swing_features_exact_diagnostic_allowlist": configs["swing"]["features"] == BASE + SWING_FEATURES,
                  "both_player_IDs_in_both_nuisances": all({"pitcher", "batter"}.issubset(c["features"]) for c in configs.values()),
                  "forbidden_features_absent": all(not FORBIDDEN.intersection(c["features"]) for c in configs.values()),
                  "pitch_policy_Z_only_count": configs["pitch"]["policy_key"] == "count",
                  "swing_policy_Z_diagnostic_cell": configs["swing"]["policy_key"] == "swing_cell"}
    builder = feature_function()
    reports = []
    for source in target_sources():
        reports.append(audit_one(*source, builder))
        print(source[0], "audit", reports[-1]["all_numeric_mismatch_checks_zero"], "HBP", reports[-1]["hbp_rows"], flush=True)
    result = {"audit_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "code": meta(Path(__file__)),
              "scope": "Independent prepared-data/action/feature lineage reconstruction after external seal, no fitting or design changes",
              "allowlist_checks": allowlists, "datasets": reports,
              "all_pass": all(allowlists.values()) and all(r["all_numeric_mismatch_checks_zero"] for r in reports),
              "limit": "Raw source CSVs were not reread wholesale: their previously established input hashes are linked in preparation audits. Direct raw IDs/context are preserved by the preparation code; transformations and schedule joins are recomputed here.",
              "sealed_code_unchanged_by_audit": True, "2026_SWING_policy_evaluations": 0}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=lambda x: x.item() if hasattr(x, "item") else str(x)), encoding="utf-8")
    if not result["all_pass"]:
        raise AssertionError("Inspect recorded lineage mismatches; no labels were changed")


if __name__ == "__main__":
    main()
