from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIRS = [ROOT / "data/raw/mlb/2024", ROOT / "data/raw/mlb/2025"]
OUT = ROOT / "data/processed"
OUT.mkdir(parents=True, exist_ok=True)

COLS = [
    "game_date", "game_pk", "at_bat_number", "pitch_number", "pitcher", "batter",
    "balls", "strikes", "pitch_name", "description", "type", "events", "stand", "p_throws",
    "on_1b", "on_2b", "on_3b", "outs_when_up", "inning", "bat_score_diff",
    "delta_pitcher_run_exp", "plate_x", "plate_z", "sz_top", "sz_bot"
]
files = [f for raw_dir in RAW_DIRS for f in sorted(raw_dir.glob("statcast_*.csv"))]
df = pd.concat([pd.read_csv(f, usecols=COLS, low_memory=False) for f in files], ignore_index=True)
df["count"] = df["balls"].astype(int).astype(str) + "-" + df["strikes"].astype(int).astype(str)
count_order = [f"{b}-{s}" for b in range(4) for s in range(3)]
df["count"] = pd.Categorical(df["count"], count_order, ordered=True)
df["pa_key"] = df["game_pk"].astype(str) + "-" + df["at_bat_number"].astype(str)

automatic = df["description"].isin(["automatic_ball", "automatic_strike"])
actual = df["pitch_name"].notna() & ~automatic
df["eligible_pitch"] = actual
swing_desc = {
    "swinging_strike", "swinging_strike_blocked", "foul", "foul_tip", "foul_bunt",
    "bunt_foul_tip", "missed_bunt", "hit_into_play"
}
df["swing"] = df["description"].isin(swing_desc)
df["whiff"] = df["description"].isin(["swinging_strike", "swinging_strike_blocked", "missed_bunt"])

outcome_map = {
    "ball": "ball", "blocked_ball": "ball", "pitchout": "ball",
    "called_strike": "called_strike",
    "swinging_strike": "swinging_strike", "swinging_strike_blocked": "swinging_strike", "missed_bunt": "swinging_strike",
    "foul": "foul", "foul_tip": "foul", "foul_bunt": "foul", "bunt_foul_tip": "foul",
    "hit_into_play": "in_play", "hit_by_pitch": "hit_by_pitch",
    "automatic_ball": "automatic_ball", "automatic_strike": "automatic_strike"
}
df["pitch_outcome"] = df["description"].map(outcome_map).fillna("other")

def rate_table(frame, group):
    g = frame.groupby(group, observed=True)
    return g.agg(
        pitches=("pitch_number", "size"),
        swings=("swing", "sum"),
        whiffs=("whiff", "sum"),
        balls=("pitch_outcome", lambda s: (s == "ball").sum()),
        called_strikes=("pitch_outcome", lambda s: (s == "called_strike").sum()),
        fouls=("pitch_outcome", lambda s: (s == "foul").sum()),
        in_play=("pitch_outcome", lambda s: (s == "in_play").sum()),
        hbp=("pitch_outcome", lambda s: (s == "hit_by_pitch").sum()),
        strike_results=("type", lambda s: (s == "S").sum()),
        in_play_results=("type", lambda s: (s == "X").sum()),
        pitcher_run_value=("delta_pitcher_run_exp", "sum")
    ).reset_index()

basic = rate_table(df[actual], ["count"])
for numerator in ["swings", "balls", "called_strikes", "fouls", "in_play", "hbp"]:
    basic[numerator + "_pct"] = 100 * basic[numerator] / basic["pitches"]
basic["whiff_per_swing_pct"] = 100 * basic["whiffs"] / basic["swings"]
basic["strike_result_pct"] = 100 * basic["strike_results"] / basic["pitches"]
basic["pitcher_run_value_per_100"] = 100 * basic["pitcher_run_value"] / basic["pitches"]
basic.to_csv(OUT / "count_summary_2024_2025.csv", index=False, encoding="utf-8-sig")

mix = df[actual].groupby(["count", "pitch_name"], observed=True).agg(
    pitches=("pitch_number", "size"), swings=("swing", "sum"), whiffs=("whiff", "sum"),
    balls=("pitch_outcome", lambda s: (s == "ball").sum()),
    pitcher_run_value=("delta_pitcher_run_exp", "sum")
).reset_index()
mix["selection_pct"] = 100 * mix["pitches"] / mix.groupby("count", observed=True)["pitches"].transform("sum")
mix["swing_pct"] = 100 * mix["swings"] / mix["pitches"]
mix["whiff_per_swing_pct"] = 100 * mix["whiffs"] / mix["swings"]
mix["ball_pct"] = 100 * mix["balls"] / mix["pitches"]
mix["pitcher_run_value_per_100"] = 100 * mix["pitcher_run_value"] / mix["pitches"]
mix.to_csv(OUT / "count_pitch_mix_2024_2025.csv", index=False, encoding="utf-8-sig")

outcomes = df.groupby(["count", "pitch_outcome"], observed=True).size().rename("pitches").reset_index()
outcomes["pct"] = 100 * outcomes["pitches"] / outcomes.groupby("count", observed=True)["pitches"].transform("sum")
outcomes.to_csv(OUT / "count_next_pitch_outcomes_2024_2025.csv", index=False, encoding="utf-8-sig")

