"""Prespecified external-year nuisance cross-fitting; no development refitting."""
from pathlib import Path
import argparse, json, pickle, shutil, sys, traceback
import numpy as np
import pandas as pd
import engine as E

B=Path(__file__).resolve().parent; ROOT=B.parents[3]; AN=B.parent
KEY=['game_pk','at_bat_number','pitch_number']
COUNTS=[f'{b}-{s}' for b in range(4) for s in range(3)]
REGIONS=['HIGH','LOW','INSIDE','OUTSIDE','CENTER']

def seal_check():
    for x in E.read(B/'plan_seal.json')['files']:
        if E.sha(ROOT/x['path'])!=x['sha256']: raise AssertionError('sealed input/code changed: '+x['path'])

def regions(d):
    valid=np.isfinite(d[['plate_x','plate_z','sz_top','sz_bot']].to_numpy(float)).all(axis=1)&d.sz_top.gt(d.sz_bot).to_numpy()
    x=d.plate_x*np.where(d.stand.eq('R'),1,np.where(d.stand.eq('L'),-1,np.nan))
    return dict(CENTER=valid & d.plate_x.abs().le(17/24)&d.plate_z.ge(d.sz_bot)&d.plate_z.le(d.sz_top),
        HIGH=valid&d.plate_z.gt(d.sz_top),LOW=valid&d.plate_z.lt(d.sz_bot),INSIDE=valid&x.lt(-17/24),OUTSIDE=valid&x.gt(17/24))

def family(model,count): return 4 if model=='pitch_sb' and count in ['0-2','1-2'] else 236

def summarize(whole,mask,c,fam):
    d=whole[mask];n=len(d);r=dict(n_all=len(whole),n=n,coverage=n/len(whole) if len(whole) else 0,games=d.game_pk.nunique(),PA=len(d[KEY[:2]].drop_duplicates()),pitchers=d.pitcher.nunique(),batters=d.batter.nunique(),action1_rate_all=whole.A.mean(),action1_rate=d.A.mean())
    for a in [0,1]:
        prob=d.p if a else 1-d.p;w=d.A.eq(a)/prob;wg=w.groupby(d.game_pk).sum();pos=w[w>0]
        r.update({f'rows{a}':int(d.A.eq(a).sum()),f'ESS{a}':float(w.sum()**2/np.square(w).sum()) if len(pos) else 0.,f'games{a}':d.loc[d.A.eq(a),'game_pk'].nunique(),f'max_game_share{a}':float(wg.max()/wg.sum()) if len(pos) else 1.,f'max_weight{a}':w.max(),f'weight_p99_{a}':pos.quantile(.99),f'Q{a}':d['phi'+str(a)].mean(),f'gcomp{a}':d['mu'+str(a)].mean(),f'naive{a}':d.loc[d.A.eq(a),'Y'].mean()})
    reasons=[]
    if n<c['min_rows']:reasons.append('n<500')
    if min(r['ESS0'],r['ESS1'])<c['min_ess']:reasons.append('armESS<200')
    if min(r['games0'],r['games1'])<c['min_arm_games']:reasons.append('armGames<100')
    if r['coverage']<c['min_coverage']:reasons.append('coverage<.5')
    if max(r['max_game_share0'],r['max_game_share1'])>c['max_game_share']:reasons.append('maxGameShare>.05')
    st=E.cluster_stat(d,d.phi1-d.phi0,fam)
    r.update(delta=st[0],SE=st[1],nominal95_low=st[2],nominal95_high=st[3],adjusted95_low=st[4],adjusted95_high=st[5],family=fam,support_gate=not reasons,support_reasons=';'.join(reasons),naive_delta=r['naive1']-r['naive0'],gcomp_delta=r['gcomp1']-r['gcomp0'])
    r['gcomp_aipw_flip']=r['gcomp_delta']*r['delta']<0
    r['p_min']=d.p.min();r['p01']=d.p.quantile(.01);r['p50']=d.p.median();r['p99']=d.p.quantile(.99);r['p_max']=d.p.max()
    return r

