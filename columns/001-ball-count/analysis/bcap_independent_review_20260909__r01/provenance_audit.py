"""Read-only independent hashes, explicit historical resolutions and UTC chronology."""
from pathlib import Path
import json,hashlib,datetime,difflib,sys
import pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];AN=ROOT/'columns/001-ball-count/analysis';OUT=HERE/'provenance';OUT.mkdir(exist_ok=True)
START=datetime.datetime.now(datetime.timezone.utc).isoformat();CACHE={};INPUTS=set();ROWS=[];EVENTS=[];CHECKS=[]
def sha(p):
 p=Path(p);INPUTS.add(p)
 if p not in CACHE:CACHE[p]=hashlib.file_digest(p.open('rb'),'sha256').hexdigest() if p.is_file() else None
 return CACHE[p]
def read(p):INPUTS.add(Path(p));return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def check(k,ok,detail=''):CHECKS.append(dict(check=k,status='PASS' if ok else 'FAIL',detail=detail))
def pair(owner,p,expected,role='current',actualpath=None):
 actual=sha(actualpath or ROOT/p);ROWS.append(dict(owner=owner,path=p,actual_path=str(actualpath or ROOT/p),role=role,expected=expected,actual=actual,status='PASS' if actual==expected else 'FAIL'));return actual==expected
def walk(obj,owner,ptr=''):
 if isinstance(obj,dict):
  if 'path' in obj and 'sha256' in obj:
   path=obj['path'];expected=obj['sha256'];actualpath=None;role='current'
   if owner=='bcap_execution_evidence_20260909.json' and path=='models/bcap/run.py' and expected=='da6d7bf3f2b8f10386be886d7eef4d1255dfc934fd04d7fcd3edb478f0054710':
    actualpath=AN/'runs/bcap_pitch__mlb_2024_2025__20260909__r01/artifacts/run_failed_source.py';role='explicit_failed_source_archive'
   if owner=='bcap_document_update_20260909.json' and ptr.startswith('/inputs_read/'):
    updates=read(AN/'bcap_document_update_20260909.json')['modified_MD']
    for entry in updates:
     if entry['path']==path and entry['before_sha256']==expected:
      actualpath=ROOT/entry['backup'];role='document_input_before_update_backup';break
   pair(owner+ptr,path,expected,role,actualpath)
  for k,v in obj.items():walk(v,owner,ptr+'/'+str(k))
 elif isinstance(obj,list):
  for k,v in enumerate(obj):walk(v,owner,ptr+'/'+str(k))
def event(label,time,source):EVENTS.append(dict(event=label,utc=time,source=source))
sealpath=ROOT/'models/bcap/external_seal_20260909_r01.json';seal=read(sealpath);walk(seal,'final_seal');event('final_local_seal',seal['sealed_at_utc'],str(sealpath))
corepath=ROOT/'models/bcap/external_seal_core_20260909_r01.json';core=read(corepath);walk(core,'core_seal');event('core_local_seal',core['sealed_at_utc'],str(corepath))
main=[]
for p in sorted((AN/'runs').glob('bcap_*/manifest.json')):
 m=read(p);rid=m['run_id']
 if m.get('started_at_utc'):event(rid+' start',m['started_at_utc'],str(p))
 if m.get('finished_at_utc'):event(rid+' finish',m['finished_at_utc'],str(p))
 if rid=='bcap_pitch__mlb_2024_2025__20260909__r01':
  for entry in m.get('code',[]):pair(rid,entry['path'],entry['sha256'],'failed_source_archive' if entry['path']=='models/bcap/run.py' else 'current',p.parent/'artifacts/run_failed_source.py' if entry['path']=='models/bcap/run.py' else None)
  ext=read(p.parent/'provenance_extension_20260909.json');check('failed_manifest_historical_hash',sha(p)==ext['original_manifest_sha256']);walk(ext,rid+'/extension')
  check('failed_run_prefit',m['status']=='FAILED' and not list((p.parent/'artifacts').glob('*nuisance*')))
  old=(p.parent/'artifacts/run_failed_source.py').read_text(encoding='utf-8-sig').splitlines();new=(ROOT/'models/bcap/run.py').read_text(encoding='utf-8-sig').splitlines()
  (OUT/'failed_to_successful_source.diff').write_text('\n'.join(difflib.unified_diff(old,new,fromfile='failed r01 frozen source',tofile='sealed successful engine')),encoding='utf-8')
 else:walk(m,rid)
 if m.get('role','').startswith('external_'):
  log=p.parent/'artifacts/external_access_log.json'
  if log.exists():
   l=read(log);walk(l,rid+'/external_access');tm=l['first_current_task_BCAP_external_row_access_utc'];event(rid+' first BCAP result access',tm,str(log));check(rid+'/seal_before_access',tm>seal['sealed_at_utc'])
  if 'swing__mlb_2026' in rid:
   check('SWING2026_withheld_evaluation_zero',m['status']=='WITHHELD' and m['outcome_evaluations']==0)
   check('SWING2026_no_scores_or_replacement',not list((p.parent/'artifacts').glob('*scores*')) and not (p.parent/'artifacts/fixed_development_predictions.pkl').exists())
 for file in ['frozen_run.py','frozen_data.py']:
  fp=p.parent/'artifacts'/file
  if fp.exists():check(rid+'/'+file,sha(fp)==sha(ROOT/'models/bcap'/file.replace('frozen_','')))
