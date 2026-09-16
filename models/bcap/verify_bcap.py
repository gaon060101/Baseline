"""Independent BCAP arithmetic, denominator, row-key and split verifier.

Does not import the BCAP estimation engine, fit models, acquire data, or choose
policies. An OPE score is reconstructed as policy regression + a single observed
action importance residual, independently of the engine's two-action score mix.
CLI output is a new audit, never an overwrite of an existing result.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]
KEY = ["game_pk", "at_bat_number", "pitch_number"]
REQUIRED = KEY + ["game_year", "count", "A", "Y", "p", "mu0", "mu1",
                  "phi0", "phi1", "support", "policy_p1",
                  "conservative_change", "conservative_p1", "fold", "repertoire",
                  "final_event", "result", "pitcher", "batter", "measurement_support"]
WEIGHTS = {
    2023: {"walk": .696, "hit_by_pitch": .726, "single": .883,
           "double": 1.244, "triple": 1.569, "home_run": 2.004},
    2024: {"walk": .689, "hit_by_pitch": .720, "single": .882,
           "double": 1.254, "triple": 1.590, "home_run": 2.050},
    2025: {"walk": .691, "hit_by_pitch": .722, "single": .882,
           "double": 1.252, "triple": 1.584, "home_run": 2.037},
}
WEIGHTS[2026] = WEIGHTS[2025].copy()
ZERO_EVENTS = {"strikeout", "strikeout_double_play", "field_out", "force_out",
               "grounded_into_double_play", "double_play", "fielders_choice_out",
               "sac_fly", "sac_bunt", "sac_fly_double_play", "sac_bunt_double_play",
               "triple_play", "field_error", "fielders_choice"}
FORBIDDEN_BOTH = {"description", "events", "final_event", "Y", "value", "result",
                  "launch_speed", "launch_angle", "bb_type", "hit_location",
                  "woba_value", "delta_run_exp", "post_bat_score"}
FORBIDDEN_PITCH = {"pitch_type", "pitch_name", "release_speed", "plate_x", "plate_z",
                   "pfx_x", "pfx_z", "zone", "type", "swing", "Swing", "A"}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def max_error(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    assert np.isfinite(a).all() and np.isfinite(b).all(), "Nonfinite values"
    return float(np.max(np.abs(a - b), initial=0.))


def checked_bool(s, label):
    if s.dtype == bool:
        return s.to_numpy()
    assert s.notna().all(), f"Missing {label}"
    mapping = {True: True, False: False, 1: True, 0: False,
               "True": True, "False": False, "true": True, "false": False}
    v = s.map(mapping)
    assert v.notna().all(), f"Nonboolean {label}"
    return v.astype(bool).to_numpy()


def policy_score(y, a, p, mu0, mu1, d):
    """Single-residual OPE form, not a reuse of supplied phi columns."""
    observed_mu = mu0 + a * (mu1 - mu0)
    chosen_regression = mu0 + d * (mu1 - mu0)
    likelihood_ratio = np.empty(len(y), dtype=float)
    actual1 = a == 1
    likelihood_ratio[actual1] = d[actual1] / p[actual1]
    likelihood_ratio[~actual1] = (1 - d[~actual1]) / (1 - p[~actual1])
    return chosen_regression + likelihood_ratio * (y - observed_mu)


def cluster_se(values, games):
    """Ratio-of-totals influence formula; unequal game sizes are retained."""
    if len(values) == 0:
        return None
    t = pd.DataFrame({"v": values, "game": games})
    by = t.groupby("game").v.agg(["sum", "size"])
    g = len(by)
    if g < 2:
        return None
    centered_totals = by["sum"].to_numpy() - by["size"].to_numpy() * t.v.mean()
    return float(np.sqrt(g / (g - 1) * np.dot(centered_totals, centered_totals)) / len(t))


def verify_frame(frame, model, trim=.05, columns=None, atol=1e-9):
    """Return independent per-count values and diagnostics for supplied scores.

    columns maps canonical verifier names to engine names. Conservative change
    identifies the intervention region; outside it the contribution is observed Y.
    The same support mask is used for every policy and both actions.
    """
    assert model.lower() in {"pitch", "swing"}
    model = model.lower()
    columns = columns or {}
    d = frame.rename(columns={v: k for k, v in columns.items()}).copy()
    missing = sorted(set(REQUIRED) - set(d.columns))
    assert not missing, f"Missing required columns: {missing}"
    assert len(d) > 0, "Empty evaluation frame"
    assert d[KEY].notna().all().all(), "Missing pitch key"
    assert not d.duplicated(KEY).any(), "Duplicate evaluation pitch key"
    assert set(d["count"]).issubset(COUNTS), "Invalid pre-pitch count"
    for name in KEY + ["game_year"]:
        vals = d[name].to_numpy(dtype=float)
        assert np.isfinite(vals).all() and np.equal(vals, np.floor(vals)).all(), name
    assert (d.pitch_number >= 1).all()
    assert d.groupby("game_pk").fold.nunique().max() == 1, "Game split across folds"
    assert d.groupby(KEY[:2]).fold.nunique().max() == 1, "PA split across folds"
    assert d.groupby(KEY[:2]).Y.nunique().max() == 1, "Inconsistent final PA Y"
    assert d.groupby(KEY[:2]).game_year.nunique().max() == 1, "Inconsistent PA season"
    assert set(d.game_year).issubset(WEIGHTS), "Unexpected season weights"
    assert set(d.A).issubset({0, 1}), "Nonbinary action"
    for name in ["Y", "p", "mu0", "mu1", "phi0", "phi1", "policy_p1", "conservative_p1"]:
        assert np.isfinite(d[name].to_numpy(dtype=float)).all(), f"Nonfinite {name}"
    assert d.p.between(0, 1, inclusive="neither").all(), "Zero/one propensity"
    assert d.policy_p1.between(0, 1).all() and d.conservative_p1.between(0, 1).all()
    assert d.Y.between(0, 2.05).all(), "Y outside OBS raw-weight range"
    support = checked_bool(d.support, "support")
    repertoire = checked_bool(d.repertoire, "repertoire")
    measurement = checked_bool(d.measurement_support, "measurement_support")
    expected_support = (d.p.to_numpy() >= trim) & (d.p.to_numpy() <= 1 - trim) & repertoire & measurement
    assert np.array_equal(support, expected_support), "Support differs from p trimming and training repertoire restriction"
    change = checked_bool(d.conservative_change, "conservative_change")
    y, a, p, m0, m1 = [d[n].to_numpy(dtype=float) for n in ["Y", "A", "p", "mu0", "mu1"]]
    s0 = policy_score(y, a, p, m0, m1, np.zeros(len(d)))
    s1 = policy_score(y, a, p, m0, m1, np.ones(len(d)))
    errors = {"phi0_max_abs": max_error(s0, d.phi0), "phi1_max_abs": max_error(s1, d.phi1)}
    assert max(errors.values()) <= atol, f"AIPW mismatch {errors}"
    learned = policy_score(y, a, p, m0, m1, d.policy_p1.to_numpy(dtype=float))
    conservative = policy_score(y, a, p, m0, m1, d.conservative_p1.to_numpy(dtype=float))
    conservative[~change] = y[~change]
    for name, expected in [("policy_value", learned), ("conservative_value", conservative)]:
        if name in d:
            errors[name + "_max_abs"] = max_error(expected, d[name])
            assert errors[name + "_max_abs"] <= atol
    errors["policy_direct_vs_phi_mix_max_abs"] = max_error(
        learned, (1 - d.policy_p1.to_numpy()) * d.phi0.to_numpy() + d.policy_p1.to_numpy() * d.phi1.to_numpy())
    assert errors["policy_direct_vs_phi_mix_max_abs"] <= atol
    result_check = "NOT_AVAILABLE: final_event not supplied"
    if "final_event" in d:
        assert d.final_event.notna().all()
        assert d.groupby(KEY[:2]).final_event.nunique().max() == 1
        expected_y = np.full(len(d), np.nan)
        for yr in WEIGHTS:
            mapping = {event: 0. for event in ZERO_EVENTS} | WEIGHTS[yr]
            mask = d.game_year.eq(yr)
            expected_y[mask] = d.loc[mask, "final_event"].map(mapping).to_numpy()
        assert np.isfinite(expected_y).all(), "Unknown/ineligible final event"
        err = max_error(expected_y, y)
        assert err <= atol, f"Wrong OBS season Y: {err}"
        errors["OBS_final_event_Y_max_abs"] = err
        event_results = {event: "OUT" for event in ZERO_EVENTS}
        event_results.update({"strikeout": "K", "strikeout_double_play": "K",
                              "field_error": "OTHER", "fielders_choice": "OTHER",
                              "walk": "BB", "hit_by_pitch": "HBP", "single": "1B",
                              "double": "2B", "triple": "3B", "home_run": "HR"})
        assert d.final_event.astype(str).map(event_results).eq(d.result.astype(str)).all(), "Wrong OBS event class"
        result_check = "PASS"
    direction = -1. if model == "pitch" else 1.
    summaries = []
    all_scenarios = {"always0": s0, "always1": s1, "learned": learned,
                     "conservative": conservative, "observed": y}
    for count in COUNTS + ["ALL"]:
        base = np.ones(len(d), dtype=bool) if count == "ALL" else d["count"].eq(count).to_numpy()
        mask = base & support
        n = int(mask.sum())
        row = {"count": count, "N_all": int(base.sum()), "N": n,
               "support_rate": float(mask.sum() / base.sum()) if base.any() else None}
        if not n:
            summaries.append(row)
            continue
        part = d.loc[mask]
        row.update(games=int(part.game_pk.nunique()), PA=int(part[KEY[:2]].drop_duplicates().shape[0]),
                   N0=int((a[mask] == 0).sum()), N1=int((a[mask] == 1).sum()),
                   observed_action1_rate=float(a[mask].mean()),
                   Q0=float(s0[mask].mean()), Q1=float(s1[mask].mean()),
                   delta=float((s1[mask] - s0[mask]).mean()),
                   delta_cluster_SE=cluster_se(s1[mask] - s0[mask], part.game_pk.to_numpy()),
                   change_region_rate=float(change[mask].mean()),
                   actual_switch_rate=float((d.policy_p1.to_numpy()[mask] * (1 - a[mask]) +
                                             (1 - d.policy_p1.to_numpy()[mask]) * a[mask]).mean()))
        for name, score in all_scenarios.items():
            value = float(score[mask].mean())
            row[f"V_{name}"] = value
            row[f"gain_{name}"] = float(direction * (score[mask] - y[mask]).mean())
            row[f"gain_{name}_cluster_SE"] = cluster_se(direction * (score[mask] - y[mask]), part.game_pk.to_numpy())
        for action in [0, 1]:
            weights = np.zeros(n)
            actual = a[mask] == action
            probs = p[mask] if action else 1 - p[mask]
            weights[actual] = 1 / probs[actual]
            sw, sw2 = weights.sum(), weights @ weights
            row[f"ESS{action}"] = float(sw * sw / sw2) if sw2 else 0.
            wg = pd.Series(weights).groupby(part.game_pk.to_numpy()).sum().to_numpy()
            row[f"max_game_weight_share{action}"] = float(wg.max(initial=0.) / sw) if sw else None
        summaries.append(row)
    assert sum(r["N"] for r in summaries[:-1]) == summaries[-1]["N"], "Count support sum"
    return {"status": "PASS", "model": model, "rows": len(d),
            "eligible_games": int(d.game_pk.nunique()), "eligible_PA": int(d[KEY[:2]].drop_duplicates().shape[0]),
            "supported_rows": int(support.sum()), "trim": trim,
            "errors": errors, "final_event_Y_check": result_check,
            "independent_values": summaries,
            "scope": "Arithmetic/keys/denominators only. Not causal identification, nuisance consistency, or full-refit uncertainty."}


def verify_fold_records(records):
    """Check explicit training/evaluation game sets for every provided fit."""
    if isinstance(records, dict):
        records = records["records"]
    assert records, "No split records"
    checked = []
    parents = [r for r in records if r.get("role") in {"outer_evaluation", "policy_oof", "external_ope"}]
    for rec in records:
        train = set(map(int, rec["train_games"]))
        evaluate = set(map(int, rec["evaluation_games"]))
        assert train and evaluate, "Empty training/evaluation games"
        assert not (train & evaluate), f"Game leakage in {rec.get('fit_id')}"
        ancestor_ids = []
        for parent in parents:
            if rec["fit_id"].startswith(parent["fit_id"] + "/"):
                heldout = set(map(int, parent["evaluation_games"]))
                allowed = set(map(int, parent["train_games"]))
                assert not ((train | evaluate) & heldout), f"Ancestor holdout leakage {rec['fit_id']} under {parent['fit_id']}"
                assert (train | evaluate) <= allowed, f"Nested split outside parent train {rec['fit_id']}"
                ancestor_ids.append(parent["fit_id"])
        if "outer_evaluation_games" in rec:
            outer = set(map(int, rec["outer_evaluation_games"]))
            assert not train & outer, f"Outer leakage in {rec.get('fit_id')}"
            if rec.get("role") in {"inner", "tuning", "policy_learning", "calibration"}:
                assert not evaluate & outer
        checked.append({"fit_id": rec.get("fit_id"), "train_games": len(train),
                        "evaluation_games": len(evaluate), "intersection": 0,
                        "verified_ancestor_holdouts": ancestor_ids})
    return {"status": "PASS", "records": checked}


def verify_features(config, model):
    features = config["features"]
    if isinstance(features, dict):
        features = features[model]
    if isinstance(features, dict):
        features = features["X"]
    forbidden = FORBIDDEN_BOTH | (FORBIDDEN_PITCH if model == "pitch" else set())
    assert not set(features) & forbidden, f"Forbidden current/post-action feature: {set(features) & forbidden}"
    assert {"pitcher", "batter"}.issubset(features), "Missing player effect in X"
    return {"status": "PASS", "checked_X": features,
            "scope": "Feature names only; derivation lineage must be audited separately."}


def numerical_fixture():
    """Check engine centered ridge against an independent dense direct solution.

    Deliberately synthetic; this verifies implementation and unseen-block behavior,
    not empirical fit, identification, or performance on the actual MLB dataset.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("bcap_engine_numerical_fixture", Path(__file__).with_name("run.py"))
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    i = np.arange(60)
    train = pd.DataFrame({"pitcher": (i % 3).astype(str), "batter": (i % 7).astype(str),
                          "count": np.where(i % 4 == 0, "1-0", "0-0"),
                          "venue": (i % 2).astype(str)})
    fs = list(train.columns)
    y = .31 + .2 * (i % 3 == 1) - .1 * (i % 7 == 4) + .03 * np.sin(i)
    alpha = 7.3
    dictionaries = [sorted(train[f].unique()) for f in fs]
    matrices = [(train[f].to_numpy()[:, None] == np.array(levels)[None, :]).astype(float)
                for f, levels in zip(fs, dictionaries)]
    means = [x.mean(axis=0) for x in matrices]
    centered = np.concatenate([x - m for x, m in zip(matrices, means)], axis=1)
    direct_beta = np.linalg.solve(centered.T @ centered + alpha * np.eye(centered.shape[1]),
                                  centered.T @ (y - y.mean()))
    logs = []
    actual = engine.Ridge(train, y, fs, alpha, "independent_dense_fixture", logs)
    train_expected = y.mean() + centered @ direct_beta
    train_error = max_error(actual.predict(train), train_expected)
    coef_error = max_error(actual.beta, direct_beta)
    evaluation = pd.DataFrame({"pitcher": ["UNSEEN", "1", "UNSEEN", "0"],
                               "batter": ["UNSEEN", "2", "3", "UNSEEN"],
                               "count": ["UNSEEN", "0-0", "1-0", "0-0"],
                               "venue": ["UNSEEN", "0", "1", "UNSEEN"]})
    blocks = []
    for f, levels, center in zip(fs, dictionaries, means):
        block = np.zeros((len(evaluation), len(levels)))
        for row, value in enumerate(evaluation[f]):
            if value in levels:
                block[row] -= center
                block[row, levels.index(value)] += 1
        blocks.append(block)
    expected = y.mean() + np.concatenate(blocks, axis=1) @ direct_beta
    predictions = actual.predict(evaluation)
    unseen_error = max_error(predictions, expected)
    assert abs(predictions[0] - y.mean()) < 1e-12, "All-unseen effects must be exactly zero"
    assert max(train_error, coef_error, unseen_error) < 1e-8
    bad = [{"fit_id": "outer0", "role": "outer_evaluation", "train_games": [1, 2], "evaluation_games": [3]},
           {"fit_id": "outer0/inner0/cal", "role": "calibration", "train_games": [1], "evaluation_games": [3]}]
    caught_ancestor = False
    try:
        verify_fold_records(bad)
    except AssertionError:
        caught_ancestor = True
    assert caught_ancestor, "Verifier failed to reject parent holdout contamination"
    return {"status": "PASS", "synthetic_only": True, "alpha": alpha, "training_rows": len(train),
            "coefficient_max_abs_error": coef_error, "training_prediction_max_abs_error": train_error,
            "known_unseen_prediction_max_abs_error": unseen_error,
            "all_unseen_prediction_equals_training_intercept": True,
            "ancestor_leakage_fixture_rejected": caught_ancestor,
            "fit_diagnostics": logs, "engine_sha256": sha(Path(__file__).with_name("run.py"))}


