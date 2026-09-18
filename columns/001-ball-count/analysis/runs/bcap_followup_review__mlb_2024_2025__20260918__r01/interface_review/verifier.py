import copy
import hashlib
import html
import importlib.util
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
COMPOSE = ROOT / "models/bcap/decomposition/v0.1.0/compose.py"
PYTHON = Path(r"C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe")
SNAPSHOT = "2026-09-18 interface review snapshot before root appends review links"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def branch(p=0.0, mean=None, supported=False):
    return {"p": p, "mean_W": mean, "supported": supported}


def fixture():
    take_names = ["TAKE_BALL", "TAKE_CALLED_STRIKE", "TAKE_HBP"]
    swing_names = ["BUNT_FOUL", "BUNT_FOUL_TIP", "BUNT_MISS", "IN_PLAY", "SWING_FOUL", "SWING_FOUL_TIP", "SWING_MISS"]
    def pred(row, fold, action, values, direct):
        names = take_names if action == "Take" else swing_names
        branches = {n: branch() for n in names}
        for n, p, mean in values:
            branches[n] = branch(p, mean, True)
        return {"row_id": row, "action": action, "prediction_fold": fold,
                "branches": branches, "direct_mean_W": direct}
    return {
        "schema_version": "1", "synthetic": True,
        "fit_provenance": "independent synthetic contract fixture; no model fitting",
        "outcome_definition": {"kind": "final_PA_W", "unit": "season_weighted_final_PA_W",
                               "weight_manifest_sha256": "0" * 64},
        "fold_training_games": {"fold-A": ["train-A"], "fold-B": ["train-B"]},
        "reference_rows": [
            {"row_id": "s1", "game_pk": "eval-A", "at_bat_number": "1", "pitch_number": "1", "outer_fold": "fold-A", "count": "0-2", "season": 2024, "regions": ["HIGH", "OUTSIDE"], "observed_description": "ball"},
            {"row_id": "s2", "game_pk": "eval-B", "at_bat_number": "2", "pitch_number": "1", "outer_fold": "fold-B", "count": "0-2", "season": 2025, "regions": ["HIGH", "OUTSIDE"], "observed_description": "swinging_strike"},
        ],
        "predictions": [
            pred("s1", "fold-A", "Take", [("TAKE_BALL", .8, .6), ("TAKE_CALLED_STRIKE", .2, .1)], .31),
            pred("s1", "fold-A", "Swing", [("SWING_MISS", .5, .1), ("IN_PLAY", .5, .5)], .33),
            pred("s2", "fold-B", "Take", [("TAKE_BALL", .2, .2), ("TAKE_CALLED_STRIKE", .8, .05)], .09),
            pred("s2", "fold-B", "Swing", [("SWING_MISS", .25, .2), ("IN_PLAY", .75, .6)], .47),
        ]}


