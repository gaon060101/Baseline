"""One necessary FF/non-FF crossfit, using the unmodified V2 numerical engine."""
from pathlib import Path
import sys,json,argparse,pickle,shutil,traceback
import numpy as np
import pandas as pd
import engine as E
ROOT=Path(__file__).resolve().parents[4];CODE=Path(__file__).parent;AN=ROOT/'columns/001-ball-count/analysis'
KEY=['game_pk','at_bat_number','pitch_number']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bundle',required=True);ap.add_argument('--run-id',required=True);a=ap.parse_args();b=ROOT/a.bundle
 plan=E.read(b/'analysis_plan.json');c=E.read(CODE/'specification.yaml');prep=E.read(b/'preparation.json')
 assert a.run_id==plan['new_run'];run=AN/'runs'/a.run_id;assert not run.exists()
 for x in E.read(b/'plan_seal.json')['files']:assert E.sha(ROOT/x['path'])==x['sha256']
 art=run/'artifacts';art.mkdir(parents=True)
 for name in ['engine.py','prepare.py','run.py','specification.yaml']:shutil.copy2(CODE/name,art/('frozen_'+name))
 m={'run_id':a.run_id,'model_id':c['model_id'],'version':c['version'],'model_status':'DRAFT','status':'RUNNING','scope':'2024/2025 FF/non-FF development only','started_at_utc':E.now(),'configuration':c,'input':prep['output'],'definition':E.meta(CODE/'specification.yaml'),'plan':E.meta(b/'analysis_plan.json'),'code':[E.meta(CODE/n) for n in ['engine.py','prepare.py','run.py']],'environment':E.environment(),'command':[sys.executable]+sys.argv,'external_evaluations':0,'bootstrap_replicates':0,'old_FB_refits':0,'SWING_SB_refits':0}
 E.js(run/'manifest.json',m);checks=[]
 def ck(n,yes,detail=None):
  checks.append({'check':n,'status':'PASS' if yes else 'FAIL','detail':detail})
  if not yes:raise AssertionError(n)
 try:
  d=pd.read_pickle(ROOT/prep['output']['path']);d=E.features(d,c).reset_index(drop=True)
  ck('input_hash',E.sha(ROOT/prep['output']['path'])==prep['output']['sha256'])
  ck('years_and_keys',set(d.game_year)=={2024,2025} and d.row_id.is_unique and not d.duplicated(KEY).any())
  ck('action_binary_closed',d.pitch_type.isin(sum(c['action_codes'].values(),[])).all() and np.array_equal(d.A,d.pitch_type.eq('FF').astype(int)))
  fs=c['features'];oldc=E.read(ROOT/'models/bcap/pitch/v0.2.0/specification.yaml')
  ck('identical_feature_list',fs==oldc['features'])
  ck('no_current_post_action_features',not set(fs)&{'pitch_type','pitch_group','description','Y','result','final_event','plate_x','plate_z','zone','A','A_pitch','A_pitch_sb','A_swing','release_speed','pfx_x','pfx_z','events','sz_top','sz_bot'})
  ck('identical_fixed_alphas',c['fixed_alpha']==oldc['fixed_alpha'])
  ck('same_seed_folds',np.array_equal(E.folds(d,3,c['seed']),d.fold.to_numpy()))
  ck('game_split_unique',d.groupby('game_pk').fold.nunique().eq(1).all())
  E.csv(art/'fold_membership.csv',d[['row_id']+KEY+['game_year','A','fold']])
  logs=[];records=[];parts=[]
  for k in range(3):
   tr=d[d.fold.ne(k)];te=d[d.fold.eq(k)];label='fold'+str(k);E.split_record(records,label,'development_oof',tr,te)
   print(E.now(),label,'train',len(tr),'evaluate',len(te),flush=True)
   nu,tu=E.nuisance(tr,c,label,c['seed']+2000+k,logs,records,frozen_alpha=c['fixed_alpha'])
   ck(label+'_no_tuning',len(tu)==0)
   ck(label+'_training_calibration_separation',not set(nu.calibration_rows.game_pk)&set(te.game_pk))
   rc=pd.crosstab(tr.pitcher.astype(str),tr.A).reindex(columns=[0,1],fill_value=0)
   ck(label+'_new_action_support',nu.repertoire==(rc.min(axis=1)>=c['min_entity_arm_training']).to_dict())
   p=art/'fits'/label/'nuisance.pkl';p.parent.mkdir(parents=True)
   with p.open('wb') as f:pickle.dump(nu,f,protocol=5)
   sc=E.score(te,nu.predict(te,c),c)
   for col in ['row_id','fold','pitch_type','known_count_exception']:sc[col]=te[col]
   ck(label+'_finite',np.isfinite(sc[['p','mu0','mu1','phi0','phi1']]).all().all())
   ck(label+'_converged',all(x['converged'] for x in logs))
   for ar in [0,1]:
    prob=sc.p.to_numpy() if ar else 1-sc.p.to_numpy();mu=sc['mu'+str(ar)].to_numpy();manual=mu+np.where(sc.A.to_numpy()==ar,(sc.Y.to_numpy()-mu)/prob,0.)
    ck(label+f'_phi{ar}_arithmetic',np.allclose(manual,sc['phi'+str(ar)],rtol=0,atol=1e-12))
   for rec in records:
    if rec['fit_id'].startswith(label+'/'):ck(rec['fit_id']+'_outer_holdout_excluded',not set(te.game_pk)&(set(rec['train_games'])|set(rec['evaluation_games'])))
   parts.append(sc);E.csv(art/'fit_diagnostics.csv',logs);E.js(art/'fold_records.json',records);E.js(art/'progress.json',{'at_utc':E.now(),'completed_fold':k})
  s=pd.concat(parts).sort_index();s.to_pickle(art/'scores.pkl')
  ck('all_eligible_scored_once',len(s)==len(d) and s.row_id.is_unique and set(s.row_id)==set(d.row_id))
  ck('count_row_totals',int(s.groupby('count',observed=True).size().sum())==len(d))
  metrics={'n':len(s),'support':int(s.support.sum()),'coverage':float(s.support.mean()),'games':int(s.game_pk.nunique()),'MSE':float(np.square(s.Y-np.where(s.A.eq(1),s.mu1,s.mu0)).mean()),'Brier':float(np.square(s.A-s.p).mean()),'all_fit_converged':all(x['converged'] for x in logs),'fit_logs':len(logs),'policy_learning':False}
  E.js(art/'metrics.json',metrics);E.js(art/'basic_checks.json',{'status':'PASS','checks':checks,'scope':'Production basic checks, not independent full review'})
  m.update(status='COMPLETE',model_status='EXPERIMENTAL',finished_at_utc=E.now(),metrics=metrics,outputs=[E.meta(p) for p in sorted(art.rglob('*')) if p.is_file()]);E.js(run/'manifest.json',m)
  (run/'README.md').write_text(f"# {a.run_id}\n\nCOMPLETE · {c['model_id']} · EXPERIMENTAL. 2024·2025 개발 결과, 외부 검증 미실시.\n",encoding='utf-8')
  print(E.now(),'COMPLETE',json.dumps(metrics),flush=True)
 except Exception:
  m.update(status='FAILED',finished_at_utc=E.now(),error=traceback.format_exc());E.js(run/'manifest.json',m);E.js(art/'basic_checks.json',{'status':'FAIL','checks':checks,'error':m['error']});raise
if __name__=='__main__':main()
