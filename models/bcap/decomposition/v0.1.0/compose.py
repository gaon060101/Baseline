"""BCAP-DECOMP DRAFT: supplied component predictions -> descriptive W means.

No training, AIPW, policy learning, or uncertainty estimation is performed here.
The input producer is responsible for eligibility, features and nuisance fitting.
"""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

MODEL_ID = "BCAP-DECOMP-v0.1.0"
UNIT = "season_weighted_final_PA_W"
DESCRIPTION = {
    "ball": ("Take", "TAKE_BALL"),
    "blocked_ball": ("Take", "TAKE_BALL"),
    "called_strike": ("Take", "TAKE_CALLED_STRIKE"),
    "hit_by_pitch": ("Take", "TAKE_HBP"),
    "swinging_strike": ("Swing", "SWING_MISS"),
    "swinging_strike_blocked": ("Swing", "SWING_MISS"),
    "foul": ("Swing", "SWING_FOUL"),
    "foul_tip": ("Swing", "SWING_FOUL_TIP"),
    "foul_bunt": ("Swing", "BUNT_FOUL"),
    "missed_bunt": ("Swing", "BUNT_MISS"),
    "bunt_foul_tip": ("Swing", "BUNT_FOUL_TIP"),
    "hit_into_play": ("Swing", "IN_PLAY"),
}
BRANCHES = {a: sorted({b for aa, b in DESCRIPTION.values() if aa == a})
            for a in ("Take", "Swing")}
REGIONS = {"CENTER", "HIGH", "LOW", "INSIDE", "OUTSIDE"}


def classify_description(description):
    """Unknown labels remain unsupported, never filled as Take."""
    return DESCRIPTION.get(description)


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label}: finite number required")
    if not math.isfinite(value):
        raise ValueError(f"{label}: nonfinite value")
    return float(value)


def string(value, label):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label}: nonempty string required")
    return value


