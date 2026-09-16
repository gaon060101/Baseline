"""Read-only structural verification; never fit models or collect data."""
from pathlib import Path
import ast
import csv
import hashlib
import importlib.util
import json
import os
import re
import sys
from unittest.mock import patch
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "columns/001-ball-count/analysis"
OBS = "bcai_obs__mlb_2024_2025__20260907__r01"
RIDGE = "bcai_ridge__mlb_2024_2025__20260907__r01"
OUT = BASE / "runs" / OBS / "artifacts"
checks = {}
def digest(p):
    with p.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
def read(p):
    return p.read_text(encoding="utf-8-sig")
migration = json.loads(read(ROOT / "models/migration_20260908.json"))
allowed = {
    "AGENTS.md", "README.md", "guides/analysis.md",
    "columns/001-ball-count/column.md", "columns/001-ball-count/sources.md",
    "columns/001-ball-count/analysis/handoff_count_advantage.md",
    "columns/001-ball-count/analysis/count_advantage_2024_2025.md",
    *["columns/001-ball-count/analysis/" + n for n in
      ["analyze_count_advantage.py", "verify_count_advantage.py", "write_advantage_report.py"]]
}
moves = {x["path"]: x["to"] for x in migration["moves"]}
preserved = data_files = 0
for item in migration["before"]:
    old = item["path"]
    p = ROOT / moves.get(old, old)
    assert p.is_file(), str(p)
    if old in moves:
        assert not (ROOT / old).exists(), "Duplicate old artifact: " + old
    if old not in allowed:
        assert p.stat().st_size == item["bytes"] and digest(p) == item["sha256"], str(p)
        preserved += 1
    if "/data/" in old:
        data_files += 1
checks["original_inventory"] = len(migration["before"])
checks["unchanged_or_byte_identical_moved_files"] = preserved
checks["preserved_data_files"] = data_files
checks["moved_artifacts"] = len(moves)
assert set(p.name for p in OUT.iterdir()) == {Path(p).name for p in moves}
a = json.loads(read(OUT / "advantage_audit.json"))
for item in a["inputs"]:
    p = BASE.parent / item["path"].replace("\\", "/")
    assert p.is_file() and digest(p) == item["sha256"], str(p)
checks["historical_input_hashes"] = len(a["inputs"])
for alias, model_id, version, state, variant in [
    (OBS, "BCAI-OBS-v1.0.0", "1.0.0", "VALIDATED", "observed"),
    (RIDGE, "BCAI-RIDGE-v0.1.0", "0.1.0", "EXPERIMENTAL", "ridge")
]:
    m = json.loads(read(BASE / "runs" / alias / "manifest.json"))
    assert re.fullmatch(r"bcai_(obs|ridge)__mlb_2024_2025__20260907__r01", alias)
    assert (m["run_id"],m["model_id"],m["version"],m["model_status"]) == (alias,model_id,version,state)
    s = json.loads(read(ROOT / m["model_definition"]))
    assert (s["model_id"],s["version"],s["status"]) == (model_id,version,state)
    required = ["input_fields","result_classification","weights","baseline","grade_boundaries","exclusions","duplicates","season_mix","uncertainty","hyperparameters","output_fields"]
    assert all(k in s for k in required)
    for key in ["weights","scale","league_R_PA","baseline_value","season_mix","bootstrap_replicates","seed","simultaneous_critical"]:
        assert m["parameters"][key] == a[key], key
    for p in m["code"] + [m["cache"],m["report"],m["input_audit"]]:
        assert (ROOT / p).is_file(), p
    for item in m["artifacts"]:
        assert digest(ROOT / item["path"]) == item["sha256"]
    if variant == "ridge":
        assert m["ridge_diagnostics"] == a["model"]
        assert m["refit_uncertainty"] is None and not m["converged_to_tolerance"]
        assert s["hyperparameters"]["alpha"] == [20,100,500]
        assert s["hyperparameters"]["solver"]["max_iterations"] == 150
        assert s["hyperparameters"]["solver"]["tolerance"] == 1e-7
checks["model_run_ids_and_specs"] = "PASS"
for p in ROOT.rglob("*.py"):
    compile(read(p), str(p), "exec")
