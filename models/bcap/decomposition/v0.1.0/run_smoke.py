"""Small explicitly synthetic checks; no MLB fitting or raw-file scan."""
import argparse
import copy
import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import compose


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture():
    data = {
        "schema_version": "1", "synthetic": True,
        "fit_provenance": "모의 입력: 실제 선수·MLB 예측·학습 결과가 아님",
        "outcome_definition": {"kind": "final_PA_W", "unit": compose.UNIT,
                               "weight_manifest_sha256": "0" * 64},
        "fold_training_games": {"0": ["synthetic-game-2"], "1": ["synthetic-game-1"]},
        "reference_rows": [], "predictions": []}
    for i in range(2):
        rid = f"synthetic-row-{i+1}"
        data["reference_rows"].append({"row_id": rid, "game_pk": f"synthetic-game-{i+1}",
            "at_bat_number": "1", "pitch_number": "1", "outer_fold": str(i),
            "season": 2024, "count": "0-2", "regions": ["HIGH", "OUTSIDE"],
            "observed_description": ["ball", "hit_into_play"][i]})
        for action in compose.BRANCHES:
            branches = {b: {"p": 0.0, "mean_W": None, "supported": False}
                        for b in compose.BRANCHES[action]}
            if action == "Take":
                branches["TAKE_BALL"] = {"p": [.9, .1][i], "mean_W": [.8, .2][i], "supported": True}
                branches["TAKE_CALLED_STRIKE"] = {"p": [.1, .9][i], "mean_W": 0.0, "supported": True}
                direct = [.7, .1][i]
            else:
                branches["IN_PLAY"] = {"p": 1.0, "mean_W": [.3, .5][i], "supported": True}
                direct = [.35, .55][i]
            data["predictions"].append({"row_id": rid, "action": action,
                "prediction_fold": str(i), "branches": branches, "direct_mean_W": direct})
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True, help="새 실행 폴더; 완료 파일 덮어쓰기 금지")
    args = parser.parse_args()
    output = args.out.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("Use a new empty run directory")
    artifacts = output / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=False)
    model_dir = Path(__file__).resolve().parent
    root = model_dir.parents[3]
    previous_spec = root / "models/bcap/swing/v0.2.0/specification.yaml"
    actual = json.loads(previous_spec.read_text(encoding="utf-8-sig"))["actions"]
    checks = []

    def record(name, passed, detail=None):
        if not passed:
            raise AssertionError(name)
        checks.append({"name": name, "status": "PASS", "detail": detail})

    expected_descriptions = set(actual["Take"] + actual["Swing"])
    record("closed_mapping_matches_existing_12_descriptions", set(compose.DESCRIPTION) == expected_descriptions)
    record("mapped_action_matches_existing_definition", all(compose.classify_description(d)[0] == a
        for a in ("Take", "Swing") for d in actual[a]))
    record("unknown_description_not_take", compose.classify_description("automatic_ball") is None)
    data = fixture()
    result = compose.calculate(data)
    overall = next(r for r in result["summaries"] if r["level"] == "overall")
    record("rowwise_probability_times_W", math.isclose(overall["Take"]["mean_W"], .37))
    record("not_product_of_group_means", not math.isclose(overall["Take"]["mean_W"], .25),
           "모의자료 E[p*m]=0.37, E[p]*E[m]=0.25; MLB 값 아님")
    record("paired_action_delta", math.isclose(overall["delta_Swing_minus_Take_W"], .03, abs_tol=1e-12))
    record("same_row_direct_gcomp_comparator", math.isclose(overall["decomposed_minus_direct_delta_W"], -.02, abs_tol=1e-12))
    record("overlap_regions_not_duplicate_overall", overall["n"] == 2 and
           sum(r["n"] for r in result["summaries"] if r["level"] == "count_region") == 4)

    def reject(name, edit):
        bad = copy.deepcopy(data)
        edit(bad)
        try:
            compose.calculate(bad)
        except ValueError as exc:
            record(name, True, str(exc))
        else:
            record(name, False)

    reject("probability_sum_rejected", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(p=.8))
    reject("missing_positive_mass_value_rejected", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(mean_W=None))
    reject("unsupported_positive_mass_rejected", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(supported=False))
    reject("reference_action_mismatch_rejected", lambda d: d["predictions"].pop())
    reject("unknown_description_rejected", lambda d: d["reference_rows"][0].update(observed_description="pitchout"))
    reject("training_game_overlap_rejected", lambda d: d["fold_training_games"]["0"].append("synthetic-game-1"))
    reject("prediction_fold_mismatch_rejected", lambda d: d["predictions"][0].update(prediction_fold="1"))
    reject("missing_branch_rejected", lambda d: d["predictions"][0]["branches"].pop("TAKE_HBP"))
    reject("partial_direct_comparator_rejected", lambda d: d["predictions"][0].pop("direct_mean_W"))
    reject("nonfinite_probability_rejected", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(p=float("nan")))
    reject("inconsistent_regions_rejected", lambda d: d["reference_rows"][0].update(regions=["CENTER", "HIGH"]))
    input_path = artifacts / "synthetic_input.json"
    input_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result_path = artifacts / "synthetic_output.json"
    command = [sys.executable, "-B", str(model_dir / "compose.py"), "--input", str(input_path), "--output", str(result_path)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    persisted = json.loads(result_path.read_text(encoding="utf-8"))
    record("CLI_result_matches_function", persisted["summaries"] == result["summaries"])
    rerun = subprocess.run(command, check=False, capture_output=True, text=True)
    record("CLI_preserves_existing_output", rerun.returncode != 0 and json.loads(result_path.read_text(encoding="utf-8")) == persisted)
    checks_path = artifacts / "checks.json"
    checks_path.write_text(json.dumps({"synthetic": True, "n_checks": len(checks), "checks": checks,
        "not_performed": ["MLB fitting", "actual calibration", "statistical validation", "AIPW", "uncertainty"]},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paths = [model_dir / "compose.py", model_dir / "run_smoke.py", model_dir / "specification.yaml",
             model_dir / "input_contract.md", previous_spec, input_path, result_path, checks_path]
    manifest = {"run_id": output.name, "model_id": compose.MODEL_ID, "version": "0.1.0", "status": "DRAFT",
        "execution_kind": "synthetic_interface_smoke_only", "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "raw_MLB_read": False, "model_fitting": False,
        "command": command, "checks_passed": len(checks), "input_output_code_sha256": {
            p.relative_to(root).as_posix(): sha(p) for p in paths},
        "not_estimated": ["empirical_branch_probability_or_W", "new_MLB_action_value", "AIPW", "confidence_interval", "scenario", "policy"]}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"모의 인터페이스 확인 {len(checks)}개 PASS; 실제 MLB 모델 적합 없음")


if __name__ == "__main__":
    main()
