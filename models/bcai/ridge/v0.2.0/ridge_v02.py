"""BCAI Ridge v0.2: development only until freeze.json exists. Python + NumPy/Pandas/SciPy."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
from pathlib import Path
import sys,json,hashlib,datetime,platform,argparse,traceback
ROOT=Path(__file__).resolve().parents[4]
COL=ROOT/'columns/001-ball-count'; ANAL=COL/'analysis'; MODEL=Path(__file__).resolve().parent
sys.path.insert(0,str(ANAL/'runtime_ridge_v02'))
import numpy as np
import pandas as pd
import scipy
from scipy import sparse,linalg
COUNTS=[f'{b}-{s}' for b in range(4) for s in range(3)]
FEATURES=['batter','pitcher','game_year','venue','matchup','score_bin','base_state','outs_when_up','inning_bin']
ALPHAS=[1.,3.,10.,30.,100.,300.,1000.,3000.,10000.,30000.]
WEIGHTS={2023:dict(BB=.696,HBP=.726,**{'1B':.883,'2B':1.244,'3B':1.569,'HR':2.004}),2024:dict(BB=.689,HBP=.720,**{'1B':.882,'2B':1.254,'3B':1.590,'HR':2.050}),2025:dict(BB=.691,HBP=.722,**{'1B':.882,'2B':1.252,'3B':1.584,'HR':2.037})}
WEIGHTS[2026]=WEIGHTS[2025].copy()
OBS=ANAL/'runs/bcai_obs__mlb_2024_2025__20260907__r01'
OLD=json.loads((ROOT/'models/bcai/observed/v1.0.0/specification.yaml').read_text(encoding='utf-8'))
EVENTS={v:k for k,vs in OLD['result_classification'].items() for v in vs}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def meta(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def writejson(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
def csv(p,d):pd.DataFrame(d).to_csv(p,index=False,encoding='utf-8-sig')
def environment():return dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,executable=sys.executable)
def make_pa(d,schedules):
    keys=['game_pk','at_bat_number'];d=d.sort_values(keys+['pitch_number']).reset_index(drop=True)
    assert not d.duplicated(keys+['pitch_number']).any()
    d['count']=d.balls.astype(int).astype(str)+'-'+d.strikes.astype(int).astype(str)
    assert set(d['count']).issubset(COUNTS)
    d['pa_id']=pd.factorize(pd.MultiIndex.from_frame(d[keys]))[0]
    p=d.drop_duplicates('pa_id').set_index('pa_id').copy();last=d.drop_duplicates('pa_id',keep='last').set_index('pa_id')
    p['event']=last.events;p['result']=p.event.map(EVENTS)
    p['exclusion']=np.select([p.event.isna(),p.event.eq('intent_walk'),p.event.eq('catcher_interf'),p.event.eq('truncated_pa'),p.result.isna(),p['count'].ne('0-0')],['missing_final','intentional_walk','catcher_interference','truncated','unknown_event','no_observed_0_0'],default='included')
    audit={'rows':len(d),'all_PA':len(p),'exclusions':p.exclusion.value_counts().to_dict(),'multiple_events_PA':int((d.groupby('pa_id').events.count()>1).sum())}
    p=p[p.exclusion.eq('included')].copy();p['value']=[WEIGHTS[int(y)].get(e,0) for y,e in zip(p.game_year,p.result)]
    venue={g['gamePk']:g['venue']['id'] for sc in schedules for day in sc['dates'] for g in day['games']}
    p['venue']=p.game_pk.map(venue);assert p.venue.notna().all()
    p['venue']=p.venue.astype(int)
    p['base_state']=sum(p[f'on_{b}b'].notna().astype(int)*2**(b-1) for b in (1,2,3))
    p['score_bin']=pd.cut(p.bat_score_diff,[-np.inf,-4,-1,0,3,np.inf],labels=['trailing4+','trailing1-3','tie','leading1-3','leading4+']).astype(str)
    p['matchup']=p.stand.fillna('?')+p.p_throws.fillna('?');p['inning_bin']=p.inning.clip(upper=10)
    r=d[['pa_id','count']].drop_duplicates();r=r[r.pa_id.isin(p.index)]
    rows=pd.Index(p.index).get_indexer(r.pa_id);cols=pd.Index(COUNTS).get_indexer(r['count'])
    reach=sparse.csr_matrix((np.ones(len(r)),(rows,cols)),shape=(len(p),12))
    assert np.all(reach[:,0].toarray()==1)
    audit.update(eligible_PA=len(p),games=int(p.game_pk.nunique()),first_date=str(p.game_date.min()),last_date=str(p.game_date.max()))
    return p.reset_index(drop=True),reach,audit

def folds(p,k,seed):
    g=np.sort(p.game_pk.unique());np.random.default_rng(seed).shuffle(g)
    m={v:i%k for i,v in enumerate(g)}
    return p.game_pk.map(m).to_numpy()

class Design:
    def __init__(self,p):
        self.maps=[];self.blocks=[];off=0;rr=[];cc=[]
        for f in FEATURES:
            values=p[f].fillna('missing').astype(str)
            levels=sorted(values.unique());m={v:off+i for i,v in enumerate(levels)}
            self.maps.append(m);self.blocks.append((off,off+len(levels)));off+=len(levels)
            rr.append(np.arange(len(p)));cc.append(values.map(m).to_numpy())
        self.X=sparse.csr_matrix((np.ones(len(p)*len(FEATURES)),(np.concatenate(rr),np.concatenate(cc))),shape=(len(p),off))
        self.mean=np.asarray(self.X.mean(axis=0)).ravel()
    def predict(self,p,beta,intercept):
        pred=np.full(len(p),intercept);flags={};past={}
        for f,m,(lo,hi) in zip(FEATURES,self.maps,self.blocks):
            v=p[f].fillna('missing').astype(str).map(m);known=v.notna().to_numpy();idx=v.fillna(0).astype(int).to_numpy()
            center=self.mean[lo:hi]@beta[lo:hi]
            pred[known]+=beta[idx[known]]-center
            flags[f]=~known
            past[f]=np.where(known,np.asarray(self.X.sum(axis=0)).ravel()[idx],0).astype(int)
        return pred,flags,past
    def serial(self):return {'features':FEATURES,'maps':self.maps,'blocks':self.blocks,'mean':self.mean.tolist(),'training_counts':np.asarray(self.X.sum(axis=0)).ravel().astype(int).tolist()}

def prepare(p,reach):
    design=Design(p);base=p.groupby('game_year').value.mean().to_dict();z=p.value.to_numpy()/p.game_year.map(base).to_numpy()
    X=design.X;G=(X.T@X).tocsr();mu=design.mean;n=len(p);ym=z.mean();b=np.asarray(X.T@(z-ym)).ravel()
    counts=np.asarray(reach.sum(0)).ravel();cx=(reach.T@X).toarray()/counts[:,None]-mu
    # J monitor includes evaluation-mean centering, intercept cancels.
    monitor=cx-cx[[0]]
    return dict(design=design,G=G,mu=mu,n=n,z=z,ym=ym,b=b,yy=float(np.sum((z-ym)**2)),base=base,monitor=monitor)

def solve(pr,alpha,label,art,random_start=False,independent=False):
    X=pr['design'].X;mu=pr['mu'];G=pr['G'];b=pr['b'];n=pr['n'];k=len(b)
    def A(v):return G@v-n*mu*(mu@v)+alpha*v
    def obj(v):return pr['yy']-2*v@b+v@A(v)
    diag=G.diagonal()-n*mu**2+alpha
    beta=np.random.default_rng(811).normal(0,.02,k) if random_start else np.zeros(k)
    res=b-A(beta);z=res/diag;direction=z.copy();rz=res@z;prevobj=obj(beta);startobj=prevobj;history=[];first=None;at_first=None;firstpred=None;prev_delta=None;osc=0;abnormal=0
    for it in range(1,5001):
        ad=A(direction);denom=direction@ad
        if denom<=np.finfo(float).tiny:
            res=b-A(beta);z=res/diag;direction=z.copy();rz=res@z;ad=A(direction);denom=direction@ad
        delta=np.zeros(k) if denom<=np.finfo(float).tiny else direction*(rz/denom)
        beta+=delta;fitdelta=np.asarray(X@delta).ravel()-mu@delta;change=float(np.max(np.abs(fitdelta)))
        current=obj(beta);rel=abs(current-prevobj)/max(1,abs(prevobj));grad=b-A(beta);gradrel=float(np.max(np.abs(grad))/max(1,np.max(np.abs(b))))
        jdelta=float(np.max(np.abs(100*pr['monitor']@delta)))
        if prev_delta is not None and delta@prev_delta<0:osc+=1
        if current>prevobj+1e-9*max(1,abs(prevobj)):abnormal+=1
        history.append(dict(iteration=it,objective=current,relative_objective_change=rel,max_prediction_change=change,max_count_index_change=jdelta,gradient_relative=gradrel,step_direction_reversal=bool(prev_delta is not None and delta@prev_delta<0)))
        if first is None and change<1e-7 and rel<1e-12 and gradrel<1e-10:
            first=it;at_first=beta.copy();firstpred=np.asarray(X@beta).ravel()-mu@beta
        if first is not None and it>=first+10:break
        newres=res-ad*(rz/denom) if denom>np.finfo(float).tiny else grad.copy()
        # Refresh residual periodically to avoid drift in finite precision.
        if it%50==0:newres=grad.copy()
        zz=newres/diag;rznew=newres@zz
        direction=zz+direction*(rznew/rz) if rz>np.finfo(float).tiny else zz.copy()
        res=newres;rz=rznew;prevobj=current;prev_delta=delta.copy()
    pred=np.asarray(X@beta).ravel()-mu@beta+pr['ym']
    diagout=dict(fit_id=label,alpha=alpha,converged=first is not None,iterations=it,first_convergence_iteration=first,max_last_change=change,relative_objective_change=rel,gradient_relative=gradrel,objective_start=startobj,objective_end=current,abnormal_increases=abnormal,direction_reversals=osc,max_count_index_step_last=jdelta,
                 extra_iterations=it-first if first else 0,post_convergence_max_prediction_drift=float(np.max(np.abs(pred-pr['ym']-firstpred))) if first else None,post_convergence_max_index_drift=float(np.max(np.abs(100*pr['monitor']@(beta-at_first)))) if first else None)
    if independent:
        dense=G.toarray()-n*np.outer(mu,mu)+alpha*np.eye(k)
        direct=linalg.solve(dense,b,assume_a='pos')
        diagout['independent_cholesky_coef_maxdiff']=float(np.max(np.abs(direct-beta)))
        diagout['independent_cholesky_prediction_maxdiff']=float(np.max(np.abs(X@(direct-beta)-mu@(direct-beta))))
    csv(art/'diagnostics'/f'{label}.csv',history)
    with (art/'fit_diagnostics.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(diagout)+'\n')
    if first is None or abnormal:raise RuntimeError(f'Convergence failure {label}: {diagout}')
    if diagout['post_convergence_max_prediction_drift']>=1e-7:raise RuntimeError(f'Unstable after convergence {label}')
    return beta,diagout

def predict(pr,p,beta):
    zn,flags,past=pr['design'].predict(p,beta,pr['ym'])
    # Training overall W average is reconstructed from category frequencies for season.
    seasonmap=pr['design'].maps[FEATURES.index('game_year')]
    fallback=sum(pr['base'][int(y)]*pr['mu'][idx] for y,idx in seasonmap.items())
    scale=p.game_year.map(pr['base']).fillna(fallback).to_numpy()
    return zn*scale,zn,scale,flags,past

def score(p,pred,scale):
    raw=p.value.to_numpy();loss=(raw/scale-pred/scale)**2;closs=(raw/scale-1)**2
    return dict(N=len(p),games=int(p.game_pk.nunique()),MSE=float(loss.mean()),constant_MSE=float(closs.mean()),improvement_pct=float(100*(1-loss.mean()/closs.mean())),raw_MSE=float(np.mean((raw-pred)**2)),raw_constant_MSE=float(np.mean((raw-scale)**2)))

def index_table(p,reach,pred):
    out=[]
    for year,mask in [('combined',np.ones(len(p),dtype=bool))]+[(str(y),p.game_year.eq(y).to_numpy()) for y in sorted(p.game_year.unique())]:
        I=np.zeros(12);J=np.zeros(12);nums=np.zeros(12)
        for y in sorted(p.loc[mask,'game_year'].unique()):
            use=mask&p.game_year.eq(y).to_numpy();R=reach[use];nn=np.asarray(R.sum(0)).ravel();v=p.loc[use,'value'].to_numpy();base=v.mean();w=use.sum()/mask.sum()
            res=(v-pred[use])/base
            I+=w*100*np.asarray(R.T@v).ravel()/nn/base
            J+=w*(100+100*(np.asarray(R.T@res).ravel()/nn-res.mean()));nums+=nn
        for j,c in enumerate(COUNTS):out.append(dict(period=year,count=c,N=int(nums[j]),I=I[j],J=J[j],shift=J[j]-I[j],direction_I=int(np.sign(round(I[j]-100,8))),direction_J=int(np.sign(round(J[j]-100,8)))))
    return pd.DataFrame(out)

def grid_search(p,reach,k,seed,stage,art,allrows,selectedrows):
    f=folds(p,k,seed);csv(art/f'{stage}_folds.csv',p[['game_pk']].assign(fold=f).drop_duplicates())
    local=[]
    for fold in range(k):
        tr=f!=fold;te=~tr;pr=prepare(p.loc[tr].reset_index(drop=True),reach[tr])
        for alpha in ALPHAS:
            label=f'{stage}_f{fold}_a{int(alpha)}';beta,di=solve(pr,alpha,label,art)
            pred,zn,scale,flags,_=predict(pr,p.loc[te],beta);row=dict(stage=stage,fold=fold,alpha=alpha,**score(p.loc[te],pred,scale));local.append(row);allrows.append(row)
        print(stage,'fold',fold,'grid complete',flush=True)
    frame=pd.DataFrame(local);ag=frame.groupby('alpha').agg(mean_MSE=('MSE','mean'),sd_MSE=('MSE','std'),constant_MSE=('constant_MSE','mean')).reset_index();ag['SE']=ag.sd_MSE/np.sqrt(k)
    best=ag.sort_values(['mean_MSE','alpha'],ascending=[True,False]).iloc[0];onese=ag[ag.mean_MSE<=best.mean_MSE+best.SE].alpha.max()
    decision=dict(stage=stage,selected_alpha=float(best.alpha),one_SE_alpha=float(onese),min_at_boundary=bool(best.alpha in [min(ALPHAS),max(ALPHAS)]),minimum_mean_MSE=float(best.mean_MSE))
    csv(art/f'{stage}_alpha_summary.csv',ag);selectedrows.append(decision)
    if decision['min_at_boundary']:raise RuntimeError(f'Grid boundary requires development-only review: {decision}')
    return float(best.alpha)

def develop(run_id):
    run=ANAL/'runs'/run_id
    if run.exists():raise FileExistsError('New run ID required')
    art=run/'artifacts';(art/'diagnostics').mkdir(parents=True)
    manifest=dict(run_id=run_id,model_id='BCAI-RIDGE-v0.2.0',version='0.2.0',model_status='EXPERIMENTAL',status='RUNNING',role='development',run_date=datetime.date.today().isoformat(),started_at=now(),environment=environment(),external_data_used_for_tuning=False,code=[meta(Path(__file__))])
    writejson(run/'manifest.json',manifest)
    try:
        inputs=[ANAL/'advantage_input_cache.pkl']+[COL/f'data/raw/mlb/{y}/schedule_{y}.json' for y in (2024,2025)]
        data=pd.read_pickle(inputs[0]);assert set(data.game_year.unique())=={2024,2025}
        p,reach,audit=make_pa(data,[json.loads(f.read_text(encoding='utf-8-sig')) for f in inputs[1:]])
        assert len(p)==364124
        csv(art/'sample_audit.csv',[audit]);writejson(art/'sample_audit.json',audit)
        p.to_pickle(art/'development_PA.pkl');sparse.save_npz(art/'development_reach.npz',reach)
        f=folds(p,5,20260908);csv(art/'outer_folds.csv',p[['game_pk']].assign(fold=f).drop_duplicates())
        allrows=[];decisions=[];outerrows=[];oof=np.zeros(len(p));scales=np.zeros(len(p))
        for outer in range(5):
            tr=f!=outer;te=~tr
            alpha=grid_search(p.loc[tr].reset_index(drop=True),reach[tr],3,20261000+outer,f'outer{outer}_inner',art,allrows,decisions)
            pr=prepare(p.loc[tr].reset_index(drop=True),reach[tr]);beta,di=solve(pr,alpha,f'outer{outer}_refit',art,independent=(outer==0))
            pred,zn,scale,flags,_=predict(pr,p.loc[te],beta);oof[te]=pred;scales[te]=scale
            outerrows.append(dict(fold=outer,selected_alpha=alpha,**score(p.loc[te],pred,scale)))
            print('OUTER',outer,'selected',alpha,'MSE',outerrows[-1]['MSE'],flush=True)
        alpha=grid_search(p,reach,5,20261108,'final_cv',art,allrows,decisions)
        pr=prepare(p,reach);beta,di=solve(pr,alpha,'final_fit',art,independent=True)
        beta_alt,di_alt=solve(pr,alpha,'final_alternate_initialization',art,random_start=True)
        altpred=float(np.max(np.abs(pr['design'].X@(beta-beta_alt)-pr['mu']@(beta-beta_alt))))
        assert altpred<1e-7
        pred,_,scale,flags,past=predict(pr,p,beta)
        cvscore=score(p,oof,scales);csv(art/'outer_scores.csv',outerrows);csv(art/'alpha_fold_scores.csv',allrows);csv(art/'alpha_selection.csv',decisions)
        csv(art/'development_scores.csv',[dict(role='nested_OOF',**cvscore),dict(role='training_in_sample',**score(p,pred,scale))])
        table=index_table(p,reach,oof);csv(art/'count_indices.csv',table);csv(art/'in_sample_indices.csv',index_table(p,reach,pred))
        original=pd.read_csv(OBS/'artifacts/advantage_count_results.csv')
        compare=original[['count','index','adjusted_index_alpha20','adjusted_index_alpha100','adjusted_index_alpha500']].merge(table[table.period.eq('combined')][['count','I','J','shift']],on='count')
        assert np.max(np.abs(compare['index']-compare.I))<1e-9
        csv(art/'legacy_comparison.csv',compare)
        oldaudit=json.loads((OBS/'artifacts/advantage_audit.json').read_text(encoding='utf-8'))
        csv(art/'legacy_alpha_scores.csv',[dict(alpha=k,OOF_MSE=v['OOF_MSE'],constant_MSE=v['constant_MSE'],improvement_pct=100*(1-v['OOF_MSE']/v['constant_MSE']),all_converged=False) for k,v in oldaudit['model'].items()])
        csv(art/'development_predictions.csv',p[['game_pk','at_bat_number','game_year','value']].assign(outer_fold=f,OOF_prediction_W=oof,training_scale=scales))
        fitlog=[json.loads(x) for x in (art/'fit_diagnostics.jsonl').read_text().splitlines()];csv(art/'all_fit_diagnostics.csv',fitlog)
        assert all(x['converged'] and x['max_last_change']<1e-7 for x in fitlog)
        state=dict(model_id='BCAI-RIDGE-v0.2.0',version='0.2.0',selected_alpha=alpha,design=pr['design'].serial(),beta=beta.tolist(),intercept=pr['ym'],base=pr['base'],external_base=float(p.value.mean()),features=FEATURES,weights=WEIGHTS)
        writejson(art/'frozen_model.json',state)
        freeze=dict(frozen_at=now(),model_id=state['model_id'],development_run=run_id,selected_alpha=alpha,external_evaluations_started=False,external_snapshot_cutoff='2026-09-07',external_2023_role='external_reproduction',external_2026_role='external_forward_time',files=[meta(MODEL/'development_plan.md'),meta(Path(__file__)),meta(art/'frozen_model.json')])
        writejson(art/'freeze.json',freeze)
        manifest.update(status='COMPLETE',completed_at=now(),model_definition='models/bcai/ridge/v0.2.0/specification.yaml',period='2024_2025',data_period=audit,inputs=[meta(f) for f in inputs],raw_input_audit=meta(OBS/'artifacts/advantage_audit.json'),exclusions=OLD['exclusions'],features=FEATURES,alpha_candidates=ALPHAS,alpha_selection='nested 5x3; final 5fold minimum MSE; one-SE comparison',selected_alpha=alpha,fold_seed=20260908,solver='centered Gram Jacobi-PCG',tolerance=1e-7,max_iterations=5000,convergence={'all_fits':len(fitlog),'all_converged':True,'max_last_change':max(x['max_last_change'] for x in fitlog),'iteration_range':[min(x['iterations'] for x in fitlog),max(x['iterations'] for x in fitlog)],'alternate_initialization_prediction_maxdiff':altpred},metrics=cvscore,code=[meta(Path(__file__))],artifacts=[meta(f) for f in sorted(art.rglob('*')) if f.is_file()])
        writejson(run/'manifest.json',manifest)
        print('DEVELOPMENT FROZEN',alpha,cvscore,manifest['convergence'],flush=True)
    except Exception as exc:
        manifest.update(status='FAILED',error=str(exc),failed_at=now());writejson(run/'manifest.json',manifest);raise

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--develop');args=ap.parse_args()
    if args.develop:develop(args.develop)
