"""Read-only independent validation of BCAP nested-refit bootstrap artifacts.

Recreates draws, multiplicities, every split hash and training sample size from
the preserved development data/seeds without importing any BCAP model engine.
Recomputes count aggregation and finite-replicate stability with statistics.
Bootstrap row-level nuisance predictions were not saved; therefore this audit
does not claim a second per-replicate AIPW reconstruction from such predictions.
Outputs must be new files inside this review directory. Never fits models.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
RUNS = ROOT / "columns/001-ball-count/analysis/runs"
RUN_IDS = ["bcap_pitch__mlb_2024_2025__20260909__r03", "bcap_swing__mlb_2024_2025__20260909__r02"]
COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]
METRICS = ["Q0", "Q1", "delta", "learned_gain", "conservative_gain", "learned_action1_share", "n_supported", "coverage"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_meta(path):
    p = Path(path)
    return {"path": p.resolve().relative_to(ROOT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size}


def game_hash(games):
    return hashlib.sha256(json.dumps(sorted(map(int, games)), separators=(",", ":")).encode("utf-8")).hexdigest()


def split(games, k, seed):
    # Independent set-level implementation; no decision rows or engine.folds.
    order = np.random.default_rng(int(seed)).permutation(np.array(sorted(games), dtype=np.int64))
    return [set(map(int, order[j::k])) for j in range(k)]


def close(actual, expected, label, tolerance=1e-9):
    a, b = float(actual), float(expected)
    assert np.isfinite(a) and np.isfinite(b), "Nonfinite " + label
    error = abs(a - b)
    assert error <= tolerance, f"{label}: saved={a}, independent={b}, error={error}"
    return error


def bools(series):
    values = series.map({True: True, False: False, "True": True, "False": False, 1: True, 0: False})
    assert values.notna().all()
    return values.astype(bool)


def source_aggregates(frame, variant):
    d = frame.loc[frame["eligible_" + variant], ["game_pk", "game_year", "at_bat_number", "count", "A_" + variant]].copy()
    d = d.rename(columns={"A_" + variant: "A"})
    d["A"] = d.A.astype(int)
    by_game = d.groupby("game_pk", observed=True).agg(n=("A", "size"), n1=("A", "sum"),
                                                     PA=("at_bat_number", "nunique"), year=("game_year", "first"))
    by_game["n0"] = by_game.n - by_game.n1
    by_count = {str(c): g.groupby("game_pk", observed=True).agg(n=("A", "size"), n1=("A", "sum"), PA=("at_bat_number", "nunique"))
                for c, g in d.groupby("count", observed=True)}
    return by_game, by_count


def recreate_draws(by_game, sample_seed):
    rng = np.random.default_rng(int(sample_seed))
    counts = Counter()
    season_draws = {}
    for year in sorted(by_game.year.unique()):
        population = np.array(sorted(map(int, by_game.index[by_game.year.eq(year)])), dtype=np.int64)
        draw = rng.choice(population, size=len(population), replace=True)
        counts.update(map(int, draw))
        season_draws[str(int(year))] = len(draw)
    return counts, season_draws


def split_and_fit_expectations(games, evaluation_seed, config, by_game, multiplicity):
    all_games = set(games)
    expected_records, fit_counts, nuisance_labels = {}, {}, []

    def n_for(subset, arm=None):
        field = "n" if arm is None else "n" + str(arm)
        return sum(int(by_game.loc[g, field]) * multiplicity[g] for g in subset)

    def record(label, role, tr, ev, parent_train=None, parent_test=None):
        assert tr and ev and not tr & ev
        if parent_train is not None:
            assert (tr | ev) <= parent_train and not (tr | ev) & parent_test
        expected_records[label] = {"role": role, "train_original_games": len(tr), "evaluation_original_games": len(ev),
                                   "intersection_n": 0, "train_games_sha256": game_hash(tr), "evaluation_games_sha256": game_hash(ev)}

    def nuisance(label, training, seed, outer_train, outer_test):
        parts = split(training, 5, seed)
        calibration, tune = parts[0], parts[1]
        base, fitting = training - calibration, training - calibration - tune
        record(label + "/cal", "calibration", base, calibration, outer_train, outer_test)
        record(label + "/tune", "tuning", fitting, tune, outer_train, outer_test)
        for target in ["p", "m0", "m1"]:
            arm = None if target == "p" else int(target[-1])
            for alpha in config["alphas"]:
                fit_counts[label + "/tune/" + target + "/" + str(alpha)] = n_for(fitting, arm)
        fit_counts[label + "/prop"] = n_for(base)
        fit_counts[label + "/m0"] = n_for(training, 0)
        fit_counts[label + "/m1"] = n_for(training, 1)
        fit_counts[label + "/calibrator"] = n_for(calibration)
        nuisance_labels.append(label)

    outer = split(all_games, config["outer_folds"], evaluation_seed)
    for k, outer_test in enumerate(outer):
        outer_train = all_games - outer_test
        label = "outer" + str(k)
        record(label, "outer_evaluation", outer_train, outer_test)
        inner_seed = evaluation_seed + 1000 + 100 * k
        inner = split(outer_train, config["inner_folds"], inner_seed)
        for j, inner_test in enumerate(inner):
            inner_train = outer_train - inner_test
            lab = label + "/inner" + str(j)
            record(lab, "policy_oof", inner_train, inner_test, outer_train, outer_test)
            # Descendant game sets must exclude both original outer and inner tests.
            nuisance(lab, inner_train, inner_seed + 100 + j, inner_train, outer_test | inner_test)
        nuisance(label + "/evaluation_nuisance", outer_train, evaluation_seed + 2000 + k, outer_train, outer_test)
    return outer, expected_records, fit_counts, nuisance_labels


def verify_one(folder, number, config, bootstrap_seed, by_game, by_count):
    audit = read(folder / "replicate_audit.json")
    sample_seed = int(bootstrap_seed) + number - 1
    evaluation_seed = int(config["seed"]) + 100000 + 10000 * (number - 1)
    assert audit["replicate"] == number and audit["sample_seed"] == sample_seed and audit["evaluation_seed"] == evaluation_seed
    mult, season_draws = recreate_draws(by_game, sample_seed)
    membership = pd.read_csv(folder / "sampled_game_multiplicity_and_outer_fold.csv")
    assert not membership.game_pk.duplicated().any(), "Original game has more than one saved outer fold"
    assert set(map(int, membership.game_pk)) == set(mult)
    assert membership.multiplicity.ge(1).all() and membership.multiplicity.eq(membership.multiplicity.astype(int)).all()
    for r in membership.itertuples():
        assert r.multiplicity == mult[int(r.game_pk)]
        assert r.game_year == r.sampled_season == by_game.loc[r.game_pk, "year"]
    assert int(membership.multiplicity.sum()) == sum(season_draws.values()) == audit["drawn_games_with_multiplicity"]
    outer, expected_records, fit_counts, nuisance_labels = split_and_fit_expectations(set(mult), evaluation_seed, config, by_game, mult)
    expected_fold = {game: k for k, group in enumerate(outer) for game in group}
    assert membership.fold.eq(membership.game_pk.map(expected_fold)).all()
    recorded_folds = pd.read_csv(folder / "fold_audit.csv").set_index("fit_id")
    assert set(recorded_folds.index) == set(expected_records)
    for label, expected in expected_records.items():
        for field, value in expected.items():
            assert recorded_folds.loc[label, field] == value, f"Split mismatch {number}:{label}:{field}"
    assert int(audit["split_records_checked"]) == len(expected_records)
    # Every fit's multiplicity-weighted training N is checked against original data.
    fit = pd.read_csv(folder / "fit_diagnostics.csv").set_index("fit_id")
    assert not fit.index.duplicated().any() and set(fit.index) == set(fit_counts)
    for label, expected_n in fit_counts.items():
        assert int(fit.loc[label, "n"]) == expected_n, f"Training rows mismatch {number}:{label}"
    assert bools(fit.converged).all() and audit["all_fits_converged"] is True
    ridge = fit[~fit.index.str.endswith("/calibrator")]
    cal = fit[fit.index.str.endswith("/calibrator")]
    assert ridge.solver_info.eq(0).all() and ridge.relative_gradient.lt(config["solver"]["relative_gradient_limit"]).all()
    assert ridge.iterations.le(config["solver"]["maxiter"]).all() and cal.slope.ge(0).all()
    assert np.isfinite(cal.loss).all() and cal.iterations.le(1000).all()
    assert int(audit["fit_count"]) == len(fit)
    tuning = pd.read_csv(folder / "tuning.csv")
    assert set(tuning.fit_id) == set(nuisance_labels) and len(tuning) == audit["tuning_candidates_evaluated"]
    for label in nuisance_labels:
        for target in ["p", "m0", "m1"]:
            t = tuning[tuning.fit_id.eq(label) & tuning.target.eq(target)]
            assert len(t) == len(config["alphas"]) and set(t.alpha) == set(config["alphas"])
            assert t.metric.eq("Brier" if target == "p" else "MSE").all()
            assert np.isfinite(t.loss).all() and t.loss.ge(0).all()
            chosen = t.sort_values(["loss", "alpha"], ascending=[True, False]).iloc[0].alpha
            actual_fit = label + ("/prop" if target == "p" else "/" + target)
            assert fit.loc[actual_fit, "alpha"] == chosen, "Tuning selection mismatch " + actual_fit
    values = pd.read_csv(folder / "action_policy_values.csv")
    assert len(values) == 13 and not values[["level", "state"]].duplicated().any()
    assert set(values.loc[values.level.eq("count"), "state"]) == set(COUNTS)
    assert values.replicate.eq(number).all() and values.sample_seed.eq(sample_seed).all() and values.evaluation_seed.eq(evaluation_seed).all()
    overall = values[values.level.eq("overall")].iloc[0]
    assert overall.state == "ALL"
    expected_all_rows = sum(int(by_game.loc[g, "n"]) * count for g, count in mult.items())
    assert overall.n_all == expected_all_rows == audit["sample_rows"] == audit["score_rows"]
    assert audit["unique_original_games"] == len(mult) == overall.unique_original_games_all
    errors = {}
    direction = -1 if config["variant"] == "pitch" else 1
    for row in values.itertuples():
        source = by_game if row.level == "overall" else by_count[row.state]
        present = set(map(int, source.index)) & set(mult)
        n = sum(int(source.loc[g, "n"]) * mult[g] for g in present)
        n1 = sum(int(source.loc[g, "n1"]) * mult[g] for g in present)
        pa_upper = sum(int(source.loc[g, "PA"]) for g in present)
        assert row.n_all == n and row.unique_original_games_all == len(present)
        assert 0 <= row.n_supported <= row.n_all
        assert 0 <= row.unique_original_games_supported <= len(present)
        assert 0 <= row.unique_original_PA_supported <= min(pa_upper, row.n_supported)
        checks = {"coverage": (row.coverage, row.n_supported / row.n_all),
                  "all_action1_rate": (row.all_action1_rate, n1 / n),
                  "delta": (row.delta, row.Q1 - row.Q0),
                  "learned_gain": (row.learned_gain, direction * (row.learned_value - row.observed_value)),
                  "conservative_gain": (row.conservative_gain, direction * (row.conservative_value - row.observed_value)),
                  "conservative_retention_value": (row.conservative_value, row.observed_value),
                  "conservative_zero_gain": (row.conservative_gain, 0)}
        for name, pair in checks.items():
            error = close(*pair, label=f"{number}:{row.state}:{name}")
            errors[name] = max(errors.get(name, 0), error)
        assert 0 <= row.learned_action1_share <= 1 and 0 <= row.observed_value <= 2.05
    counts = values[values.level.eq("count")]
    assert counts.n_all.sum() == overall.n_all and counts.n_supported.sum() == overall.n_supported
    assert counts.unique_original_PA_supported.max() <= overall.unique_original_PA_supported <= counts.unique_original_PA_supported.sum()
    for name in ["Q0", "Q1", "delta", "observed_value", "learned_value", "learned_gain", "conservative_value", "conservative_gain", "learned_action1_share"]:
        independent = statistics.fsum(float(x) * int(n) for x, n in zip(counts[name], counts.n_supported)) / int(overall.n_supported)
        errors["supported_count_aggregation_" + name] = close(overall[name], independent, name)
    for name in ["all_action1_rate", "Brier_all", "MSE_all"]:
        independent = statistics.fsum(float(x) * int(n) for x, n in zip(counts[name], counts.n_all)) / int(overall.n_all)
        errors["all_count_aggregation_" + name] = close(overall[name], independent, name)
    assert audit["original_game_crossfold"] == 0 and audit["original_PA_crossfold"] == 0
    assert audit["all_train_evaluation_game_intersections_zero"] is True and audit["no_confidence_interval"] is True
    result = {"replicate": number, "status": "PASS", "sample_seed": sample_seed, "evaluation_seed": evaluation_seed,
              "drawn_games": sum(season_draws.values()), "unique_original_games": len(mult), "source_weighted_rows": expected_all_rows,
              "season_draws": season_draws, "original_game_membership_unique": True,
              "all_outer_inner_tuning_calibration_set_hashes_recreated": True, "split_records_checked": len(expected_records),
              "training_fit_counts_recreated": len(fit_counts), "all_fits_converged": True,
              "saved_tuning_choices_rechecked": len(nuisance_labels) * 3,
              "runtime_original_game_PA_crossfold_flags_zero": True,
              "arithmetic_max_abs_errors": errors,
              "raw_bootstrap_row_score_recomputation": "NOT_AVAILABLE: per-replicate score rows and fitted nuisances were not saved",
              "inputs": [file_meta(folder / name) for name in ["replicate_audit.json", "sampled_game_multiplicity_and_outer_fold.csv",
                                                               "fold_audit.csv", "fit_diagnostics.csv", "tuning.csv", "action_policy_values.csv"]]}
    return result, values


def independent_stability(frame, run_id):
    rows = []
    for (level, state), group in frame.groupby(["level", "state"], observed=True):
        for metric in METRICS:
            numbers = [float(x) for x in group[metric].dropna()]
            rows.append({"run_id": run_id, "level": level, "state": state, "metric": metric, "replicates": len(numbers),
                         "mean": statistics.fmean(numbers), "SD": statistics.stdev(numbers) if len(numbers) > 1 else None,
                         "minimum": min(numbers), "maximum": max(numbers),
                         "positive_fraction": sum(x > 0 for x in numbers) / len(numbers),
                         "interpretation": "Finite full-nested-learning stability summary; not a confidence interval"})
    return rows


def compare_stability(path, independent):
    saved = pd.read_csv(path).set_index(["level", "state", "metric"])
    expected = pd.DataFrame(independent).set_index(["level", "state", "metric"])
    assert set(saved.index) == set(expected.index)
    errors = {}
    for key in saved.index:
        assert saved.loc[key, "replicates"] == expected.loc[key, "replicates"]
        for col in ["mean", "SD", "minimum", "maximum", "positive_fraction"]:
            err = close(saved.loc[key, col], expected.loc[key, col], str(key) + ":" + col,
                        tolerance=1e-7 if key[-1] == "n_supported" else 1e-9)
            errors[col] = max(errors.get(col, 0), err)
    return {"rows": len(saved), "max_abs_errors": errors, "input": file_meta(path)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True)
    ap.add_argument("--require-complete", action="store_true")
    args = ap.parse_args()
    out = Path(args.output).resolve()
    assert out.is_relative_to(HERE) and out.suffix == ".json", "Output must be a new JSON inside review directory"
    companion = out.with_name(out.stem + "_independent_stability.csv")
    assert not out.exists() and not companion.exists(), "Never overwrite a previous audit"
    snapshots = []
    for run_id in RUN_IDS:
        run = RUNS / run_id
        manifest = read(run / "manifest.json")
        progress = read(run / "artifacts/progress.json")
        assert manifest["role"] == "full_pipeline_game_bootstrap_stability"
        assert manifest["planned_replicates"] == progress["planned"] == 8
        completed = int(progress["completed_replicates"])
        assert 1 <= completed <= 8
        if args.require_complete:
            assert manifest["status"] == "COMPLETE" and completed == 8, "Bootstrap not complete: " + run_id
        snapshots.append((run_id, run, manifest, progress, completed, file_meta(run / "manifest.json"), file_meta(run / "artifacts/progress.json")))
    source_inputs = [{r["path"]: r["sha256"] for r in m[2]["inputs"] if "/data/processed/" in r["path"]} for m in snapshots]
    assert len(source_inputs[0]) == 1 and source_inputs[0] == source_inputs[1]
    source_rel, expected_sha = next(iter(source_inputs[0].items()))
    source = ROOT / source_rel
    assert sha(source) == expected_sha
    prepared = pd.read_pickle(source)
    assert set(prepared.game_year.unique()) == {2024, 2025}
    results, all_stability = [], []
    for run_id, run, manifest, progress, completed, manifest_meta, progress_meta in snapshots:
        for rec in manifest["code"] + manifest["inputs"]:
            assert sha(ROOT / rec["path"]) == rec["sha256"], "Preserved bootstrap input/code changed: " + rec["path"]
        by_game, by_count = source_aggregates(prepared, manifest["configuration"]["variant"])
        checks, frames = [], []
        for number in range(1, completed + 1):
            folder = run / "artifacts" / f"replicate_{number:02d}"
            check, values = verify_one(folder, number, manifest["configuration"], manifest["bootstrap_seed"], by_game, by_count)
            checks.append(check)
            frames.append(values)
        independent_values = pd.concat(frames, ignore_index=True)
        cumulative_file = run / "artifacts/replicate_values.csv"
        cumulative = pd.read_csv(cumulative_file)
        cumulative = cumulative[cumulative.replicate.le(completed)]
        sorting = ["replicate", "level", "state"]
        pd.testing.assert_frame_equal(cumulative.sort_values(sorting).reset_index(drop=True),
                                      independent_values.sort_values(sorting).reset_index(drop=True), check_dtype=False, atol=1e-10, rtol=1e-12)
        stability = independent_stability(independent_values, run_id)
        all_stability.extend(stability)
        final = manifest["status"] == "COMPLETE" and completed == 8
        stability_check = compare_stability(run / "artifacts/stability_summary.csv", stability) if final else None
        if final:
            assert manifest["completed_replicates"] == 8 and manifest["no_full_learning_confidence_interval"] is True
            assert manifest["final_policy_modified"] is False
        results.append({"run_id": run_id, "model_id": manifest["model_id"], "run_status": manifest["status"],
                        "status": "PASS" if final else "PASS_COMPLETED_REPLICATES",
                        "planned_replicates": 8, "checked_replicates": completed,
                        "stability_summary_checked": final, "stability_summary_comparison": stability_check,
                        "source_manifest_snapshot": manifest_meta, "source_progress_snapshot": progress_meta,
                        "cumulative_values_input": file_meta(cumulative_file), "cumulative_values_match_replicates": True,
                        "replicate_checks": checks})
    both_complete = all(r["status"] == "PASS" and r["checked_replicates"] == 8 for r in results)
    if args.require_complete:
        assert both_complete
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_stability).to_csv(companion, index=False, encoding="utf-8-sig")
    record = {"status": "PASS" if both_complete else "PASS_COMPLETED_REPLICATES",
              "checked_at_utc": datetime.now(timezone.utc).isoformat(), "both_completed_8": both_complete,
              "full_learning_interval_validated": False, "recommendation_gate_upgrade": False,
              "scope": "Independent resampling/split-hash/training-N/arithmetic/aggregation audit of full nested evaluation learner refits; not CI for frozen final full-development policy",
              "limits": ["Eight repetitions support descriptive SD/range/sign frequency only, not95% inference",
                         "Bootstrap row-level scores/nuisance predictions were not stored; per-replicate raw AIPW cannot be independently recomputed without refitting",
                         "Saved runtime PA/game crossfold zero checks corroborated by independently reconstructed original-game membership and every split hash",
                         "Original-game clustering does not remove cross-game dependence of players or series"],
              "source_data": file_meta(source), "runs": results,
              "code": file_meta(__file__), "command": [sys.executable] + sys.argv,
              "independent_stability_output": file_meta(companion)}
    with out.open("x", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")
    print(json.dumps({"status": record["status"], "both_completed_8": both_complete,
                      "runs": [{k: r[k] for k in ["run_id", "checked_replicates", "status", "stability_summary_checked"]} for r in results],
                      "output": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
