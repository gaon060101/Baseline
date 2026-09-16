"""Independent saved-score arithmetic for the prespecified 2023 S/B primary cells.

This script does not import the production engine, fit a model, resample data,
change support rules, or revise any prior result. Run only after the sealed
external evaluation is complete. The output is exclusively created once.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
BUNDLE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "columns/001-ball-count/analysis/runtime_ridge_v02"))
import numpy as np
import pandas as pd
from scipy.stats import t

RUN = ROOT / "columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2023__20260914__r01"
OUTPUT = BUNDLE / "primary_verification.json"
COUNTS = ("0-2", "1-2")
FAMILY = 4


def now():
    return datetime.now(timezone.utc).isoformat()


def metadata(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": digest.hexdigest(),
            "bytes": path.stat().st_size}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    if OUTPUT.exists():
        raise FileExistsError("Preserve the completed independent verification: " + str(OUTPUT))
    record = {"started_at_utc": now(), "scope": "Independent saved-score arithmetic, 2023 S/B 0-2 and 1-2 only",
              "run_id": RUN.name, "method": "AIPW reconstructed from A,Y,p,mu; pandas game-total cluster variance; scipy t quantiles",
              "interval_scope": "Conditional on the fitted nuisance scores; no nuisance refitting, resampling, or between-game player dependence adjustment",
              "family": FAMILY, "checks": [], "counts": {}, "code": metadata(__file__),
              "not_checked": ["raw-source labels", "nuisance fitting correctness", "measurement equivalence", "full pipeline audit"],
              "support_scope": "Row support reconstructed from stored propensity and stored training-arm/measurement flags; the flags themselves are not re-derived"}

    def check(name, valid, detail=None):
        record["checks"].append({"name": name, "status": "PASS" if bool(valid) else "FAIL", "detail": detail})

    def same(name, actual, expected, tolerance=1e-12):
        error = abs(float(actual) - float(expected))
        check(name, np.isfinite(error) and error <= tolerance,
              {"recalculated": float(actual), "stored": float(expected), "absolute_difference": float(error), "tolerance": tolerance})

    try:
        seal = read_json(BUNDLE / "plan_seal.json")
        manifest = read_json(RUN / "manifest.json")
        if manifest["status"] != "COMPLETE":
            raise RuntimeError("The target external run is not COMPLETE")
        record["plan_sealed_at_utc"] = seal["sealed_at_utc"]
        sealed = {item["path"]: item["sha256"] for item in seal["files"]}
        for path in (Path(__file__), BUNDLE / "plan.json"):
            item = metadata(path)
            check("sealed_" + path.name, sealed.get(item["path"]) == item["sha256"])
        if any(item["status"] == "FAIL" for item in record["checks"]):
            raise RuntimeError("Independent verifier or plan does not match the preregistered seal")
        paths = [RUN / "artifacts/scores.pkl", RUN / "artifacts/values.csv", RUN / "manifest.json", BUNDLE / "plan.json", BUNDLE / "plan_seal.json"]
        record["inputs"] = [metadata(path) for path in paths]
        record["first_result_read_at_utc"] = now()
        scores = pd.read_pickle(paths[0])
        values = pd.read_csv(paths[1])
        for count in COUNTS:
            whole = scores.loc[scores["count"].eq(count)].copy()
            matching = values.loc[values["count"].eq(count) & values["model"].eq("pitch_sb")
                                  & values["population"].eq("own") & values["region"].eq("ALL")]
            if len(matching) != 1 or whole.empty:
                raise ValueError("Expected one nonempty primary cell: " + count)
            saved = matching.iloc[0]
            check(count + "/year", whole.game_year.eq(2023).all() and saved.year == 2023)
            check(count + "/action_orientation", saved.action0 == "B" and saved.action1 == "S")
            check(count + "/primary_family", saved.family == FAMILY)
            check(count + "/keys", not whole.duplicated(["game_pk", "at_bat_number", "pitch_number"]).any())
            check(count + "/one_fold_per_game", whole.groupby("game_pk", observed=True).fold.nunique().eq(1).all())
            a = whole.A.to_numpy(dtype=int)
            y = whole.Y.to_numpy(dtype=float)
            probability = whole.p.to_numpy(dtype=float)
            mean0 = whole.mu0.to_numpy(dtype=float)
            mean1 = whole.mu1.to_numpy(dtype=float)
            check(count + "/finite_inputs", np.isfinite(np.column_stack([y, probability, mean0, mean1])).all())
            check(count + "/binary_action_probability", np.isin(a, [0, 1]).all() and ((probability > 0) & (probability < 1)).all())
            if not record["checks"][-1]["status"] == "PASS":
                raise ValueError("Invalid action/probability")
            # Compute residual corrections using action masks, independently of
            # the production engine's vectorized score function.
            value0 = mean0.copy()
            value1 = mean1.copy()
            observed0 = a == 0
            observed1 = a == 1
            value0[observed0] += (y[observed0] - mean0[observed0]) / (1 - probability[observed0])
            value1[observed1] += (y[observed1] - mean1[observed1]) / probability[observed1]
            for arm, rebuilt in ((0, value0), (1, value1)):
                max_error = float(np.max(np.abs(rebuilt - whole["phi" + str(arm)].to_numpy(float))))
                check(count + "/phi" + str(arm), max_error <= 1e-12, {"max_absolute_error": max_error})
            support = ((probability >= .05) & (probability <= .95)
                       & whole.repertoire.to_numpy(bool) & whole.measurement_support.to_numpy(bool))
            check(count + "/row_support", np.array_equal(support, whole.support.to_numpy(bool)))
            data = whole.loc[support]
            n = len(data)
            if n == 0:
                raise ValueError("No supported rows: " + count)
            difference = value1[support] - value0[support]
            estimate = float(np.mean(difference))
            # Group sums of centered row contrasts retain all within-game
            # repeated PA/pitch dependence. No production aggregation is called.
            grouped = pd.DataFrame({"game": data.game_pk.to_numpy(), "contrast": difference})
            by_game = grouped.groupby("game", sort=True).agg(total=("contrast", "sum"), rows=("contrast", "size"))
            games = len(by_game)
            if games <= 1:
                raise ValueError("At least two games required")
            centered_totals = by_game.total.to_numpy() - by_game.rows.to_numpy() * estimate
            variance = float(np.dot(centered_totals, centered_totals)) * games / (games - 1) / (n * n)
            se = float(np.sqrt(variance))
            nominal_critical = float(t.ppf(1 - .05 / 2, df=games - 1))
            adjusted_critical = float(t.ppf(1 - .05 / (2 * FAMILY), df=games - 1))
            rebuilt = {"n_all": len(whole), "n": n, "coverage": n / len(whole), "games": games,
                       "Q0": float(np.mean(value0[support])), "Q1": float(np.mean(value1[support])),
                       "delta": estimate, "SE": se,
                       "nominal95_low": estimate - nominal_critical * se,
                       "nominal95_high": estimate + nominal_critical * se,
                       "adjusted95_low": estimate - adjusted_critical * se,
                       "adjusted95_high": estimate + adjusted_critical * se}
            for arm in (0, 1):
                chosen = data.A.to_numpy() == arm
                denominator = data.p.to_numpy() if arm else 1 - data.p.to_numpy()
                weights = np.zeros(n, dtype=float)
                weights[chosen] = 1 / denominator[chosen]
                total_weight = float(np.sum(weights))
                squared_weight = float(np.dot(weights, weights))
                game_weights = pd.DataFrame({"game": data.game_pk.to_numpy(), "weight": weights}).groupby("game").weight.sum()
                rebuilt["rows" + str(arm)] = int(np.sum(chosen))
                rebuilt["ESS" + str(arm)] = total_weight * total_weight / squared_weight if squared_weight else 0.0
                rebuilt["games" + str(arm)] = int(data.loc[data.A.eq(arm), "game_pk"].nunique())
                rebuilt["max_game_share" + str(arm)] = float(game_weights.max() / total_weight) if total_weight else 1.0
                rebuilt["max_weight" + str(arm)] = float(weights.max())
            reasons = []
            if n < 500:
                reasons.append("n<500")
            if min(rebuilt["ESS0"], rebuilt["ESS1"]) < 200:
                reasons.append("armESS<200")
            if min(rebuilt["games0"], rebuilt["games1"]) < 100:
                reasons.append("armGames<100")
            if rebuilt["coverage"] < .5:
                reasons.append("coverage<.5")
            if max(rebuilt["max_game_share0"], rebuilt["max_game_share1"]) > .05:
                reasons.append("maxGameShare>.05")
            for field, value in rebuilt.items():
                same(count + "/" + field, value, saved[field], 1e-8 if field.startswith("ESS") else 1e-12)
            same(count + "/Q1_minus_Q0", rebuilt["Q1"] - rebuilt["Q0"], rebuilt["delta"])
            check(count + "/sample_sum", rebuilt["rows0"] + rebuilt["rows1"] == n)
            check(count + "/support_gate", bool(saved.support_gate) == (len(reasons) == 0))
            saved_reasons = "" if pd.isna(saved.support_reasons) else str(saved.support_reasons)
            check(count + "/support_reasons", saved_reasons == ";".join(reasons))
            rebuilt.update(support_gate=not reasons, support_reasons=reasons, t_df=games - 1,
                           nominal_critical=nominal_critical, adjusted_critical=adjusted_critical,
                           contrast="Q(S) minus Q(B); positive means B has lower allowed W")
            record["counts"][count] = rebuilt
    except Exception as error:
        record["error"] = type(error).__name__ + ": " + str(error)
    record["finished_at_utc"] = now()
    record["status"] = "PASS" if "error" not in record and record["checks"] and all(item["status"] == "PASS" for item in record["checks"]) else "FAIL"
    with OUTPUT.open("x", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({"status": record["status"], "output": str(OUTPUT), "checks": len(record["checks"]),
                      "failed_checks": [x["name"] for x in record["checks"] if x["status"] == "FAIL"], "error": record.get("error")}, ensure_ascii=False))
    if record["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
