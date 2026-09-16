"""Read-only numerical/provenance checks; no fitting, downloading or re-evaluation."""
from pathlib import Path
import json,hashlib,re,csv,datetime
ROOT=Path(__file__).resolve().parents[1];A=ROOT/'columns/001-ball-count/analysis';M=ROOT/'models/bcai/ridge/v0.2.0'
def read(p):return Path(p).read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(rec):
    p=ROOT/rec['path'];assert p.is_file(),str(p);assert sha(p)==rec['sha256'],str(p)
    if 'bytes' in rec:assert p.stat().st_size==rec['bytes']
def rows(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
checks={};count=0
old=A/'runs/bcai_obs__mlb_2024_2025__20260907__r01'
for alias in ['bcai_obs__mlb_2024_2025__20260907__r01','bcai_ridge__mlb_2024_2025__20260907__r01']:
    manifest=json.loads(read(A/'runs'/alias/'manifest.json'))
    for rec in manifest['artifacts']:check(rec);count+=1
audit=json.loads(read(old/'artifacts/advantage_audit.json'))
for rec in audit['inputs']:
    check(dict(rec,path='columns/001-ball-count/'+rec['path'].replace('\\','/')));count+=1
checks['historical_artifact_and_input_hashes']=count
seal=json.loads(read(M/'external_protocol_seal.json'))
for rec in seal['files']:check(rec)
checks['external_protocol_hashes']=len(seal['files'])
dev=A/'runs/bcai_ridge__mlb_2024_2025__20260908__r02';freeze=json.loads(read(dev/'artifacts/freeze.json'))
for rec in freeze['files']:check(rec)
runs=['bcai_ridge__mlb_2024_2025__20260908__r02','bcai_ridge__mlb_2024_2025__20260908__r03','bcai_ridge__mlb_2023__20260908__r01','bcai_ridge__mlb_2026_ytd_20260907__20260909__r01']
for run in runs:
    mm=json.loads(read(A/'runs'/run/'manifest.json'))
    assert mm['status']=='COMPLETE' and mm['model_id']=='BCAI-RIDGE-v0.2.0'
    assert mm['external_data_used_for_tuning'] is False
    for rec in mm['inputs']+mm['artifacts']+mm['code']:check(rec)
    if mm['role'].startswith('external'):
        assert mm['evaluation_passes']==1
        assert datetime.datetime.fromisoformat(mm['started_at'])>datetime.datetime.fromisoformat(freeze['frozen_at'])
        aa=json.loads(read(A/'runs'/run/'artifacts/acquisition_audit.json'));assert not aa['missing_games'] and aa['duplicate_pitch_keys']==0
        pp=rows(A/'runs'/run/'artifacts/predictions.csv')
        assert len(pp)==mm['sample']['eligible_PA']
        scale=mm['baseline']['training_fixed'];n=len(pp)
        mse=sum(((float(x['value'])-float(x['prediction_W']))/scale)**2 for x in pp)/n
        assert abs(mse-mm['metrics']['MSE'])<1e-10
        assert all(x['unseen_game_year']=='True' for x in pp)
        for rr in rows(A/'runs'/run/'artifacts/count_indices.csv'):
            if rr['count']=='0-0':assert abs(float(rr['J'])-100)<1e-8
checks['completed_manifests_and_independent_external_MSE']=len(runs)
for run in ['bcai_ridge__mlb_2024_2025__20260908__r01','bcai_ridge__mlb_2026_ytd_20260907__20260908__r01']:
    assert json.loads(read(A/'runs'/run/'manifest.json'))['status']=='FAILED'
checks['failed_runs_preserved']=2
diag=rows(dev/'artifacts/all_fit_diagnostics.csv')
assert len(diag)==207
assert all(x['converged']=='True' and float(x['max_last_change'])<1e-7 and int(x['extra_iterations'])==10 and int(x['abnormal_increases'])==0 for x in diag)
assert all(float(x['post_convergence_max_prediction_drift'])<1e-7 for x in diag)
checks['all_207_fits_converged']=True
sel=rows(dev/'artifacts/alpha_selection.csv');assert all(float(x['selected_alpha'])==300 and x['min_at_boundary']=='False' for x in sel)
checks['all_six_selection_stages_alpha300']=True
fold=rows(dev/'artifacts/outer_folds.csv');assert len({x['game_pk'] for x in fold})==len(fold)==4859
for p in (dev/'artifacts').glob('*_folds.csv'):
    f=rows(p);assert len({x['game_pk'] for x in f})==len(f)
checks['one_fold_per_game']=True
spec=json.loads(read(M/'specification.yaml'));assert spec['version']=='0.2.0' and spec['status']=='EXPERIMENTAL'
docs=[ROOT/'README.md',ROOT/'models/registry.md',ROOT/'models/bcai/README.md',ROOT/'columns/001-ball-count/column.md',ROOT/'columns/001-ball-count/sources.md']+list(M.glob('*.md'))
links=0
for p in docs:
    for match in re.findall(r'\]\(([^)]+)\)',read(p)):
        link=match.strip('<>').split('#')[0]
        if not link or '://' in link or link.startswith('mailto:'):continue
        assert (p.parent/link).resolve().exists(),f'{p}: {link}'
        links+=1
checks['internal_links']=links
for p in list(M.glob('*.py'))+[Path(__file__)]:compile(read(p),str(p),'exec')
checks['source_compile']=True
extension=A/'runs/bcai_ridge__mlb_2026_ytd_20260907__20260909__r01/manifest_extension.json'
ext=json.loads(read(extension));check(ext['acquisition_adapter']);check(ext['acquisition_audit']);assert ext['model_or_inference_changed'] is False
checks['2026_acquisition_only_repair_provenance']=True
out=dict(checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,status='PASS')
(M/'structure_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
