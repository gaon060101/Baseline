"""Immutable, pitch-level BCAP preparation from previously acquired Statcast CSVs.

No network access. Current description is used for adjudicated action/record labels,
never as a current prediction feature. All previous-pitch features are shifted within
the same PA before any current-row eligibility filter. Category dictionaries and
missing-value imputation for nuisance models are deliberately not learned here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
COL = ROOT / "columns/001-ball-count"
RAW = COL / "data/raw/mlb"
KEYS = ["game_pk", "at_bat_number", "pitch_number"]
PA_KEYS = KEYS[:2]
COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]
FB = ("FF", "SI", "FC")
# Closed vocabulary established by the 2024/2025 raw-code and pitch-name audit.
NFB = ("SL", "CH", "ST", "CU", "FS", "KC", "SV", "FA", "EP", "KN", "FO", "CS", "SC")
SWING = ("swinging_strike", "swinging_strike_blocked", "foul", "foul_tip",
         "hit_into_play", "foul_bunt", "missed_bunt", "bunt_foul_tip")
# Scored HBP is an adjudicated no-attempt outcome under rule 5.05(b)(2).
TAKE = ("ball", "blocked_ball", "called_strike", "hit_by_pitch")
BUNT = ("foul_bunt", "missed_bunt", "bunt_foul_tip")
AUTO = ("automatic_ball", "automatic_strike")
PITCHOUT = ("pitchout", "swinging_pitchout", "foul_pitchout")
USECOLS = KEYS + [
    "game_date", "game_type", "game_year", "balls", "strikes", "pitcher", "batter",
    "events", "description", "pitch_type", "pitch_name", "des", "stand", "p_throws",
    "on_1b", "on_2b", "on_3b", "outs_when_up", "inning", "bat_score_diff",
    "release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "sz_top", "sz_bot",
]


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def meta(path):
    p = Path(path)
    return {"path": p.resolve().relative_to(ROOT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size}


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False,
                                    default=lambda x: x.item() if hasattr(x, "item") else str(x)), encoding="utf-8")


def csv(path, frame):
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def source_paths(year):
    if year in (2024, 2025):
        folder = RAW / str(year)
        return sorted(folder.glob("statcast_*.csv")), folder / f"schedule_{year}.json"
    if year == 2023:
        folder = RAW / "2023/snapshot_20260908_ridge_v02"
        return sorted(folder.glob("statcast_*.csv")), folder / "schedule_2023.json"
    if year == 2026:
        folder = RAW / "2026/snapshot_20260908_ridge_v02"
        files = sorted(folder.glob("statcast_*.csv"))
        files += sorted((RAW / "2026/supplement_20260909_ridge_v02").glob("statcast_*.csv"))
        return files, folder / "schedule_2026.json"
    raise ValueError(f"Unspecified season {year}")


def derive_zone(d):
    """Fixed geometric diagnostic regions; these are not official strike calls."""
    height = d.sz_top - d.sz_bot
    z = (d.plate_z - d.sz_bot) / height.where(height.gt(0))
    valid = d[["plate_x", "plate_z", "sz_top", "sz_bot"]].notna().all(axis=1) & height.gt(0)
    inner = d.plate_x.abs().le(17 / 24 - 0.15) & z.between(0.10, 0.90)
    outside = d.plate_x.abs().gt(17 / 24 + 0.15) | z.lt(-0.10) | z.gt(1.10)
    zone = np.select([~valid, inner, outside], ["MISSING", "INNER", "OUT"], default="BOUNDARY")
    return z, zone


def prepare(years, output_path, audit_dir, external_seal=None):
    """Prepare all observed rows, retaining separate PA and action eligibility flags.

    Returns (prepared_dataframe, audit). The pickle includes all rows, including
    excluded PAs, so denominators and labels can be independently audited. External
    execution requires a caller-supplied seal; the run engine verifies its hashes.
    """
    years = [int(y) for y in years]
    if set(years) & {2023, 2026}:
        if external_seal is None or not Path(external_seal).is_file():
            raise RuntimeError("External raw access requires an existing explicit BCAP seal path")
    output_path = Path(output_path).resolve()
    audit_dir = Path(audit_dir).resolve()
    if output_path.exists() or (audit_dir.exists() and any(audit_dir.iterdir())):
        raise FileExistsError("Preparation output/audit already exists; use a new run name")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)
    started = now()
    pieces, inputs, headers, schedule_audits, venue, official_dates = [], [], [], [], {}, {}
    for year in years:
        files, schedule_path = source_paths(year)
        if not files or not schedule_path.is_file():
            raise FileNotFoundError(f"Existing {year} source snapshot incomplete")
        schedule = json.loads(schedule_path.read_text(encoding="utf-8-sig"))
        cutoff = "2026-09-07" if year == 2026 else f"{year}-12-31"
        games = [g for day in schedule["dates"] for g in day["games"]
                 if g["gameType"] == "R" and g["status"]["abstractGameState"] == "Final"
                 and g["status"].get("detailedState") != "Cancelled" and g["officialDate"] <= cutoff]
        expected = {int(g["gamePk"]) for g in games}
        venue.update({g["gamePk"]: g["venue"]["id"] for g in games})
        official_dates.update({g["gamePk"]: g["officialDate"] for g in games})
        inputs.append(meta(schedule_path))
        this_year = []
        for i, path in enumerate(files):
            header = list(pd.read_csv(path, nrows=0).columns)
            missing = sorted(set(USECOLS) - set(header))
            if missing:
                raise ValueError(f"Missing required CSV fields in {path.name}: {missing}")
            piece = pd.read_csv(path, usecols=USECOLS, low_memory=False)
            assert piece.game_year.eq(year).all() and piece.game_type.eq("R").all()
            info = meta(path)
            info["rows"] = len(piece)
            inputs.append(info)
            headers.append({"path": info["path"], "columns": header, "missing_requested": missing})
            this_year.append(piece)
            if (i + 1) % 10 == 0:
                print(f"prepared source {year}: {i + 1}/{len(files)}", flush=True)
        raw_year = pd.concat(this_year, ignore_index=True)
        found = set(raw_year.game_pk.unique())
        missing_games = sorted(expected - found)
        extras = sorted(found - expected)
        schedule_audits.append({"year": year, "cutoff": cutoff, "expected_games": len(expected),
                                "raw_rows": len(raw_year), "missing_games": missing_games,
                                "extra_games_excluded": extras})
        if missing_games:
            raise AssertionError(f"Missing scheduled games: {missing_games}")
        pieces.append(raw_year[raw_year.game_pk.isin(expected)].copy())
    d = pd.concat(pieces, ignore_index=True).sort_values(KEYS).reset_index(drop=True)
    del pieces, this_year, raw_year
    assert not d[KEYS].isna().any().any()
    duplicates = int(d.duplicated(KEYS).sum())
    if duplicates:
        raise AssertionError(f"Duplicate pitch keys: {duplicates}")
    assert d.balls.between(0, 3).all() and d.strikes.between(0, 2).all()
    for col in KEYS + ["game_year", "balls", "strikes", "pitcher", "batter"]:
        if d[col].isna().any():
            raise AssertionError(f"Required identifier/count missing: {col}")
        d[col] = d[col].astype("int64")
    d["count"] = d.balls.astype(str) + "-" + d.strikes.astype(str)
    d["pa_id"] = pd.factorize(pd.MultiIndex.from_frame(d[PA_KEYS]))[0]
    d["row_id"] = np.arange(len(d), dtype="int64")
    group = d.groupby("pa_id", sort=False)
    first = d.drop_duplicates("pa_id").set_index("pa_id")
    last = d.drop_duplicates("pa_id", keep="last").set_index("pa_id")
    obs = json.loads((ROOT / "models/bcai/observed/v1.0.0/specification.yaml").read_text(encoding="utf-8"))
    weight_spec = json.loads((ROOT / "models/bcai/ridge/v0.2.0/specification.yaml").read_text(encoding="utf-8"))["weights"]
    weights = {y: weight_spec[str(2025 if y == 2026 else y)] for y in years}
    event_map = {event: result for result, events in obs["result_classification"].items() for event in events}
    pa = first[KEYS + ["game_year", "game_date", "count"]].copy()
    pa["final_event"] = last.events
    pa["result"] = pa.final_event.map(event_map)
    pa["pa_exclusion"] = np.select([
        pa.final_event.isna(), pa.final_event.eq("intent_walk"), pa.final_event.eq("catcher_interf"),
        pa.final_event.eq("truncated_pa"), pa.result.isna(), pa["count"].ne("0-0"),
    ], ["missing_final", "intentional_walk", "catcher_interference", "truncated", "unknown_event", "no_observed_0_0"], default="included")
    pa["Y"] = [weights[y].get(result, 0.0) if reason == "included" else np.nan
               for y, result, reason in zip(pa.game_year, pa.result, pa.pa_exclusion)]
    for col in ["final_event", "result", "pa_exclusion", "Y"]:
        d[col] = d.pa_id.map(pa[col])
    d["eligible_pa"] = d.pa_exclusion.eq("included")
    # No current or future outcome is used for the following prepitch features.
    d["venue"] = d.game_pk.map(venue)
    d["official_date"] = d.game_pk.map(official_dates)
    assert d.venue.notna().all() and d.official_date.notna().all()
    d["venue"] = d.venue.astype("int64")
    d["matchup"] = d.stand.fillna("?") + d.p_throws.fillna("?")
    d["base_state"] = sum(d[f"on_{b}b"].notna().astype("int8") * 2 ** (b - 1) for b in (1, 2, 3))
    d["inning_bin"] = d.inning.clip(upper=10)
    d["score_bin"] = pd.cut(d.bat_score_diff, [-np.inf, -4, -1, 0, 3, np.inf],
                             labels=["trailing4+", "trailing1-3", "tie", "leading1-3", "leading4+"]).astype(str)
    d["pitch_number_bin"] = d.pitch_number.clip(upper=8)
    d["prev_pitch_number"] = group.pitch_number.shift(1)
    d["prev_pitch_type"] = group.pitch_type.shift(1).fillna("MISSING_PREVIOUS")
    d["prev_description"] = group.description.shift(1).fillna("MISSING_PREVIOUS")
    d["prev_release_speed"] = group.release_speed.shift(1)
    d["prev_release_speed_bin"] = np.floor(d.prev_release_speed / 5).astype("Int64").astype(str)
    is_first = ~d.pa_id.duplicated()
    for col in ["prev_pitch_type", "prev_description", "prev_release_speed_bin"]:
        d.loc[is_first, col] = "START"
    d["pitch_group"] = np.select([d.pitch_type.isin(FB), d.pitch_type.isin(NFB)], ["FB", "NFB"], default="UNCLASSIFIED")
    automatic = d.description.isin(AUTO)
    pitchout = d.pitch_type.eq("PO") | d.description.isin(PITCHOUT)
    d["reason_pitch"] = np.select([
        ~d.eligible_pa, automatic, pitchout, d.pitch_type.isna(), ~d.pitch_type.isin(FB + NFB),
    ], ["PA_EXCLUDED", "automatic_record", "pitchout", "missing_pitch_type", "unmapped_pitch_type"], default="included")
    pitch_label = d.pitch_type.map({**{x: 1 for x in FB}, **{x: 0 for x in NFB}}).astype("Int8")
    d["A_pitch"] = pitch_label.mask(automatic | pitchout)
    d["eligible_pitch"] = d.reason_pitch.eq("included")
    d["reason_swing"] = np.select([
        ~d.eligible_pa, automatic, pitchout, d.description.isna(), ~d.description.isin(SWING + TAKE),
    ], ["PA_EXCLUDED", "automatic_record", "pitchout", "missing_description", "unmapped_description"], default="included")
    swing_label = d.description.map({**{x: 1 for x in SWING}, **{x: 0 for x in TAKE}}).astype("Int8")
    d["A_swing"] = swing_label.mask(automatic | pitchout)
    d["eligible_swing"] = d.reason_swing.eq("included")
    d["bunt_explicit"] = d.description.isin(BUNT)
    # Audit-only outcome text: not a prediction input or exclusion condition.
    d["inplay_bunt_text_flag"] = d.description.eq("hit_into_play") & d.des.fillna("").str.contains(r"\bbunts?\b", case=False, regex=True)
    d["hbp_adjudicated_take"] = d.description.eq("hit_by_pitch")
    d["zone_z_normalized"], d["zone"] = derive_zone(d)
    d["measurement_missing"] = d[["release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "sz_top", "sz_bot"]].isna().any(axis=1)
    nonterminal = d.pa_id.eq(d.pa_id.shift(-1))
    next_b, next_s = d.balls.shift(-1), d.strikes.shift(-1)
    delta_b, delta_s = next_b - d.balls, next_s - d.strikes
    count_transition_ok = ((delta_b.eq(1) & delta_s.eq(0)) | (delta_b.eq(0) & delta_s.eq(1)) |
                           (delta_b.eq(0) & delta_s.eq(0)))
    anomalies = nonterminal & ~count_transition_ok
    d["pitch_sequence_gap_before"] = ~is_first & d.pitch_number.ne(d.prev_pitch_number + 1)
    checks = {"duplicate_pitch_keys": duplicates, "invalid_counts": 0,
              "first_pitch_number_not_one_PA": int(first.pitch_number.ne(1).sum()),
              "pitch_sequence_gaps": int(d.pitch_sequence_gap_before.sum()),
              "nonmonotonic_pitch_numbers": int((~is_first & d.pitch_number.le(d.prev_pitch_number)).sum()),
              "count_transition_anomalies": int(anomalies.sum()),
              "multiple_nonnull_events_PA": int(group.events.count().gt(1).sum()),
              "multiple_distinct_nonnull_events_PA": int(group.events.nunique().gt(1).sum()),
              "missing_last_event_with_earlier_nonnull_PA": int((last.events.isna() & group.events.count().gt(0)).sum()),
              "PA_multiple_pitchers": int(group.pitcher.nunique().gt(1).sum()),
              "PA_multiple_batters": int(group.batter.nunique().gt(1).sum()),
              "prev_features_first_row_clear": bool(d.loc[is_first, "prev_release_speed"].isna().all()),
              "Y_constant_within_PA": bool(d.groupby("pa_id").Y.nunique().le(1).all()),
              "eligible_pitch_label_complete": bool(d.loc[d.eligible_pitch, "A_pitch"].notna().all()),
              "eligible_swing_label_complete": bool(d.loc[d.eligible_swing, "A_swing"].notna().all())}
    csv(audit_dir / "raw_pitch_codes.csv", d.groupby(["game_year", "pitch_type", "pitch_name"], dropna=False).size().rename("rows").reset_index())
    csv(audit_dir / "raw_descriptions.csv", d.groupby(["game_year", "description"], dropna=False).size().rename("rows").reset_index())
    csv(audit_dir / "description_action_audit.csv", d.groupby(["game_year", "description", "A_swing", "reason_swing"], dropna=False).size().rename("rows").reset_index())
    csv(audit_dir / "pa_exclusions.csv", pa.groupby(["game_year", "final_event", "result", "pa_exclusion"], dropna=False).size().rename("PA").reset_index())
    csv(audit_dir / "pa_index.csv", pa.reset_index())
    csv(audit_dir / "current_row_exclusions.csv", pd.concat([
        d.groupby(["game_year", "count", f"reason_{variant}"], dropna=False).size().rename("rows").reset_index().rename(columns={f"reason_{variant}": "reason"}).assign(model=variant)
        for variant in ["pitch", "swing"]], ignore_index=True))
    csv(audit_dir / "missingness.csv", pd.DataFrame([
        {"game_year": y, "field": c, "rows": len(g), "missing": int(g[c].isna().sum())}
        for y, g in d.groupby("game_year") for c in USECOLS if c != "des"]))
    csv(audit_dir / "sequence_anomalies.csv", d.loc[anomalies | d.pitch_sequence_gap_before, KEYS + ["count", "description", "prev_pitch_number", "pitch_sequence_gap_before"]])
    csv(audit_dir / "bunt_and_hbp_audit.csv", d.groupby("game_year").agg(
        explicit_bunt_rows=("bunt_explicit", "sum"), inplay_bunt_text_rows=("inplay_bunt_text_flag", "sum"),
        adjudicated_hbp_take_rows=("hbp_adjudicated_take", "sum"), rows=("row_id", "size")).reset_index())
    # Keep raw text used only for audit out of the modeling pickle altogether.
    d = d.drop(columns=["des"])
    for c in d.select_dtypes(include="object").columns:
        d[c] = d[c].astype("category")
    d.to_pickle(output_path)
    audit = {"started_at": started, "completed_at": now(), "years": years, "raw_rows": len(d),
             "all_PA": len(pa), "games": int(d.game_pk.nunique()),
             "eligible_PA": int(pa.pa_exclusion.eq("included").sum()),
             "eligible_pitch_rows": int(d.eligible_pitch.sum()), "eligible_swing_rows": int(d.eligible_swing.sum()),
             "PA_exclusions": pa.pa_exclusion.value_counts().to_dict(),
             "pitch_exclusions": d.reason_pitch.value_counts().to_dict(),
             "swing_exclusions": d.reason_swing.value_counts().to_dict(),
             "checks": checks, "schedule": schedule_audits, "weights": weights,
             "action_map": {"FB": FB, "NFB": NFB, "Swing": SWING, "Take": TAKE},
             "zone_rule": {"x_half_width_feet": 17 / 24, "x_margin_feet": 0.15, "z_normalized_margin": 0.10,
                           "inner": "abs(x)<=17/24-0.15 & .1<=z_norm<=.9",
                           "out": "abs(x)>17/24+.15 or z_norm<-.1 or z_norm>1.1",
                           "boundary": "valid geometry remaining", "missing": "any geometry missing or sz_top<=sz_bot"},
             "scope": "observed completed-PA-selected pitch decisions; broad adjudicated offer/no-offer; no causal identification certification",
             "inplay_bunt_detection": "audit-only case-insensitive narrative regex; incomplete proxy, no row exclusions or model inputs",
             "category_storage": "pandas categories compress raw strings only; training feature dictionaries must be rebuilt per fold",
             "output": meta(output_path), "code": meta(__file__), "inputs": inputs,
             "external_seal": str(external_seal) if external_seal else None}
    write_json(audit_dir / "raw_headers.json", headers)
    write_json(audit_dir / "preparation_audit.json", audit)
    print(json.dumps({k: audit[k] for k in ["raw_rows", "all_PA", "eligible_PA", "games", "eligible_pitch_rows", "eligible_swing_rows", "checks"]}, ensure_ascii=False), flush=True)
    return d, audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--audit-dir", required=True)
    parser.add_argument("--external-seal")
    args = parser.parse_args()
    prepare(args.years, args.output, args.audit_dir, args.external_seal)