def verify_saved_policies(directory, model):
    """Relearn only the stated finite policy from saved training scores to check it.

    This is a deterministic audit of existing policy selections, not tuning a new
    policy. Actual evaluation-game outcomes never enter the check or selection.
    """
    folder = Path(directory)
    outer = json.loads((folder / "outer_policies.json").read_text(encoding="utf-8-sig"))
    final = json.loads((folder / "final_policy.json").read_text(encoding="utf-8-sig"))
    records = json.loads((folder / "fold_records.json").read_text(encoding="utf-8-sig"))
    record_map = {r["fit_id"]: r for r in records}
    cases = [(f"outer{k}", policy, folder / f"outer{k}_policy_training_scores.pkl")
             for k, policy in enumerate(outer)]
    cases.append(("final_policy", final, folder / "final_policy_training_scores.pkl"))
    checks = []
    for label, policy, source in cases:
        d = pd.read_pickle(source)
        assert not d.duplicated(KEY).any(), f"Duplicate policy-training rows: {label}"
        assert d.groupby("game_pk").fold.nunique().max() == 1
        games = set(map(int, d.game_pk.unique()))
        if label in record_map:
            parent = record_map[label]
            assert games == set(map(int, parent["train_games"])), f"Policy training game coverage {label}"
            assert not games & set(map(int, parent["evaluation_games"])), f"Policy uses outer holdout {label}"
        for fold, chunk in d.groupby("fold"):
            rec = record_map[f"{label}/inner{int(fold)}"]
            assert set(map(int, chunk.game_pk.unique())) == set(map(int, rec["evaluation_games"]))
            assert not set(map(int, chunk.game_pk.unique())) & set(map(int, rec["train_games"]))
        a, y, p, m0, m1 = [d[x].to_numpy(dtype=float) for x in ["A", "Y", "p", "mu0", "mu1"]]
        phi0 = policy_score(y, a, p, m0, m1, np.zeros(len(d)))
        phi1 = policy_score(y, a, p, m0, m1, np.ones(len(d)))
        err = max(max_error(phi0, d.phi0), max_error(phi1, d.phi1))
        assert err < 1e-9
        support = checked_bool(d.support, "support")
        expected_support = d.p.between(.05, .95).to_numpy() & checked_bool(d.repertoire, "repertoire") & checked_bool(d.measurement_support, "measurement_support")
        assert np.array_equal(support, expected_support)
        t = pd.DataFrame({"state": d[policy["key"]].astype(str).to_numpy(),
                          "delta": phi1 - phi0, "game": d.game_pk.to_numpy()})[support]
        grouped = t.groupby("state").agg(delta=("delta", "mean"), n=("delta", "size"), games=("game", "nunique"))
        assert set(grouped.index) == set(policy["states"]), f"Policy state dictionary {label}"
        max_delta_error = 0.
        for state, row in grouped.iterrows():
            saved = policy["states"][state]
            action = int(row.delta < 0) if model == "pitch" else int(row.delta > 0)
            assert int(saved["p1"]) == action, f"Policy action sign {label}:{state}"
            assert int(saved["n"]) == int(row.n) and int(saved["games"]) == int(row.games)
            max_delta_error = max(max_delta_error, abs(float(saved["delta"]) - float(row.delta)))
        assert max_delta_error < 1e-9
        assert policy["fallback_p1"] == .5 and policy["conservative_change"] is False
        checks.append({"policy": label, "states": len(grouped), "rows": len(d),
                       "supported_rows": int(support.sum()), "games": len(games),
                       "score_max_abs_error": err, "policy_delta_max_abs_error": max_delta_error,
                       "source_sha256": sha(source)})
    return {"status": "PASS", "policies": checks,
            "policy_definition_hashes": [{"path": str(folder / name), "sha256": sha(folder / name)}
                                          for name in ["outer_policies.json", "final_policy.json", "fold_records.json"]]}


