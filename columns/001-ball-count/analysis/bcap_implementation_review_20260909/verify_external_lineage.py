"""Post-seal deterministic BCAP audit; does not change any estimator or policy.

This audit was added after sealing solely to check equality to frozen source
policies and development rosters. It calculates no new effect, tunes no threshold,
and never mutates the sealed files or completed runs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]


def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--development-run", required=True)
    ap.add_argument("--seal", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    run, dev, seal_path, out = [Path(p).resolve() for p in [args.run, args.development_run, args.seal, args.output]]
    assert not out.exists(), "Preserve previous audits"
    manifest, development, seal = read(run / "manifest.json"), read(dev / "manifest.json"), read(seal_path)
    assert manifest["status"] == "COMPLETE" and development["status"] == "COMPLETE"
    assert manifest["model_id"] == development["model_id"]
    for record in seal["files"]:
        assert sha(ROOT / record["path"]) == record["sha256"], "Sealed file changed: " + record["path"]
    variant = development["configuration"]["variant"]
    inputs = [r for r in development["inputs"] if "/data/processed/" in r["path"] and r["path"].endswith(".pkl")]
    assert len(inputs) == 1
    prepared = ROOT / inputs[0]["path"]
    assert sha(prepared) == inputs[0]["sha256"]
    original = pd.read_pickle(prepared)
    eligible = original["eligible_" + variant]
    pitchers = set(original.loc[eligible, "pitcher"].astype(str))
    batters = set(original.loc[eligible, "batter"].astype(str))
    original_rows = int(eligible.sum())
    del original
    policy_file = dev / "artifacts/final_policy.json"
    policy = read(policy_file)
    policy_sha = sha(policy_file)
    assert manifest["policy_source"]["sha256"] == policy_sha
    checks = []
    for name in ["scores.pkl", "fixed_development_predictions.pkl"]:
        file = run / "artifacts" / name
        d = pd.read_pickle(file)
        expected_policy = d[policy["key"]].astype(str).map({k: v["p1"] for k, v in policy["states"].items()}).fillna(policy["fallback_p1"])
        expected_pitcher = d.pitcher.astype(str).isin(pitchers)
        expected_batter = d.batter.astype(str).isin(batters)
        assert d.policy_p1.eq(expected_policy).all(), "External policy changed"
        assert not d.conservative_change.any(), "Conservative policy changed"
        assert d.known_pitcher.eq(expected_pitcher).all(), "Pitcher flags differ from development roster"
        assert d.known_batter.eq(expected_batter).all(), "Batter flags differ from development roster"
        checks.append({"file": name, "rows": len(d), "sha256": sha(file),
                       "all_policy_probabilities_match": True, "conservative_retains_all_rows": True,
                       "known_pitcher_flags_match": True, "known_batter_flags_match": True,
                       "pitcher_unseen_rows": int((~expected_pitcher).sum()),
                       "batter_unseen_rows": int((~expected_batter).sum())})
        del d
    result = {"status": "PASS", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "run_id": manifest["run_id"], "development_run_id": development["run_id"],
              "seal_sha256": sha(seal_path), "sealed_files_checked": len(seal["files"]),
              "fixed_policy_sha256": policy_sha, "prepared_input": inputs[0],
              "development_eligible_rows": original_rows, "development_pitchers": len(pitchers),
              "development_batters": len(batters), "checks": checks,
              "code": {"path": str(Path(__file__).resolve()), "sha256": sha(__file__)},
              "command": [sys.executable] + sys.argv,
              "scope": "Post-seal equality/hash/roster audit only; no estimator, policy, threshold or model change"}
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({k: result[k] for k in ["status", "run_id", "sealed_files_checked", "checks"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
