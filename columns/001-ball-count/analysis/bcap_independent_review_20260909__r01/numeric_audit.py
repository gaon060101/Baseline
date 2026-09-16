"""Fresh independent saved-score audit. No producer modules imported; no fitting.
OPE uses a factual-residual expression; cluster variance uses grouped sums/counts.
Writes exclusively next to this file. See predeclared review_protocol.json.
"""
from pathlib import Path
import sys,json,datetime,hashlib,platform
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'columns/001-ball-count/analysis/runtime_ridge_v02'))
from scipy.stats import t
OUT=HERE/'numeric';OUT.mkdir(exist_ok=True)
RUNS=ROOT/'columns/001-ball-count/analysis/runs'
IDS=['bcap_pitch__mlb_2024_2025__20260909__r02','bcap_swing__mlb_2024_2025__20260909__r01','bcap_pitch__mlb_2023__20260909__r01','bcap_swing__mlb_2023__20260909__r01','bcap_pitch__mlb_2026_ytd_20260907__20260909__r01']
START=datetime.datetime.now(datetime.timezone.utc).isoformat()
CHECKS=[];BAD=[];INPUTS=set();SUMMARIES=[]
def read(p):
 INPUTS.add(Path(p));return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def frame(p):
 INPUTS.add(Path(p));return pd.read_pickle(p) if str(p).endswith('.pkl') else pd.read_csv(p)
def compare(tag,a,b,kind='value'):
 a=np.asarray(a);b=np.asarray(b)
 if a.shape!=b.shape:
  BAD.append(dict(check=tag,error='shape',actual=str(a.shape),expected=str(b.shape)));CHECKS.append(dict(check=tag,n=0,bad=1));return
 if kind=='exact':
  eq=(a==b)|(pd.isna(a)&pd.isna(b));diff=np.zeros(a.shape);rel=diff
 else:
  a=a.astype(float);b=b.astype(float)
  atol,rtol={'value':(1e-10,1e-9),'ci':(1e-9,1e-8),'ess':(1e-6,1e-9)}[kind]
  eq=np.isclose(a,b,atol=atol,rtol=rtol,equal_nan=True)
  with np.errstate(invalid='ignore',divide='ignore'):
   diff=np.abs(a-b);rel=diff/np.maximum(np.abs(b),1e-15)
  diff=np.nan_to_num(diff,nan=0,posinf=float('inf'));rel=np.nan_to_num(rel,nan=0,posinf=float('inf'))
 nbad=int(np.size(eq)-np.sum(eq));CHECKS.append(dict(check=tag,n=int(a.size),bad=nbad,max_absolute_error=float(np.max(diff,initial=0)),max_relative_error=float(np.max(rel,initial=0)),tolerance=kind))
 for i in np.flatnonzero(~eq)[:20]:BAD.append(dict(check=tag,index=int(i),actual=str(a.ravel()[i]),expected=str(b.ravel()[i])))
def tabcheck(name,actual,path,keys):
 actual=pd.DataFrame(actual);expected=frame(path)
 compare(name+'/row_count',len(actual),len(expected),'exact')
 if actual.empty:return
 aa=actual.set_index(keys).sort_index();bb=expected.set_index(keys).sort_index()
 compare(name+'/keys',np.array([str(x) for x in aa.index]),np.array([str(x) for x in bb.index]),'exact')
 if not aa.index.equals(bb.index):return
 for col in bb.columns:
  if col not in aa: compare(name+'/'+col,np.full(len(aa),np.nan),bb[col]);continue
  kind='exact' if col in ['n','n_all','games','PA','pitchers','batters','n_arm','arm_games0','arm_games1','grade','reason','suggested_action','candidate_direction','different_target','clusters','conditional','unit','players_pitcher','players_batter'] else 'ess' if 'ESS' in col else 'ci' if col=='se' or 'low' in col or 'high' in col else 'value'
  compare(name+'/'+col,aa[col],bb[col],kind)
 actual.to_csv(OUT/(name.replace('/','__')+'.csv'),index=False)
def ope(d,prob,p=None):
 p=d.p.to_numpy() if p is None else np.asarray(p)
 a=d.A.to_numpy();y=d.Y.to_numpy();m0=d.mu0.to_numpy();m1=d.mu1.to_numpy()
 factual=m0+a*(m1-m0)
 return m0+prob*(m1-m0)+(a*prob/p+(1-a)*(1-prob)/(1-p))*(y-factual)
