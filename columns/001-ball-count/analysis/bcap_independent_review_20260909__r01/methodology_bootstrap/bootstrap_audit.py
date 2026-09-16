"""Independent 2026-09-09 resampling and stored-aggregate audit. Never fits models.

No BCAP engine or previous verifier is imported. Resampling is recreated from
source game aggregates; graph partitions and fit row counts are derived anew.
"""
import sys, json, hashlib, platform, math, datetime
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/백창현/Desktop/Baseline')
OUT = Path(__file__).resolve().parent
RUNS = ROOT/'columns/001-ball-count/analysis/runs'
START = datetime.datetime.now(datetime.timezone.utc).isoformat()
INPUTS = {}
COMPARISONS = []
def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def record(path):
    path=Path(path);key=path.relative_to(ROOT).as_posix()
    if key not in INPUTS:INPUTS[key]={'path':key,'sha256':digest(path),'bytes':path.stat().st_size}
    return path
def readj(p):return json.loads(record(p).read_text(encoding='utf-8-sig'))
def readc(p):return pd.read_csv(record(p))
def check(label,actual,expected,exact=False):
    if exact:
        good=bool(actual==expected);ae=None;re=None
    else:
        actual=float(actual);expected=float(expected)
        if math.isnan(actual) or math.isnan(expected):good=False;ae=None;re=None
        else:
            ae=abs(actual-expected);re=ae/max(abs(expected),1e-300)
            good=math.isfinite(actual) and math.isfinite(expected) and ae<=1e-9+1e-8*abs(expected)
    COMPARISONS.append({'check':label,'actual':actual,'expected':expected,'status':'PASS' if good else 'FAIL','absolute_error':ae,'relative_error':re,'exact':exact})
def gh(g):return hashlib.sha256(json.dumps(sorted(int(x) for x in g),separators=(',',':')).encode()).hexdigest()
def allocation(g,k,seed):
    vals=np.array(sorted(g),dtype=np.int64)
    permutation=np.random.default_rng(int(seed)).permutation(len(vals))
    return {int(vals[j]):i%k for i,j in enumerate(permutation)}
def put_csv(name,frame):
    with (OUT/name).open('x',encoding='utf-8-sig',newline='') as f:pd.DataFrame(frame).to_csv(f,index=False)
def put_json(name,obj):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)