def compare_summary(result, path, atol=1e-9):
    reported = pd.read_csv(path)
    if "level" in reported:
        reported = reported[reported.level.isin(["count", "overall"])].copy()
    reported = reported.rename(columns={"state": "count", "n": "N", "n_all": "N_all",
                                       "coverage": "support_rate", "se": "delta_cluster_SE",
                                       "action1_rate": "observed_action1_rate",
                                       "max_game_share0": "max_game_weight_share0",
                                       "max_game_share1": "max_game_weight_share1"})
    recomputed = pd.DataFrame(result["independent_values"])
    assert "count" in reported
    assert not reported["count"].duplicated().any()
    common = sorted((set(reported.columns) & set(recomputed.columns)) - {"count"})
    assert {"Q0", "Q1", "delta", "N"}.issubset(common), "Summary lacks required comparable columns"
    joined = reported.merge(recomputed, on="count", how="left", suffixes=("_reported", "_independent"), validate="one_to_one")
    errors = {}
    for c in common:
        x, z = joined[f"{c}_reported"], joined[f"{c}_independent"]
        assert np.array_equal(x.isna(), z.isna()), f"Missingness differs: {c}"
        valid = x.notna()
        if valid.any():
            errors[c] = max_error(x[valid], z[valid])
            assert errors[c] <= atol, f"Summary differs {c}: {errors[c]}"
    return {"status": "PASS", "max_abs_errors": errors, "rows": len(reported), "sha256": sha(path)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rows")
    ap.add_argument("--model", choices=["pitch", "swing"])
    ap.add_argument("--output", required=True)
    ap.add_argument("--numerical-fixture", action="store_true")
    ap.add_argument("--trim", type=float, default=.05)
    ap.add_argument("--columns", help="JSON file mapping verifier columns to input columns")
    ap.add_argument("--summary")
    ap.add_argument("--folds")
    ap.add_argument("--config")
    ap.add_argument("--policy-directory")
    args = ap.parse_args()
    output = Path(args.output)
    assert not output.exists(), "Preserve existing audits; choose new output filename"
    if args.numerical_fixture:
        result = numerical_fixture()
        result.update(checked_at_utc=datetime.now(timezone.utc).isoformat(),
                      verifier_sha256=sha(__file__), command=sys.argv)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
            f.write("\n")
        print(json.dumps(result, ensure_ascii=False))
        return
    assert args.rows and args.model, "--rows and --model required for actual data verification"
    rows_path = Path(args.rows)
    data = pd.read_pickle(rows_path) if rows_path.suffix in {".pkl", ".pickle"} else pd.read_csv(rows_path)
    columns = json.loads(Path(args.columns).read_text(encoding="utf-8-sig")) if args.columns else None
    result = verify_frame(data, args.model, args.trim, columns)
    result.update(checked_at_utc=datetime.now(timezone.utc).isoformat(),
                  rows_file={"path": str(rows_path.resolve()), "sha256": sha(rows_path)},
                  verifier={"path": str(Path(__file__).resolve()), "sha256": sha(__file__)},
                  command=sys.argv)
    result["additional_inputs"] = [{"path": str(Path(path).resolve()), "sha256": sha(path)}
                                   for path in [args.columns, args.summary, args.folds, args.config] if path]
    if args.summary:
        result["reported_summary_comparison"] = compare_summary(result, args.summary)
    if args.folds:
        result["fold_records"] = verify_fold_records(json.loads(Path(args.folds).read_text(encoding="utf-8-sig")))
    if args.config:
        result["features"] = verify_features(json.loads(Path(args.config).read_text(encoding="utf-8-sig")), args.model)
    if args.policy_directory:
        result["saved_policies"] = verify_saved_policies(args.policy_directory, args.model)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"status": result["status"], "rows": result["rows"],
                      "supported_rows": result["supported_rows"], "errors": result["errors"],
                      "output": str(output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
