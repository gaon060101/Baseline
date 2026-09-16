"""Reuse old/new OOF scores once for the prespecified own/common comparisons."""
from pathlib import Path
import argparse,sys,shutil,traceback
import numpy as np
import pandas as pd
import engine as E
ROOT=Path(__file__).resolve().parents[4];CODE=Path(__file__).parent;AN=ROOT/'columns/001-ball-count/analysis'
COUNTS=[f'{b}-{s}' for b in range(4) for s in range(3)]
KEY=['game_pk','at_bat_number','pitch_number']
NAMES={'NO_SUPPORT':'비교 표본·겹침 부족','UNSTABLE':'추정 방식·연도·분할 불안정','SMALL_RANGE':'설정 범위 안 작은 차이','CONSISTENT_DEVELOPMENT':'개발자료 내 일관된 방향','UNCERTAIN':'차이 크기·방향 불확실'}

def stats(whole,selected,c,family):
 d=whole[selected];n=len(d);nall=len(whole);own=int(whole.support.sum())
 r={'n_all':nall,'n':n,'own_n':own,'coverage':n/nall if nall else 0,'common_over_own':n/own if own else 0,'games':int(d.game_pk.nunique()),'PA':len(d[KEY[:2]].drop_duplicates()),'pitchers':int(d.pitcher.nunique()),'batters':int(d.batter.nunique()),'action1_rate_all':float(whole.A.mean()),'action1_rate':float(d.A.mean())}
 for ar in [0,1]:
  pp=d.p.to_numpy() if ar else 1-d.p.to_numpy();w=d.A.eq(ar).to_numpy()/pp;wg=pd.Series(w).groupby(d.game_pk.to_numpy()).sum();pos=w[w>0]
  r.update({f'rows{ar}':int(d.A.eq(ar).sum()),f'all_rows{ar}':int(whole.A.eq(ar).sum()),f'games{ar}':int(d.loc[d.A.eq(ar),'game_pk'].nunique()),f'ESS{ar}':float(w.sum()**2/np.square(w).sum()) if len(pos) else 0.,f'max_game_share{ar}':float(wg.max()/wg.sum()) if len(pos) else 1.,f'max_weight{ar}':float(w.max()) if len(w) else 0.,f'weight_p99_{ar}':float(np.quantile(pos,.99)) if len(pos) else np.nan,f'naive{ar}':float(d.loc[d.A.eq(ar),'Y'].mean()),f'gcomp{ar}':float(d['mu'+str(ar)].mean()),f'Q{ar}':float(d['phi'+str(ar)].mean())})
 reasons=[]
 if n<c['min_rows']:reasons.append('n<500')
 if min(r['ESS0'],r['ESS1'])<c['min_ess']:reasons.append('armESS<200')
 if min(r['games0'],r['games1'])<c['min_arm_games']:reasons.append('armGames<100')
 if r['coverage']<c['min_coverage']:reasons.append('coverage<.5')
 if max(r['max_game_share0'],r['max_game_share1'])>c['max_game_share']:reasons.append('maxGameShare>.05')
 st=E.cluster_stat(d,d.phi1-d.phi0,family)
 r.update(delta=st[0],SE=st[1],nominal95_low=st[2],nominal95_high=st[3],adjusted95_low=st[4],adjusted95_high=st[5],family=family,support_gate=not reasons,support_reasons=';'.join(reasons),naive_delta=r['naive1']-r['naive0'],gcomp_delta=r['gcomp1']-r['gcomp0'],correction0=r['Q0']-r['gcomp0'],correction1=r['Q1']-r['gcomp1'])
 r['correction_delta']=r['delta']-r['gcomp_delta'];r['raw_gcomp_flip']=r['naive_delta']*r['gcomp_delta']<0;r['gcomp_aipw_flip']=r['gcomp_delta']*r['delta']<0
 return r

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bundle',required=True);a=ap.parse_args();b=ROOT/a.bundle;plan=E.read(b/'analysis_plan.json');c=E.read(CODE/'specification.yaml')
 run=AN/'runs'/plan['comparison_run'];assert not run.exists();art=run/'artifacts';art.mkdir(parents=True)
 for name in ['engine.py','compare.py','specification.yaml']:shutil.copy2(CODE/name,art/('frozen_'+name))
 for x in E.read(b/'plan_seal.json')['files']:assert E.sha(ROOT/x['path'])==x['sha256']
 oldrun=AN/'runs'/plan['old_run'];newrun=AN/'runs'/plan['new_run'];newman=E.read(newrun/'manifest.json');assert newman['status']=='COMPLETE'
 m={'run_id':plan['comparison_run'],'model_id':'BCAP-PITCH-FF-v0.1.0','version':'0.1.0','model_status':'DRAFT','status':'RUNNING','scope':'Saved-score development comparison, no model fitting','started_at_utc':E.now(),'models':['BCAP-PITCH-v0.2.0','BCAP-PITCH-FF-v0.1.0'],'plan':E.meta(b/'analysis_plan.json'),'configuration':c,'code':[E.meta(CODE/x) for x in ['engine.py','compare.py']],'environment':E.environment(),'command':[sys.executable]+sys.argv,'inputs':[E.meta(p) for p in [oldrun/'artifacts/scores.pkl',oldrun/'artifacts/count_values.csv',newrun/'artifacts/scores.pkl']],'model_fits':0,'external_evaluations':0}
 E.js(run/'manifest.json',m);E.js(b/'result_access_log.json',{'old_results':'Viewed before extension plan, source attribution only.','new_FF_first_aggregate_access_at_utc':E.now(),'plan_sealed_at_utc':E.read(b/'plan_seal.json')['sealed_at_utc'],'notice':'New FF score summaries first computed by this comparison run; fitting generated row scores earlier as recorded in training manifest.'})
 checks=[]
 def ck(n,v):
  checks.append({'check':n,'status':'PASS' if v else 'FAIL'})
  if not v:raise AssertionError(n)
 try:
  f=pd.read_pickle(newrun/'artifacts/scores.pkl').set_index('row_id').sort_index()
  o=pd.read_pickle(oldrun/'artifacts/scores.pkl').set_index('row_id').sort_index()
  ck('identical_eligible_row_ids',o.index.equals(f.index) and o.index.is_unique)
  ck('keys_year_count_fold_Y_equal',o[KEY+['game_year','count','fold','Y']].equals(f[KEY+['game_year','count','fold','Y']]))
  ck('two_actions_from_correct_codes',f.A.eq(f.pitch_type.eq('FF')).all() and o.A.eq(f.pitch_type.isin(['FF','SI','FC'])).all())
  o['pitch_type']=f.pitch_type;cm=o.support&f.support
  for d in [o,f]:d['common_support']=cm
  membership=o[KEY+['game_year','count','fold']].copy();membership['support_FB']=o.support;membership['support_FF']=f.support;membership['common_support']=cm;membership.to_pickle(art/'comparison_membership.pkl')
  primary=[];aux=[];composition=[];propensity=[];calibration=[];exclusion=[]
  old_counts=pd.read_csv(oldrun/'artifacts/count_values.csv').set_index('count')
  for scheme,s in [('FB',o),('FF',f)]:
   for count in COUNTS:
    whole=s[s['count'].eq(count)]
    for ar,g in whole.groupby('A',observed=True):
     for selection,mask in [('all',pd.Series(True,index=g.index)),('own',g.support),('common',g.common_support)]:
      gg=g[mask];p=gg.p
      propensity.append(dict(scheme=scheme,count=count,action=int(ar),population=selection,n=len(gg),p_min=p.min(),p01=p.quantile(.01),p05=p.quantile(.05),p50=p.quantile(.5),p95=p.quantile(.95),p99=p.quantile(.99),p_max=p.max(),below005=float(p.lt(.05).mean()),above095=float(p.gt(.95).mean())))
    for bin,g in whole.groupby(pd.cut(whole.p,np.linspace(0,1,11),include_lowest=True),observed=True):calibration.append(dict(scheme=scheme,count=count,bin=str(bin),n=len(g),mean_p=g.p.mean(),actual1=g.A.mean(),Brier=np.square(g.A-g.p).mean()))
    reasons=np.select([~whole.repertoire,~whole.p.between(.05,.95)],['training_action_support','propensity_tail'],default='supported')
    for reason,n in pd.Series(reasons).value_counts().items():exclusion.append(dict(scheme=scheme,count=count,reason=reason,n=int(n)))
    for pop in ['own','common']:
     mask=whole.support if pop=='own' else whole.common_support
     r=stats(whole,mask,c,255);r.update(scheme=scheme,population=pop,count=count,action1='FB' if scheme=='FB' else 'FF',action0='NFB' if scheme=='FB' else 'non-FF')
     if scheme=='FB' and pop=='own':
      legacy=old_counts.loc[count];oldst=E.cluster_stat(whole[mask],whole.loc[mask,'phi1']-whole.loc[mask,'phi0'],219)
      ck(count+'_reuse_old_no_refit_values',np.allclose([r['Q0'],r['Q1'],r['delta'],r['SE'],oldst[4],oldst[5]],[legacy.Q0,legacy.Q1,legacy.delta,legacy.SE,legacy.family95_low,legacy.family95_high],atol=1e-12,rtol=0) and r['n']==legacy.n)
      r.update(legacy219_low=legacy.family95_low,legacy219_high=legacy.family95_high,legacy_evidence=legacy.evidence)
     primary.append(r)
     selected=whole[mask]
     for code,g in selected.groupby('pitch_type',observed=True):composition.append(dict(scheme=scheme,population=pop,count=count,pitch_type=str(code),component=str(code) if code in ['FF','SI','FC'] else 'legacy_NFB',action=int(g.A.iloc[0]),n=len(g),fraction_of_selected=len(g)/len(selected)))
     for level,levels in [('year',[2024,2025]),('fold',[0,1,2])]:
      col='game_year' if level=='year' else 'fold'
      for value in levels:
       wh=whole[whole[col].eq(value)];ma=wh.support if pop=='own' else wh.common_support;ar=stats(wh,ma,c,1);ar.update(scheme=scheme,population=pop,count=count,level=level,value=value,interval_role='individual nominal95; development descriptive only');aux.append(ar)
  pr=pd.DataFrame(primary);au=pd.DataFrame(aux);margin=.01
  for i,r in pr.iterrows():
   ss=au[au.scheme.eq(r.scheme)&au.population.eq(r.population)&au['count'].eq(r['count'])]
   supported=ss[ss.support_gate]
   method_material=r.gcomp_delta*r.delta<0 and min(abs(r.gcomp_delta),abs(r.delta))>=margin
   subgroup_material=any(len(g) and g.delta.min()<=-margin and g.delta.max()>=margin for _,g in supported.groupby('level'))
   same_sign=len(supported)==5 and bool((supported.delta*r.delta>0).all())
   year_flip=any(g.delta.min()<0<g.delta.max() for _,g in supported[supported.level.eq('year')].groupby('level'))
   fold_flip=any(g.delta.min()<0<g.delta.max() for _,g in supported[supported.level.eq('fold')].groupby('level'))
   excludes=r.adjusted95_low>0 or r.adjusted95_high<0
   small=r.adjusted95_low>=-margin and r.adjusted95_high<=margin
   consistent=excludes and abs(r.delta)>=margin and same_sign and not method_material
   category='NO_SUPPORT' if not r.support_gate else 'UNSTABLE' if method_material or subgroup_material else 'SMALL_RANGE' if small else 'CONSISTENT_DEVELOPMENT' if consistent else 'UNCERTAIN'
   reasons=[]
   if not r.support_gate:reasons.append(r.support_reasons)
   if r.gcomp_aipw_flip:reasons.append('결과모형/AIPW 부호 반전')
   if year_flip:reasons.append('연도별 부호 차이')
   if fold_flip:reasons.append('분할별 부호 차이')
   if method_material or subgroup_material:reasons.append('±0.01W 이상 실질 반전')
   if small:reasons.append('보정 구간 전체가±0.01W 안')
   if not small and abs(r.delta)<margin:reasons.append('점추정 작지만 작은 차이 확정 범위 아님')
   nominal_excludes=r.nominal95_low>0 or r.nominal95_high<0
   if nominal_excludes and not excludes:reasons.append('개별 구간 방향은 있으나 다중비교 보정 후 보류')
   elif not excludes:reasons.append('구간이0 포함')
   if len(supported)<5:reasons.append(f'연도/fold 중 {5-len(supported)}개 지원 미달')
   if consistent:reasons.append('보정 구간0 배제·연도2/fold3 동일 방향')
   pr.loc[i,'category']=category;pr.loc[i,'judgment']=NAMES[category];pr.loc[i,'reason']='; '.join(reasons)
   pr.loc[i,'point_direction']=r.action1 if r.delta<0 else r.action0 if r.delta>0 else '동률'
   pr.loc[i,'all_subgroups_supported']=len(supported)==5;pr.loc[i,'subgroup_sign_consistent']=same_sign
   pr.loc[i,'material_instability']=method_material or subgroup_material
   pr.loc[i,'interval_beyond_practical_margin']=r.adjusted95_low>margin or r.adjusted95_high<-margin
   if not r.support_gate:pr.loc[i,'point_direction']='보류'
  ck('48_primary_240_aux',len(pr)==48 and len(au)==240)
  ck('all_action_denominators',pr.rows0.add(pr.rows1).eq(pr.n).all() and au.rows0.add(au.rows1).eq(au.n).all())
  ck('same_common_denominators',pr[pr.population.eq('common')].groupby('count').n.nunique().eq(1).all())
  ck('Q_delta_arithmetic',np.allclose(pr.Q1-pr.Q0,pr.delta,rtol=0,atol=1e-12))
  ck('finite_primary_scores',np.isfinite(pr[['delta','SE','Q0','Q1']]).all().all())
  ck('all_primary_sample_counts',all(int(g.n_all.sum())==len(o) for _,g in pr.groupby(['scheme','population'])))
  comp=pd.DataFrame(composition)
  ck('composition_counts',all(int(comp[comp.scheme.eq(r.scheme)&comp.population.eq(r.population)&comp['count'].eq(r['count'])].n.sum())==r.n for _,r in pr.iterrows()))
  ck('aux_aggregates_match_primary',all(int(au[au.scheme.eq(r.scheme)&au.population.eq(r.population)&au['count'].eq(r['count'])&au.level.eq(level)].n.sum())==r.n for _,r in pr.iterrows() for level in ['year','fold']))
  for name,data in [('primary_values',pr),('year_fold_values',au),('pitch_composition',comp),('propensity_by_count_action',propensity),('calibration',calibration),('support_exclusions',exclusion)]:E.csv(art/(name+'.csv'),data)
  wide=pr.pivot(index='count',columns=['population','scheme'],values=['delta','adjusted95_low','adjusted95_high','n','coverage','ESS0','ESS1','judgment','reason']);wide.columns=['__'.join(x) for x in wide.columns];wide=wide.reindex(COUNTS);E.csv(art/'comparison_12counts.csv',wide.reset_index())
  E.js(art/'basic_checks.json',{'status':'PASS','checks':checks,'scope':'Production saved-score aggregation checks; no independent verifier or refit'})
  summary={'rows_eligible':len(o),'FB_own':int(o.support.sum()),'FF_own':int(f.support.sum()),'common':int(cm.sum()),'FB_only':int((o.support&~f.support).sum()),'FF_only':int((f.support&~o.support).sum()),'neither':int((~o.support&~f.support).sum()),'family':255,'category_counts':pr.groupby(['scheme','population','category']).size().rename('n').reset_index().to_dict('records')}
  E.js(art/'summary.json',summary)
  m.update(status='COMPLETE',model_status='EXPERIMENTAL',finished_at_utc=E.now(),summary=summary,outputs=[E.meta(p) for p in sorted(art.iterdir()) if p.is_file()]);E.js(run/'manifest.json',m)
  (run/'README.md').write_text(f"# {plan['comparison_run']}\n\nCOMPLETE · 저장 점수 재집계 · 외부 검증 미실시.\n",encoding='utf-8')
  print(E.now(),'COMPLETE',pr[['scheme','population','count','delta','judgment']].to_json(orient='records',force_ascii=True),flush=True)
 except Exception:
  m.update(status='FAILED',finished_at_utc=E.now(),error=traceback.format_exc());E.js(run/'manifest.json',m);raise
if __name__=='__main__':main()
