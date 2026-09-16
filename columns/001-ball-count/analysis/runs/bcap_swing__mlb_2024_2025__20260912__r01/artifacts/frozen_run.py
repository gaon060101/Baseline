"""V2 development only: three game folds, reused nuisance/AIPW, basic production checks."""
from pathlib import Path
import sys,json,datetime,argparse,pickle,traceback,shutil
import numpy as np
import pandas as pd
import engine as E
ROOT=Path(__file__).resolve().parents[4];COL=ROOT/'columns/001-ball-count';AN=COL/'analysis';CODE=Path(__file__).resolve().parent
COUNTS=[f'{b}-{s}' for b in range(4) for s in range(3)]
REGIONS=['HIGH','LOW','INSIDE','OUTSIDE','CENTER']
NAMES={'HIGH':'상(높음)','LOW':'하(낮음)','INSIDE':'좌(몸쪽)','OUTSIDE':'우(바깥쪽)','CENTER':'가운데(존 안)'}
KEY=['game_pk','at_bat_number','pitch_number']
def regions(d):
 valid=np.isfinite(d[['plate_x','plate_z','sz_top','sz_bot']].to_numpy(dtype=float)).all(axis=1)&d.sz_top.gt(d.sz_bot).to_numpy()
 x=d.plate_x*np.where(d.stand.eq('R'),1,np.where(d.stand.eq('L'),-1,np.nan))
 return {'CENTER':valid & d.plate_x.abs().le(17/24) & d.plate_z.ge(d.sz_bot) & d.plate_z.le(d.sz_top),'HIGH':valid & d.plate_z.gt(d.sz_top),'LOW':valid & d.plate_z.lt(d.sz_bot),'INSIDE':valid & x.lt(-17/24),'OUTSIDE':valid & x.gt(17/24)}
def make_groups(s,model):
 yield 'overall','ALL','ALL','ALL',s
 for count in COUNTS:
  sub=s[s['count'].eq(count)];yield 'count',count,'ALL','ALL',sub
  if model=='swing':
   for region in REGIONS:
    z=sub[sub['region_'+region]];yield 'region',count,region,'ALL',z
    for group in ['FB','NFB']:yield 'region_pitch',count,region,group,z[z.pitch_group.eq(group)]
def summarize(s,c):
 rows=[]
 for level,count,region,pitchgroup,whole in make_groups(s,c['variant']):
  d=whole[whole.support];n=len(d);nall=len(whole)
  base=dict(level=level,count=count,region=region,region_name=NAMES.get(region,region),pitch_group=pitchgroup,n_all=nall,n=n,coverage=n/nall if nall else np.nan,games=d.game_pk.nunique(),PA=d[KEY[:2]].drop_duplicates().shape[0],pitchers=d.pitcher.nunique(),batters=d.batter.nunique(),action1_rate_all=whole.A.mean(),action1_rate=d.A.mean(),action0_rate_all=1-whole.A.mean(),action0_rate=1-d.A.mean(),observed_Y=d.Y.mean(),action0=c['action0'],action1=c['action1'])
  for a in [0,1]:
   aw=d.A.eq(a).astype(float)/(d.p if a else 1-d.p)
   ss=float(np.square(aw).sum());weightgames=aw.groupby(d.game_pk).sum()
   base[f'rows{a}']=int(d.A.eq(a).sum());base[f'ESS{a}']=float(aw.sum()**2/ss) if ss else 0.
   base[f'games{a}']=d.loc[d.A.eq(a),'game_pk'].nunique();base[f'max_game_share{a}']=float(weightgames.max()/weightgames.sum()) if weightgames.sum() else np.nan
  sufficient=(n>=c['min_rows'] and min(base['ESS0'],base['ESS1'])>=c['min_ess'] and min(base['games0'],base['games1'])>=c['min_arm_games'] and base['coverage']>=c['min_coverage'] and max(base['max_game_share0'],base['max_game_share1'])<=c['max_game_share'])
  if n:
   st=E.cluster_stat(d,d.phi1-d.phi0,c['comparison_family'])
   raw=c['action1'] if (st[0]>0 if c['better']=='higher' else st[0]<0) else c['action0'] if st[0]!=0 else 'TIE'
   base.update(Q0=float(d.phi0.mean()),Q1=float(d.phi1.mean()),gcomp0=float(d.mu0.mean()),gcomp1=float(d.mu1.mean()),delta=st[0],SE=st[1],nominal95_low=st[2],nominal95_high=st[3],family95_low=st[4],family95_high=st[5],arithmetic_direction=raw,point_direction=raw if sufficient else None,evidence='비교 자료 부족' if not sufficient else '차이 불명확' if st[4]<=0<=st[5] else '관찰상 방향 뚜렷',large_point_difference=abs(st[0])>=c['practical_delta_W'])
  else:base.update(Q0=np.nan,Q1=np.nan,delta=np.nan,point_direction=None,evidence='비교 자료 부족')
  base.update(support_gate=bool(sufficient),recommendation=None,unit='W per selected current decision; not PA sum')
  if level.startswith('region'):
   countbase=s[s['count'].eq(count)]
   base['fraction_of_count_all']=nall/len(countbase) if len(countbase) else np.nan
  rows.append(base)
 return pd.DataFrame(rows)
