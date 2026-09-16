"""Audit raw score timing against explicitly pre-pitch bat_score/fld_score.

Reads existing local CSVs only. No model fitting, outcome analysis or SWING2026
evaluation. The source lists are the completed BCAP preparation audit records.
"""
from pathlib import Path
import argparse
import datetime as dt
import hashlib
import json

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ANAL = ROOT / "columns/001-ball-count/analysis"
KEYS = ["game_pk", "at_bat_number", "pitch_number"]
FIELDS = ["bat_score_diff", "bat_score", "fld_score", "post_bat_score"]
PREPARATIONS = [
    ANAL / "bcap_preparation_20260909_r01/preparation_audit.json",
    ANAL / "runs/bcap_pitch__mlb_2023__20260909__r01/artifacts/preparation/preparation_audit.json",
    ANAL / "runs/bcap_pitch__mlb_2026_ytd_20260907__20260909__r01/artifacts/preparation/preparation_audit.json",
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(HERE / "score_timing_validation.json"))
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise FileExistsError("Audit output exists; choose a fresh --output")
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    file_results, mismatches, scoring_examples = [], [], []
    for prep_path in PREPARATIONS:
        prep = read(prep_path)
        assert prep.get("completed_at")
        files = [item for item in prep["inputs"] if item["path"].endswith(".csv")]
        for index, item in enumerate(files):
            path = ROOT / item["path"]
            year = next(y for y in [2023, 2024, 2025, 2026] if f"/mlb/{y}/" in item["path"])
            frame = pd.read_csv(path, usecols=KEYS + FIELDS, low_memory=False)
            expected = frame.bat_score - frame.fld_score
            post_proxy = frame.post_bat_score - frame.fld_score
            complete_pre = frame[["bat_score_diff", "bat_score", "fld_score"]].notna().all(axis=1)
            pre_match = np.isclose(frame.bat_score_diff, expected, rtol=0, atol=0, equal_nan=False)
            complete_post = frame[FIELDS].notna().all(axis=1)
            scoring = complete_post & frame.post_bat_score.ne(frame.bat_score)
            post_match = np.isclose(frame.bat_score_diff, post_proxy, rtol=0, atol=0, equal_nan=False)
            bad = ~pre_match
            entry = {"year": year, "path": item["path"], "preparation_input_sha256": item["sha256"],
                     "raw_hash_recomputed": False, "bytes_unchanged": path.stat().st_size == item["bytes"],
                     "rows": len(frame), "preparation_rows_match": len(frame) == item["rows"],
                     "missing_pre_score_rows": int((~complete_pre).sum()),
                     "missing_post_score_rows": int(frame.post_bat_score.isna().sum()),
                     "pre_score_difference_mismatch_rows": int(bad.sum()),
                     "scoring_rows_pre_post_different": int(scoring.sum()),
                     "scoring_rows_match_pre_difference": int((scoring & pre_match).sum()),
                     "scoring_rows_match_post_difference": int((scoring & post_match).sum()),
                     "max_abs_difference_from_pre": float((frame.bat_score_diff - expected).abs().max()),
                     "score_changes_observed": sorted(map(float, (frame.loc[scoring, "post_bat_score"] - frame.loc[scoring, "bat_score"]).unique()))}
            file_results.append(entry)
            for row in frame.loc[bad, KEYS + FIELDS].head(max(0, 30 - len(mismatches))).to_dict("records"):
                mismatches.append({"year": year, "path": item["path"], **row})
            if sum(x["year"] == year for x in scoring_examples) < 3:
                for row in frame.loc[scoring, KEYS + FIELDS].head(3 - sum(x["year"] == year for x in scoring_examples)).to_dict("records"):
                    scoring_examples.append({"year": year, **row})
            if (index + 1) % 15 == 0:
                print("score timing files", prep["years"], index + 1, "/", len(files), flush=True)
    sums = ["rows", "missing_pre_score_rows", "missing_post_score_rows", "pre_score_difference_mismatch_rows",
            "scoring_rows_pre_post_different", "scoring_rows_match_pre_difference", "scoring_rows_match_post_difference"]
    seasons = []
    for year in [2023, 2024, 2025, 2026]:
        records = [item for item in file_results if item["year"] == year]
        seasons.append({"year": year, "files": len(records), **{field: sum(item[field] for item in records) for field in sums},
                        "all_file_row_counts_and_bytes_match_preparation": all(item["bytes_unchanged"] and item["preparation_rows_match"] for item in records)})
    totals = {field: sum(item[field] for item in file_results) for field in sums}
    passed = totals["pre_score_difference_mismatch_rows"] == 0 and totals["missing_pre_score_rows"] == 0 and totals["scoring_rows_pre_post_different"] > 0 and totals["scoring_rows_match_post_difference"] == 0 and all(s["all_file_row_counts_and_bytes_match_preparation"] for s in seasons)
    result = {"status": "PASS" if passed else "ISSUE", "started_at_utc": started,
              "completed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "code": {"path": Path(__file__).relative_to(ROOT).as_posix(), "sha256": sha(__file__)},
              "official_field_definition_source": "https://baseballsavant.mlb.com/csv-docs",
              "source_interpretation": "Official documentation labels bat_score and fld_score as pre-pitch scores. Their raw difference is checked independently against bat_score_diff. post_bat_score is used only to distinguish scoring rows.",
              "formula_checked": "bat_score_diff == bat_score - fld_score on every existing raw CSV row",
              "post_formula_diagnostic_only": "post_bat_score - fld_score; scoring rows must differ from pre-pitch score difference",
              "totals": totals, "seasons": seasons, "file_checks": file_results,
              "mismatch_examples": mismatches, "scoring_examples": scoring_examples,
              "source_list_audits": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in PREPARATIONS],
              "2026_SWING_evaluations": 0, "estimator_or_sealed_code_changes": False,
              "limitation": "Original raw CSV hashes are cited from preparation, not recomputed during this selected-column scan; row counts and file sizes are checked. This timing audit does not identify causal effects."}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=lambda x: x.item() if hasattr(x, "item") else str(x)), encoding="utf-8")
    print(result["status"], totals, flush=True)
    if not passed:
        raise AssertionError("Raw score timing issue: inspect new validation record")


if __name__ == "__main__":
    main()
