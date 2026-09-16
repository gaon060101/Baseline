"""V2 development numerical core reused from BCAP v0.1.0. No external/policy/bootstrap entry points."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys, json, hashlib, datetime, platform, argparse, traceback, pickle
ROOT=Path(__file__).resolve().parents[4]
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
SAVE_DIR=None
def save_tuning_model(model,label):
    if SAVE_DIR is not None:
        path=Path(SAVE_DIR)/(label+'.pkl');path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('wb') as f:pickle.dump(model,f,protocol=5)
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
    if frozen_alpha is None:split_record(records,label+'/tune','tuning',fit,tune)
    fs=c['features'];model=Nuisance();choices={};tuning=[]
    if frozen_alpha is None:
        for target in ['p','m0','m1']:
            ar=None if target=='p' else int(target[-1]);ft=fit if ar is None else fit[fit.A.eq(ar)]
            ev=tune if ar is None else tune[tune.A.eq(ar)]
            y=ft.A.to_numpy(dtype=float) if ar is None else ft.Y.to_numpy()
            for alpha in c['alphas']:
                reg=Ridge(ft,y,fs,alpha,label+'/tune/'+target+'/'+str(alpha),logs)
                save_tuning_model(reg,label+'/tune/'+target+'/'+str(alpha))
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
    model.calibration_rows=cal[['row_id','game_pk','A']].copy();model.calibration_rows['raw_propensity']=r
    model.training_games=sorted(map(int,train.game_pk.unique()));model.internal_seed=seed
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