def fit(year,model):
    seal_check();plan=E.read(B/'plan.json');task=plan['runs'][str(year)][model];run=AN/'runs'/task['run_id'];assert not run.exists()
    art=run/'artifacts';art.mkdir(parents=True)
    c=E.read(ROOT/task['definition']);c['weights']=plan['weights'];c['fixed_alpha']=task['fixed_alpha']
    m=dict(run_id=task['run_id'],model_id=c['model_id'],version=c['version'],model_status='EXPERIMENTAL',status='RUNNING',year=year,scope='Fixed algorithm external-year 3-fold nuisance crossfit for adjusted pattern replication; not frozen development prediction or policy evaluation',started_at_utc=E.now(),configuration=c,plan=E.meta(B/'plan.json'),seal=E.meta(B/'plan_seal.json'),command=[sys.executable]+sys.argv,environment=E.environment())
    E.js(run/'manifest.json',m)
    if task['measurement_hold']:
        m.update(status='WITHHELD_MEASUREMENT',reason='2026 plate plane and strike-zone definition differ; no validated conversion',measurement=E.meta(B/'measurement_review.json'),finished_at_utc=E.now(),model_fits=0)
        E.js(run/'manifest.json',m);return
    checks=[]
    def ck(name,yes,detail=None):
        checks.append(dict(check=name,status='PASS' if bool(yes) else 'FAIL',detail=detail))
        if not yes:raise AssertionError(name)
    try:
        for p in [B/'engine.py',Path(__file__),ROOT/task['definition']]:shutil.copy2(p,art/('frozen_'+p.name))
        prep=E.read(B/f'preparation_{year}'/'preparation.json');inp=ROOT/prep['output']['path']
        E.js(art/'external_access_log.json',dict(first_current_task_model_row_access_utc=E.now(),plan_sealed_at_utc=E.read(B/'plan_seal.json')['sealed_at_utc'],prior_exposure=plan['prior_exposure'],question='external pattern replication via fixed algorithm, not frozen predictor test'))
        ck('prepared_hash',E.sha(inp)==prep['output']['sha256']);m['input']=E.meta(inp)
        d=pd.read_pickle(inp);eligible='eligible_pitch' if model=='pitch_ff' else 'eligible_'+model
        d=d[d[eligible]].copy();d['A']=d['A_pitch_ff' if model=='pitch_ff' else 'A_'+model].astype(int)
        d=E.features(d,c).reset_index(drop=True)
        ck('year_keys',set(d.game_year)=={year} and d.row_id.is_unique and not d.duplicated(KEY).any())
        ck('count_action_Y',d['count'].isin(COUNTS).all() and d.A.isin([0,1]).all() and np.isfinite(d.Y).all())
        forbidden={'description','events','Y','result','final_event','A','pitch_type','prev_pitch_type'}
        if model!='swing':forbidden|={'release_speed','pfx_x','pfx_z','plate_x','plate_z','zone','sz_top','sz_bot','swing_cell','relative_z_bin','plate_x_bin'}
        if model in ['pitch','pitch_ff']:forbidden.add('pitch_group')
        ck('no_forbidden_features',not forbidden&set(c['features']))
        if model=='pitch_ff':ck('FF_closed_action',d.pitch_type.isin(plan['actions']['FB']+plan['actions']['NFB']).all() and d.A.eq(d.pitch_type.eq('FF')).all())
        fd=E.folds(d,3,plan['seed']);d['fold']=fd
        ck('one_fold_per_game',d.groupby('game_pk').fold.nunique().eq(1).all())
        E.csv(art/'fold_membership.csv',d[['row_id']+KEY+['game_year','A','fold']])
        logs=[];records=[];parts=[];E.SAVE_DIR=None
        for k in range(3):
            tr=d[fd!=k];te=d[fd==k];label='fold'+str(k);E.split_record(records,label,'external_oof',tr,te)
            print(E.now(),year,model,label,'train',len(tr),'evaluate',len(te),flush=True)
            nu,tu=E.nuisance(tr,c,label,plan['seed']+2000+k,logs,records,frozen_alpha=c['fixed_alpha'])
            ck(label+'_no_external_tuning',not tu)
            ck(label+'_training_games',set(nu.training_games)==set(tr.game_pk))
            for rec in records:
                if rec['fit_id'].startswith(label+'/'):ck(rec['fit_id']+'_inside_training',not set(te.game_pk)&(set(rec['train_games'])|set(rec['evaluation_games'])))
            path=art/'fits'/label/'nuisance.pkl';path.parent.mkdir(parents=True)
            with path.open('wb') as f:pickle.dump(nu,f,protocol=5)
            s=E.score(te,nu.predict(te,c),c)
            for col in ['row_id','fold','pitch_type','known_count_exception']:s[col]=te[col]
            if model=='swing':
                rr=regions(te)
                for name,flag in rr.items():s['region_'+name]=np.asarray(flag)
                ck(label+'_region_max_two',np.stack([np.asarray(x) for x in rr.values()]).sum(axis=0).max()<=2)
            ck(label+'_finite_predictions',np.isfinite(s[['p','mu0','mu1','phi0','phi1']]).all().all())
            ck(label+'_converged',all(x['converged'] for x in logs))
            parts.append(s);E.csv(art/'fit_diagnostics.csv',logs);E.js(art/'fold_records.json',records)
        s=pd.concat(parts).sort_values('row_id');s.to_pickle(art/'scores.pkl')
        ck('all_rows_once',len(s)==len(d) and s.row_id.is_unique)
        rows=[]
        for count in COUNTS:
            wh=s[s['count'].eq(count)]
            groups=[('ALL',wh)] if model!='swing' else [(r,wh[wh['region_'+r]]) for r in REGIONS]
            for region,g in groups:
                v=summarize(g,g.support,c,family(model,count));v.update(year=year,model=model,count=count,region=region,population='own',action0=c['action0'],action1=c['action1'])
                if model=='swing':v['fraction_of_count_all']=len(g)/len(wh)
                rows.append(v)
        vals=pd.DataFrame(rows);E.csv(art/'values.csv',vals)
        ck('Q_delta',np.allclose(vals.Q1-vals.Q0,vals.delta,atol=1e-12,rtol=0,equal_nan=True))
        ck('same_denominator',vals.rows0.add(vals.rows1).eq(vals.n).all())
        diag=[];cal=[];known=[];ex=[]
        dev=plan['development_rosters']
        s['known_dev_pitcher']=s.pitcher.isin(dev['pitcher']);s['known_dev_batter']=s.batter.isin(dev['batter'])
        for tag,mask in [('all',np.ones(len(s),bool)),('known_dev_both',s.known_dev_pitcher&s.known_dev_batter),('unseen_dev_any',~(s.known_dev_pitcher&s.known_dev_batter)),('unknown_external_nuisance_any',~(s.known_pitcher&s.known_batter))]:
            g=s[mask];known.append(dict(group=tag,n=len(g),support=int(g.support.sum()),MSE=np.square(g.Y-np.where(g.A.eq(1),g.mu1,g.mu0)).mean(),Brier=np.square(g.A-g.p).mean(),metric_scope='external own OOF nuisance; not frozen development predictor'))
        for count,g in s.groupby('count',observed=True):
            for name,gg in [('all',g),('support',g[g.support])]:
                diag.append(dict(count=count,population=name,n=len(gg),p_min=gg.p.min(),p01=gg.p.quantile(.01),p05=gg.p.quantile(.05),p50=gg.p.median(),p95=gg.p.quantile(.95),p99=gg.p.quantile(.99),p_max=gg.p.max(),Brier=np.square(gg.A-gg.p).mean()))
            for name,gg in g.groupby(pd.cut(g.p,np.linspace(0,1,11),include_lowest=True),observed=True):cal.append(dict(count=count,bin=str(name),n=len(gg),mean_p=gg.p.mean(),actual1=gg.A.mean()))
        why=np.select([~s.measurement_support,~s.repertoire,~s.p.between(.05,.95)],['measurement','training_arm_support','propensity_tail'],default='supported')
        for reason,n in pd.Series(why).value_counts().items():ex.append(dict(reason=reason,n=int(n)))
        E.csv(art/'propensity.csv',diag);E.csv(art/'calibration.csv',cal);E.csv(art/'known_unseen.csv',known);E.csv(art/'support_exclusions.csv',ex)
        if model=='swing':
            audit=[]
            for count,g in s.groupby('count',observed=True):
                copies=g[['region_'+r for r in REGIONS]].sum(axis=1)
                audit.append(dict(count=count,unique_rows=len(g),assigned_unique_rows=int(copies.gt(0).sum()),overlap_rows=int(copies.eq(2).sum()),membership_total=int(copies.sum()),unassigned=int(copies.eq(0).sum())))
            E.csv(art/'region_overlap_counts.csv',audit)
        metrics=dict(n=len(s),support=int(s.support.sum()),games=s.game_pk.nunique(),all_fit_converged=all(x['converged'] for x in logs),fit_logs=len(logs),MSE=np.square(s.Y-np.where(s.A.eq(1),s.mu1,s.mu0)).mean(),Brier=np.square(s.A-s.p).mean(),metric_scope='external own OOF nuisance only',policy_learning=False)
        E.js(art/'metrics.json',metrics);E.js(art/'basic_checks.json',dict(status='PASS',checks=checks))
        m.update(status='COMPLETE',finished_at_utc=E.now(),metrics=metrics,outputs=[E.meta(p) for p in sorted(art.rglob('*')) if p.is_file()]);E.js(run/'manifest.json',m)
        print(E.now(),'COMPLETE',year,model,flush=True)
    except Exception:
        m.update(status='FAILED',finished_at_utc=E.now(),error=traceback.format_exc());E.js(run/'manifest.json',m);E.js(art/'basic_checks.json',dict(status='FAIL',checks=checks,error=m['error']));raise