for n in ['bcap_execution_evidence_20260909.json','bcap_execution_commands_20260909.json','bcap_document_update_20260909.json']:
 p=AN/n;obj=read(p);walk(obj,n)
 if n.startswith('bcap_execution_evidence'):
  for path,h in obj['original_snapshots'].items():pair('historical_snapshot',path,h)
  event('execution_evidence_generated',obj['created_at_utc'],str(p))
 if n.startswith('bcap_document'):
  event('current_document_update',obj['updated_at_utc'],str(p))
  for r in obj['modified_MD']:
   pair('document_after',r['path'],r['after_sha256'])
   if r.get('backup'):pair('document_before',r['path'],r['before_sha256'],'before_update_backup',ROOT/r['backup'])
   else:check('new_document_no_previous_backup/'+r['path'],r.get('before_sha256') is None)
 if n.startswith('bcap_execution_commands'):
  event('commands_reconstructed_after_execution',obj['recorded_at_utc'],str(p));check('commands_admit_not_independent_shell_history',all('not shell history' in x.get('source','') for x in obj['commands']))
for p,label in [(AN/'bcap_implementation_review_20260909/postseal_descriptive_comparison/comparison_manifest.json','postseal_descriptive'),(AN/'bcap_implementation_review_20260909/behavior_comparison_manifest.json','postseal_behavior'),(AN/'bcap_final_validation_20260909/validation.json','producer_final_audit')]:
 o=read(p);walk(o,label);tm=o.get('created_at_utc',o.get('checked_at_utc'));event(label,tm,str(p));check(label+'/after_seal',tm>seal['sealed_at_utc'])
orig=read(AN/'handoff_bcap_review_evidence.json')
snap=AN/'bcap_original_handoff_20260909'
for x in orig['files']:
 target=ROOT/x['path'];candidate=snap/target.name
 if sha(target)!=x['sha256'] and candidate.exists():pair('original_handoff',x['path'],x['sha256'],'historical_snapshot',candidate)
 else:pair('original_handoff',x['path'],x['sha256'])
legacy=read(AN/'bcap_implementation_review_20260909/legacy_asset_preservation.json');walk(legacy['source_evidence'],'legacy_sources')
legacyrows=[]
def pointer(obj,ptr):
 for part in ptr.split('/')[1:]:obj=obj[int(part)] if isinstance(obj,list) else obj[part.replace('~1','/').replace('~0','~')]
 return obj
for x in legacy['files']:
 current=sha(ROOT/x['path']);r=dict(path=x['path'],stored_status=x['status'],current_hash_matches_inventory=current==x['current_sha256'])
 base=x.get('selected_baseline')
 if base:
  entry=pointer(read(ROOT/base['source']),base['pointer']);candidates=[entry.get(k) for k in ['sha256','historical_code_sha256','before_sha256','after_sha256','current_sha256']]
  r.update(baseline_source=base['source'],pointer=base['pointer'],baseline_claim_present=base['expected_sha256'] in candidates,baseline_hash_matches_current=current==base['expected_sha256'],historical_only=base['historical_only'])
  if x['status'] in ['VERIFIED','VERIFIED_HISTORICAL']:check('legacy/'+x['path'],r['baseline_claim_present'] and r['baseline_hash_matches_current'])
 legacyrows.append(r)
for x in legacy['historical_reference_differences']:
 entry=pointer(read(ROOT/x['source']),x['pointer']);check('historical_reference/'+x['path'],x['expected_sha256'] in entry.values() and sha(ROOT/x['path'])!=x['expected_sha256'])
pd.DataFrame(legacyrows).to_csv(OUT/'legacy_baseline_recheck.csv',index=False)
pd.DataFrame(ROWS).to_csv(OUT/'hash_comparisons.csv',index=False);pd.DataFrame(CHECKS).to_csv(OUT/'checks.csv',index=False);pd.DataFrame(EVENTS).sort_values('utc').to_csv(OUT/'utc_timeline.csv',index=False)
bad=[r for r in ROWS+CHECKS if r['status']=='FAIL']
result=dict(status='FAIL' if bad else 'PASS',started_at_utc=START,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),hash_comparisons=len(ROWS),checks=len(CHECKS),failures=bad,legacy_baseline_verified=sum(x['stored_status'] in ['VERIFIED','VERIFIED_HISTORICAL'] for x in legacyrows),legacy_no_verifiable_prior_baseline=sum(x['stored_status'] not in ['VERIFIED','VERIFIED_HISTORICAL'] for x in legacyrows),historical_reference_resolution='First pass compared historical entries to current paths and was retained in first_pass_unresolved_historical_references.json. Resolved only from explicit source archive and before-update backups, verified against recorded hashes. No numeric engine or old evidence was changed.',limitations=['Local recorded UTC/hashes do not prove universal nonexposure or public preregistration.','Reconstructed producer commands are not independent shell history.','Historical legacy references were resolved from stored evidence, not current paths blindly.','Source-file byte equality supports the recorded final core; it cannot reconstruct every prior in-memory execution.'])
(OUT/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'evidence.json').write_text(json.dumps(dict(command=[sys.executable]+sys.argv,inputs=[dict(path=str(p),sha256=sha(p)) for p in sorted(INPUTS)],code_sha256=sha(Path(__file__))),ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False),flush=True)
