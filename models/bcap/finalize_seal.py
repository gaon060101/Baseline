"""Add prespecified postprocessing/refit sources to a new final seal, never mutate one."""
from pathlib import Path
import json,datetime,hashlib,argparse
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--core',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    dest=Path(a.output);assert not dest.exists();s=json.loads(Path(a.core).read_text(encoding='utf-8'))
    for f in s['files']:assert sha(ROOT/f['path'])==f['sha256']
    s['core_seal']={'path':Path(a.core).resolve().relative_to(ROOT).as_posix(),'sha256':sha(a.core)}
    s['core_sealed_at_utc']=s['sealed_at_utc'];s['sealed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    for name in ['refit_stability.py','supplement_diagnostics.py','build_report.py','check_artifacts.py','finalize_seal.py']:
        f=ROOT/'models/bcap'/name
        s['files'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size})
    dependencies=['models/bcai/observed/v1.0.0/specification.yaml','models/bcai/ridge/v0.2.0/specification.yaml','columns/001-ball-count/analysis/bcap_request_original.txt','columns/001-ball-count/analysis/bcap_preparation_20260909_r01/preparation_audit.json']
    for name in dependencies:
        f=ROOT/name;s['files'].append({'path':name,'sha256':sha(f),'bytes':f.stat().st_size})
    from data import source_paths
    s['external_input_hashes_before_action_result_access']=[]
    for year in [2023,2026]:
        paths,schedule=source_paths(year)
        for f in paths+[schedule]:s['external_input_hashes_before_action_result_access'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size})
    s['sealed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    s['predeclared_diagnostic_scope']='IPW/g-computation, known-unseen individual conditional intervals, baseline prediction and 8 complete nested game-bootstrap refits per model are supplementary; no inference/policy gate upgrades. Main 1536 family excludes fixed-development-nuisance AIPW and sensitivity/known-unseen/training intervals.'
    dest.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8');print(s['sealed_at_utc'],sha(dest))
