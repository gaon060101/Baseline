"""Independent saved-artifact audit. Never imports production engine or refits."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import sys, json, pickle, hashlib, datetime, platform, gc
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
RUNS=ROOT/'columns/001-ball-count/analysis/runs'
START=datetime.datetime.now(datetime.timezone.utc).isoformat()
CHECKS=[]; EVIDENCE={}; DIFFS=[]; FITS=[]; POLICY=[]
DEV={'pitch':'bcap_pitch__mlb_2024_2025__20260909__r02','swing':'bcap_swing__mlb_2024_2025__20260909__r01'}
EXT={'pitch':[(2023,'bcap_pitch__mlb_2023__20260909__r01'),(2026,'bcap_pitch__mlb_2026_ytd_20260907__20260909__r01')],'swing':[(2023,'bcap_swing__mlb_2023__20260909__r01')]}

def stamp(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def evidence(p):
    p=Path(p); key=p.relative_to(ROOT).as_posix()
    if key not in EVIDENCE:
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
        EVIDENCE[key]={'path':key,'sha256':h.hexdigest(),'bytes':p.stat().st_size,'read_at_utc':stamp()}
    return p
def js(p):return json.loads(evidence(p).read_text(encoding='utf-8-sig'))
def frame(p):return pd.read_pickle(evidence(p))
def table(p):return pd.read_csv(evidence(p))
def check(run,name,ok,scope='',**extra):
    CHECKS.append(dict(run_id=run,check=name,status='PASS' if ok else 'FAIL',scope=scope,**extra))
def note(run,name,scope):CHECKS.append(dict(run_id=run,check=name,status='NOT_VERIFIABLE',scope=scope))
def numeric(run,name,a,b,atol=1e-8,rtol=1e-8):
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    good=np.isclose(a,b,atol=atol,rtol=rtol,equal_nan=True)
    finite=np.isfinite(a)&np.isfinite(b);delta=np.abs(a[finite]-b[finite])
    check(run,name,bool(np.all(good)),n=int(a.size),mismatch_n=int(np.sum(~good)),max_absolute_error=float(delta.max(initial=0)),max_relative_error=float((delta/np.maximum(np.abs(b[finite]),1e-300)).max(initial=0)),atol=atol,rtol=rtol)
    if not np.all(good):
        for i in np.flatnonzero(~good)[:100]:DIFFS.append(dict(run_id=run,check=name,position=int(i),reconstructed=float(a[i]),saved=float(b[i])))
def exact(run,name,a,b):
    a=np.asarray(a);b=np.asarray(b);good=a==b
    check(run,name,bool(np.all(good)),n=int(a.size),mismatch_n=int(np.sum(~good)))
def assign(d,k,seed):
    g=np.unique(d.game_pk.to_numpy()).copy();np.random.default_rng(seed).shuffle(g)
    lookup=dict(zip(g,np.arange(len(g))%k));return d.game_pk.map(lookup).to_numpy()
def games(d):return set(map(int,d.game_pk.unique()))
def materialize(p,variant):
    x=frame(p);d=x.loc[x['eligible_'+variant]].copy();del x
    d['A']=d['A_'+variant].astype(int);d=d.reset_index(drop=True)
    if variant=='swing':
        for col,width in [('release_speed',5),('pfx_x',.5),('pfx_z',.5),('plate_x',.35)]:
            v=pd.to_numeric(d[col],errors='coerce').to_numpy(dtype=float)
            d[col+'_bin']=pd.Series(np.where(np.isnan(v),-999,np.floor(v/width))).astype(int).astype(str)
        z=((d.plate_z-d.sz_bot)/(d.sz_top-d.sz_bot)).to_numpy(dtype=float)
        d['relative_z_bin']=pd.Series(np.where(np.isfinite(z),np.floor(z/.2),-999)).astype(int).astype(str)
        d['swing_cell']=d['count'].astype(str)+'|'+d.zone.astype(str)+'|'+d.pitch_group.astype(str)
    return d
def strings(d,f):return d[f].astype('string').fillna('MISSING').astype(str)

class Container:pass
class ModelReader(pickle.Unpickler):
    def find_class(self,module,name):
        if module in ('__main__','run') and name in ('Nuisance','Ridge','Design'):return Container
        if module=='builtins' and name in ('set','frozenset'):return super().find_class(module,name)
        if module.startswith('numpy') and name in ('_frombuffer','_reconstruct','ndarray','dtype','scalar'):return super().find_class(module,name)
        raise pickle.UnpicklingError('Unapproved model global '+module+'.'+name)
def model(p):
    with evidence(p).open('rb') as f:return ModelReader(f).load()
def predict(reg,d):
    # Explicit reference coding of centered blocks; unknown levels add zero.
    ans=np.full(len(d),reg.intercept,dtype=float)
    for f,m,(lo,hi) in zip(reg.design.features,reg.design.maps,reg.design.blocks):
        ix=strings(d,f).map(m).fillna(-1).to_numpy(dtype=int);ok=ix>=0
        center=float(np.dot(reg.design.mean[lo:hi],reg.beta[lo:hi]))
        ans[ok]+=reg.beta[ix[ok]]-center
    return ans
def sigmoid(v):
    # Stable direct calculation independent of scipy.special.expit.
    v=np.asarray(v);out=np.empty_like(v);pos=v>=0
    out[pos]=1/(1+np.exp(-v[pos]));a=np.exp(v[~pos]);out[~pos]=a/(1+a);return out

def verify_records(run,d,c,art,development=True,year=None):
    rec=js(art/'fold_records.json'); lookup={r['fit_id']:r for r in rec};expected={};nuisance_train={};seeds={}
    def record(label,role,tr,te):expected[label]=(role,games(tr),games(te))
    def nurecord(label,tr,seed):
        f=assign(tr,5,seed);record(label+'/cal','calibration',tr[f!=0],tr[f==0]);record(label+'/tune','tuning',tr[f>=2],tr[f==1]);nuisance_train[label]=tr.index.to_numpy();seeds[label]=seed
    fold=assign(d,3,c['seed'] if development else c['seed']+year)
    if development:
        for k in range(3):
            tr=d[fold!=k];te=d[fold==k];lab='outer'+str(k);record(lab,'outer_evaluation',tr,te)
            ff=assign(tr,2,c['seed']+1000+100*k)
            for j in range(2):
                label=lab+'/inner'+str(j);record(label,'policy_oof',tr[ff!=j],tr[ff==j]);nurecord(label,tr[ff!=j],c['seed']+1000+100*k+100+j)
            nurecord(lab+'/evaluation_nuisance',tr,c['seed']+2000+k)
        ff=assign(d,2,c['seed']+9000)
        for j in range(2):
            lab='final_policy/inner'+str(j);record(lab,'policy_oof',d[ff!=j],d[ff==j]);nurecord(lab,d[ff!=j],c['seed']+9000+100+j)
        nurecord('final_nuisance',d,c['seed']+9900)
    else:
        for k in range(3):
            lab='external'+str(k);tr=d[fold!=k];te=d[fold==k];record(lab,'external_ope',tr,te);nurecord(lab,tr,c['seed']+year+100+k)
    check(run,'fold_record_labels_exact',len(lookup)==len(rec) and set(lookup)==set(expected),records=len(rec),expected_records=len(expected))
    for label,(role,tr,te) in expected.items():
        r=lookup[label];check(run,'fold/'+label,r['role']==role and set(r['train_games'])==tr and set(r['evaluation_games'])==te and not (tr&te),train_games=len(tr),evaluation_games=len(te),overlap=len(tr&te))
        ancestors=[name for name in expected if label.startswith(name+'/') and expected[name][0] in ('outer_evaluation','policy_oof','external_ope')]
        for a in ancestors:
            holdout=expected[a][2]
            check(run,'ancestor_holdout/'+label+'/under/'+a,not ((tr|te)&holdout),ancestor_evaluation_games=len(holdout),descendant_overlap=len((tr|te)&holdout))
    logs=table(art/'fit_diagnostics.csv');tuning=table(art/'tuning.csv') if development else None
    check(run,'fit_ids_unique',logs.fit_id.is_unique,fit_records=len(logs))
    ridge=logs[logs.alpha.notna()];cal=logs[logs.fit_id.str.endswith('/calibrator')]
    check(run,'recorded_ridge_convergence',bool((ridge.solver_info.eq(0)&ridge.relative_gradient.lt(c['solver']['relative_gradient_limit'])&ridge.converged.eq(True)).all()),fits=len(ridge),maximum_relative_gradient=float(ridge.relative_gradient.max()),maximum_iterations=int(ridge.iterations.max()),evidence='Saved logs; only final coefficients receive independent actual residual checks below')
    check(run,'recorded_calibration_convergence',bool(cal.converged.eq(True).all()),fits=len(cal),evidence='Saved optimizer success; only final saved calibrator gets objective/gradient recreation')
    chosen={}
    for lab,idx in nuisance_train.items():
        tr=d.loc[idx];ff=assign(tr,5,seeds[lab]);fit=tr[ff>=2];base=tr[ff!=0];cald=tr[ff==0]
        selected={}
        if development:
            for target in ['p','m0','m1']:
                t=tuning[tuning.fit_id.eq(lab)&tuning.target.eq(target)]
                check(run,'tuning_candidates/'+lab+'/'+target,len(t)==len(c['alphas']) and set(t.alpha)==set(c['alphas']) and t.loss.notna().all(),n=len(t))
                best=t.sort_values(['loss','alpha'],ascending=[True,False]).iloc[0];selected[target]=int(best.alpha)
        else:selected=js(RUNS/DEV[c['variant']]/'artifacts/final_hyperparameters.json')
        chosen[lab]=selected
        for _,row in logs[logs.fit_id.str.startswith(lab+'/')].iterrows():
            suffix=row.fit_id[len(lab)+1:]
            if suffix=='prop':n=len(base);alpha=selected['p']
            elif suffix=='calibrator':n=len(cald);alpha=None
            elif suffix in ('m0','m1'):n=int(tr.A.eq(int(suffix[-1])).sum());alpha=selected[suffix]
            elif suffix.startswith('tune/'):
                target=suffix.split('/')[1];n=len(fit) if target=='p' else int(fit.A.eq(int(target[-1])).sum());alpha=int(suffix.split('/')[-1])
            else:continue
            check(run,'fit_training_size/'+row.fit_id,int(row.n)==n,expected_n=n,stored_n=int(row.n))
            if alpha is not None:check(run,'fit_alpha/'+row.fit_id,float(row.alpha)==alpha,expected_alpha=alpha,stored_alpha=float(row.alpha))
    if development:check(run,'final_selected_alphas',chosen['final_nuisance']==js(art/'final_hyperparameters.json'),choices=chosen['final_nuisance'])
    note(run,'nonfinal_fit_dictionary_and_actual_residual','No nonfinal fitted model objects saved. Training-only dictionary logic and row counts inspected; saved solver logs alone do not independently reproduce all nuisance fits or tuning losses.')
    return fold,nuisance_train,seeds,logs,chosen

def row_link(run,name,s,d,expected_index):
    exact(run,name+'/index',s.index.to_numpy(),np.sort(expected_index))
    x=d.loc[s.index]
    for col in ['game_pk','at_bat_number','pitch_number','A','Y','pitcher','batter','count']:
        exact(run,name+'/source_'+col,s[col].to_numpy(),x[col].to_numpy())
def metadata_prediction(run,name,s,train,c,development_roster=None):
    counts=pd.crosstab(train[c['support_entity']].astype(str),train.A).reindex(columns=[0,1],fill_value=0)
    repertoire=(counts.min(axis=1)>=c['min_entity_arm_training']).to_dict()
    expected=s[c['support_entity']].astype(str).map(repertoire).fillna(False).to_numpy(dtype=bool)
    exact(run,name+'/repertoire',expected,s.repertoire.to_numpy())
    roster=train if development_roster is None else development_roster
    for who in ['pitcher','batter']:
        exact(run,name+'/known_'+who,s[who].astype(str).isin(set(roster[who].astype(str))).to_numpy(),s['known_'+who].to_numpy())
def verify_policy(run,name,s,policy,c):
    p=s.p.to_numpy();a=s.A.to_numpy();y=s.Y.to_numpy();m0=s.mu0.to_numpy();m1=s.mu1.to_numpy()
    difference=m1+a/p*(y-m1)-m0-(1-a)/(1-p)*(y-m0)
    z=s[c['policy_key']].astype(str).to_numpy();support=s.support.to_numpy();states={}
    for key in sorted(set(z[support])):
        mask=support&(z==key);delta=float(np.mean(difference[mask]));action=int(delta<0) if c['variant']=='pitch' else int(delta>0)
        states[key]=action;stored=policy['states'].get(key,{})
        ok=bool(stored) and stored['n']==int(mask.sum()) and stored['games']==s.loc[mask,'game_pk'].nunique() and stored['p1']==action and np.isclose(stored['delta'],delta,atol=1e-10,rtol=1e-9)
        check(run,name+'/state/'+key,ok,rows=int(mask.sum()),recomputed_delta=delta,stored_delta=stored.get('delta'),recomputed_p1=action,stored_p1=stored.get('p1'))
        POLICY.append(dict(run_id=run,policy=name,state=key,n=int(mask.sum()),delta=delta,p1=action,stored_delta=stored.get('delta'),stored_p1=stored.get('p1')))
    check(run,name+'/state_set',set(states)==set(policy['states']),states=len(states))
    check(run,name+'/fallback_and_scope',policy['key']==c['policy_key'] and policy['fallback_p1']==.5 and policy['conservative_change'] is False)
    check(run,name+'/tie_rule_source',True,scope='Independent strict <0 (PITCH) / >0 (SWING) implements action0 at exact zero; empirical zero-delta states counted below',exact_tie_states=sum(row['delta']==0 for row in POLICY if row['run_id']==run and row['policy']==name))
    return states
def apply_check(run,name,s,policy):
    values=s[policy['key']].astype(str).map({k:v['p1'] for k,v in policy['states'].items()}).fillna(policy['fallback_p1']).to_numpy()
    exact(run,name+'/applied_policy_probability',values,s.policy_p1.to_numpy())
    check(run,name+'/conservative_gate',s.conservative_change.eq(False).all() and np.array_equal(s.conservative_value.to_numpy(),s.Y.to_numpy()))

def final_fit_checks(run,d,c,nu,art,logs):
    ff=assign(d,5,c['seed']+9900);groups={'prop':d[ff!=0],'m0':d[d.A.eq(0)],'m1':d[d.A.eq(1)]}
    check(run,'final_object_alpha',nu.alpha==js(art/'final_hyperparameters.json'))
    for name,train in groups.items():
        reg=nu.prop if name=='prop' else nu.out[int(name[-1])];design=reg.design
        y=train.A.to_numpy(dtype=float) if name=='prop' else train.Y.to_numpy(dtype=float)
        check(run,'final_dictionary_features/'+name,design.features==c['features'] and 'pitcher' in design.features and 'batter' in design.features,features=design.features)
        mean=np.zeros(design.width);xx=[];offset=0;mapsok=True
        for f,m,block in zip(design.features,design.maps,design.blocks):
            values=strings(train,f);lev=sorted(values.unique());mapping={str(v):offset+i for i,v in enumerate(lev)}
            mapsok &= mapping==m and tuple(block)==(offset,offset+len(lev))
            ix=values.map(mapping).to_numpy(dtype=int);xx.append(ix);mean+=np.bincount(ix,minlength=design.width)/len(train);offset+=len(lev)
        check(run,'final_dictionary_training_only/'+name,mapsok and offset==design.width,rows=len(train),dictionary_width=design.width)
        numeric(run,'final_dictionary_means/'+name,mean,design.mean)
        numeric(run,'final_intercept/'+name,[y.mean()],[reg.intercept])
        pr=predict(reg,train);res=pr-y;alpha=nu.alpha['p' if name=='prop' else name]
        gradient=np.zeros(design.width);rhs=np.zeros(design.width)
        centered_y=y-y.mean()
        for ix in xx:
            gradient+=np.bincount(ix,weights=res,minlength=design.width)
            rhs+=np.bincount(ix,weights=centered_y,minlength=design.width)
        gradient-=len(train)*mean*res.mean();gradient+=alpha*reg.beta
        rel=float(np.max(np.abs(gradient))/max(1,np.max(np.abs(rhs))))
        objective=float(res@res+alpha*(reg.beta@reg.beta))
        check(run,'final_actual_normal_equation/'+name,rel<c['solver']['relative_gradient_limit'],relative_gradient=rel,limit=c['solver']['relative_gradient_limit'],objective=objective,rows=len(train),method='Bincount reconstruction of centered X transpose residual + alpha beta; no Gram/PCG or production functions')
        row=logs[logs.fit_id.eq('final_nuisance/'+name)].iloc[0]
        FITS.append(dict(run_id=run,component=name,n=len(train),relative_gradient=rel,stored_relative_gradient=float(row.relative_gradient),objective=objective,alpha=alpha))
        del xx,pr,res
    cald=d[ff==0];raw=predict(nu.prop,cald);a=cald.A.to_numpy(dtype=float);z=nu.cal[0]+nu.cal[1]*raw;e=sigmoid(z)
    loss=float(np.mean(np.logaddexp(0,z)-a*z)+1e-6*nu.cal[1]**2)
    grad=np.array([np.mean(e-a),np.mean((e-a)*raw)+2e-6*nu.cal[1]])
    row=logs[logs.fit_id.eq('final_nuisance/calibrator')].iloc[0]
    numeric(run,'final_calibration_objective',[loss],[row.loss],atol=1e-10,rtol=1e-9)
    numeric(run,'final_calibration_parameters',nu.cal,[row.intercept,row.slope])
    check(run,'final_calibration_feasible',nu.cal[1]>=0,gradient=grad.tolist(),gradient_max=float(np.max(np.abs(grad))),scope='Actual objective/gradient recomputed; optimizer stops on objective tolerance as well as gtol. No universal 1e-10 gradient certification inferred from success flag.')
    metadata_prediction(run,'final_model_rosters',d.assign(repertoire=d[c['support_entity']].astype(str).map(nu.repertoire).fillna(False),known_pitcher=d.pitcher.astype(str).isin(nu.known_pitcher),known_batter=d.batter.astype(str).isin(nu.known_batter)),d,c)

def external_checks(variant,year,run,nu,policy,devdata):
    art=RUNS/run/'artifacts';manifest=js(art.parent/'manifest.json');c=manifest['configuration'];d=materialize(ROOT/manifest['inputs'][0]['path'],variant)
    fold,nuisance_train,seeds,logs,chosen=verify_records(run,d,c,art,False,year)
    s=frame(art/'scores.pkl');row_link(run,'external_OPE_rows',s,d,d.index.to_numpy());exact(run,'external_OPE_fold',fold,s.fold.to_numpy());apply_check(run,'external_final_development_policy',s,policy)
    for k in range(3):metadata_prediction(run,'external_OPE_fold'+str(k),s[s.fold.eq(k)],d.loc[nuisance_train['external'+str(k)]],c,devdata)
    del s
    s=frame(art/'fixed_development_predictions.pkl');row_link(run,'fixed_model_rows',s,d,d.index.to_numpy());apply_check(run,'fixed_final_development_policy',s,policy)
    raw=predict(nu.prop,d);p=np.clip(sigmoid(nu.cal[0]+nu.cal[1]*raw),c['numerical_epsilon'],1-c['numerical_epsilon'])
    for col,value in [('raw_propensity',raw),('p',p),('mu0',predict(nu.out[0],d)),('mu1',predict(nu.out[1],d))]:numeric(run,'fixed_prediction/'+col,value,s[col].to_numpy())
    metadata_prediction(run,'fixed_prediction',s,devdata,c)
    ms=np.ones(len(d),dtype=bool)
    if variant=='swing':ms=d.zone.ne('MISSING').to_numpy()&d[['release_speed','pfx_x','pfx_z','plate_x','plate_z','sz_top','sz_bot']].notna().all(axis=1).to_numpy()&d.pitch_group.isin(['FB','NFB']).to_numpy()
    rep=d[c['support_entity']].astype(str).map(nu.repertoire).fillna(False).to_numpy(dtype=bool)
    exact(run,'fixed_prediction/measurement_support',ms,s.measurement_support.to_numpy());exact(run,'fixed_prediction/support',(p>=c['trim'])&(p<=1-c['trim'])&rep&ms,s.support.to_numpy())
    print(stamp(),'completed external',run,flush=True);del d,s;gc.collect()

def main():
    evidence(OUT/'review_folds_prediction.py');evidence(OUT.parent/'review_protocol.json')
    for variant,run in DEV.items():
        print(stamp(),'start',run,flush=True)
        art=RUNS/run/'artifacts';manifest=js(art.parent/'manifest.json');c=manifest['configuration'];d=materialize(ROOT/manifest['inputs'][0]['path'],variant)
        fold,nuisance_train,seeds,logs,chosen=verify_records(run,d,c,art)
        policies=js(art/'outer_policies.json');s=frame(art/'scores.pkl');row_link(run,'development_outer_rows',s,d,d.index.to_numpy());exact(run,'development_outer_fold',fold,s.fold.to_numpy())
        for k in range(3):
            ss=s[s.fold.eq(k)];apply_check(run,'outer'+str(k),ss,policies[k]);metadata_prediction(run,'outer'+str(k),ss,d.loc[nuisance_train['outer'+str(k)+'/evaluation_nuisance']],c)
        del s
        for k in range(3):
            s=frame(art/('outer'+str(k)+'_policy_training_scores.pkl'));row_link(run,'outer'+str(k)+'_policy_training',s,d,d.index[fold!=k].to_numpy());tr=d[fold!=k]
            expected_fold=assign(tr,2,c['seed']+1000+100*k);exact(run,'outer'+str(k)+'_policy_inner_fold',expected_fold,s.fold.to_numpy())
            verify_policy(run,'outer'+str(k),s,policies[k],c)
            for j in range(2):metadata_prediction(run,'outer'+str(k)+'/inner'+str(j),s[s.fold.eq(j)],d.loc[nuisance_train['outer'+str(k)+'/inner'+str(j)]],c)
            del s
        policy=js(art/'final_policy.json');s=frame(art/'final_policy_training_scores.pkl');row_link(run,'final_policy_training',s,d,d.index.to_numpy());exact(run,'final_policy_inner_fold',assign(d,2,c['seed']+9000),s.fold.to_numpy());verify_policy(run,'final_policy',s,policy,c)
        for j in range(2):metadata_prediction(run,'final_policy/inner'+str(j),s[s.fold.eq(j)],d.loc[nuisance_train['final_policy/inner'+str(j)]],c)
        del s;gc.collect();nu=model(art/'final_nuisance.pkl');final_fit_checks(run,d,c,nu,art,logs)
        for year,external_run in EXT[variant]:external_checks(variant,year,external_run,nu,policy,d)
        del d,nu;gc.collect()
    pd.DataFrame(CHECKS).to_csv(OUT/'checks.csv',index=False,encoding='utf-8-sig');pd.DataFrame(DIFFS).to_csv(OUT/'mismatches.csv',index=False,encoding='utf-8-sig');pd.DataFrame(FITS).to_csv(OUT/'final_actual_fit_diagnostics.csv',index=False,encoding='utf-8-sig');pd.DataFrame(POLICY).to_csv(OUT/'independent_policies.csv',index=False,encoding='utf-8-sig')
    (OUT/'validation.json').write_text(json.dumps({'started_at_utc':START,'finished_at_utc':stamp(),'counts':pd.Series([c['status'] for c in CHECKS]).value_counts().to_dict(),'checks':CHECKS},ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
    outputs=[p for p in OUT.iterdir() if p.is_file()]
    for p in outputs:evidence(p)
    env={'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'executable':sys.executable,'platform':platform.platform(),'argv':sys.argv,'scipy_used':False,'production_functions_imported':False,'model_refitting':False,'new_external_model_evaluation':False,'execution_class':['reaggregate_existing_summaries','restore_policy_from_saved_Y_A_nuisance','regenerate_predictions_from_existing_fit','evaluate_saved_coefficient_normal_equations']}
    (OUT/'evidence_manifest.json').write_text(json.dumps({'started_at_utc':START,'finished_at_utc':stamp(),'environment':env,'files':list(EVIDENCE.values())},ensure_ascii=False,indent=2),encoding='utf-8')
    print(stamp(),'DONE',pd.Series([c['status'] for c in CHECKS]).value_counts().to_dict(),flush=True)

if __name__=='__main__':main()
