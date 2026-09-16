"""Add BCAP descriptive diagnostics to a fresh folder; never refit or alter runs.

Known/unseen intervals are individual fixed-score game-cluster normal
approximations, outside the main prespecified Bonferroni family. No interval here
qualifies a policy for recommendation. No network or external-data acquisition.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import NormalDist
import sys

import numpy as np
import pandas as pd

from verify_bcap import sha, policy_score, cluster_se, checked_bool

ROOT = Path(__file__).resolve().parents[2]
Z95 = NormalDist().inv_cdf(.975)


def json_read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def csv(p, rows):
    pd.DataFrame(rows).to_csv(p, index=False, encoding="utf-8-sig")


def interval(values, games, prefix):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return {prefix: None, prefix + "_SE": None, prefix + "_low95": None, prefix + "_high95": None}
    mean = float(values.mean())
    se = cluster_se(values, np.asarray(games))
    return {prefix: mean, prefix + "_SE": se,
            prefix + "_low95": mean - Z95 * se if se is not None else None,
            prefix + "_high95": mean + Z95 * se if se is not None else None}


def grouped(d):
    yield "overall", "ALL", d
    for count, g in d.groupby("count", observed=True):
        yield "count", str(count), g
    if "swing_cell" in d:
        for cell, g in d.groupby("swing_cell", observed=True):
            yield "cell", str(cell), g
    kp, kb = checked_bool(d.known_pitcher, "known_pitcher"), checked_bool(d.known_batter, "known_batter")
    for entity, known in [("pitcher", kp), ("batter", kb)]:
        yield "known_marginal", entity + "_known", d[known]
        yield "known_marginal", entity + "_unseen", d[~known]
    for p in [True, False]:
        for b in [True, False]:
            label = "pitcher_" + ("known" if p else "unseen") + "_batter_" + ("known" if b else "unseen")
            yield "known_joint", label, d[(kp == p) & (kb == b)]
    yield "known_combined", "both_known", d[kp & kb]
    yield "known_combined", "at_least_one_unseen", d[~(kp & kb)]


def prediction_metrics(d, baseline, stage, kind, state):
    n = len(d)
    item = {"stage": stage, "level": kind, "state": state, "rows": n,
            "PA": len(d[["game_pk", "at_bat_number"]].drop_duplicates()), "games": d.game_pk.nunique()}
    if not n:
        return item
    a, y, p = [d[x].to_numpy(dtype=float) for x in ["A", "Y", "p"]]
    prediction = d.mu0.to_numpy() + a * (d.mu1.to_numpy() - d.mu0.to_numpy())
    retrospective = float(y.mean())
    item.update(MSE=float(np.mean((y - prediction) ** 2)), Brier=float(np.mean((a - p) ** 2)),
                log_loss=float(-np.mean(a * np.log(p) + (1 - a) * np.log1p(-p))),
                frozen_development_constant=baseline,
                frozen_development_constant_MSE=float(np.mean((y - baseline) ** 2)),
                retrospective_group_constant=retrospective,
                retrospective_group_constant_MSE=float(np.mean((y - retrospective) ** 2)),
                actual_action1_rate=float(a.mean()), mean_p=float(p.mean()),
                support_rate=float(d.support.mean()))
    return item


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True, help="Existing completed run directory")
    ap.add_argument("--development-run", required=True, help="Matching model development run directory")
    ap.add_argument("--output", required=True, help="New directory outside completed runs")
    args = ap.parse_args()
    run, dev, out = [Path(x).resolve() for x in [args.run, args.development_run, args.output]]
    assert not out.exists(), "Preserve prior supplements; use a fresh directory"
    assert not out.is_relative_to(run) and not out.is_relative_to(dev), "Do not modify completed run contents"
    manifest, dev_manifest = json_read(run / "manifest.json"), json_read(dev / "manifest.json")
    assert manifest["status"] == "COMPLETE" and dev_manifest["status"] == "COMPLETE"
    assert manifest["model_id"] == dev_manifest["model_id"]
    model = manifest["configuration"]["variant"]
    baseline = float(dev_manifest["metrics"]["Y_mean"])
    sign = -1 if model == "pitch" else 1
    stages = [("evaluation_nuisance", run / "artifacts/scores.pkl")]
    fixed = run / "artifacts/fixed_development_predictions.pkl"
    if fixed.exists():
        stages.append(("fixed_development_prediction", fixed))
    all_values, all_metrics, all_calibration, global_calibration, sources = [], [], [], [], []
    for stage, path in stages:
        d = pd.read_pickle(path)
        sources.append({"stage": stage, "path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)})
        bin_id = np.minimum((d.p.to_numpy() * 10).astype(int), 9)
        ece, maxgap = 0., 0.
        for b in range(10):
            part = d[bin_id == b]
            if not len(part):
                continue
            mean_p, rate = float(part.p.mean()), float(part.A.mean())
            gap = abs(mean_p - rate)
            ece += len(part) / len(d) * gap
            maxgap = max(maxgap, gap)
            all_calibration.append({"stage": stage, "bin": b, "lower": b / 10, "upper": (b + 1) / 10,
                                    "lower_inclusive": True, "upper_inclusive": b == 9,
                                    "rows": len(part), "games": part.game_pk.nunique(),
                                    "mean_p": mean_p, "action1_rate": rate, "absolute_gap": gap})
        global_calibration.append({"stage": stage, "rows": len(d), "ECE_10_fixed_bins": ece,
                                   "maximum_bin_gap": maxgap,
                                   "definition": "Row-weighted absolute observed-minus-predicted rate in fixed [0,.1,...,1] bins"})
        for kind, state, allrows in grouped(d):
            if kind in {"overall", "known_marginal", "known_joint", "known_combined"}:
                all_metrics.append(prediction_metrics(allrows, baseline, stage, kind, state))
            sup = allrows[allrows.support]
            n = len(sup)
            row = {"stage": stage, "level": kind, "state": state, "rows_all": len(allrows), "rows": n,
                   "support_rate": n / len(allrows) if len(allrows) else None,
                   "PA": len(sup[["game_pk", "at_bat_number"]].drop_duplicates()),
                   "games": sup.game_pk.nunique(), "pitchers": sup.pitcher.nunique(), "batters": sup.batter.nunique(),
                   "unit": "Raw W per selected current decision, not accumulated PA improvement",
                   "interval_scope": "Individual95 fixed-score game-cluster normal; outside main multiplicity family"}
            if not n:
                row["status"] = "NO_COMMON_SUPPORT"
                all_values.append(row)
                continue
            a, y, p, m0, m1, p1 = [sup[x].to_numpy(dtype=float) for x in ["A", "Y", "p", "mu0", "mu1", "policy_p1"]]
            games = sup.game_pk.to_numpy()
            q0 = policy_score(y, a, p, m0, m1, np.zeros(n))
            q1 = policy_score(y, a, p, m0, m1, np.ones(n))
            candidate = policy_score(y, a, p, m0, m1, p1)
            cp1 = sup.conservative_p1.to_numpy(dtype=float)
            conservative = policy_score(y, a, p, m0, m1, cp1)
            change = checked_bool(sup.conservative_change, "conservative_change")
            conservative[~change] = y[~change]
            for action in [0, 1]:
                w = np.where(a == action, 1 / (p if action else 1 - p), 0.)
                sw, sw2 = w.sum(), w @ w
                game_weights = pd.Series(w).groupby(games).sum()
                row.update({f"N{action}": int((a == action).sum()), f"ESS{action}": float(sw * sw / sw2) if sw2 else 0.,
                            f"arm_games{action}": int(sup.loc[sup.A.eq(action), "game_pk"].nunique()),
                            f"max_game_weight_share{action}": float(game_weights.max() / sw) if sw else None,
                            f"IPW_unnormalized_Q{action}": float(np.mean(w * y)),
                            f"Hajek_ratio_Q{action}": float(w @ y / sw) if sw else None,
                            f"gcomp_Q{action}": float((m1 if action else m0).mean())})
            for name, vals in [("Q0", q0), ("Q1", q1), ("delta", q1 - q0),
                               ("V_observed", y), ("V_candidate", candidate), ("V_conservative", conservative),
                               ("candidate_gain", sign * (candidate - y)),
                               ("conservative_gain", sign * (conservative - y))]:
                row.update(interval(vals, games, name))
            row.update(status="DESCRIPTIVE_ONLY", actual_action1_rate=float(a.mean()),
                       candidate_expected_action1_share=float(p1.mean()),
                       candidate_share_minus_actual=float(p1.mean() - a.mean()),
                       candidate_expected_disagreement=float(np.mean(p1 * (1 - a) + (1 - p1) * a)),
                       candidate_stochastic_row_fraction=float(np.mean((p1 > 0) & (p1 < 1))),
                       conservative_change_region_share=float(change.mean()),
                       conservative_expected_action1_share=float(np.where(change, cp1, a).mean()),
                       conservative_expected_disagreement=float(np.mean(np.where(change, cp1 * (1 - a) + (1 - cp1) * a, 0.))))
            all_values.append(row)
    out.mkdir(parents=True)
    csv(out / "same_target_estimators_policy_shares_and_subgroups.csv", all_values)
    csv(out / "prediction_baselines_and_known_unseen.csv", all_metrics)
    csv(out / "calibration_bins.csv", all_calibration)
    csv(out / "calibration_summary.csv", global_calibration)
    provenance = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "model_id": manifest["model_id"],
                  "run_id": manifest["run_id"], "development_run": dev_manifest["run_id"],
                  "sources": sources, "code": [{"path": str(Path(__file__).resolve()), "sha256": sha(__file__)},
                                                 {"path": "models/bcap/verify_bcap.py", "sha256": sha(Path(__file__).with_name("verify_bcap.py"))}],
                  "frozen_constant_source": "Development manifest metrics.Y_mean (full eligible development-row mean). Valid fixed external baseline; development comparison itself is a pooled descriptive reference, not an independent OOF baseline.",
                  "retrospective_constant": "Evaluation subgroup mean observed Y. Outcome-informed hindsight baseline, never used for external predictions.",
                  "known_definition": "Copied from saved scores: development nuisance-training roster for development; frozen complete-development roster for external.",
                  "IPW": "Unnormalized arithmetic mean indicator(A=a)*Y/p(a); Hajek is separately named weighted sum divided by weight sum. All share primary support mask.",
                  "intervals": "Individual normal95 fixed-score game-cluster intervals, no refit uncertainty or multiplicity certification. No recommendation gates upgraded.",
                  "fixed_development_stage": "Any fixed-nuisance AIPW values are descriptive transport diagnostics, not the external-refit OPE or additional independent validation.",
                  "command": sys.argv,
                  "outputs": [{"path": x.relative_to(ROOT).as_posix(), "sha256": sha(x)} for x in sorted(out.glob("*.csv"))]}
    with (out / "supplement_manifest.json").open("x", encoding="utf-8") as f:
        json.dump(provenance, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"status": "COMPLETE", "run_id": manifest["run_id"], "output": str(out),
                      "value_rows": len(all_values), "predictive_rows": len(all_metrics)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