checks["python_compile"] = "PASS"
# Load only the path helper; no pipeline imports/side effects.
ns = {"__file__":str(BASE / "bcai_paths.py")}
exec(compile(read(BASE / "bcai_paths.py"),"bcai_paths.py","exec"),ns)
with patch.dict(os.environ, {}, clear=True):
    assert ns["output_dir"]() == OUT
    try:
        ns["output_dir"](writable=True)
        raise AssertionError("Missing output setting allowed")
    except ValueError:
        pass
for target in [OUT, BASE.parent / "data/processed", BASE / "runs" / RIDGE / "artifacts"]:
    with patch.dict(os.environ, {"BCAI_OUTPUT_DIR":str(target)}):
        try:
            ns["output_dir"](writable=True)
            raise AssertionError("Unsafe output allowed")
        except ValueError:
            pass
new = BASE / "runs/bcai_obs__mlb_2024_2025__20990101__r99/artifacts"
with patch.dict(os.environ, {"BCAI_OUTPUT_DIR":str(new)}), patch.object(Path,"mkdir") as mk:
    assert ns["output_dir"](writable=True) == new
    mk.assert_called_once()
assert ns["CACHE"].is_file() and ns["COLUMN"] == BASE.parent
checks["input_output_resolution_and_archive_protection"] = "PASS"
# Check existing results, without recomputing PA or bootstrap samples.
with (OUT / "advantage_count_results.csv").open(encoding="utf-8-sig",newline="") as f:
    rows = list(csv.DictReader(f))
assert len(rows) == 12 and {r["count"] for r in rows} == {f"{b}-{s}" for b in range(4) for s in range(3)}
for r in rows:
    assert all(k in r for k in ["index","confirmed_grade","adjusted_index_alpha20","adjusted_index_alpha100","adjusted_index_alpha500"])
    assert float(r["CI95_low"]) <= float(r["index"]) <= float(r["CI95_high"])
# Execute only pure classification functions, no analysis statements.
tree = ast.parse(read(BASE / "analyze_count_advantage.py"))
funcs = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {"grade","confirmed"}]
fns = {}
exec(compile(ast.Module(body=funcs,type_ignores=[]),"pure_classification","exec"),fns)
for r in rows:
    assert fns["grade"](float(r["index"])) == r["grade"]
    assert fns["confirmed"](float(r["simultaneous95_low"]),float(r["simultaneous95_high"])) == r["confirmed_grade"]
for key, value in [("WEIGHTS",{int(k):v for k,v in a["weights"].items()}),("SCALE",{int(k):v for k,v in a["scale"].items()}),("RPA",{int(k):v for k,v in a["league_R_PA"].items()})]:
    n = next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==key for t in n.targets))
    assert eval(compile(ast.Expression(n.value),"constants","eval"),{"dict":dict}) == value
import numpy as np
import pandas as pd
with np.load(OUT / "advantage_bootstrap.npz") as z:
    assert z["index"].shape == z["runs"].shape == (2000,12)
    assert list(z["counts"]) == [r["count"] for r in rows]
checks["existing_results_fields_grades_arrays_constants"] = "PASS"
checks["runtime"] = {"python":sys.version.split()[0],"numpy":np.__version__,"pandas":pd.__version__}
# Markdown inline file links + simple heading fragments, excluding fenced examples.
def stripped(s):
    return re.sub(r"```.*?```","",s,flags=re.S)
def anchors(s):
    out = set()
    for heading in re.findall(r"^#{1,6}\s+(.+)$",stripped(s),re.M):
        heading = re.sub(r"[^\w\s\-가-힣]","",heading.lower()).strip().replace(" ","-")
        out.add(heading)
    return out
broken = []
count = 0
for p in ROOT.rglob("*.md"):
    for dest in re.findall(r"\]\(([^\n)]+)\)",stripped(read(p))):
        dest = dest.strip("<>")
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:",dest):
            continue
        dest = unquote(dest)
        path, _, fragment = dest.partition("#")
        target = (p.parent / path).resolve() if path else p
        count += 1
        if not target.exists() or (fragment and target.suffix==".md" and fragment not in anchors(read(target))):
            broken.append({"source":str(p.relative_to(ROOT)),"link":dest})
assert not broken, json.dumps(broken,ensure_ascii=False)
checks["markdown_links_checked"] = count
checks["broken_markdown_links"] = 0
checks["full_pipeline_rerun"] = "NOT RUN: structure-only; no fit or bootstrap"
print(json.dumps(checks,ensure_ascii=False,indent=2))
