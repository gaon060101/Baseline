"""Whole-game bootstrap of the complete nested development evaluation procedure.

Each replicate relearns preprocessing dictionaries, shrinkage choices, calibration,
nuisance fits and inner policy selection, then evaluates on outer games. This is a
small-replicate stability diagnostic, not a percentile or other 95% confidence
interval. It does not modify the frozen final development policy or nuisance.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import traceback

import run as engine

import numpy as np
import pandas as pd


def list_hash(values):
    payload = json.dumps(sorted(map(int, values)), separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def draw_games(d, seed):
    """Stratify seasons; duplicated draws retain the original game identifier."""
    rng = np.random.default_rng(seed)
    records = []
    for year, group in d.groupby("game_year", observed=True):
        games = np.sort(group.game_pk.unique())
        sampled = rng.choice(games, size=len(games), replace=True)
        for game in sampled:
            records.append({"game_pk": int(game), "sampled_season": int(year), "bootstrap_draw_id": len(records)})
    draws = pd.DataFrame(records)
    sample = d.merge(draws, on="game_pk", how="inner", validate="many_to_many", sort=False).reset_index(drop=True)
    assert sample.game_year.eq(sample.sampled_season).all()
    multiplicity = draws.groupby(["sampled_season", "game_pk"], observed=True).size().rename("multiplicity").reset_index()
    expected_rows = int(d.game_pk.map(multiplicity.set_index("game_pk").multiplicity).fillna(0).sum())
    assert len(sample) == expected_rows
    return sample, draws, multiplicity


def summaries(scores, c, replicate, sample_seed, evaluation_seed):
    rows = []
    groups = [("overall", "ALL", scores)]
    groups.extend(("count", str(count), scores[scores["count"].astype(str).eq(count)])
                  for count in [f"{b}-{s}" for b in range(4) for s in range(3)])
    for level, state, allrows in groups:
        s = allrows[allrows.support]
        sign = -1 if c["variant"] == "pitch" else 1
        record = {"replicate": replicate, "sample_seed": sample_seed, "evaluation_seed": evaluation_seed,
                  "level": level, "state": state, "n_all": len(allrows), "n_supported": len(s),
                  "coverage": len(s) / len(allrows) if len(allrows) else np.nan,
                  "unique_original_games_all": int(allrows.game_pk.nunique()),
                  "unique_original_games_supported": int(s.game_pk.nunique()),
                  "unique_original_PA_supported": int(s[["game_pk", "at_bat_number"]].drop_duplicates().shape[0]),
                  "Q0": float(s.phi0.mean()), "Q1": float(s.phi1.mean()),
                  "delta": float((s.phi1 - s.phi0).mean()),
                  "observed_value": float(s.Y.mean()), "learned_value": float(s.policy_value.mean()),
                  "learned_gain": float((sign * (s.policy_value - s.Y)).mean()),
                  "conservative_value": float(s.conservative_value.mean()),
                  "conservative_gain": float((sign * (s.conservative_value - s.Y)).mean()),
                  "learned_action1_share": float(s.policy_p1.mean()),
                  "all_action1_rate": float(allrows.A.mean()),
                  "Brier_all": float(np.mean((allrows.A - allrows.p) ** 2)) if len(allrows) else np.nan,
                  "MSE_all": float(np.mean((allrows.Y - np.where(allrows.A.eq(1), allrows.mu1, allrows.mu0)) ** 2)) if len(allrows) else np.nan,
                  "unit": "W per selected current decision; bootstrap multiplicities retained",
                  "uncertainty_role": "full nested relearning stability; no 95% interval or recommendation"}
        rows.append(record)
    return rows


def compact_fold_records(records):
    rows = []
    for record in records:
        tr, ev = set(record["train_games"]), set(record["evaluation_games"])
        overlap = sorted(tr & ev)
        if overlap:
            raise AssertionError("Original-game leakage in bootstrap: " + record["fit_id"])
        rows.append({"fit_id": record["fit_id"], "role": record["role"],
                     "train_original_games": len(tr), "evaluation_original_games": len(ev),
                     "intersection_n": len(overlap), "train_games_sha256": list_hash(tr),
                     "evaluation_games_sha256": list_hash(ev)})
    return rows


def run_bootstrap(args):
    source_run = engine.ANAL / "runs" / args.development_run
    source_manifest = source_run / "manifest.json"
    source = engine.read(source_manifest)
    if source["status"] != "COMPLETE" or source.get("role") != "development_2024_2025":
        raise ValueError("A completed ordinary development run is required")
    c = copy.deepcopy(source["configuration"])
    if c["variant"] != args.model:
        raise ValueError("Model differs from source development configuration")
    data_path = Path(args.data).resolve()
    data_meta = engine.meta(data_path)
    matched = [m for m in source["inputs"] if m["path"] == data_meta["path"]]
    if len(matched) != 1 or matched[0]["sha256"] != data_meta["sha256"]:
        raise ValueError("Data must exactly match completed source development input")
    # The fitted procedure itself must match the development version being studied.
    for name in ["run.py", "data.py"]:
        rel = (engine.MODEL / name).relative_to(engine.ROOT).as_posix()
        original = [m for m in source["code"] if m["path"] == rel]
        if len(original) != 1 or engine.sha(engine.ROOT / rel) != original[0]["sha256"]:
            raise ValueError("Development engine changed before bootstrap: " + rel)
    if args.replicates < 2:
        raise ValueError("At least two replicates required for a stability diagnostic")
    dest, artifacts, manifest = engine.new_run(c, "full_pipeline_game_bootstrap_stability", args.run_id)
    manifest.update(
        source_development_run=args.development_run,
        inputs=[data_meta, engine.meta(source_manifest)],
        code=[engine.meta(engine.MODEL / "run.py"), engine.meta(engine.MODEL / "data.py"), engine.meta(Path(__file__).resolve())],
        planned_replicates=args.replicates,
        bootstrap_seed=args.bootstrap_seed,
        sampling="Within each season, sample the original number of eligible games with replacement; keep original game_pk in every duplicate draw",
        evaluation="All outer/inner nuisance preprocessing, tuning, calibration and policy selection refit in every replicate",
        final_policy_modified=False,
        interpretation="Small-replicate algorithm stability only. No full-learning 95% CI, recommendation gate, or replacement of fixed-score conditional intervals",
        command=[sys.executable] + sys.argv,
    )
    engine.js(dest / "manifest.json", manifest)
    all_values, all_replicates = [], []
    try:
        original = pd.read_pickle(data_path)
        original = original[original["eligible_" + args.model]].copy()
        original["A"] = original["A_" + args.model].astype(int)
        original = engine.features(original, c).reset_index(drop=True)
        if set(original.game_year.unique()) != {2024, 2025}:
            raise ValueError("Only development seasons 2024/2025 may enter this diagnostic")
        for replicate in range(args.replicates):
            sample_seed = args.bootstrap_seed + replicate
            evaluation_seed = c["seed"] + 100000 + 10000 * replicate
            out = artifacts / f"replicate_{replicate + 1:02d}"
            out.mkdir()
            started = engine.now()
            sample, draws, multiplicity = draw_games(original, sample_seed)
            outer = engine.folds(sample, c["outer_folds"], evaluation_seed)
            membership = sample[["game_pk", "game_year"]].assign(fold=outer).drop_duplicates()
            game_fold_n = membership.groupby("game_pk").fold.nunique()
            if game_fold_n.max() != 1:
                raise AssertionError("Copies of an original game were assigned different outer folds")
            membership = membership.merge(multiplicity, on="game_pk", validate="one_to_one")
            engine.csv(out / "sampled_game_multiplicity_and_outer_fold.csv", membership)
            scores, logs, records, tuning = engine.evaluate_development(sample, c, out, seed=evaluation_seed, save_rows=False)
            fold_audit = compact_fold_records(records)
            # Score rows independently verify the rule after the actual fitting path.
            original_game_crossfold = int(scores.groupby("game_pk", observed=True).fold.nunique().gt(1).sum())
            original_PA_crossfold = int(scores.groupby(["game_pk", "at_bat_number"], observed=True).fold.nunique().gt(1).sum())
            assert original_game_crossfold == 0 and original_PA_crossfold == 0
            assert len(scores) == len(sample)
            values = summaries(scores, c, replicate + 1, sample_seed, evaluation_seed)
            all_converged = all(bool(record["converged"]) for record in logs)
            if not all_converged:
                raise AssertionError("At least one bootstrap nuisance/calibration fit did not converge")
            summary = {"replicate": replicate + 1, "started_at_utc": started, "finished_at_utc": engine.now(),
                       "sample_seed": sample_seed, "evaluation_seed": evaluation_seed,
                       "drawn_games_with_multiplicity": len(draws), "unique_original_games": int(sample.game_pk.nunique()),
                       "sample_rows": len(sample), "score_rows": len(scores),
                       "all_fits_converged": all_converged, "fit_count": len(logs), "tuning_candidates_evaluated": len(tuning),
                       "split_records_checked": len(records), "original_game_crossfold": original_game_crossfold,
                       "original_PA_crossfold": original_PA_crossfold, "all_train_evaluation_game_intersections_zero": True,
                       "no_confidence_interval": True}
            engine.csv(out / "action_policy_values.csv", values)
            engine.csv(out / "fit_diagnostics.csv", logs)
            engine.csv(out / "tuning.csv", tuning)
            engine.csv(out / "fold_audit.csv", fold_audit)
            engine.js(out / "replicate_audit.json", summary)
            all_values.extend(values)
            all_replicates.append(summary)
            engine.csv(artifacts / "replicate_values.csv", all_values)
            engine.csv(artifacts / "replicate_audits.csv", all_replicates)
            engine.js(artifacts / "progress.json", {"completed_replicates": len(all_replicates), "planned": args.replicates, "at": engine.now()})
            print(engine.now(), args.model, "bootstrap replicate", replicate + 1, "COMPLETE", flush=True)
            del sample, draws, multiplicity, scores, logs, records, tuning
        frame = pd.DataFrame(all_values)
        stability = []
        for (level, state), group in frame.groupby(["level", "state"], observed=True):
            for metric in ["Q0", "Q1", "delta", "learned_gain", "conservative_gain", "learned_action1_share", "n_supported", "coverage"]:
                values = group[metric].dropna()
                stability.append({"level": level, "state": state, "metric": metric, "replicates": len(values),
                                  "mean": values.mean(), "SD": values.std(ddof=1), "minimum": values.min(), "maximum": values.max(),
                                  "positive_fraction": values.gt(0).mean(),
                                  "interpretation": "Finite bootstrap diagnostic range/SD/sign frequency; not a confidence interval"})
        engine.csv(artifacts / "stability_summary.csv", stability)
        manifest.update(completed_replicates=len(all_replicates), all_fits_converged=True,
                        all_original_game_crossfold_zero=True, all_original_PA_crossfold_zero=True,
                        no_full_learning_confidence_interval=True,
                        limitation="Eight default replicates characterize gross refit sensitivity only; many more replicates and valid tie-sensitive policy inference are needed for full-learning intervals. Season-stratified games do not resolve cross-game player/series dependence.")
        engine.complete(dest, artifacts, manifest)
    except Exception:
        manifest.update(error=traceback.format_exc(), completed_replicates=len(all_replicates))
        engine.complete(dest, artifacts, manifest, "FAILED")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["pitch", "swing"], required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--development-run", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--replicates", type=int, default=8)
    parser.add_argument("--bootstrap-seed", type=int, default=20261909)
    run_bootstrap(parser.parse_args())