def load_module():
    spec = importlib.util.spec_from_file_location("compose_review", COMPOSE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def approx(actual, expected, tol=1e-12):
    return math.isclose(actual, expected, rel_tol=0, abs_tol=tol)


def main():
    HERE.mkdir(parents=True, exist_ok=True)
    doc = fixture()
    fixture_path = HERE / "synthetic_input.json"
    fixture_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mod = load_module()
    result = mod.calculate(doc)
    (HERE / "synthetic_output.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    checks = []
    def add(name, ok, expected, actual, evidence="synthetic_execution"):
        checks.append({"name": name, "status": "PASS" if ok else "FAIL", "expected": expected, "actual": actual, "evidence_type": evidence})

    overall = next(x for x in result["summaries"] if x["level"] == "overall")
    expected_vals = {
        "n": 2, "take_mean": .29, "swing_mean": .40, "delta": .11,
        "direct_delta": .20, "decomp_minus_direct": -.09,
        "take_ball": .26, "take_called": .03, "swing_miss": .05, "swing_inplay": .35,
    }
    actual_vals = {
        "n": overall["n"], "take_mean": overall["Take"]["mean_W"], "swing_mean": overall["Swing"]["mean_W"],
        "delta": overall["delta_Swing_minus_Take_W"], "direct_delta": overall["direct_delta_W"],
        "decomp_minus_direct": overall["decomposed_minus_direct_delta_W"],
        "take_ball": overall["Take"]["component_contributions_W"]["TAKE_BALL"],
        "take_called": overall["Take"]["component_contributions_W"]["TAKE_CALLED_STRIKE"],
        "swing_miss": overall["Swing"]["component_contributions_W"]["SWING_MISS"],
        "swing_inplay": overall["Swing"]["component_contributions_W"]["IN_PLAY"],
    }
    add("exact_composition", all(approx(actual_vals[k], v) if isinstance(v, float) else actual_vals[k] == v for k, v in expected_vals.items()), expected_vals, actual_vals)
    groups = {(x["level"], x["count"], x["region"]): x["n"] for x in result["summaries"]}
    expected_groups = {("overall", "ALL", "ALL"): 2, ("count", "0-2", "ALL"): 2, ("count_region", "0-2", "HIGH"): 2, ("count_region", "0-2", "OUTSIDE"): 2}
    add("overlap_regions_no_overall_duplication", groups == expected_groups, "four groups each n=2; no n=4", [{"level": k[0], "count": k[1], "region": k[2], "n": v} for k, v in groups.items()])
    add("not_product_of_means", approx(overall["Take"]["mean_W"], .29) and not approx(overall["Take"]["mean_W"], .2375), {"correct": .29, "wrong_product_of_means": .2375}, overall["Take"]["mean_W"])
    diags = {x["action"]: x for x in result["observed_action_predictive_diagnostics"]}
    diag_actual = {"Take_brier": diags["Take"]["multiclass_brier_sum"], "Swing_brier": diags["Swing"]["multiclass_brier_sum"], "Take_logloss": diags["Take"]["log_loss"], "Swing_logloss": diags["Swing"]["log_loss"]}
    diag_expected = {"Take_brier": .08, "Swing_brier": 1.125, "Take_logloss": -math.log(.8), "Swing_logloss": -math.log(.25)}
    add("observed_action_diagnostics", all(approx(diag_actual[k], v) for k, v in diag_expected.items()), diag_expected, diag_actual)

    def reject(name, mutate, contains):
        bad = copy.deepcopy(doc); mutate(bad)
        try: mod.calculate(bad); actual = "accepted"
        except Exception as exc: actual = f"{type(exc).__name__}: {exc}"
        add(name, actual != "accepted" and contains in actual, f"reject containing {contains!r}", actual, "negative_synthetic_execution")
    reject("invalid_probability_sum", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(p=.7), "sum to 1")
    reject("positive_mass_missing_mu", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(mean_W=None), "lacks supported")
    reject("positive_mass_unsupported", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(supported=False), "lacks supported")
    reject("missing_action_row", lambda d: d["predictions"].pop(), "exactly the same")
    reject("duplicate_action_row", lambda d: d["predictions"].append(copy.deepcopy(d["predictions"][0])), "duplicate row/action")
    reject("unknown_label", lambda d: d["reference_rows"][0].update(observed_description="mystery"), "unclassified")
    reject("train_eval_overlap", lambda d: d["fold_training_games"]["fold-A"].append("eval-A"), "overlaps")
    reject("fold_mismatch", lambda d: d["predictions"][0].update(prediction_fold="fold-B"), "differs")
    reject("inconsistent_regions", lambda d: d["reference_rows"][0].update(regions=["HIGH", "LOW"]), "inconsistent")
    reject("partial_direct", lambda d: d["predictions"][0].update(direct_mean_W=None), "cover every")
    reject("nonfinite_probability", lambda d: d["predictions"][0]["branches"]["TAKE_BALL"].update(p=float("nan")), "nonfinite")

    cli_out = HERE / "cli_output.json"
    if cli_out.exists(): cli_out.unlink()
    run = subprocess.run([str(PYTHON), "-B", str(COMPOSE), "--input", str(fixture_path), "--output", str(cli_out)], capture_output=True, text=True)
    add("cli_first_write", run.returncode == 0 and cli_out.exists(), "returncode 0 and output created", {"returncode": run.returncode, "stderr": run.stderr.strip()}, "cli_execution")
    before = sha(cli_out)
    rerun = subprocess.run([str(PYTHON), "-B", str(COMPOSE), "--input", str(fixture_path), "--output", str(cli_out)], capture_output=True, text=True)
    after = sha(cli_out)
    add("cli_overwrite_refusal", rerun.returncode != 0 and before == after, "nonzero return and unchanged SHA256", {"returncode": rerun.returncode, "before": before, "after": after, "stderr_tail": rerun.stderr.strip().splitlines()[-1]}, "cli_execution")

    spec = json.loads((ROOT / "models/bcap/swing/v0.2.0/specification.yaml").read_text(encoding="utf-8-sig"))
    mapping = {k: v[0] for k, v in mod.DESCRIPTION.items()}
    exp_mapping = {x: "Take" for x in spec["actions"]["Take"]} | {x: "Swing" for x in spec["actions"]["Swing"]}
    add("description_mapping_vs_swing_spec", mapping == exp_mapping, exp_mapping, mapping, "code_config_comparison")

    manifests = [
        ROOT / "columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/manifest.json",
        ROOT / "columns/001-ball-count/analysis/runs/bcai_state_delta__mlb_2024_2025__20260917__r01/manifest.json",
        ROOT / "columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r01/manifest.json"]
    hash_evidence = []
    for mp in manifests:
        m = json.loads(mp.read_text(encoding="utf-8-sig")); base = mp.parent
        entries = []
        for section in ("inputs_sha256", "code_sha256"):
            for p, expected in m.get(section, {}).items(): entries.append((ROOT / Path(p), expected, section))
        for p, expected in m.get("outputs_sha256", {}).items(): entries.append((base / Path(p), expected, "outputs_sha256"))
        for item in m.get("input", []): entries.append((ROOT / item["path"], item["sha256"], "input"))
        if isinstance(m.get("configuration"), dict): entries.append((ROOT / m["configuration"]["path"], m["configuration"]["sha256"], "configuration"))
        if isinstance(m.get("code"), dict): entries.append((ROOT / m["code"]["path"], m["code"]["sha256"], "code"))
        for item in m.get("outputs", []): entries.append((ROOT / item["path"], item["sha256"], "outputs"))
        for p, expected in m.get("input_output_code_sha256", {}).items(): entries.append((ROOT / p, expected, "input_output_code_sha256"))
        for path, expected, section in entries:
            actual = sha(path) if path.is_file() else None
            hash_evidence.append({"manifest": str(mp.relative_to(ROOT)), "section": section, "path": str(path.relative_to(ROOT)), "expected": expected, "actual": actual, "match": actual == expected})
    add("three_manifest_declared_small_hashes", all(x["match"] for x in hash_evidence), "all declared small input/code/config/output hashes match", hash_evidence, "sha256_recalculation")

    md = ROOT / "columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md"
    hp = md.with_suffix(".html")
    md_text = md.read_text(encoding="utf-8-sig")
    md_text = re.sub(r"\[([^]]+)\]\([^)]+\)", r"\1", md_text)
    html_text = hp.read_text(encoding="utf-8-sig")
    html_text = re.sub(r"<(style|script)\b.*?</\1>", " ", html_text, flags=re.I | re.S)
    visible = re.sub(r"<[^>]+>", " ", html_text)
    number_pattern = r"(?<![A-Za-z])[-+]?\d[\d,]*(?:\.\d+)?%?"
    md_nums = re.findall(number_pattern, md_text)
    html_nums = re.findall(number_pattern, html.unescape(visible))
    md_counter, html_counter = Counter(md_nums), Counter(html_nums)
    extra_html = html_counter - md_counter
    add("followup_report_md_html_numeric_tokens",
        not (md_counter - html_counter) and extra_html == Counter({"001": 1}),
        {"all_md_numeric_tokens_in_html": True, "permitted_html_only_document_label": {"001": 1}, "count": len(md_nums), "tokens": dict(md_counter)},
        {"count": len(html_nums), "tokens": dict(html_counter), "md_only": dict(md_counter - html_counter), "html_only": dict(extra_html)},
        "document_parse_no_csv_recalculation")

    link_docs = [ROOT / p for p in [
        "models/bcap/decomposition/v0.1.0/model_card.md", "models/bcap/decomposition/v0.1.0/validation.md",
        "models/bcai/state_delta/v0.1.0/model_card.md", "models/bcai/state_delta/v0.1.0/validation.md",
        "columns/001-ball-count/model_research_followup_20260917.md", "columns/001-ball-count/analysis/handoff_bcap_followup_20260917.md",
        "columns/001-ball-count/analysis/handoff_bcap_review.md"]]
    link_results = []
    for path in link_docs:
        text = path.read_text(encoding="utf-8-sig")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if re.match(r"^[a-z]+://|^#", target): continue
            clean = target.split("#", 1)[0]
            if not clean: continue
            resolved = (path.parent / clean).resolve()
            link_results.append({"document": str(path.relative_to(ROOT)), "target": target, "exists": resolved.exists()})
    add("new_cards_reports_handoff_local_links", all(x["exists"] for x in link_results), "all parsed local Markdown targets exist", link_results, "local_link_resolution")

    mutable = []
    for name in ("document_update.json", "delivery_check.json"):
        p = manifests[0].parent / name
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        item = {"path": str(p.relative_to(ROOT)), "current_sha256": sha(p), "classification": "mutable process/document record, not an immutable run output"}
        if name == "document_update.json":
            item["recorded_document_after_hashes"] = []
            for update in data.get("updates", []):
                target = ROOT / update["path"]
                current = sha(target) if target.is_file() else None
                item["recorded_document_after_hashes"].append({"path": update["path"], "recorded_after": update["after_sha256"], "current": current, "still_equal": current == update["after_sha256"]})
        else:
            item["recorded_checker_hashes"] = {k: v for k, v in data.items() if "sha256" in k.lower()}
        mutable.append(item)
    add("mutable_document_delivery_records_classified", True, "record current hashes without treating later handoff/PPT mutation as immutable result mismatch", mutable, "provenance_classification")

    payload = {"snapshot": SNAPSHOT, "synthetic_fixture": True, "source_hashes": {"compose.py": sha(COMPOSE), "input_contract.md": sha(ROOT / "models/bcap/decomposition/v0.1.0/input_contract.md"), "swing_specification.yaml": sha(ROOT / "models/bcap/swing/v0.2.0/specification.yaml")}, "summary": {"total": len(checks), "passed": sum(x["status"] == "PASS" for x in checks), "failed": sum(x["status"] == "FAIL" for x in checks)}, "checks": checks}
    (HERE / "checks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 1 if payload["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