event_result = np.select(
    [df.events.isin({"single", "double", "triple", "home_run"}), df.events.isin({"strikeout", "strikeout_double_play"}),
     df.events.isin({"walk", "intent_walk"}), df.events.eq("hit_by_pitch"), df.events.isin({"field_out", "force_out", "grounded_into_double_play", "double_play", "fielders_choice_out", "sac_fly", "sac_bunt", "sac_fly_double_play", "triple_play"})],
    ["hit", "strikeout", "walk", "hit_by_pitch", "out"], default="")
df["immediate_result"] = np.where(event_result != "", event_result, df["pitch_outcome"])
immediate = df.groupby(["count", "immediate_result"], observed=True).size().rename("pitches").reset_index()
immediate["pct"] = 100 * immediate["pitches"] / immediate.groupby("count", observed=True)["pitches"].transform("sum")
immediate.to_csv(OUT / "count_immediate_results_2024_2025.csv", index=False, encoding="utf-8-sig")

final = df[df["events"].notna()][["pa_key", "events"]].drop_duplicates("pa_key", keep="last")
reached = df[["pa_key", "count"]].drop_duplicates().merge(final, on="pa_key", how="left")
hits = {"single", "double", "triple", "home_run"}
walks = {"walk", "intent_walk"}
strikeouts = {"strikeout", "strikeout_double_play"}
outs = {"field_out", "force_out", "grounded_into_double_play", "double_play", "fielders_choice_out", "sac_fly", "sac_bunt", "sac_fly_double_play", "triple_play"}
reached["pa_result"] = np.select(
    [reached.events.isin(hits), reached.events.isin(strikeouts), reached.events.isin(walks),
     reached.events.eq("hit_by_pitch"), reached.events.isin(outs), reached.events.isna(), reached.events.eq("truncated_pa")],
    ["hit", "strikeout", "walk", "hit_by_pitch", "out", "missing", "truncated"], default="other")
pa = reached.groupby(["count", "pa_result"], observed=True).size().rename("plate_appearances").reset_index()
pa["pct"] = 100 * pa["plate_appearances"] / pa.groupby("count", observed=True)["plate_appearances"].transform("sum")
pa.to_csv(OUT / "count_plate_appearance_results_2024_2025.csv", index=False, encoding="utf-8-sig")

score = pd.to_numeric(df["bat_score_diff"], errors="coerce")
df["score_state"] = pd.cut(score, [-np.inf, -3, -1, 0, 2, np.inf], labels=["pitcher_leads_3plus", "pitcher_leads_1to2", "tie", "pitcher_trails_1to2", "pitcher_trails_3plus"])
df["base_state"] = np.where(df.on_1b.notna(), "1", "0") + np.where(df.on_2b.notna(), "1", "0") + np.where(df.on_3b.notna(), "1", "0")
context = rate_table(df[actual & df.score_state.notna()], ["count", "score_state", "base_state", "outs_when_up"])
context["swing_pct"] = 100 * context["swings"] / context["pitches"]
context["ball_pct"] = 100 * context["balls"] / context["pitches"]
context["pitcher_run_value_per_100"] = 100 * context["pitcher_run_value"] / context["pitches"]
context.to_csv(OUT / "count_game_context_2024_2025.csv", index=False, encoding="utf-8-sig")

choice = df[actual & df.score_state.notna()].groupby(["count", "score_state", "base_state", "pitch_name"], observed=True).agg(
    pitches=("pitch_number", "size"), swings=("swing", "sum"), whiffs=("whiff", "sum"),
    balls=("pitch_outcome", lambda s: (s == "ball").sum()), pitcher_run_value=("delta_pitcher_run_exp", "sum")
).reset_index()
choice["selection_pct"] = 100 * choice["pitches"] / choice.groupby(["count", "score_state", "base_state"], observed=True)["pitches"].transform("sum")
choice["pitcher_run_value_per_100"] = 100 * choice["pitcher_run_value"] / choice["pitches"]
choice["ball_pct"] = 100 * choice["balls"] / choice["pitches"]
choice["whiff_per_swing_pct"] = 100 * choice["whiffs"] / choice["swings"]
choice.to_csv(OUT / "count_context_pitch_choices_2024_2025.csv", index=False, encoding="utf-8-sig")

top_used = mix.sort_values(["count", "pitches"], ascending=[True, False]).groupby("count", observed=True).head(1)
best = mix[mix.pitches >= 500].sort_values(["count", "pitcher_run_value_per_100"], ascending=[True, False]).groupby("count", observed=True).head(1)
summary = {
    "rows": int(len(df)), "eligible_actual_pitches": int(actual.sum()), "automatic_events": int(automatic.sum()),
    "missing_pitch_name": int(df.pitch_name.isna().sum()), "plate_appearances": int(df.pa_key.nunique()),
    "missing_final_event_pas": int(df.pa_key.nunique() - final.pa_key.nunique()),
    "counts": {str(r["count"]): int(r["pitches"]) for _, r in basic.iterrows()},
    "top_used_pitch": {str(r["count"]): {"pitch": r.pitch_name, "pct": round(r.selection_pct, 2)} for _, r in top_used.iterrows()},
    "best_observed_pitch_min500": {str(r["count"]): {"pitch": r.pitch_name, "rv_per_100": round(r.pitcher_run_value_per_100, 3), "n": int(r.pitches)} for _, r in best.iterrows()}
}
(ROOT / "analysis/count_analysis_2024_2025_combined_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))