def compare(year):
    seal_check();p=E.read(B/'plan.json');run=AN/'runs'/p['comparison_runs'][str(year)];assert not run.exists();art=run/'artifacts';art.mkdir(parents=True)
    paths={model:AN/'runs'/p['runs'][str(year)][model]['run_id']/'artifacts/scores.pkl' for model in ['pitch','pitch_ff']}
    ss={k:pd.read_pickle(v).set_index('row_id').sort_index() for k,v in paths.items()};o=ss['pitch'];f=ss['pitch_ff']
    assert o.index.equals(f.index) and o[KEY+['game_year','count','fold','Y']].equals(f[KEY+['game_year','count','fold','Y']])
    common=o.support&f.support;mem=o[KEY+['count','fold']].copy();mem['support_FB']=o.support;mem['support_FF']=f.support;mem['common_support']=common;mem.to_pickle(art/'comparison_membership.pkl')
    rows=[];foldrows=[];comp=[]
    for model,s in ss.items():
        c=E.read(ROOT/p['runs'][str(year)][model]['definition'])
        for count in COUNTS:
            wh=s[s['count'].eq(count)]
            for pop in ['own','common']:
                mask=wh.support if pop=='own' else common.loc[wh.index]
                r=summarize(wh,mask,c,236);r.update(year=year,model=model,count=count,region='ALL',population=pop,action0=c['action0'],action1=c['action1']);rows.append(r)
                for code,g in wh[mask].groupby('pitch_type',observed=True):comp.append(dict(model=model,count=count,population=pop,pitch_type=code,n=len(g)))
                for k in range(3):
                    ww=wh[wh.fold.eq(k)];kk=ww.support if pop=='own' else common.loc[ww.index]
                    rr=summarize(ww,kk,c,1);rr.update(year=year,model=model,count=count,region='ALL',population=pop,fold=k,interval_role='descriptive nominal only, no subgroup significance claim');foldrows.append(rr)
    E.csv(art/'values.csv',rows);E.csv(art/'fold_values.csv',foldrows);E.csv(art/'pitch_composition.csv',comp)
    E.js(art/'basic_checks.json',dict(status='PASS',same_eligible_keys_counts_folds_Y=True,common_support=int(common.sum()),no_fitting=True))
    E.js(run/'manifest.json',dict(run_id=run.name,model_id='BCAP-PITCH-FF-v0.1.0',models=['BCAP-PITCH-v0.2.0','BCAP-PITCH-FF-v0.1.0'],model_status='EXPERIMENTAL',status='COMPLETE',year=year,completed_at_utc=E.now(),inputs=[E.meta(v) for v in paths.values()],plan=E.meta(B/'plan.json'),outputs=[E.meta(v) for v in art.iterdir() if v.is_file()]))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,choices=[2023,2026],required=True);ap.add_argument('--model',choices=['pitch_sb','swing','pitch','pitch_ff','compare'],required=True);a=ap.parse_args()
    if a.model=='compare':compare(a.year)
    else:fit(a.year,a.model)
