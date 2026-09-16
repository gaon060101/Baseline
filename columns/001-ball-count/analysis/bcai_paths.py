"""BCAI legacy joint pipeline paths. Importing this module never creates files."""
from pathlib import Path
import os
import re

ANALYSIS = Path(__file__).resolve().parent
COLUMN = ANALYSIS.parent
CACHE = ANALYSIS / "advantage_input_cache.pkl"
RUNS = ANALYSIS / "runs"
ARCHIVED = RUNS / "bcai_obs__mlb_2024_2025__20260907__r01" / "artifacts"

def output_dir(writable=False):
    setting = os.environ.get("BCAI_OUTPUT_DIR")
    target = Path(setting).resolve() if setting else ARCHIVED
    if writable:
        if not setting:
            raise ValueError("Set BCAI_OUTPUT_DIR to a NEW run's artifacts directory; archived results are read-only.")
        if target == ARCHIVED or ARCHIVED in target.parents:
            raise ValueError("Historical r01 artifacts must not be overwritten.")
        if target.parent.parent != RUNS.resolve() or target.name != "artifacts":
            raise ValueError("Output must be analysis/runs/<run_id>/artifacts.")
        if not re.fullmatch(r"bcai_obs__mlb_2024_2025__\d{8}__r\d{2,}", target.parent.name):
            raise ValueError("This legacy pipeline supports only bcai_obs__mlb_2024_2025__YYYYMMDD__rNN.")
        if (target.parent / "manifest.json").exists():
            raise ValueError("Registered runs are immutable; choose a new run ID.")
        target.mkdir(parents=True, exist_ok=True)
    return target
