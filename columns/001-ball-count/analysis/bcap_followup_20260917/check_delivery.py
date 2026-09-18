"""새 소형 산출물의 구문·링크·해시만 확인. 분석 재실행은 없음."""
import ast
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "columns/001-ball-count/analysis/runs"
REPORT = RUNS / "bcap_followup__mlb_2024_2025__20260917__r01"
STATE = RUNS / "bcai_state_delta__mlb_2024_2025__20260917__r01"
DECOMP = RUNS / "bcap_decomp__synthetic_smoke__20260917__r01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    output = REPORT / "delivery_check.json"
    if output.exists():
        raise FileExistsError(output)
    pyfiles = list((ROOT / "models/bcai/state_delta/v0.1.0").glob("*.py")) + list((ROOT / "models/bcap/decomposition/v0.1.0").glob("*.py")) + list(Path(__file__).parent.glob("*.py"))
    for p in pyfiles:
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    docs = [REPORT / "artifacts/report.md", STATE / "report.md", DECOMP / "README.md"]
    docs += list((ROOT / "models/bcai/state_delta/v0.1.0").glob("*.md"))
    docs += list((ROOT / "models/bcap/decomposition/v0.1.0").glob("*.md"))
    missing = []
    link_count = 0
    for p in docs:
        for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", p.read_text(encoding="utf-8")):
            if href.startswith(("http://", "https://", "#")):
                continue
            dest = p.parent / href.split("#", 1)[0]
            link_count += 1
            if not dest.exists():
                missing.append({"file": str(p.relative_to(ROOT)), "href": href})
    assert not missing, missing
    hashes = []
    manifest = json.loads((REPORT / "manifest.json").read_text(encoding="utf-8"))
    for key in ("inputs_sha256", "code_sha256"):
        for path, expected in manifest[key].items():
            assert sha(ROOT / path) == expected, path
            hashes.append(path)
    for path, expected in manifest["outputs_sha256"].items():
        assert sha(REPORT / path) == expected, path
        hashes.append(str((REPORT / path).relative_to(ROOT)))
    decomp = json.loads((DECOMP / "manifest.json").read_text(encoding="utf-8"))
    for path, expected in decomp["input_output_code_sha256"].items():
        assert sha(ROOT / path) == expected, path
        hashes.append(path)
    state = json.loads((STATE / "manifest.json").read_text(encoding="utf-8"))
    def check_records(obj):
        if isinstance(obj, dict):
            if "path" in obj and "sha256" in obj:
                assert sha(ROOT / obj["path"]) == obj["sha256"], obj["path"]
                hashes.append(obj["path"])
            for v in obj.values():
                check_records(v)
        elif isinstance(obj, list):
            for v in obj:
                check_records(v)
    check_records(state)
    doc_updates = json.loads((REPORT / "document_update.json").read_text(encoding="utf-8"))
    for rec in doc_updates["updates"]:
        assert sha(ROOT / rec["path"]) == rec["after_sha256"]
    html = (REPORT / "artifacts/report.html").read_text(encoding="utf-8")
    assert html.count("<table>") == 5 and html.count("</table>") == 5
    result = {"status": "PASS", "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "새 파일 구문·로컬 링크·기록 해시·HTML 5표 구조 확인; 브라우저 시각 확인/통계 재검증 아님",
              "syntax_files": len(pyfiles), "local_links": link_count,
              "hash_records": len(hashes), "documents_updated": len(doc_updates["updates"]),
              "new_training": False, "full_validation": False,
              "checker_sha256": sha(Path(__file__)),
              "document_updater_sha256": sha(Path(__file__).with_name("update_documents.py"))}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
