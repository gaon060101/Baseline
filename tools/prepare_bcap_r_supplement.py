"""2026 archived-file transport and explicit R configurations; no estimates."""
import hashlib
import json
from pathlib import Path
import shutil
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
COL=ROOT/'columns/001-ball-count'
AUDIT=COL/'analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260909__r01/artifacts/preparation/preparation_audit.json'
PLAN=COL/'analysis/bcap_external_20260914__r01/plan.json'
REPORT=COL/'analysis/r_supplement_20260928'
OUT=COL/'data/processed/r_bcai_supplement_20260928/2026'
BCAP=COL/'data/processed/r_bcap_supplement_20260928/2026'
FIELDS=['game_pk','at_bat_number','pitch_number','game_year','game_date','balls','strikes','events']

def rel(path):return Path(path).relative_to(ROOT).as_posix()
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')

def main():
    if OUT.exists() or BCAP.exists() or REPORT.exists():raise FileExistsError('Supplement output path exists')
    old=json.loads(AUDIT.read_text(encoding='utf-8-sig'));plan=json.loads(PLAN.read_text(encoding='utf-8-sig'))
    sources=[x for x in old['inputs'] if x['path'].endswith('.csv')]
    schedules=[x for x in old['inputs'] if x['path'].endswith('schedule_2026.json')]
    assert len(sources)==35 and len(schedules)==1
    for item in sources+schedules:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    OUT.mkdir(parents=True);REPORT.mkdir(parents=True)
    parts=[pd.read_csv(ROOT/x['path'],usecols=FIELDS)[FIELDS] for x in sources]
    frame=pd.concat(parts,ignore_index=True)
    assert len(frame)==639042
    target=OUT/'pitches.csv';frame.to_csv(target,index=False,encoding='utf-8-sig')
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in sources+schedules)
    provenance={'role':'format transport only; exact archived 35 files and eight fields; no filtering, new data or estimates',
      'source_audit':{'path':rel(AUDIT),'sha256':sha(AUDIT)},'inputs':sources,
      'rows':len(frame),'columns':FIELDS,'output':{'path':rel(target),'sha256':sha(target),'bytes':target.stat().st_size}}
    write(OUT/'pitches.provenance.json',provenance)
    weight={'year':2026,**plan['weights']['2026']}
    assert {k:v for k,v in weight.items() if k!='year'}==plan['weights']['2025']
    write(REPORT/'weights.json',{'analysis_year':2026,'frozen_weight_year':2025,'weights':[weight],
      'source':{'path':rel(PLAN),'sha256':sha(PLAN)},'cutoff':'2026-09-07'})
    season={'year':2026,'cutoff':'2026-09-07','scope':'archived_partial_season','schedule':schedules[0]['path']}
    bcaiid='bcai_supplement__mlb_2026_ytd_20260907__20260928__r01'
    bcai={'run_id':bcaiid,'model_id':'BCAI-OBS-v1.0.0','version':'1.0.0',
      'input_csv':[rel(target)],'input_provenance':[rel(OUT/'pitches.provenance.json')],'years':[2026],
      'seasons':[season],'weights':[weight],'weights_source':rel(REPORT/'weights.json'),
      'bootstrap_replicates':2000,'seed':20260928+2026,'comparisons':[],'tolerance':1e-9,
      'data_source':'Archived MLB Baseball Savant Statcast; frozen 2026-09-07 cutoff; 2025 weights',
      'source_notes':rel(COL/'sources.md')}
    bcairun=COL/'analysis/runs'/bcaiid
    assert not bcairun.exists();write(bcairun/'config.json',bcai)
    snapshot=bcairun/'execution_snapshot';snapshot.mkdir()
    for name in ['run.R','bcai.R']:shutil.copy2(ROOT/'models/bcai/observed/v1.0.0/r'/name,snapshot/name)
    prep={'years':[2026],'input_csv':[x['path'] for x in sources],'seasons':[season],'weights':[weight],
      'weights_source':rel(REPORT/'weights.json'),'source_notes':rel(COL/'sources.md'),
      'output_rds':rel(BCAP/'prepared.rds'),'audit_dir':rel(BCAP/'audit')}
    write(REPORT/'bcap_preparation_config.json',prep)
    snapshot=REPORT/'bcap_preparation_snapshot';snapshot.mkdir();shutil.copy2(ROOT/'models/bcap/r/prepare_raw.R',snapshot/'prepare_raw.R')
    for model in ['pitch','pitch_ff']:
      rid=f'bcap_{model}_r_supplement__mlb_2026_ytd_20260907__20260928__r01'
      cfg={'model':model,'years':[2026],'input_rds':rel(BCAP/'prepared.rds'),
         'output_dir':rel(COL/'analysis/runs'/rid),'comparison_family':255,'seed':20260928+2026,
         'purpose':'2026-09-07 archived supplement with frozen 2025 weights; no SB/SWING measurement application'}
      write(REPORT/f'{model}_config.json',cfg)
      snap=REPORT/f'{model}_execution_snapshot';snap.mkdir()
      for name in ['run.R','engine.R']:shutil.copy2(ROOT/'models/bcap/r'/name,snap/name)
    print(json.dumps({'rows':len(frame),'raw_files':len(sources),'source_unchanged':True,'configs':rel(REPORT)},ensure_ascii=False))

if __name__=='__main__':main()
