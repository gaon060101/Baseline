"""Descriptive post-seal BCAP comparison of unchanged saved estimates.

This exact comparison recipe was written after external estimates were available.
It is not an additional preregistered test, policy learning, an oracle comparison,
or evidence sufficient to upgrade a grade. No p-values or new fitted models.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "columns/001-ball-count/analysis/runs"
COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]
CASES = [
    ("pitch", "2023", "bcap_pitch__mlb_2024_2025__20260909__r02", "bcap_pitch__mlb_2023__20260909__r01"),
    ("pitch", "2026", "bcap_pitch__mlb_2024_2025__20260909__r02", "bcap_pitch__mlb_2026_ytd_20260907__20260909__r01"),
    ("swing", "2023", "bcap_swing__mlb_2024_2025__20260909__r01", "bcap_swing__mlb_2023__20260909__r01"),
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def correlation(x, y, rank=False):
    x, y = pd.Series(x, dtype=float), pd.Series(y, dtype=float)
    if len(x) < 3 or x.nunique() < 2 or y.nunique() < 2:
        return None
    if rank:
        x, y = x.rank(method="average"), y.rank(method="average")
    return float(np.corrcoef(x.to_numpy(), y.to_numpy())[0, 1])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    out = Path(args.output).resolve()
    assert not out.exists(), "Preserve prior descriptive comparisons"
    rows, summaries, inputs = [], [], []
    fields = ["n_all", "n", "coverage", "games", "PA", "ESS0", "ESS1", "Q0", "Q1", "delta", "grade"]
    for model, year, dev_id, ext_id in CASES:
        dev, ext = RUNS / dev_id, RUNS / ext_id
        assert read(dev / "manifest.json")["status"] == "COMPLETE"
        assert read(ext / "manifest.json")["status"] == "COMPLETE"
        policy = read(dev / "artifacts/final_policy.json")
        d = pd.read_csv(dev / "artifacts/action_values.csv")
        e = pd.read_csv(ext / "artifacts/action_values.csv")
        for p in [dev / "manifest.json", ext / "manifest.json", dev / "artifacts/final_policy.json",
                  dev / "artifacts/action_values.csv", ext / "artifacts/action_values.csv"]:
            inputs.append({"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)})
        for level in (["count"] if model == "pitch" else ["count", "cell"]):
            expected = COUNTS if level == "count" else [f"{count}|{zone}|{group}" for count in COUNTS
                                                      for zone in ["INNER", "BOUNDARY", "OUT"] for group in ["FB", "NFB"]]
            dd = d[d.level.eq(level)].set_index("state")
            ee = e[e.level.eq(level)].set_index("state")
            assert set(expected) <= set(dd.index) and set(expected) <= set(ee.index)
            local = []
            for state in expected:
                a, b = dd.loc[state], ee.loc[state]
                rec = {"model": model, "external_year": year, "level": level, "state": state,
                       "development_run": dev_id, "external_run": ext_id,
                       "comparison_scope": "POST_SEAL_DESCRIPTIVE; different season/reference populations"}
                rec.update({"development_" + k: a[k] for k in fields})
                rec.update({"external_" + k: b[k] for k in fields})
                have = bool(a.n > 0 and b.n > 0 and np.isfinite(a.delta) and np.isfinite(b.delta))
                gate = bool(have and a.grade != "NO_SUPPORT" and b.grade != "NO_SUPPORT")
                rec.update(both_have_supported_rows=have, both_meet_empirical_support_gate=gate)
                nonzero = bool(have and a.delta != 0 and b.delta != 0)
                rec["direction_comparable_nonzero"] = nonzero
                rec["delta_direction_agreement"] = bool(np.sign(a.delta) == np.sign(b.delta)) if nonzero else None
                rec["delta_external_minus_development"] = float(b.delta - a.delta) if have else None
                comparable_policy = model == "pitch" or level == "cell"
                if comparable_policy:
                    action_p1 = float(policy["states"].get(state, {"p1": policy["fallback_p1"]})["p1"])
                    rec["frozen_policy_action1_probability"] = action_p1
                    ext_direction = int(b.delta < 0) if model == "pitch" else int(b.delta > 0)
                    rec["frozen_policy_matches_external_estimated_direction"] = bool(action_p1 == ext_direction) if have and b.delta != 0 and action_p1 in [0, 1] else None
                    rec["policy_comparison_status"] = "ESTIMATED_DIRECTION_NOT_OPTIMAL_TRUTH"
                else:
                    rec["frozen_policy_action1_probability"] = None
                    rec["frozen_policy_matches_external_estimated_direction"] = None
                    rec["policy_comparison_status"] = "NOT_APPLICABLE_SWING_POLICY_VARIES_WITHIN_COUNT"
                local.append(rec)
                rows.append(rec)
            table = pd.DataFrame(local)
            for filter_name in ["both_have_supported_rows", "both_meet_empirical_support_gate"]:
                paired = table[table[filter_name]]
                comparable = paired[paired.direction_comparable_nonzero]
                pol = paired.frozen_policy_matches_external_estimated_direction.dropna()
                summaries.append({"model": model, "external_year": year, "level": level,
                                  "filter": filter_name, "expected_states": len(expected), "paired_states": len(paired),
                                  "direction_comparable_states": len(comparable),
                                  "direction_agree_states": int(comparable.delta_direction_agreement.sum()),
                                  "direction_agree_fraction": float(comparable.delta_direction_agreement.mean()) if len(comparable) else None,
                                  "Pearson_delta_unweighted_states": correlation(paired.development_delta, paired.external_delta),
                                  "Spearman_delta_average_tie_ranks_unweighted_states": correlation(paired.development_delta, paired.external_delta, True),
                                  "frozen_policy_direction_comparable_states": len(pol),
                                  "frozen_policy_matches_external_estimated_direction_states": int(pol.sum()),
                                  "frozen_policy_estimated_direction_match_fraction": float(pol.mean()) if len(pol) else None,
                                  "p_values": "NOT_COMPUTED", "grade_upgrade": False,
                                  "scope": "Post-seal descriptive aggregate of existing estimates; no common cross-season reference population"})
    withheld = RUNS / "bcap_swing__mlb_2026_ytd_20260907__20260909__r01/manifest.json"
    assert read(withheld)["status"] == "WITHHELD"
    inputs.append({"path": withheld.relative_to(ROOT).as_posix(), "sha256": sha(withheld)})
    out.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(out / "paired_count_and_cell_estimates.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(summaries).to_csv(out / "direction_and_correlation_summary.csv", index=False, encoding="utf-8-sig")
    result = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "status": "COMPLETE_DESCRIPTIVE_ONLY",
              "post_seal_recipe": True, "external_estimates_previously_read": True,
              "request_scope": "The original request included external direction and association metrics; this exact aggregation recipe was fixed only after external results existed.",
              "estimand_limit": "Each estimate standardizes its own season's supported observed decision rows. Correlations compare state-level estimates, not a common-population treatment effect or optimal-policy truth.",
              "filter_limit": "Support-gate subset uses already-saved empirical grades; does not remove identification or full-learning uncertainty gates. All full12 counts and72 relevant SWING cells are still listed.",
              "correlations": "Unweighted across states; Spearman uses average tie ranks; fewer than3 or constant series yields unavailable. No pvalues, uncertainty intervals or hypothesis tests.",
              "policy_limit": "Frozen development policy is compared only to estimated external AIPW direction on matching policy states. SWING aggregate counts have no single policy action and are explicitly N/A. No external policy was learned.",
              "SWING_2026": "WITHHELD_MEASUREMENT_NONCOMPARABILITY; no comparison generated",
              "inputs": inputs, "summaries": summaries, "listed_rows": len(rows),
              "code": {"path": str(Path(__file__).resolve()), "sha256": sha(__file__)},
              "command": [sys.executable] + sys.argv,
              "outputs": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in sorted(out.glob("*.csv"))]}
    with (out / "comparison_manifest.json").open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"status": result["status"], "listed_rows": len(rows), "summaries": summaries}, ensure_ascii=False))


if __name__ == "__main__":
    main()