def stat(d,values,cluster='game_pk'):
 values=np.asarray(values);n=len(values)
 if not n:return [np.nan]*7
 mean=values.mean();g=pd.DataFrame({'g':d[cluster].to_numpy(),'v':values}).groupby('g').v.agg(['sum','size'])
 G=len(g);center=g['sum'].to_numpy()-g['size'].to_numpy()*mean
 se=np.sqrt((G/max(G-1,1))*np.square(center).sum())/n
 z,zf=t.ppf([.975,1-.05/(2*1536)],max(G-1,1))
 return mean,se,mean-z*se,mean+z*se,mean-zf*se,mean+zf*se,G
def audit(run_id,fixed=False):
 model='swing' if 'swing' in run_id else 'pitch';art=RUNS/run_id/'artifacts'
 c=read(RUNS/run_id/'manifest.json')['configuration']
 s=frame(art/('fixed_development_predictions.pkl' if fixed else 'scores.pkl')).reset_index(drop=True)
 tag=run_id+('/fixed' if fixed else '/main');dest=art/'fixed_prediction_diagnostics' if fixed else art
 compare(tag+'/unique_keys',s[['game_pk','at_bat_number','pitch_number']].drop_duplicates().shape[0],len(s),'exact')
 compare(tag+'/numeric_complete',np.isfinite(s[['Y','A','p','mu0','mu1']].to_numpy()).all(),True,'exact')
 compare(tag+'/p_bounds',s.p.between(1e-6,1-1e-6).all(),True,'exact')
 compare(tag+'/A_binary',s.A.isin([0,1]).all(),True,'exact')
 if '2024_2025' in run_id and not fixed:
  policies=read(art/'outer_policies.json');dp=np.empty(len(s))
  for k,p in enumerate(policies):
   mask=s.fold.eq(k);dp[mask]=s.loc[mask,p['key']].astype(str).map({x:v['p1'] for x,v in p['states'].items()}).fillna(p['fallback_p1'])
 else:
  devid=IDS[1] if model=='swing' else IDS[0];p=read(RUNS/devid/'artifacts/final_policy.json')
  dp=s[p['key']].astype(str).map({x:v['p1'] for x,v in p['states'].items()}).fillna(p['fallback_p1']).to_numpy()
 compare(tag+'/policy_from_training_file',dp,s.policy_p1,'exact')
 q0=ope(s,0);q1=ope(s,1);vp=ope(s,dp)
 for name,vals in [('phi0',q0),('phi1',q1),('policy_value',vp),('conservative_value',s.Y)]:compare(tag+'/'+name,vals,s[name])
 compare(tag+'/conservative_H0',s.conservative_change,np.zeros(len(s),dtype=bool),'exact')
 compare(tag+'/support_predicate',s.measurement_support&s.repertoire&s.p.between(.05,.95),s.support,'exact')
 s['r0']=q0;s['r1']=q1;s['rv']=vp
 summaries=[];policiesout=[];props=[];sens=[]
 groups=[('overall','ALL',s)]+[('count',str(k),d) for k,d in s.groupby('count',observed=True)]
 if model=='swing':groups += [('cell',str(k),d) for k,d in s.groupby('swing_cell',observed=True)]
 for level,state,allrows in groups:
  d=allrows.loc[allrows.support];n=len(d)
  base=dict(level=level,state=state,n_all=len(allrows),n=n,coverage=n/len(allrows),games=d.game_pk.nunique(),PA=len(d[['game_pk','at_bat_number']].drop_duplicates()),pitchers=d.pitcher.nunique(),batters=d.batter.nunique(),action1_rate_all=allrows.A.mean(),action1_rate=d.A.mean())
  for arm in [0,1]:
   pa=allrows.p.to_numpy() if arm else 1-allrows.p.to_numpy();w=(allrows.A.to_numpy()==arm)/pa
   ps=d.p.to_numpy() if arm else 1-d.p.to_numpy();ws=(d.A.to_numpy()==arm)/ps;wp=w[w>0]
   ess=ws.sum()**2/np.square(ws).sum() if np.square(ws).sum() else 0.
   wg=pd.Series(ws).groupby(d.game_pk.to_numpy()).sum();share=wg.max()/wg.sum() if wg.sum() else np.nan
   base.update({f'ESS{arm}':ess,f'arm_games{arm}':d.loc[d.A.eq(arm),'game_pk'].nunique(),f'max_game_share{arm}':share})
   rec=dict(level=level,state=state,action=arm,n_arm=int(allrows.A.eq(arm).sum()),ESS_support=ess,ESS_untrimmed=w.sum()**2/np.square(w).sum() if np.square(w).sum() else 0.,weight_max=np.max(w),weight_gt10_rate=np.mean(wp>10) if len(wp) else np.nan,weight_gt20_rate=np.mean(wp>20) if len(wp) else np.nan,max_game_share=share)
   for quant in [0,.01,.05,.1,.5,.9,.95,.99,1]:rec['p_q'+str(quant)]=np.quantile(pa,quant);rec['positive_weight_q'+str(quant)]=np.quantile(wp,quant) if len(wp) else np.nan
   props.append(rec)
  if n:
   st=stat(d,d.r1-d.r0);base.update(Q0=d.r0.mean(),Q1=d.r1.mean(),gcomp0=d.mu0.mean(),gcomp1=d.mu1.mean(),delta=st[0],se=st[1],CI95_low=st[2],CI95_high=st[3],simultaneous95_low=st[4],simultaneous95_high=st[5])
   gate=(n>=500 and min(base['ESS0'],base['ESS1'])>=200 and min(base['arm_games0'],base['arm_games1'])>=100 and base['coverage']>=.5 and max(base['max_game_share0'],base['max_game_share1'])<=.05)
   base.update(grade='UNCERTAIN' if gate else 'NO_SUPPORT',reason='IDENTIFICATION_AND_FULL_LEARNING_UNCERTAINTY' if gate else 'SAMPLE_OR_OVERLAP_GATE',suggested_action=np.nan,candidate_direction=c['action1'] if (st[0]<0 if model=='pitch' else st[0]>0) else c['action0'])
   for name,prob in [('observed',None),('always_0',0),('always_1',1),('learned',dp[d.index]),('conservative',None),('stochastic_half',.5)]:
    v=d.Y.to_numpy() if prob is None else ope(d,prob)
    vs=stat(d,v);gs=stat(d,(v-d.Y.to_numpy())*(-1 if model=='pitch' else 1))
    policiesout.append(dict(level=level,state=state,policy=name,n=n,value=vs[0],CI95_low=vs[2],CI95_high=vs[3],gain=gs[0],gain_low=gs[4],gain_high=gs[5],unit='W per selected current decision; not summed PA value',conditional=True))
  else:base.update(grade='NO_SUPPORT',reason='NO_COMMON_SUPPORT',suggested_action=np.nan)
  summaries.append(base)
  masks={'untrimmed':allrows.measurement_support,'trim_002':allrows.measurement_support&allrows.repertoire&allrows.p.between(.02,.98),'trim_005':allrows.support,'trim_010':allrows.measurement_support&allrows.repertoire&allrows.p.between(.1,.9),'clip_010_same_target':allrows.support,'first_count_visit':allrows.support&~allrows.duplicated(['game_pk','at_bat_number','count'])}
  for setting,mask in masks.items():
   a=allrows[mask]
   if len(a):
    clipped=np.clip(a.p,.1,.9) if setting=='clip_010_same_target' else np.clip(a.p,1e-6,1-1e-6)
    qq0=ope(a,0,clipped);qq1=ope(a,1,clipped)
    sens.append(dict(level=level,state=state,setting=setting,n=len(a),coverage=len(a)/len(allrows),Q0=qq0.mean(),Q1=qq1.mean(),delta=(qq1-qq0).mean(),different_target=setting not in ['trim_005','clip_010_same_target']))
  if n:
   for cl in ['pitcher','batter']:
    st=stat(d,d.r1-d.r0,cl);sens.append(dict(level=level,state=state,setting='fixed_score_cluster_'+cl,n=n,delta=st[0],low=st[4],high=st[5],clusters=st[6],different_target=False))
 for name,rows,keys in [('action_values',summaries,['level','state']),('policy_values',policiesout,['level','state','policy']),('propensity_overlap',props,['level','state','action']),('sensitivity',sens,['level','state','setting'])]:tabcheck(tag+'/'+name,rows,dest/(name+'.csv'),keys)
 cal=[]
 for binid,d in s.groupby(pd.cut(s.p,np.linspace(0,1,11),include_lowest=True),observed=True):cal.append(dict(bin=str(binid),n=len(d),mean_p=d.p.mean(),observed_rate=d.A.mean(),Brier=np.square(d.A-d.p).mean()))
 tabcheck(tag+'/calibration',cal,dest/'calibration.csv',['bin'])
 group=np.select([s.known_pitcher&s.known_batter,s.known_pitcher&~s.known_batter,~s.known_pitcher&s.known_batter],['both_known','pitcher_known_batter_unseen','pitcher_unseen_batter_known'],default='both_unseen');known=[]
 for name,d in s.groupby(group):
  sup=d[d.support];known.append(dict(group=name,n=len(d),games=d.game_pk.nunique(),coverage=d.support.mean(),MSE=np.square(d.Y-(d.mu0+d.A*(d.mu1-d.mu0))).mean(),Brier=np.square(d.A-d.p).mean(),Q0=sup.r0.mean(),Q1=sup.r1.mean(),policy_value=sup.rv.mean()))
 tabcheck(tag+'/known_unseen',known,dest/'known_unseen.csv',['group'])
 status=np.select([~s.measurement_support,~s.repertoire,~s.p.between(.05,.95)],['measurement','entity_arm_training','propensity_tail'],default='supported')
 ex=s.assign(support_status=status).groupby(['count','A','support_status'],observed=True).agg(n=('Y','size'),players_pitcher=('pitcher','nunique'),players_batter=('batter','nunique'),meanY=('Y','mean')).reset_index()
 tabcheck(tag+'/support_exclusions',ex,dest/'support_exclusions.csv',['count','A','support_status'])
 metrics=dict(n=len(s),games=s.game_pk.nunique(),Y_mean=s.Y.mean(),outcome_MSE=np.square(s.Y-(s.mu0+s.A*(s.mu1-s.mu0))).mean(),Brier=np.square(s.A-s.p).mean(),log_loss=-np.mean(np.log(np.where(s.A.eq(1),s.p,1-s.p))),coverage=s.support.mean(),eligible_measurement_fraction=s.measurement_support.mean(),raw_p_outside01=(~s.raw_propensity.between(0,1)).mean())
 old=read(dest/'metrics.json')
 for k,v in metrics.items():compare(tag+'/metrics/'+k,v,old[k],'exact' if k in ['n','games'] else 'value')
 SUMMARIES.append(dict(run=run_id,stage='fixed_prediction_diagnostics' if fixed else 'main',n=len(s),support=int(s.support.sum()),grades=pd.DataFrame(summaries).grade.value_counts().to_dict(),overall_learned=next(r for r in policiesout if r['level']=='overall' and r['policy']=='learned')))
 print(tag,'done',len(s),'rows',flush=True)