def audit():
    protocol=readj(OUT.parent/'review_protocol.json')
    source=ROOT/'columns/001-ball-count/data/processed/bcap_dev_v010_20260909_r01.pkl'
    df=pd.read_pickle(record(source))
    records=[];stability_rows=[];inventory=[]
    for variant,suffix in [('pitch','r03'),('swing','r02')]:
        rid=f'bcap_{variant}__mlb_2024_2025__20260909__{suffix}'
        folder=RUNS/rid;manifest=readj(folder/'manifest.json');cfg=manifest['configuration']
        check(rid+'/completed',manifest['completed_replicates'],8,True)
        check(rid+'/status',manifest['status'],'COMPLETE',True)
        check(rid+'/final_policy_modified',manifest['final_policy_modified'],False,True)
        for item in manifest['inputs']+manifest['code']+manifest['outputs']:
            p=record(ROOT/item['path']);check(rid+'/hash/'+item['path'],digest(p),item['sha256'],True)
        d=df.loc[df['eligible_'+variant],['game_pk','game_year','count','A_'+variant]].copy()
        d.columns=['game_pk','game_year','count','A']
        agg=d.groupby(['game_year','game_pk','count'],observed=True).agg(n=('A','size'),n1=('A','sum')).reset_index()
        game=agg.groupby('game_pk',observed=True).agg(n=('n','sum'),n1=('n1','sum'),year=('game_year','first'))
        game['n0']=game.n-game.n1
        frames=[]
        for rep in range(1,9):
            prefix=f'{rid}/replicate_{rep:02d}';art=folder/'artifacts'/f'replicate_{rep:02d}'
            files=sorted(p for p in art.rglob('*') if p.is_file())
            inventory.extend({'run_id':rid,'replicate':rep,'file':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size} for p in files)
            ra=readj(art/'replicate_audit.json');member=readc(art/'sampled_game_multiplicity_and_outer_fold.csv')
            ss=int(manifest['bootstrap_seed'])+rep-1;es=int(cfg['seed'])+100000+10000*(rep-1)
            check(prefix+'/sample_seed',ra['sample_seed'],ss,True);check(prefix+'/evaluation_seed',ra['evaluation_seed'],es,True)
            rng=np.random.default_rng(ss);weights=pd.Series(0,index=game.index,dtype='int64');year_totals={}
            for yr in sorted(game.year.unique()):
                population=game.index[game.year.eq(yr)].to_numpy()
                # Uniform draws of index positions are equivalent to categorical game sampling.
                draws=rng.integers(0,len(population),size=len(population))
                counts=np.bincount(draws,minlength=len(population));weights.loc[population]=counts
                year_totals[str(int(yr))]=int(counts.sum())
            active=set(int(g) for g in weights.index[weights.gt(0)]);om=allocation(active,int(cfg['outer_folds']),es)
            check(prefix+'/member_unique',member.game_pk.is_unique,True,True)
            check(prefix+'/member_games',set(member.game_pk),active,True)
            for r in member.itertuples():
                check(prefix+f'/multiplicity/{r.game_pk}',int(r.multiplicity),int(weights.at[r.game_pk]),True)
                check(prefix+f'/outer_fold/{r.game_pk}',int(r.fold),om[int(r.game_pk)],True)
                check(prefix+f'/season/{r.game_pk}',(int(r.game_year),int(r.sampled_season)),(int(game.at[r.game_pk,'year']),)*2,True)
            check(prefix+'/drawn_games',ra['drawn_games_with_multiplicity'],int(weights.sum()),True)
            check(prefix+'/rows',ra['sample_rows'],int(game.n.dot(weights)),True)
            check(prefix+'/score_rows',ra['score_rows'],int(game.n.dot(weights)),True)
            expected_splits={};jobs=[]
            def split_record(label,role,tr,ev):
                check(prefix+'/'+label+'/overlap',len(tr&ev),0,True)
                expected_splits[label]={'role':role,'train_original_games':len(tr),'evaluation_original_games':len(ev),'intersection_n':0,'train_games_sha256':gh(tr),'evaluation_games_sha256':gh(ev)}
            for outer in range(3):
                ev={g for g in active if om[g]==outer};tr=active-ev;lab=f'outer{outer}'
                split_record(lab,'outer_evaluation',tr,ev)
                iseed=es+1000+100*outer;im=allocation(tr,2,iseed)
                for inner in range(2):
                    itest={g for g in tr if im[g]==inner};itr=tr-itest;il=f'{lab}/inner{inner}'
                    split_record(il,'policy_oof',itr,itest);jobs.append((il,itr,iseed+100+inner,ev|itest))
                jobs.append((lab+'/evaluation_nuisance',tr,es+2000+outer,ev))
            expected_n={}
            def total(gs,field):
                idx=list(gs);return int(game.loc[idx,field].dot(weights.loc[idx]))
            for lab,tr,seed,forbidden in jobs:
                part=allocation(tr,5,seed);cal={g for g in tr if part[g]==0};tune={g for g in tr if part[g]==1};base=tr-cal;fit=base-tune
                check(prefix+'/'+lab+'/all_parent_exclusions',len(tr&forbidden),0,True)
                split_record(lab+'/cal','calibration',base,cal);split_record(lab+'/tune','tuning',fit,tune)
                for target,field in [('p','n'),('m0','n0'),('m1','n1')]:
                    for alpha in cfg['alphas']:expected_n[f'{lab}/tune/{target}/{alpha}']=total(fit,field)
                for name,gs,field in [('prop',base,'n'),('m0',tr,'n0'),('m1',tr,'n1'),('calibrator',cal,'n')]:expected_n[lab+'/'+name]=total(gs,field)
            folds=readc(art/'fold_audit.csv').set_index('fit_id');fitdiag=readc(art/'fit_diagnostics.csv').set_index('fit_id');tune=readc(art/'tuning.csv')
            check(prefix+'/split_keys',set(folds.index),set(expected_splits),True)
            check(prefix+'/fit_keys',set(fitdiag.index),set(expected_n),True)
            for lab,fields in expected_splits.items():
                for field,value in fields.items():check(prefix+'/'+lab+'/'+field,folds.at[lab,field],value,True)
            for lab,n in expected_n.items():check(prefix+'/'+lab+'/training_N',int(fitdiag.at[lab,'n']),n,True)
            for lab,_,_,_ in jobs:
                for target in ['p','m0','m1']:
                    candidates=tune[tune.fit_id.eq(lab)&tune.target.eq(target)]
                    check(prefix+'/'+lab+'/'+target+'/candidate_alphas',set(candidates.alpha),set(cfg['alphas']),True)
                    chosen=sorted(zip(candidates.loss,candidates.alpha),key=lambda z:(z[0],-z[1]))[0][1]
                    check(prefix+'/'+lab+'/'+target+'/chosen',fitdiag.at[lab+('/prop' if target=='p' else '/'+target),'alpha'],chosen,True)
            ridge=fitdiag[~fitdiag.index.str.endswith('/calibrator')];cals=fitdiag[fitdiag.index.str.endswith('/calibrator')]
            check(prefix+'/ridge_logged_convergence',bool(ridge.converged.all()&ridge.solver_info.eq(0).all()&ridge.relative_gradient.lt(1e-7).all()&ridge.iterations.le(3000).all()),True,True)
            check(prefix+'/calibration_logged_success',bool(cals.converged.all()&cals.slope.ge(0).all()&np.isfinite(cals.loss).all()),True,True)
            values=readc(art/'action_policy_values.csv');frames.append(values)
            expected_counts={f'{b}-{s}' for b in range(4) for s in range(3)}
            check(prefix+'/count_keys',set(values.loc[values.level.eq('count'),'state']),expected_counts,True)
            check(prefix+'/aggregate_keys_unique',~values[['level','state']].duplicated().any(),True,True)
            overall=values[values.level.eq('overall')].iloc[0];counts=values[values.level.eq('count')]
            for r in values.itertuples():
                sourceagg=agg if r.level=='overall' else agg[agg['count'].eq(r.state)]
                w=sourceagg.game_pk.map(weights);n=int(sourceagg.n.dot(w));n1=float(sourceagg.n1.dot(w))
                check(prefix+'/'+r.state+'/n_all',r.n_all,n,True)
                check(prefix+'/'+r.state+'/all_action_rate',r.all_action1_rate,n1/n)
                check(prefix+'/'+r.state+'/coverage',r.coverage,r.n_supported/n)
                check(prefix+'/'+r.state+'/delta',r.delta,r.Q1-r.Q0)
                sign=-1 if variant=='pitch' else 1
                check(prefix+'/'+r.state+'/gain',r.learned_gain,sign*(r.learned_value-r.observed_value))
                check(prefix+'/'+r.state+'/conservative_value',r.conservative_value,r.observed_value)
                check(prefix+'/'+r.state+'/conservative_gain',r.conservative_gain,0)
            for field in ['n_all','n_supported']:check(prefix+'/'+field+'/count_sum',int(overall[field]),int(counts[field].sum()),True)
            for field in ['Q0','Q1','delta','observed_value','learned_value','learned_gain','conservative_value','conservative_gain','learned_action1_share','all_action1_rate','Brier_all','MSE_all']:
                denom='n_all' if field in ['all_action1_rate','Brier_all','MSE_all'] else 'n_supported'
                val=math.fsum(float(v)*int(n) for v,n in zip(counts[field],counts[denom]))/int(overall[denom])
                check(prefix+'/weighted_count/'+field,overall[field],val)
            records.append({'run_id':rid,'replicate':rep,'sample_seed':ss,'evaluation_seed':es,'season_draws':year_totals,'unique_games':len(active),'rows':int(game.n.dot(weights)),'split_hash_records':len(expected_splits),'fit_training_N':len(expected_n),'tuning_choices':len(jobs)*3,'persisted_files':len(files),'row_scores_or_fits_present':any(p.suffix in ['.pkl','.parquet','.npz'] for p in files)})
        vals=pd.concat(frames,ignore_index=True);cumulative=readc(folder/'artifacts/replicate_values.csv');stable=readc(folder/'artifacts/stability_summary.csv')
        key=['replicate','level','state'];a=vals.set_index(key);b=cumulative.set_index(key)
        check(rid+'/cumulative_keys',set(a.index),set(b.index),True)
        for col in a.select_dtypes(include=np.number).columns:
            for ix in a.index:check(rid+'/cumulative/'+str(ix)+'/'+col,a.at[ix,col],b.at[ix,col])
        for row in stable.itertuples():
            nums=vals.loc[vals.level.eq(row.level)&vals.state.eq(row.state),row.metric].to_numpy(dtype=float)
            nums=nums[np.isfinite(nums)];mean=math.fsum(nums)/len(nums);sd=math.sqrt(math.fsum((x-mean)**2 for x in nums)/(len(nums)-1))
            expected={'replicates':len(nums),'mean':mean,'SD':sd,'minimum':min(nums),'maximum':max(nums),'positive_fraction':sum(x>0 for x in nums)/len(nums)}
            for field,value in expected.items():check(rid+'/stability/'+row.level+'/'+row.state+'/'+row.metric+'/'+field,getattr(row,field),value,field=='replicates')
            stability_rows.append({'run_id':rid,'level':row.level,'state':row.state,'metric':row.metric,**expected})
        del d,agg,game
    # Count the declared primary family and distinguish other generated intervals.
    main_ids=['bcap_pitch__mlb_2024_2025__20260909__r02','bcap_swing__mlb_2024_2025__20260909__r01','bcap_pitch__mlb_2023__20260909__r01','bcap_swing__mlb_2023__20260909__r01','bcap_pitch__mlb_2026_ytd_20260907__20260909__r01']
    families=[]
    for rid in main_ids:
        art=RUNS/rid/'artifacts'
        for role,sub in [('primary',art),('fixed_development_prediction_diagnostic',art/'fixed_prediction_diagnostics')]:
            if not sub.exists():continue
            av=readc(sub/'action_values.csv');pv=readc(sub/'policy_values.csv')
            delta_n=int(av.simultaneous95_low.notna().sum());gain_n=int(pv.gain_low.notna().sum())
            families.append({'run_id':rid,'role':role,'action_table_rows':len(av),'nonempty_delta_intervals':delta_n,'nonempty_policy_gain_intervals':gain_n,'policy_value_individual95_intervals':int(pv.CI95_low.notna().sum()),'primary_family_members':delta_n+gain_n if role=='primary' else 0})
    family_n=sum(r['primary_family_members'] for r in families)
    check('primary_Bonferroni_family_size_bounded',family_n<=1536,True,True)
    # Compact comparisons retain failure/exact evidence in JSON; huge per-game rows are CSV.
    put_csv('bootstrap_comparisons.csv',COMPARISONS)
    put_csv('bootstrap_independent_stability.csv',stability_rows)
    put_csv('bootstrap_saved_file_inventory.csv',inventory)
    put_csv('interval_family_inventory.csv',families)
    errors=[r['absolute_error'] for r in COMPARISONS if r['absolute_error'] is not None]
    failed=[r for r in COMPARISONS if r['status']=='FAIL']
    status={'status':'PASS' if not failed else 'FAIL','scope':'Stored aggregate reaggregation and independent resampling/split/fit-N reconstruction; no original bootstrap row AIPW or prediction recreation','started_at_utc':START,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':len(COMPARISONS),'failures':len(failed),'max_absolute_error':max(errors),'primary_family_intervals':family_n,'family_bound':1536,'replicate_records':records,'raw_bootstrap_AIPW_recalculation':{'status':'NOT_VERIFIABLE','reason':'No replicate row Y/A/nuisance predictions/scores or fitted nuisance/policy objects retained; only aggregate and split/fit logs'},'full_learning_CI':{'status':'NOT_RUN','reason':'8 repetitions are stability diagnostics; neither enough repetitions nor valid tie/dependence inference established'},'model_refitting':'NOT_RUN','failed_checks':failed}
    put_json('bootstrap_validation.json',status)
    outputs=[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size} for p in OUT.glob('*') if p.is_file()]
    put_json('bootstrap_evidence_manifest.json',{'started_at_utc':START,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':[sys.executable,*sys.argv],'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'platform':platform.platform(),'bytecode_disabled':sys.dont_write_bytecode,'inputs':list(INPUTS.values()),'code':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':digest(__file__)},'outputs':outputs,'independence':'No prior validator, engine function, or fit class imported. Original aggregate values are inputs only; raw bootstrap AIPW unavailable.'})
    print(json.dumps({k:status[k] for k in ['status','checks','failures','max_absolute_error','primary_family_intervals']},ensure_ascii=False))
if __name__=='__main__':audit()
