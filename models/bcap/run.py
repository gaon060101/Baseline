"""BCAP v0.1.0. Existing local data only; new run directories are mandatory."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys, json, hashlib, datetime, platform, argparse, traceback, pickle
ROOT=Path(__file__).resolve().parents[2]
COL=ROOT/'columns/001-ball-count'; ANAL=COL/'analysis'; MODEL=Path(__file__).resolve().parent
sys.path.insert(0,str(ANAL/'runtime_ridge_v02'))
import numpy as np
import pandas as pd
import scipy
from scipy import sparse, optimize, special, stats
from scipy.sparse.linalg import cg, LinearOperator

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def meta(p): return dict(path=Path(p).resolve().relative_to(ROOT).as_posix(),sha256=sha(p),bytes=Path(p).stat().st_size)
def js(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda v:v.item() if hasattr(v,'item') else str(v)),encoding='utf-8')
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def csv(p,x): pd.DataFrame(x).to_csv(p,index=False,encoding='utf-8-sig')
def cfg(model): return read(MODEL/model/'v0.1.0/specification.yaml')
def environment(): return dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,executable=sys.executable,blas_threads=os.environ.get('OPENBLAS_NUM_THREADS'))
def folds(d,k,seed):
    g=np.sort(d.game_pk.unique());np.random.default_rng(seed).shuffle(g)
    return d.game_pk.map({v:i%k for i,v in enumerate(g)}).to_numpy()
def features(d,c):
    d=d.copy()
    if c['variant']=='swing':
        for f,step in [('release_speed',5),('pfx_x',.5),('pfx_z',.5),('plate_x',.35)]:
            d[f+'_bin']=np.floor(pd.to_numeric(d[f],errors='coerce')/step).fillna(-999).astype(int).astype(str)
        z=(d.plate_z-d.sz_bot)/(d.sz_top-d.sz_bot)
        d['relative_z_bin']=np.floor(z/.2).replace([np.inf,-np.inf],np.nan).fillna(-999).astype(int).astype(str)
        d['swing_cell']=d['count'].astype(str)+'|'+d.zone.astype(str)+'|'+d.pitch_group.astype(str)
    return d

class Design:
    """Training-only dictionaries. Unknown category has centered block effect zero."""
    def __init__(self,d,fs):
        self.features=fs;self.maps=[];self.blocks=[];off=0
        for f in fs:
            levels=sorted(d[f].astype('string').fillna('MISSING').astype(str).unique())
            self.maps.append({v:off+i for i,v in enumerate(levels)})
            self.blocks.append((off,off+len(levels)));off+=len(levels)
        self.width=off;self.X=self.matrix(d);self.mean=np.asarray(self.X.mean(axis=0)).ravel()
    def matrix(self,d):
        rr=[];cc=[]
        for f,m in zip(self.features,self.maps):
            idx=d[f].astype('string').fillna('MISSING').astype(str).map(m);known=idx.notna().to_numpy()
            rr.append(np.flatnonzero(known));cc.append(idx[known].to_numpy(dtype=int))
        return sparse.csr_matrix((np.ones(sum(map(len,rr))),(np.concatenate(rr),np.concatenate(cc))),shape=(len(d),self.width))
    def predict(self,d,beta,intercept):
        v=np.full(len(d),intercept)
        for f,m,(lo,hi) in zip(self.features,self.maps,self.blocks):
            idx=d[f].astype('string').fillna('MISSING').astype(str).map(m);known=idx.notna().to_numpy()
            v[known]+=beta[idx[known].to_numpy(dtype=int)]-self.mean[lo:hi]@beta[lo:hi]
        return v

class Ridge:
    def __init__(self,d,y,fs,alpha,label,log):
        self.design=Design(d,fs);X=self.design.X;n=len(d);u=self.design.mean
        self.intercept=float(np.mean(y));b=np.asarray(X.T@(y-self.intercept)).ravel()
        G=(X.T@X).tocsr();diag=G.diagonal()-n*u*u+alpha
        def mv(v): return G@v-n*u*(u@v)+alpha*v
        op=LinearOperator(G.shape,matvec=mv);pre=LinearOperator(G.shape,matvec=lambda v:v/diag)
        iterations=[0]
        def callback(v):iterations[0]+=1
        self.beta,info=cg(op,b,rtol=1e-9,atol=1e-11,maxiter=3000,M=pre,callback=callback)
        residual=float(np.max(np.abs(mv(self.beta)-b))/max(1,float(np.max(np.abs(b)))))
        log.append(dict(fit_id=label,n=n,features=X.shape[1],alpha=alpha,iterations=iterations[0],solver_info=info,relative_gradient=residual,converged=info==0 and residual<1e-7))
        if info or residual>=1e-7: raise RuntimeError('Ridge convergence failed '+label)
        # Matrices are training workspaces, not part of the frozen model.
        self.design.X=None
    def predict(self,d): return self.design.predict(d,self.beta,self.intercept)

def split_record(records,label,role,tr,te):
    a=sorted(map(int,tr.game_pk.unique()));b=sorted(map(int,te.game_pk.unique()))
    if set(a)&set(b): raise AssertionError('game leakage '+label)
    records.append(dict(fit_id=label,role=role,train_games=a,evaluation_games=b,intersection_n=0))

class Nuisance:
    def predict(self,d,c):
        raw=self.prop.predict(d);p=special.expit(self.cal[0]+self.cal[1]*raw)
        p=np.clip(p,c['numerical_epsilon'],1-c['numerical_epsilon'])
        m0=self.out[0].predict(d);m1=self.out[1].predict(d)
        entity=d[c['support_entity']].astype(str)
        rep=entity.map(self.repertoire).fillna(False).to_numpy(dtype=bool)
        kp=d.pitcher.astype(str).isin(self.known_pitcher).to_numpy();kb=d.batter.astype(str).isin(self.known_batter).to_numpy()
        return dict(p=p,mu0=m0,mu1=m1,repertoire=rep,known_pitcher=kp,known_batter=kb,raw_propensity=raw)

def nuisance(train,c,label,seed,logs,records,frozen_alpha=None):
    """No evaluation game participates in tuning, calibration or dictionaries."""
    f=folds(train,5,seed);cal=train[f==0];base=train[f!=0];tune=train[f==1];fit=train[f>=2]
    split_record(records,label+'/cal','calibration',base,cal)
    split_record(records,label+'/tune','tuning',fit,tune)
    fs=c['features'];model=Nuisance();choices={};tuning=[]
    if frozen_alpha is None:
        for target in ['p','m0','m1']:
            ar=None if target=='p' else int(target[-1]);ft=fit if ar is None else fit[fit.A.eq(ar)]
            ev=tune if ar is None else tune[tune.A.eq(ar)]
            y=ft.A.to_numpy(dtype=float) if ar is None else ft.Y.to_numpy()
            for alpha in c['alphas']:
                reg=Ridge(ft,y,fs,alpha,label+'/tune/'+target+'/'+str(alpha),logs)
                pr=reg.predict(ev);truth=ev.A.to_numpy() if ar is None else ev.Y.to_numpy()
                if ar is None:pr=np.clip(pr,0,1)
                loss=float(np.mean((truth-pr)**2));tuning.append(dict(fit_id=label,target=target,alpha=alpha,loss=loss,metric='Brier' if ar is None else 'MSE'))
            candidates=[x for x in tuning if x['target']==target]
            choices[target]=min(candidates,key=lambda x:(x['loss'],-x['alpha']))['alpha']
    else:choices=dict(frozen_alpha)
    model.prop=Ridge(base,base.A.to_numpy(dtype=float),fs,choices['p'],label+'/prop',logs)
    r=model.prop.predict(cal);a=cal.A.to_numpy(dtype=float)
    def obj(b):
        z=b[0]+b[1]*r;e=special.expit(z);loss=np.mean(np.logaddexp(0,z)-a*z)+1e-6*b[1]**2
        return loss,np.array([np.mean(e-a),np.mean((e-a)*r)+2e-6*b[1]])
    opt=optimize.minimize(obj,[-2.,4.],jac=True,method='L-BFGS-B',bounds=[(None,None),(0,None)],options={'gtol':1e-10,'ftol':1e-13,'maxiter':1000})
    if not opt.success: raise RuntimeError('Calibration failure '+str(opt.message))
    model.cal=opt.x;logs.append(dict(fit_id=label+'/calibrator',n=len(cal),iterations=opt.nit,converged=bool(opt.success),loss=float(opt.fun),intercept=opt.x[0],slope=opt.x[1]))
    model.out={ar:Ridge(train[train.A.eq(ar)],train.loc[train.A.eq(ar),'Y'].to_numpy(),fs,choices['m'+str(ar)],label+'/m'+str(ar),logs) for ar in [0,1]}
    rc=pd.crosstab(train[c['support_entity']].astype(str),train.A).reindex(columns=[0,1],fill_value=0)
    model.repertoire=(rc.min(axis=1)>=c['min_entity_arm_training']).to_dict()
    model.known_pitcher=set(train.pitcher.astype(str));model.known_batter=set(train.batter.astype(str));model.alpha=choices
    return model,tuning

def score(d,pr,c):
    out=d[['game_pk','at_bat_number','pitch_number','game_year','game_date','count','pitcher','batter','final_event','result','Y','A','zone','pitch_group']].copy()
    if c['variant']=='swing':out['swing_cell']=d.swing_cell.to_numpy()
    for k,v in pr.items():out[k]=v
    p=out.p.to_numpy();a=out.A.to_numpy();y=out.Y.to_numpy()
    out['phi0']=out.mu0+(1-a)/(1-p)*(y-out.mu0)
    out['phi1']=out.mu1+a/p*(y-out.mu1)
    out['measurement_support']=True
    if c['variant']=='swing':
        out['measurement_support']=d.zone.ne('MISSING').to_numpy() & d[['release_speed','pfx_x','pfx_z','plate_x','plate_z','sz_top','sz_bot']].notna().all(axis=1).to_numpy() & d.pitch_group.isin(['FB','NFB']).to_numpy()
    out['support']=out.p.between(c['trim'],1-c['trim']) & out.repertoire & out.measurement_support
    return out

def cluster_stat(d,v,family=1,cluster='game_pk'):
    v=np.asarray(v,dtype=float);n=len(v)
    if not n:return (np.nan,)*7
    point=float(v.mean());g=d[cluster].to_numpy();codes,lev=pd.factorize(g);G=len(lev)
    total=np.bincount(codes,weights=v-point);se=np.sqrt(G/max(1,G-1)*np.sum(total**2))/n
    z=stats.t.ppf(.975,max(1,G-1));zs=stats.t.ppf(1-.05/(2*family),max(1,G-1))
    return point,float(se),point-z*se,point+z*se,point-zs*se,point+zs*se,G

def learn_policy(oof,c):
    key=c['policy_key'];rows=[]
    for z,d in oof[oof.support].groupby(key,observed=True):
        delta=float((d.phi1-d.phi0).mean());st=cluster_stat(d,d.phi1-d.phi0,c['comparison_family'])
        p1=int(delta<0) if c['variant']=='pitch' else int(delta>0)
        rows.append(dict(state=str(z),p1=p1,delta=delta,n=len(d),games=d.game_pk.nunique(),conditional_low=st[4],conditional_high=st[5],candidate_only=True))
    return dict(key=key,states={x['state']:x for x in rows},fallback_p1=.5,conservative_change=False,reason='Identification and full-learning uncertainty gates not satisfied; retain observed mechanism everywhere')

def apply_policy(s,policy):
    key=policy['key'];s=s.copy();s['policy_p1']=s[key].astype(str).map({k:v['p1'] for k,v in policy['states'].items()}).fillna(policy['fallback_p1'])
    s['conservative_change']=False;s['conservative_p1']=s.policy_p1
    s['policy_value']=s.policy_p1*s.phi1+(1-s.policy_p1)*s.phi0
    s['conservative_value']=s.Y
    return s

def crossfit_policy(train,c,seed,label,logs,records,tuning):
    parts=[];f=folds(train,c['inner_folds'],seed)
    for k in range(c['inner_folds']):
        tr=train[f!=k];te=train[f==k];lab=label+'/inner'+str(k)
        split_record(records,lab,'policy_oof',tr,te)
        nu,tu=nuisance(tr,c,lab,seed+100+k,logs,records);tuning.extend(tu)
        s=score(te,nu.predict(te,c),c);s['fold']=k;parts.append(s)
    inner=pd.concat(parts).sort_index()
    return learn_policy(inner,c),inner

def evaluate_development(d,c,art,seed=None,save_rows=True):
    seed=c['seed'] if seed is None else seed;logs=[];records=[];tuning=[];parts=[];policies=[]
    fold=folds(d,c['outer_folds'],seed)
    for k in range(c['outer_folds']):
        print(now(),c['variant'],'outer',k,'start',flush=True)
        tr=d[fold!=k];te=d[fold==k];lab='outer'+str(k)
        split_record(records,lab,'outer_evaluation',tr,te)
        policy,inner=crossfit_policy(tr,c,seed+1000+k*100,lab,logs,records,tuning)
        if save_rows:inner.to_pickle(art/(lab+'_policy_training_scores.pkl'))
        nu,tu=nuisance(tr,c,lab+'/evaluation_nuisance',seed+2000+k,logs,records);tuning.extend(tu)
        s=score(te,nu.predict(te,c),c);s['fold']=k;s=apply_policy(s,policy);parts.append(s);policies.append(policy)
        if save_rows:js(art/'fit_progress.json',dict(at=now(),outer_completed=k,fit_count=len(logs)))
    result=pd.concat(parts).sort_index()
    if save_rows:
        result.to_pickle(art/'scores.pkl');js(art/'fold_records.json',records);csv(art/'fit_diagnostics.csv',logs);csv(art/'tuning.csv',tuning);js(art/'outer_policies.json',policies)
    return result,logs,records,tuning

def diagnostics(s,c,art):
    summaries=[];pols=[];prop=[];cal=[];known=[];sens=[];ex=[]
    def groups():
        yield 'overall','ALL',s
        for k,d in s.groupby('count',observed=True):yield 'count',str(k),d
        if c['variant']=='swing':
            for k,d in s.groupby('swing_cell',observed=True):yield 'cell',str(k),d
    for kind,key,allrows in groups():
        d=allrows[allrows.support];n=len(d);base=dict(level=kind,state=key,n_all=len(allrows),n=n,coverage=n/len(allrows),games=d.game_pk.nunique(),PA=d[['game_pk','at_bat_number']].drop_duplicates().shape[0],pitchers=d.pitcher.nunique(),batters=d.batter.nunique(),action1_rate_all=allrows.A.mean(),action1_rate=d.A.mean())
        for ar in [0,1]:
            aa=allrows[allrows.A.eq(ar)];pa=allrows.p if ar else 1-allrows.p;w=allrows.A.eq(ar).astype(float)/pa
            ww=d.A.eq(ar).astype(float)/(d.p if ar else 1-d.p);positive=w[w>0]
            wg=ww.groupby(d.game_pk).sum();ess=float(ww.sum()**2/(ww@ww)) if (ww@ww)>0 else 0
            base['ESS'+str(ar)]=ess;base['arm_games'+str(ar)]=d.loc[d.A.eq(ar),'game_pk'].nunique();base['max_game_share'+str(ar)]=float(wg.max()/wg.sum()) if wg.sum() else np.nan
            rec=dict(level=kind,state=key,action=ar,n_arm=len(aa),ESS_support=ess,ESS_untrimmed=float(w.sum()**2/(w@w)) if w@w else 0,weight_max=float(w.max()),weight_gt10_rate=float((positive>10).mean()),weight_gt20_rate=float((positive>20).mean()),max_game_share=base['max_game_share'+str(ar)])
            for q in [0,.01,.05,.1,.5,.9,.95,.99,1]:rec['p_q'+str(q)]=float(pa.quantile(q));rec['positive_weight_q'+str(q)]=float(positive.quantile(q))
            prop.append(rec)
        if n:
            delta=d.phi1-d.phi0;st=cluster_stat(d,delta,c['comparison_family'])
            base.update(Q0=d.phi0.mean(),Q1=d.phi1.mean(),gcomp0=d.mu0.mean(),gcomp1=d.mu1.mean(),delta=st[0],se=st[1],CI95_low=st[2],CI95_high=st[3],simultaneous95_low=st[4],simultaneous95_high=st[5])
            support_ok=min(base['ESS0'],base['ESS1'])>=c['min_ess'] and min(base['arm_games0'],base['arm_games1'])>=c['min_arm_games'] and base['coverage']>=c['min_coverage'] and max(base['max_game_share0'],base['max_game_share1'])<=c['max_game_share'] and n>=c['min_rows']
            base['grade']='UNCERTAIN' if support_ok else 'NO_SUPPORT';base['reason']='IDENTIFICATION_AND_FULL_LEARNING_UNCERTAINTY' if support_ok else 'SAMPLE_OR_OVERLAP_GATE'
            base['suggested_action']=None;base['candidate_direction']=c['action1'] if ((st[0]<0) if c['variant']=='pitch' else (st[0]>0)) else c['action0']
            for name,v in [('observed',d.Y),('always_0',d.phi0),('always_1',d.phi1),('learned',d.policy_value),('conservative',d.conservative_value),('stochastic_half',.5*(d.phi0+d.phi1))]:
                sign=-1 if c['variant']=='pitch' else 1;gain=sign*(v-d.Y);vs=cluster_stat(d,v,c['comparison_family']);gs=cluster_stat(d,gain,c['comparison_family'])
                pols.append(dict(level=kind,state=key,policy=name,n=n,value=vs[0],CI95_low=vs[2],CI95_high=vs[3],gain=gs[0],gain_low=gs[4],gain_high=gs[5],unit='W per selected current decision; not summed PA value',conditional=True))
        else:base.update(grade='NO_SUPPORT',reason='NO_COMMON_SUPPORT',suggested_action=None)
        summaries.append(base)
        for setting,mask,clip in [('untrimmed',allrows.measurement_support,1e-6),('trim_002',allrows.measurement_support&allrows.repertoire&allrows.p.between(.02,.98),1e-6),('trim_005',allrows.support,1e-6),('trim_010',allrows.measurement_support&allrows.repertoire&allrows.p.between(.1,.9),1e-6),('clip_010_same_target',allrows.support,.1),('first_count_visit',allrows.support&~allrows.duplicated(['game_pk','at_bat_number','count']),1e-6)]:
            a=allrows[mask]
            if not len(a):continue
            pp=a.p.clip(clip,1-clip);q0=a.mu0+(1-a.A)/(1-pp)*(a.Y-a.mu0);q1=a.mu1+a.A/pp*(a.Y-a.mu1)
            sens.append(dict(level=kind,state=key,setting=setting,n=len(a),coverage=len(a)/len(allrows),Q0=q0.mean(),Q1=q1.mean(),delta=(q1-q0).mean(),different_target=setting not in ['trim_005','clip_010_same_target']))
        if n:
            for cl in ['pitcher','batter']:
                st=cluster_stat(d,d.phi1-d.phi0,c['comparison_family'],cl)
                sens.append(dict(level=kind,state=key,setting='fixed_score_cluster_'+cl,n=n,delta=st[0],low=st[4],high=st[5],clusters=st[6],different_target=False))
    for k,d in s.groupby(pd.cut(s.p,np.linspace(0,1,11),include_lowest=True),observed=True):
        cal.append(dict(bin=str(k),n=len(d),mean_p=d.p.mean(),observed_rate=d.A.mean(),Brier=np.mean((d.A-d.p)**2)))
    s['known_group']=np.select([s.known_pitcher&s.known_batter,s.known_pitcher&~s.known_batter,~s.known_pitcher&s.known_batter],['both_known','pitcher_known_batter_unseen','pitcher_unseen_batter_known'],default='both_unseen')
    for k,d in s.groupby('known_group',observed=True):
        sup=d[d.support];m=np.where(d.A.eq(1),d.mu1,d.mu0)
        known.append(dict(group=k,n=len(d),games=d.game_pk.nunique(),coverage=d.support.mean(),MSE=np.mean((d.Y-m)**2),Brier=np.mean((d.A-d.p)**2),Q0=sup.phi0.mean(),Q1=sup.phi1.mean(),policy_value=sup.policy_value.mean()))
    metrics=dict(n=len(s),games=s.game_pk.nunique(),Y_mean=s.Y.mean(),outcome_MSE=np.mean((s.Y-np.where(s.A.eq(1),s.mu1,s.mu0))**2),Brier=np.mean((s.A-s.p)**2),log_loss=-np.mean(s.A*np.log(s.p)+(1-s.A)*np.log1p(-s.p)),coverage=s.support.mean(),eligible_measurement_fraction=s.measurement_support.mean(),raw_p_outside01=np.mean((s.raw_propensity<0)|(s.raw_propensity>1)))
    csv(art/'action_values.csv',summaries);csv(art/'policy_values.csv',pols);csv(art/'propensity_overlap.csv',prop);csv(art/'calibration.csv',cal);csv(art/'known_unseen.csv',known);csv(art/'sensitivity.csv',sens);js(art/'metrics.json',metrics)
    exclusions=s.assign(support_status=np.select([~s.measurement_support,~s.repertoire,~s.p.between(c['trim'],1-c['trim'])],['measurement','entity_arm_training','propensity_tail'],default='supported'))
    csv(art/'support_exclusions.csv',exclusions.groupby(['count','A','support_status'],observed=True).agg(n=('Y','size'),players_pitcher=('pitcher','nunique'),players_batter=('batter','nunique'),meanY=('Y','mean')).reset_index())
    return metrics

def new_run(c,period,runid):
    run=ANAL/'runs'/runid
    if run.exists():raise FileExistsError('Never overwrite run '+str(run))
    run.mkdir(parents=True);art=run/'artifacts';art.mkdir()
    for name in ['run.py','data.py']:(art/('frozen_'+name)).write_bytes((MODEL/name).read_bytes())
    (art/'specification.yaml').write_bytes((MODEL/c['variant']/'v0.1.0/specification.yaml').read_bytes())
    manifest=dict(run_id=runid,model_id=c['model_id'],version='0.1.0',model_status='DRAFT',status='RUNNING',role=period,started_at_utc=now(),environment=environment(),configuration=c,code=[meta(MODEL/'run.py'),meta(MODEL/'data.py')],definition=meta(MODEL/c['variant']/'v0.1.0/specification.yaml'))
    js(run/'manifest.json',manifest);return run,art,manifest
def complete(run,art,m,status='COMPLETE'):
    m.update(status=status,model_status='EXPERIMENTAL',finished_at_utc=now(),outputs=[meta(p) for p in sorted(art.rglob('*')) if p.is_file()]);js(run/'manifest.json',m)
    (run/'README.md').write_text('# '+m['run_id']+'\n\n'+status+'; EXPERIMENTAL. See manifest.json and artifacts/. Values are selected one-decision diagnostics; no recommended action.\n',encoding='utf-8')

def develop(args):
    c=cfg(args.model);run,art,m=new_run(c,'development_2024_2025',args.run_id)
    try:
        d=pd.read_pickle(args.data);d=d[d['eligible_'+args.model]].copy();d['A']=d['A_'+args.model].astype(int);d=features(d,c).reset_index(drop=True)
        m['inputs']=[meta(args.data)];js(run/'manifest.json',m)
        s,logs,records,tuning=evaluate_development(d,c,art);m['metrics']=diagnostics(s,c,art)
        print(now(),args.model,'final policy start',flush=True)
        policy,inner=crossfit_policy(d,c,c['seed']+9000,'final_policy',logs,records,tuning)
        inner.to_pickle(art/'final_policy_training_scores.pkl')
        nu,tu=nuisance(d,c,'final_nuisance',c['seed']+9900,logs,records);tuning.extend(tu)
        with (art/'final_nuisance.pkl').open('wb') as f:pickle.dump(nu,f,protocol=5)
        js(art/'final_policy.json',policy);js(art/'final_hyperparameters.json',nu.alpha);js(art/'fold_records.json',records);csv(art/'fit_diagnostics.csv',logs);csv(art/'tuning.csv',tuning)
        m['final_hyperparameters']=nu.alpha;m['all_fits_converged']=all(x['converged'] for x in logs);complete(run,art,m)
        print(now(),'COMPLETE',args.run_id,m['metrics'],flush=True)
    except Exception:
        m['error']=traceback.format_exc();complete(run,art,m,'FAILED');raise

def seal(args):
    path=Path(args.output)
    if path.exists():raise FileExistsError(path)
    files=[MODEL/'run.py',MODEL/'data.py',MODEL/'verify_bcap.py',MODEL/'design_decisions.md',MODEL/'measurement_review.md']
    for model,runid in [('pitch',args.pitch_run),('swing',args.swing_run)]:
        a=ANAL/'runs'/runid/'artifacts';mf=read(a.parent/'manifest.json');assert mf['status']=='COMPLETE'
        files.extend([MODEL/model/'v0.1.0/specification.yaml',a/'final_nuisance.pkl',a/'final_policy.json',a/'final_hyperparameters.json',a.parent/'manifest.json'])
    js(path,dict(sealed_at_utc=now(),scope='BCAP definitions, engine, verification, final development nuisance/policy, external procedure before current-task external action outcomes',prior_exposure='2023/2026 were already used for BCAI/Ridge. Hash cannot prove universal non-exposure.',files=[meta(p) for p in files],pitch_run=args.pitch_run,swing_run=args.swing_run,external_nuisance='3fold games; frozen development alpha; external train-only dictionaries and calibration; development policy fixed',swing_2026='WITHHELD_MEASUREMENT_NONCOMPARABILITY'))
    print('SEALED',str(path),sha(path),flush=True)
def checkseal(path):
    s=read(path)
    for f in s['files']:
        if sha(ROOT/f['path'])!=f['sha256']:raise RuntimeError('Seal mismatch '+f['path'])
    return s

def external(args):
    sealed=checkseal(args.seal);c=cfg(args.model);period=str(args.year);run,art,m=new_run(c,'external_'+period,args.run_id)
    m['seal']=meta(args.seal)
    if args.model=='swing' and args.year==2026:
        m['evaluation_status']='WITHHELD_MEASUREMENT_NONCOMPARABILITY';m['outcome_evaluations']=0;m['reason']='2026 plate middle / ABS zone differs; no validated bridge; no replacement model used';complete(run,art,m,'WITHHELD');return
    try:
        js(art/'external_access_log.json',dict(first_current_task_BCAP_external_row_access_utc=now(),year=args.year,prior_exposure='BCAI/Ridge used this snapshot previously',action='load existing raw, construct Y and action, evaluate fixed policy; no external policy learning',seal=meta(args.seal)))
        from data import prepare
        out=COL/'data/processed'/('bcap_'+str(args.year)+'_v010_'+args.run_id+'.pkl')
        d,preparation=prepare([args.year],out,art/'preparation',external_seal=args.seal)
        m['raw_inputs']=preparation['inputs']
        d=d[d['eligible_'+args.model]].copy();d['A']=d['A_'+args.model].astype(int);d=features(d,c).reset_index(drop=True)
        m['inputs']=[meta(out)];dev=ANAL/'runs'/sealed[args.model+'_run']/'artifacts'
        with (dev/'final_nuisance.pkl').open('rb') as f:nu=pickle.load(f)
        policy=read(dev/'final_policy.json');fixed=score(d,nu.predict(d,c),c);fixed['fold']=-1;fixed=apply_policy(fixed,policy)
        fixed.to_pickle(art/'fixed_development_predictions.pkl');(art/'fixed_prediction_diagnostics').mkdir();m['fixed_development_prediction_metrics']=diagnostics(fixed,c,art/'fixed_prediction_diagnostics')
        logs=[];records=[];tuning=[];parts=[];fd=folds(d,c['external_folds'],c['seed']+args.year)
        for k in range(c['external_folds']):
            print(now(),args.model,args.year,'external evaluation nuisance',k,flush=True)
            tr=d[fd!=k];te=d[fd==k];lab='external'+str(k);split_record(records,lab,'external_ope',tr,te)
            nf,tu=nuisance(tr,c,lab,c['seed']+args.year+100+k,logs,records,nu.alpha)
            ss=score(te,nf.predict(te,c),c);ss['fold']=k;ss=apply_policy(ss,policy)
            # Known/unseen defined against development roster, not external refit roster.
            ss['known_pitcher']=te.pitcher.astype(str).isin(nu.known_pitcher).to_numpy();ss['known_batter']=te.batter.astype(str).isin(nu.known_batter).to_numpy();parts.append(ss)
        s=pd.concat(parts).sort_index();s.to_pickle(art/'scores.pkl');js(art/'fold_records.json',records);csv(art/'fit_diagnostics.csv',logs);m['metrics']=diagnostics(s,c,art);m['policy_source']=meta(dev/'final_policy.json');m['outcome_evaluations']=1;m['all_fits_converged']=all(x['converged'] for x in logs);complete(run,art,m)
        print(now(),'COMPLETE',args.run_id,m['metrics'],flush=True)
    except Exception:
        m['error']=traceback.format_exc();complete(run,art,m,'FAILED');raise

def main():
    p=argparse.ArgumentParser();sp=p.add_subparsers(dest='command',required=True)
    d=sp.add_parser('develop');d.add_argument('--model',choices=['pitch','swing'],required=True);d.add_argument('--data',required=True);d.add_argument('--run-id',required=True)
    s=sp.add_parser('seal');s.add_argument('--pitch-run',required=True);s.add_argument('--swing-run',required=True);s.add_argument('--output',required=True)
    e=sp.add_parser('external');e.add_argument('--model',choices=['pitch','swing'],required=True);e.add_argument('--year',type=int,choices=[2023,2026],required=True);e.add_argument('--run-id',required=True);e.add_argument('--seal',required=True)
    a=p.parse_args();globals()[{'develop':'develop','seal':'seal','external':'external'}[a.command]](a)
if __name__=='__main__':main()