for rid in IDS:
 audit(rid)
 if '2024_2025' not in rid:audit(rid,True)
pd.DataFrame(CHECKS).to_csv(OUT/'comparisons.csv',index=False)
pd.DataFrame(BAD,columns=['check','index','actual','expected','error']).to_csv(OUT/'mismatches.csv',index=False)
result=dict(status='FAIL' if BAD else 'PASS',started_at_utc=START,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),execution_class='restore_AIPW_OPE_from_saved_Y_A_nuisance',comparisons=sum(x['n'] for x in CHECKS),failed_checks=sum(x['bad']>0 for x in CHECKS),max_absolute_error=max(x.get('max_absolute_error',0) for x in CHECKS),max_relative_error=max(x.get('max_relative_error',0) for x in CHECKS),runs=SUMMARIES,scope='Saved predictions, independent factual-residual OPE, training-file policy application, game/individual-player clustered intervals, diagnostics. No producer statistical functions, fit recreation or refitting. Measurement/repertoire raw reconstruction checked separately.',undefined='Empty-support values remain NaN; exact key and shape matching; NaNs compared only within matched groups. Conditional intervals are not full fitted-policy intervals.')
(OUT/'validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
evidence=dict(environment=dict(python=sys.version,numpy=np.__version__,pandas=pd.__version__,executable=sys.executable),inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()) for p in sorted(INPUTS)],code_sha256=hashlib.file_digest(Path(__file__).open('rb'),'sha256').hexdigest())
(OUT/'evidence.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:result[k] for k in ['status','comparisons','failed_checks','max_absolute_error']},ensure_ascii=False),flush=True)