def calculate(document):
    """Validate supplied paired reference rows; compose before averaging."""
    if document.get("schema_version") != "1":
        raise ValueError("schema_version must be 1")
    outcome = document.get("outcome_definition", {})
    if outcome.get("unit") != UNIT or outcome.get("kind") != "final_PA_W":
        raise ValueError("Only final PA W, without extra rewards, is accepted")
    digest = outcome.get("weight_manifest_sha256", "")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("weight_manifest_sha256 required")
    if not isinstance(document.get("synthetic"), bool):
        raise ValueError("Explicit synthetic true/false required")
    fit_provenance = string(document.get("fit_provenance"), "fit_provenance")
    train_games = document.get("fold_training_games", {})
    refs = {}
    games_to_fold = {}
    pitch_keys = set()
    for row in document.get("reference_rows", []):
        rid = string(row.get("row_id"), "row_id")
        if rid in refs:
            raise ValueError(f"duplicate row_id: {rid}")
        key = tuple(string(row.get(k), k) for k in
                    ("game_pk", "at_bat_number", "pitch_number"))
        if key in pitch_keys:
            raise ValueError(f"duplicate pitch key: {key}")
        pitch_keys.add(key)
        fold = string(row.get("outer_fold"), "outer_fold")
        game = key[0]
        if game in games_to_fold and games_to_fold[game] != fold:
            raise ValueError("one game assigned to multiple evaluation folds")
        games_to_fold[game] = fold
        if fold not in train_games or not isinstance(train_games[fold], list):
            raise ValueError("fold training-game inventory missing")
        if not train_games[fold] or any(not isinstance(g, str) for g in train_games[fold]):
            raise ValueError("training-game inventory must contain string IDs")
        if game in set(train_games[fold]):
            raise ValueError("evaluation game overlaps its training games")
        count = row.get("count")
        if count not in {f"{b}-{s}" for b in range(4) for s in range(3)}:
            raise ValueError("invalid pre-pitch count")
        if not isinstance(row.get("season"), int):
            raise ValueError("season integer required")
        regions = row.get("regions")
        if (not isinstance(regions, list) or not regions or
                len(regions) != len(set(regions)) or not set(regions) <= REGIONS):
            raise ValueError("nonempty unique five-region labels required")
        rs = set(regions)
        if (("CENTER" in rs and len(rs) != 1) or {"HIGH", "LOW"} <= rs
                or {"INSIDE", "OUTSIDE"} <= rs or len(rs) > 2):
            raise ValueError("inconsistent region membership")
        label = classify_description(row.get("observed_description"))
        if label is None:
            raise ValueError("unclassified observed description: do not impute Take")
        refs[rid] = dict(row, observed_action=label[0], observed_branch=label[1])
    if not refs:
        raise ValueError("empty reference population")
    preds = {}
    positive_support = defaultdict(int)
    zero_mass_unsupported = defaultdict(int)
    for pred in document.get("predictions", []):
        rid = pred.get("row_id")
        action = pred.get("action")
        if rid not in refs or action not in BRANCHES:
            raise ValueError("prediction has unknown reference row/action")
        key = (rid, action)
        if key in preds:
            raise ValueError("duplicate row/action prediction")
        if pred.get("prediction_fold") != refs[rid]["outer_fold"]:
            raise ValueError("prediction fold differs from reference fold")
        branches = pred.get("branches", {})
        if set(branches) != set(BRANCHES[action]):
            raise ValueError("branch partition incomplete or unexpected")
        contributions = {}
        probs = {}
        for branch, component in branches.items():
            p = number(component.get("p"), "branch probability")
            if not 0 <= p <= 1:
                raise ValueError("branch probability outside [0,1]")
            supported = component.get("supported")
            if not isinstance(supported, bool):
                raise ValueError("branch support flag required")
            mu = component.get("mean_W")
            if p > 0:
                if not supported or mu is None:
                    raise ValueError("positive branch mass lacks supported conditional W")
                contribution = p * number(mu, "conditional mean_W")
                positive_support[(action, branch)] += 1
            else:
                if mu is not None:
                    number(mu, "conditional mean_W")
                contribution = 0.0
                if not supported:
                    zero_mass_unsupported[(action, branch)] += 1
            contributions[branch] = contribution
            probs[branch] = p
        if not math.isclose(math.fsum(probs.values()), 1.0, rel_tol=0, abs_tol=1e-10):
            raise ValueError("branch probabilities must sum to 1 without renormalization")
        direct = pred.get("direct_mean_W")
        if direct is not None:
            direct = number(direct, "direct_mean_W")
        preds[key] = {"value": math.fsum(contributions.values()),
                      "contributions": contributions, "probs": probs, "direct": direct}
    expected = {(r, a) for r in refs for a in BRANCHES}
    if set(preds) != expected:
        raise ValueError("Take and Swing must cover exactly the same reference rows")
    has_direct = [p["direct"] is not None for p in preds.values()]
    if any(has_direct) and not all(has_direct):
        raise ValueError("direct comparator must cover every same row and both actions")
    groups = defaultdict(list)
    for rid, ref in refs.items():
        groups[("overall", "ALL", "ALL")].append(rid)
        groups[("count", ref["count"], "ALL")].append(rid)
        for region in ref["regions"]:
            groups[("count_region", ref["count"], region)].append(rid)
    summaries = []
    for (level, count, region), ids in sorted(groups.items()):
        result = {"level": level, "count": count, "region": region, "n": len(ids),
                  "unit": UNIT, "interpretation": "descriptive_g_computation_only"}
        for action in BRANCHES:
            result[action] = {
                "mean_W": math.fsum(preds[(r, action)]["value"] for r in ids) / len(ids),
                "component_contributions_W": {
                    b: math.fsum(preds[(r, action)]["contributions"][b] for r in ids) / len(ids)
                    for b in BRANCHES[action]},
                "mean_branch_probabilities": {
                    b: math.fsum(preds[(r, action)]["probs"][b] for r in ids) / len(ids)
                    for b in BRANCHES[action]}}
            if all(has_direct):
                result[action]["direct_mean_W"] = math.fsum(
                    preds[(r, action)]["direct"] for r in ids) / len(ids)
        result["delta_Swing_minus_Take_W"] = result["Swing"]["mean_W"] - result["Take"]["mean_W"]
        if all(has_direct):
            result["direct_delta_W"] = result["Swing"]["direct_mean_W"] - result["Take"]["direct_mean_W"]
            result["decomposed_minus_direct_delta_W"] = result["delta_Swing_minus_Take_W"] - result["direct_delta_W"]
        summaries.append(result)
    predictive = []
    for action in BRANCHES:
        ids = [r for r, ref in refs.items() if ref["observed_action"] == action]
        if not ids:
            predictive.append({"action": action, "n_observed": 0, "status": "NO_OBSERVED_ROWS"})
            continue
        briers, logs, zero_events = [], [], 0
        for rid in ids:
            truth = refs[rid]["observed_branch"]
            probs = preds[(rid, action)]["probs"]
            briers.append(math.fsum((p - int(b == truth)) ** 2 for b, p in probs.items()))
            pt = probs[truth]
            if pt == 0:
                zero_events += 1
            else:
                logs.append(-math.log(pt))
        predictive.append({"action": action, "n_observed": len(ids),
                           "multiclass_brier_sum": math.fsum(briers) / len(ids),
                           "log_loss": None if zero_events else math.fsum(logs) / len(ids),
                           "zero_probability_observed_events": zero_events,
                           "log_loss_status": "INFINITE" if zero_events else "FINITE",
                           "scope": "observed_action_only_not_counterfactual_calibration"})
    return {"model_id": MODEL_ID, "status": "DRAFT", "synthetic": document["synthetic"],
            "fit_provenance_claim": fit_provenance, "n_reference_rows": len(refs),
            "checks": {"paired_reference_keys": "PASS", "game_fold_no_train_overlap": "PASS",
                       "branch_probabilities": "PASS", "positive_mass_support_flags": "PASS",
                       "actual_fitting_and_preprocessing_provenance": "NOT_VERIFIED"},
            "summaries": summaries, "observed_action_predictive_diagnostics": predictive,
            "supplied_branch_support": [
                {"action": a, "branch": b, "n_reference": len(refs),
                 "positive_mass_supported": positive_support[(a, b)],
                 "zero_mass_unsupported": zero_mass_unsupported[(a, b)]}
                for a in BRANCHES for b in BRANCHES[a]],
            "not_estimated": ["AIPW", "confidence_intervals", "policy_value", "causal_effect",
                              "MLB_branch_models", "calibration_curve", "empirical_branch_support"]}


def main():
    parser = argparse.ArgumentParser(description="공통 참조행의 분해 W 합성; 학습하지 않음")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = args.input.read_bytes()
    result = calculate(json.loads(payload.decode("utf-8-sig")))
    result["input_sha256"] = hashlib.sha256(payload).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


if __name__ == "__main__":
    main()