def develop(model,runid):
 version='0.1.0' if model=='pitch_sb' else '0.2.0';definition=ROOT/f'models/bcap/{model}/v{version}/specification.yaml';c=E.read(definition)
 day=datetime.datetime.now().strftime('%Y%m%d');bundle=AN/f'bcap_v2_development_{day}__r01'
 prep=E.read(bundle/'preparation/preparation.json');inputpath=ROOT/prep['output']['path']
 run=AN/'runs'/runid;assert not run.exists();art=run/'artifacts';art.mkdir(parents=True)
 for p in [CODE/'engine.py',Path(__file__),CODE/'prepare.py',definition]:shutil.copyfile(p,art/('frozen_'+p.name))
 m=dict(run_id=runid,model_id=c['model_id'],version=c['version'],model_status='DRAFT',status='RUNNING',scope='2024/2025 development only; no policy learning or external evaluation',started_at_utc=E.now(),configuration=c,input=prep['output'],input_preparation=E.meta(bundle/'preparation/preparation.json'),definition=E.meta(definition),code=[E.meta(CODE/'engine.py'),E.meta(Path(__file__))],environment=E.environment(),command=[sys.executable]+sys.argv,external_evaluations=0,bootstrap_replicates=0,independent_review='NOT_RUN')
 E.js(run/'manifest.json',m);checks=[]
 def ck(name,ok,detail=''):
  checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=detail))
  if not ok:raise AssertionError(name)
 try:
  d=pd.read_pickle(inputpath);ck('only2024_2025',set(d.game_year.unique())=={2024,2025})
  d=d[d['eligible_'+model]].copy();d['A']=d['A_'+model].astype(int);d=E.features(d,c).reset_index(drop=True)
  ck('unique_keys',not d.duplicated(KEY).any());ck('binary_action_complete',d.A.isin([0,1]).all())
  ck('finite_outcome',np.isfinite(d.Y).all());ck('valid_count',d['count'].isin(COUNTS).all())
  forbidden={'pitch_type','prev_pitch_type','description','events','Y','result','final_event','des','inplay_bunt_text_flag','A','A_swing','A_pitch','A_pitch_sb'}
  if model!='swing':forbidden|={'release_speed','release_speed_bin','pfx_x','pfx_z','pfx_x_bin','pfx_z_bin','plate_x','plate_z','plate_x_bin','relative_z_bin','zone','swing_cell','sz_top','sz_bot'}
  if model=='pitch':forbidden.add('pitch_group')
  ck('allowed_predictors',not set(c['features'])&forbidden,{'features':c['features']})
  ck('coarse_lag_only',set(d.prev_pitch_group.astype(str))<= {'FB','NFB','START','MISSING_PREVIOUS','UNCLASSIFIED'})
  reg=regions(d)
  ck('known_stand_for_side_reports',d.stand.isin(['R','L']).all())
  ck('overlapping_regions_max_two',np.stack([np.asarray(v) for v in reg.values()]).sum(axis=0).max()<=2)
  ck('center_equals_geometric_SB',np.array_equal(np.asarray(reg['CENTER']),d.A_pitch_sb.fillna(0).eq(1).to_numpy()))
  fd=E.folds(d,c['outer_folds'],c['seed'])
  membership=d[['row_id']+KEY+['game_year','A']].copy();membership['fold']=fd;E.csv(art/'fold_membership.csv',membership)
  ck('one_fold_per_game',membership.groupby('game_pk').fold.nunique().eq(1).all())
  logs=[];records=[];tuning=[];parts=[];E.SAVE_DIR=art/'fits'
  for k in range(c['outer_folds']):
   tr=d[fd!=k];te=d[fd==k];label='fold'+str(k);E.split_record(records,label,'development_oof',tr,te)
   print(E.now(),model,label,'fitting',len(tr),'evaluating',len(te),flush=True)
   nu,tu=E.nuisance(tr,c,label,c['seed']+2000+k,logs,records,frozen_alpha=c['fixed_alpha']);tuning.extend(tu)
   fitpath=art/'fits'/label/'nuisance.pkl';fitpath.parent.mkdir(parents=True,exist_ok=True)
   with fitpath.open('wb') as f:pickle.dump(nu,f,protocol=5)
   sc=E.score(te,nu.predict(te,c),c);sc['row_id']=te.row_id;sc['fold']=k;sc['known_count_exception']=te.known_count_exception
   for name,flag in reg.items():sc['region_'+name]=np.asarray(flag)[fd==k]
   ck(label+'_finite_predictions',np.isfinite(sc[['p','mu0','mu1','phi0','phi1']].to_numpy()).all())
   ck(label+'_convergence',all(x['converged'] for x in logs));ck(label+'_no_game_leak',not set(tr.game_pk)&set(te.game_pk))
   parts.append(sc);E.js(art/'progress.json',dict(at_utc=E.now(),completed_fold=k,fit_count=len(logs)))
   E.csv(art/'fit_diagnostics.csv',logs);E.js(art/'fold_records.json',records)
  s=pd.concat(parts).sort_index();s.to_pickle(art/'scores.pkl');summary=summarize(s,c);E.csv(art/'action_values.csv',summary)
  for level in summary.level.unique():E.csv(art/(level+'_values.csv'),summary[summary.level.eq(level)])
  ck('OOF_rows_complete_unique',len(s)==len(d) and not s.duplicated(KEY).any())
  ck('same_action_denominator',summary.rows0.add(summary.rows1).eq(summary.n).all())
  ck('Q_difference_sign',np.allclose(summary.Q1-summary.Q0,summary.delta,atol=1e-12,equal_nan=True))
  ck('count_sum_matches_overall',int(summary.loc[summary.level.eq('count'),'n'].sum())==int(s.support.sum()) and int(summary.loc[summary.level.eq('count'),'n_all'].sum())==len(s))
  ck('finite_supported_group_values',np.isfinite(summary.loc[summary.n.gt(0),['Q0','Q1','delta','SE','family95_low','family95_high']].to_numpy()).all())
  # Confirm all nested calibration/tuning roles stay inside their top-level training games.
  for k in range(3):
   hold=set(d.loc[fd==k,'game_pk'])
   for rec in records:
    if rec['fit_id'].startswith(f'fold{k}/'):ck(rec['fit_id']+'_outer_ancestor_exclusion',not hold&(set(rec['train_games'])|set(rec['evaluation_games'])))
  E.csv(art/'tuning.csv',tuning)
  cal=[]
  for name,g in s.groupby(pd.cut(s.p,np.linspace(0,1,11),include_lowest=True),observed=True):cal.append(dict(bin=str(name),n=len(g),mean_p=g.p.mean(),actual1=g.A.mean(),Brier=np.square(g.A-g.p).mean()))
  E.csv(art/'calibration.csv',cal)
  prop=[]
  for a in [0,1]:
   p=s.p if a else 1-s.p;w=s.A.eq(a)/p;positive=w[w>0]
   prop.append(dict(action=a,n=int(s.A.eq(a).sum()),p01=p.quantile(.01),p05=p.quantile(.05),p50=p.quantile(.5),p95=p.quantile(.95),p99=p.quantile(.99),max_weight=w.max(),weight_gt10_rate=(positive>10).mean(),weight_gt20_rate=(positive>20).mean()))
  E.csv(art/'propensity_summary.csv',prop)
  reason=np.select([~s.measurement_support,~s.repertoire,~s.p.between(c['trim'],1-c['trim'])],['measurement','entity_arm_training','propensity_tail'],default='supported')
  exclusions=s.assign(support_reason=reason).groupby(['game_year','count','A','support_reason'],observed=True).size().rename('rows').reset_index();E.csv(art/'support_exclusions.csv',exclusions)
  ck('support_reason_sum',int(exclusions.rows.sum())==len(s))
  region_audit=[]
  if model=='swing':
   for count,g in s.groupby('count',observed=True):
    copies=g[['region_'+r for r in REGIONS]].sum(axis=1)
    region_audit.append(dict(count=str(count),unique_rows=len(g),assigned_unique_rows=int(copies.gt(0).sum()),overlap_rows=int(copies.eq(2).sum()),membership_total=int(copies.sum()),unassigned=int(copies.eq(0).sum())))
   E.csv(art/'region_overlap_counts.csv',region_audit)
   ck('region_overlap_sum_identity',all(x['membership_total']==x['assigned_unique_rows']+x['overlap_rows'] for x in region_audit))
  metrics=dict(n=len(s),support=int(s.support.sum()),games=int(s.game_pk.nunique()),coverage=float(s.support.mean()),Y_mean=float(s.Y.mean()),MSE=float(np.square(s.Y-np.where(s.A.eq(1),s.mu1,s.mu0)).mean()),Brier=float(np.square(s.A-s.p).mean()),logloss=float(-np.mean(s.A*np.log(s.p)+(1-s.A)*np.log1p(-s.p))),all_fit_converged=all(x['converged'] for x in logs),fit_logs=len(logs),families_planned=c['comparison_family'],displayed_delta_groups=len(summary),policy_learning=False)
  E.js(art/'metrics.json',metrics);E.js(art/'basic_checks.json',dict(status='PASS',checks=checks,scope='Production basic checks only; not independent validation',not_run=c['not_run']))
  m.update(status='COMPLETE',model_status='EXPERIMENTAL',finished_at_utc=E.now(),metrics=metrics,fit_preservation='All3 crossfit nuisance objects include coefficients/dictionaries/calibrator and calibration row scores; all SB tuning Ridge fits saved. Shared row_id/fold membership and game split records identify training rows. No final all-development fit or learned policy exists because not required for diagnostic target.',outputs=[E.meta(p) for p in sorted(art.rglob('*')) if p.is_file()]);E.js(run/'manifest.json',m)
  (run/'README.md').write_text(f"# {runid}\n\nCOMPLETE · {c['model_id']} · EXPERIMENTAL. 2024·2025 개발 결과 산출, 후속 검증 미실시.\n",encoding='utf-8')
  print(E.now(),'COMPLETE',runid,json.dumps(metrics),flush=True)
 except Exception:
  E.js(art/'basic_checks.json',dict(status='FAIL',checks=checks,error=traceback.format_exc()));m.update(status='FAILED',error=traceback.format_exc(),finished_at_utc=E.now());E.js(run/'manifest.json',m);raise
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',choices=['pitch','pitch_sb','swing'],required=True);p.add_argument('--run-id',required=True);a=p.parse_args();develop(a.model,a.run_id)
if __name__=='__main__':main()
