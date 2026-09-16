"""Source provenance snapshot for independent fold/prediction review."""
from pathlib import Path
import json,hashlib,datetime,difflib,sys
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
R=ROOT/'columns/001-ball-count/analysis/runs'
ids=['bcap_pitch__mlb_2024_2025__20260909__r02','bcap_swing__mlb_2024_2025__20260909__r01','bcap_pitch__mlb_2023__20260909__r01','bcap_swing__mlb_2023__20260909__r01','bcap_pitch__mlb_2026_ytd_20260907__20260909__r01']
def meta(p):return dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size)
files=[ROOT/p for p in ['AGENTS.md','README.md','guides/analysis.md','models/registry.md','columns/001-ball-count/column.md','columns/001-ball-count/sources.md','models/bcap/run.py','models/bcap/data.py','models/bcap/verify_bcap.py','models/bcap/design_decisions.md','models/bcap/measurement_review.md','models/bcap/README.md']]
for model in ['pitch','swing']:
    files.extend(ROOT/'models/bcap'/model/'v0.1.0'/p for p in ['model_card.md','specification.yaml','validation.md'])
result=[];diffs=[]
for rid in ids:
    a=R/rid/'artifacts';m=json.loads((a.parent/'manifest.json').read_text(encoding='utf-8-sig'));files.append(a.parent/'manifest.json')
    for p in ['frozen_run.py','frozen_data.py','specification.yaml']:files.append(a/p)
    live=(ROOT/'models/bcap/run.py').read_text(encoding='utf-8');frozen=(a/'frozen_run.py').read_text(encoding='utf-8')
    diff=list(difflib.unified_diff(frozen.splitlines(),live.splitlines(),fromfile=rid+'/frozen_run.py',tofile='models/bcap/run.py',lineterm=''));diffs.extend(diff)
    source=m['code'][0]
    result.append(dict(run_id=rid,started_at_utc=m['started_at_utc'],finished_at_utc=m.get('finished_at_utc'),frozen_vs_current_run_equal=live==frozen,frozen_run_sha256=meta(a/'frozen_run.py')['sha256'],manifest_source_hash=source['sha256'],frozen_hash_matches_manifest=meta(a/'frozen_run.py')['sha256']==source['sha256'],manifest_configuration_equals_frozen_spec=m['configuration']==json.loads((a/'specification.yaml').read_text(encoding='utf-8-sig')),pickle_artifacts=[str(p.relative_to(a)) for p in a.rglob('*.pkl')],nonfinal_fitted_objects_saved=False))
(OUT/'current_vs_frozen_run.diff').write_text('\n'.join(diffs),encoding='utf-8')
(OUT/'source_evidence.json').write_text(json.dumps(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),argv=sys.argv,files=[meta(p) for p in files],runs=result),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
