"""Independent all-source reconstruction. Never imports production implementation.
Read-only sources; all generated artifacts live beside this script. Python -B.
"""
from pathlib import Path
import sys, json, hashlib, datetime as dt, platform, gc, re
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
COL=ROOT/'columns/001-ball-count'
RUNS=COL/'analysis/runs'
START=dt.datetime.now(dt.timezone.utc).isoformat()
CHECKS=[]; EVIDENCE={}; FILE_READS=[]; SUMMARY=[]
KEY=['game_pk','at_bat_number','pitch_number']; PK=KEY[:2]
RAWCOL=KEY+['game_year','game_date','game_type','balls','strikes','pitcher','batter','events','description','pitch_type','pitch_name','des','stand','p_throws','on_1b','on_2b','on_3b','outs_when_up','inning','inning_topbot','bat_score_diff','bat_score','fld_score','home_score','away_score','post_bat_score','post_fld_score','post_home_score','post_away_score','release_speed','pfx_x','pfx_z','plate_x','plate_z','sz_top','sz_bot']
RUNIDS={'dev':['bcap_pitch__mlb_2024_2025__20260909__r02','bcap_swing__mlb_2024_2025__20260909__r01'], '2023':['bcap_pitch__mlb_2023__20260909__r01','bcap_swing__mlb_2023__20260909__r01'], '2026':['bcap_pitch__mlb_2026_ytd_20260907__20260909__r01']}

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def observe(p,expected=None,role='input'):
    p=Path(p); rel=p.relative_to(ROOT).as_posix()
    if rel not in EVIDENCE:EVIDENCE[rel]={'path':rel,'sha256':sha(p),'bytes':p.stat().st_size,'mtime_utc':dt.datetime.fromtimestamp(p.stat().st_mtime,dt.timezone.utc).isoformat(),'role':role}
    if expected is not None:
        EVIDENCE[rel]['recorded_sha256']=expected
        EVIDENCE[rel]['matches_recorded']=EVIDENCE[rel]['sha256']==expected
    FILE_READS.append(rel)
    return p
def jread(p):return json.loads(observe(p).read_text(encoding='utf-8-sig'))
def writej(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
def csv(name,d):pd.DataFrame(d).to_csv(OUT/name,index=False,encoding='utf-8-sig')
def check(dataset,item,passed,denominator=None,**detail):
    rec={'dataset':dataset,'item':item,'status':'PASS' if passed else 'FAIL','denominator':denominator,**detail};CHECKS.append(rec)
    if not passed:print('FAIL',dataset,item,detail,flush=True)
def compare(ds,col,expected,actual,ids,numeric=False):
    e=pd.Series(expected).reset_index(drop=True); a=pd.Series(actual).reset_index(drop=True)
    if numeric:
        ea=pd.to_numeric(e,errors='coerce').to_numpy(dtype=float,na_value=np.nan);aa=pd.to_numeric(a,errors='coerce').to_numpy(dtype=float,na_value=np.nan)
        match=np.isclose(ea,aa,atol=1e-10,rtol=1e-9,equal_nan=True); delta=np.abs(ea-aa);finite=np.isfinite(delta)
        mx=float(delta[finite].max()) if finite.any() else 0.; rel=np.abs(delta[finite]/np.maximum(np.abs(ea[finite]),1e-300)); mr=float(rel.max()) if len(rel) else 0.
    else:
        match=(e.astype('string').fillna('<NA>').to_numpy()==a.astype('string').fillna('<NA>').to_numpy());mx=mr=None
    bad=np.flatnonzero(~match)
    check(ds,'column:'+col,len(bad)==0,len(e),mismatch_rows=len(bad),max_absolute_error=mx,max_relative_error=mr)
    if len(bad):
        r=ids.iloc[bad[:10000]].reset_index(drop=True).copy();r['expected']=e.iloc[bad[:10000]].to_numpy();r['actual']=a.iloc[bad[:10000]].to_numpy()
        csv(ds+'__mismatch_'+col+'.csv',r)

protocol=jread(OUT.parent/'review_protocol.json')
spec=jread(ROOT/'models/bcap/pitch/v0.1.0/specification.yaml')
sspec=jread(ROOT/'models/bcap/swing/v0.1.0/specification.yaml')
obs=jread(ROOT/'models/bcai/observed/v1.0.0/specification.yaml')
ridge=jread(ROOT/'models/bcai/ridge/v0.2.0/specification.yaml')
for p in ['AGENTS.md','README.md','guides/analysis.md','models/registry.md','columns/001-ball-count/column.md','columns/001-ball-count/sources.md','models/bcap/data.py','models/bcap/run.py','models/bcap/measurement_review.md','models/bcap/design_decisions.md']:
    observe(ROOT/p)
event_map={e:r for r,es in obs['result_classification'].items() for e in es}
FB=set(spec['actions']['FB']);NFB=set(spec['actions']['NFB']);SW=set(spec['actions']['Swing']);TA=set(spec['actions']['Take'])
check('global','action_maps_two_specs',spec['actions']==sspec['actions'])
for year in [2023,2024,2025]:check('global',f'weights_{year}_match',spec['weights'][str(year)]==ridge['weights'][str(year)])

for ds,ids in RUNIDS.items():
    print('BEGIN',ds,flush=True)
    mans=[jread(RUNS/r/'manifest.json') for r in ids]
    prep_path=(COL/'analysis/bcap_preparation_20260909_r01/preparation_audit.json') if ds=='dev' else RUNS/ids[0]/'artifacts/preparation/preparation_audit.json'
    audit=jread(prep_path)
    parts=[]; schedules={}; expected_games=set(); source_stats=[]
    for inp in audit['inputs']:
        p=observe(ROOT/inp['path'],inp['sha256'])
        if p.suffix=='.json':
            sch=json.loads(p.read_text(encoding='utf-8-sig'))
            for day in sch['dates']:
                for g in day['games']:
                    if g['gameType']=='R' and g['status']['abstractGameState']=='Final' and g['status'].get('detailedState')!='Cancelled' and g['officialDate']<=('2026-09-07' if ds=='2026' else '2025-12-31'):
                        expected_games.add(g['gamePk']);schedules[g['gamePk']]=(g['venue']['id'],g['officialDate'])
        else:
            header=pd.read_csv(p,nrows=0).columns.tolist()
            missing=set(RAWCOL)-set(header)
            check(ds,'raw_columns:'+p.name,not missing,missing_columns=sorted(missing))
            d=pd.read_csv(p,usecols=RAWCOL,low_memory=False)
            d['_source_file']=p.relative_to(ROOT).as_posix();d['_source_record']=np.arange(1,len(d)+1)
            parts.append(d);source_stats.append({'path':p.relative_to(ROOT).as_posix(),'rows':len(d),'csv_record_is_1based_excluding_header':True})
    raw=pd.concat(parts,ignore_index=True);del parts,d;gc.collect()
    check(ds,'schedule_complete',expected_games==set(raw.game_pk),len(expected_games),missing_games=sorted(expected_games-set(raw.game_pk)),extra_games=sorted(set(raw.game_pk)-expected_games))
    raw=raw[raw.game_pk.isin(expected_games)].sort_values(KEY).reset_index(drop=True)
    csv(ds+'__source_files.csv',source_stats)
    ident=raw[KEY+['_source_file','_source_record']].copy()
    check(ds,'raw_required_keys_identifiers_counts_complete',not raw[KEY+['pitcher','batter','balls','strikes']].isna().any().any(),len(raw))
    check(ds,'raw_unique_keys',not raw.duplicated(KEY).any(),len(raw),duplicates=int(raw.duplicated(KEY).sum()))
    check(ds,'raw_count_range',bool(raw.balls.between(0,3).all() and raw.strikes.between(0,2).all()),len(raw))
    proc=observe(ROOT/audit['output']['path'],audit['output']['sha256']); saved=pd.read_pickle(proc)
    check(ds,'processed_row_count',len(saved)==len(raw),len(raw),saved_rows=len(saved))
    for col in RAWCOL:
        if col in saved:compare(ds,col,raw[col],saved[col],ident,numeric=pd.api.types.is_numeric_dtype(raw[col]))
    group=raw.groupby(PK,sort=False)
    first=~raw.duplicated(PK);last=~raw.duplicated(PK,keep='last')
    paid=first.cumsum().astype(int)-1
    final=raw.loc[last,PK+['events']].set_index(PK)['events']
    idx=pd.MultiIndex.from_frame(raw[PK]); fe=pd.Series(final.reindex(idx).to_numpy(),index=raw.index)
    rc=fe.map(event_map)
    startcount=(raw.loc[first,'balls'].astype(int).astype(str)+'-'+raw.loc[first,'strikes'].astype(int).astype(str)).to_numpy()
    count=raw.balls.astype(int).astype(str)+'-'+raw.strikes.astype(int).astype(str)
    start_perrow=pd.Series(startcount).iloc[paid].reset_index(drop=True)
    reason=pd.Series('included',index=raw.index)
    # Ordered priority reconstructed by assigning from least to greatest priority.
    reason.loc[start_perrow.ne('0-0')]='no_observed_0_0';reason.loc[rc.isna()]='unknown_event'
    reason.loc[fe.eq('truncated_pa')]='truncated';reason.loc[fe.eq('catcher_interf')]='catcher_interference';reason.loc[fe.eq('intent_walk')]='intentional_walk';reason.loc[fe.isna()]='missing_final'
    y=pd.Series(0.,index=raw.index)
    for yr in raw.game_year.unique():
        w=spec['weights'][str(2025 if yr==2026 else yr)]
        for outcome,weight in w.items():y.loc[raw.game_year.eq(yr)&rc.eq(outcome)]=weight
    y.loc[reason.ne('included')]=np.nan
    ex={'row_id':np.arange(len(raw)),'pa_id':paid,'count':count,'final_event':fe,'result':rc,'pa_exclusion':reason,'Y':y,'eligible_pa':reason.eq('included')}
    prev={c:group[c].shift(1) for c in ['pitch_number','pitch_type','description','release_speed','pitcher','batter']}
    ex['prev_pitch_number']=prev['pitch_number'];ex['prev_release_speed']=prev['release_speed']
    for orig,target in [('pitch_type','prev_pitch_type'),('description','prev_description')]:
        v=prev[orig].fillna('MISSING_PREVIOUS');v.loc[first]='START';ex[target]=v
    v=np.floor(prev['release_speed']/5).astype('Int64').astype(str);v.loc[first]='START';ex['prev_release_speed_bin']=v
    ex['venue']=raw.game_pk.map({k:v[0] for k,v in schedules.items()});ex['official_date']=raw.game_pk.map({k:v[1] for k,v in schedules.items()})
    ex['matchup']=raw.stand.fillna('?')+raw.p_throws.fillna('?')
    ex['base_state']=raw.on_1b.notna().astype(int)+2*raw.on_2b.notna().astype(int)+4*raw.on_3b.notna().astype(int)
    ex['inning_bin']=np.minimum(raw.inning,10);ex['pitch_number_bin']=np.minimum(raw.pitch_number,8)
    # Score independent pre-pitch sources, not the input bat_score_diff.
    pre=raw.bat_score-raw.fld_score
    homeaway=np.where(raw.inning_topbot.eq('Top'),raw.away_score-raw.home_score,raw.home_score-raw.away_score)
    compare(ds,'bat_score_diff_vs_prepitch',pre,raw.bat_score_diff,ident,True)
    compare(ds,'bat_score_diff_vs_prepitch_homeaway',homeaway,raw.bat_score_diff,ident,True)
    ex['score_bin']=pd.Series(np.select([pre<=-4,pre<0,pre==0,pre<=3],['trailing4+','trailing1-3','tie','leading1-3'],default='leading4+'))
    scoring=raw.post_bat_score.ne(raw.bat_score)|raw.post_fld_score.ne(raw.fld_score)
    scoretab=raw.loc[scoring,KEY+['_source_file','_source_record','game_year','description','events','bat_score','fld_score','post_bat_score','post_fld_score','bat_score_diff']].copy()
    scoretab['expected_pre_diff']=pre[scoring];scoretab['post_diff']=raw.post_bat_score[scoring]-raw.post_fld_score[scoring];scoretab['saved_score_bin']=saved.loc[scoring,'score_bin'].astype(str)
    csv(ds+'__scoring_pitch_rows.csv',scoretab)
    check(ds,'score_scoring_pitches_pre_not_post',bool(raw.loc[scoring,'bat_score_diff'].eq(pre[scoring]).all()),int(scoring.sum()),post_different_rows=int((raw.post_bat_score-raw.post_fld_score).ne(pre).sum()))
    auto=raw.description.isin(['automatic_ball','automatic_strike']);po=raw.pitch_type.eq('PO')|raw.description.isin(['pitchout','swinging_pitchout','foul_pitchout'])
    ex['pitch_group']=pd.Series(np.where(raw.pitch_type.isin(FB),'FB',np.where(raw.pitch_type.isin(NFB),'NFB','UNCLASSIFIED')))
    for model,field,ones,zeros in [('pitch','pitch_type',FB,NFB),('swing','description',SW,TA)]:
        ac=raw[field].map({**dict.fromkeys(ones,1),**dict.fromkeys(zeros,0)}).mask(auto|po)
        r=pd.Series('included',index=raw.index);r.loc[~raw[field].isin(ones|zeros)]='unmapped_'+field;r.loc[raw[field].isna()]='missing_'+field;r.loc[po]='pitchout';r.loc[auto]='automatic_record';r.loc[reason.ne('included')]='PA_EXCLUDED'
        ex['A_'+model]=ac;ex['reason_'+model]=r;ex['eligible_'+model]=r.eq('included')
    ex['bunt_explicit']=raw.description.isin(['foul_bunt','missed_bunt','bunt_foul_tip'])
    ex['inplay_bunt_text_flag']=raw.description.eq('hit_into_play')&raw.des.fillna('').str.contains(r'\bbunts?\b',case=False,regex=True)
    ex['hbp_adjudicated_take']=raw.description.eq('hit_by_pitch')
    height=raw.sz_top-raw.sz_bot;zn=(raw.plate_z-raw.sz_bot)/height.where(height>0)
    valid=raw[['plate_x','plate_z','sz_top','sz_bot']].notna().all(axis=1)&height.gt(0)
    inner=raw.plate_x.abs().le(17/24-.15)&zn.ge(.1)&zn.le(.9);outer=raw.plate_x.abs().gt(17/24+.15)|zn.lt(-.1)|zn.gt(1.1)
    ex['zone_z_normalized']=zn;ex['zone']=pd.Series(np.select([~valid,inner,outer],['MISSING','INNER','OUT'],default='BOUNDARY'))
    ex['measurement_missing']=raw[['release_speed','pfx_x','pfx_z','plate_x','plate_z','sz_top','sz_bot']].isna().any(axis=1)
    gap=(~first)&raw.pitch_number.ne(prev['pitch_number']+1);ex['pitch_sequence_gap_before']=gap
    for c,v in ex.items():compare(ds,c,v,saved[c],ident,numeric=c in ['Y','row_id','pa_id','venue','base_state','inning_bin','pitch_number_bin','prev_pitch_number','prev_release_speed','zone_z_normalized','A_pitch','A_swing'])
    check(ds,'Y_constant_in_PA',bool(pd.DataFrame({'pid':paid,'Y':y}).groupby('pid').Y.nunique().le(1).all()),int(first.sum()))
    switches=(~first)&(raw.pitcher.ne(prev['pitcher'])|raw.batter.ne(prev['batter']))
    n_events=group.events.transform('count');multi=n_events.gt(1);missing_last_earlier=fe.isna()&n_events.gt(0)
    nextb=group.balls.shift(-1);nexts=group.strikes.shift(-1)
    db=nextb-raw.balls;ss=nexts-raw.strikes;nonterminal=~last
    broad=nonterminal&~((db.eq(1)&ss.eq(0))|(db.eq(0)&ss.eq(1))|(db.eq(0)&ss.eq(0)))
    # Stricter description-specific next-count check, does not assume every event is a physical pitch.
    ball=raw.description.isin(['ball','blocked_ball','automatic_ball','pitchout']); strike=raw.description.isin(['called_strike','swinging_strike','swinging_strike_blocked','foul_tip','missed_bunt','bunt_foul_tip','automatic_strike','foul_bunt'])
    foul=raw.description.eq('foul')
    strict=nonterminal&((ball&~(db.eq(1)&ss.eq(0)))|(strike&~(db.eq(0)&ss.eq(1)))|(foul&~(db.eq(0)&ss.eq(np.where(raw.strikes<2,1,0)))))
    anomalies=gap|switches|multi|missing_last_earlier|broad|strict|(first&raw.pitch_number.ne(1))
    details=raw.loc[anomalies,KEY+['_source_file','_source_record','game_year','pitcher','batter','balls','strikes','pitch_type','description','events']].copy()
    for k,v in {'gap':gap,'player_switch':switches,'multiple_events':multi,'missing_last_with_earlier_event':missing_last_earlier,'broad_count_anomaly':broad,'strict_description_count_anomaly':strict,'prev_pitcher':prev['pitcher'],'prev_batter':prev['batter'],'next_balls':nextb,'next_strikes':nexts,'saved_prev_pitch_type':saved.prev_pitch_type.astype(str),'saved_prev_description':saved.prev_description.astype(str),'saved_prev_release_speed':saved.prev_release_speed,'pa_exclusion':reason}.items():details[k]=v[anomalies]
    csv(ds+'__sequence_and_switch_cases.csv',details)
    hbp=raw.description.eq('hit_by_pitch');hbpm=hbp&~raw.events.eq('hit_by_pitch');hbp_final=hbp&~fe.eq('hit_by_pitch')
    hbpd=raw.loc[hbp,KEY+['_source_file','_source_record','game_year','description','events','des','pitch_type']].copy();hbpd['final_event']=fe[hbp];hbpd['A_swing']=ex['A_swing'][hbp];hbpd['eligible_swing']=ex['eligible_swing'][hbp];hbpd['zone']=ex['zone'][hbp];csv(ds+'__hbp_cases.csv',hbpd)
    check(ds,'description_HBP_matches_current_event',not hbpm.any(),int(hbp.sum()),mismatches=int(hbpm.sum()))
    check(ds,'description_HBP_matches_final_PA_event',not hbp_final.any(),int(hbp.sum()),mismatches=int(hbp_final.sum()))
    check(ds,'strict_lags_first_row_clear',bool(pd.Series(ex['prev_release_speed'])[first].isna().all()),int(first.sum()))
    csv(ds+'__raw_pitch_codes.csv',raw.groupby(['game_year','pitch_type','pitch_name'],dropna=False).size().rename('rows').reset_index())
    csv(ds+'__raw_descriptions.csv',raw.groupby(['game_year','description'],dropna=False).size().rename('rows').reset_index())
    ctab=[]
    for model in ['pitch','swing']:
        tmp=pd.DataFrame({'model':model,'game_year':raw.game_year,'action':ex['A_'+model].fillna(-1),'pa_exclusion':reason,'reason':ex['reason_'+model],'measurement_missing':ex['measurement_missing'],'zone':ex['zone'],'pitch_group':ex['pitch_group']})
        ctab.append(tmp.groupby(list(tmp.columns),dropna=False).size().rename('rows').reset_index())
    csv(ds+'__selection_by_model_season_action_reason.csv',pd.concat(ctab))
    csv(ds+'__PA_exclusions.csv',pd.DataFrame({'game_year':raw.game_year[first],'final_event':fe[first],'result':rc[first],'pa_exclusion':reason[first]}).groupby(['game_year','final_event','result','pa_exclusion'],dropna=False).size().rename('PA').reset_index())
    for rid,man in zip(ids,mans):
        model=man['configuration']['variant'];mini=raw.loc[ex['eligible_'+model],KEY+['game_year','game_date','pitcher','batter']].copy().reset_index(drop=True)
        for c in ['count','final_event','result','Y','zone','pitch_group']:mini[c]=pd.Series(ex[c])[ex['eligible_'+model]].reset_index(drop=True)
        mini['A']=ex['A_'+model][ex['eligible_'+model]].reset_index(drop=True)
        sp=RUNS/rid/'artifacts/scores.pkl';spmeta=next(v for v in man['outputs'] if v['path'].endswith('/scores.pkl'));s=pd.read_pickle(observe(sp,spmeta['sha256']))
        check(rid,'eligible_rows_match_scores',len(s)==len(mini),len(mini),saved_rows=len(s))
        for c in mini.columns:compare(rid,c,mini[c],s[c],mini[KEY],numeric=c in KEY+['game_year','pitcher','batter','Y','A'])
        meas=np.ones(len(mini),dtype=bool)
        if model=='swing':meas=(pd.Series(ex['zone']).ne('MISSING')&~ex['measurement_missing']&pd.Series(ex['pitch_group']).isin(['FB','NFB']))[ex['eligible_swing']].to_numpy()
        compare(rid,'measurement_support',meas,s.measurement_support,mini[KEY])
        selector=pd.DataFrame({'run_id':rid,'game_year':mini.game_year,'action':mini.A,'support':s.support,'measurement_support':meas,'repertoire':s.repertoire,'propensity_in_bounds':s.p.between(.05,.95)})
        selector['exclusion_reason']=np.select([~selector.measurement_support,~selector.repertoire,~selector.propensity_in_bounds],['measurement','entity_arm_training','propensity_tail'],default='supported')
        csv(rid+'__support_by_season_action.csv',selector.groupby(list(selector.columns),dropna=False).size().rename('rows').reset_index())
        # External SWING prep is separately saved: full field equality against independently reconstructed data.
        if ds=='2023' and model=='swing':
            pmeta=man['inputs'][0];p2=pd.read_pickle(observe(ROOT/pmeta['path'],pmeta['sha256']))
            for c,v in ex.items():compare(rid,c,v,p2[c],ident,numeric=c in ['Y','row_id','pa_id','venue','base_state','inning_bin','pitch_number_bin','prev_pitch_number','prev_release_speed','zone_z_normalized','A_pitch','A_swing'])
            for c in RAWCOL:
                if c in p2:compare(rid,'raw_'+c,raw[c],p2[c],ident,numeric=pd.api.types.is_numeric_dtype(raw[c]))
            del p2
        del s,mini,selector
    summary={'dataset':ds,'rows':len(raw),'PA':int(first.sum()),'games':int(raw.game_pk.nunique()),'source_files':len(source_stats),'scoring_rows':int(scoring.sum()),'eligible_pitch':int(ex['eligible_pitch'].sum()),'eligible_swing_labels_only_2026':int(ex['eligible_swing'].sum()),'sequence_gaps':int(gap.sum()),'first_pitch_number_not_1_PA':int((first&raw.pitch_number.ne(1)).sum()),'multiple_events_PA':int(raw.loc[multi].drop_duplicates(PK).shape[0]),'missing_final_with_earlier_PA':int(raw.loc[missing_last_earlier].drop_duplicates(PK).shape[0]),'player_switch_rows':int(switches.sum()),'pitcher_switch_rows':int(((~first)&raw.pitcher.ne(prev['pitcher'])).sum()),'batter_switch_rows':int(((~first)&raw.batter.ne(prev['batter'])).sum()),'broad_count_anomalies':int(broad.sum()),'strict_description_count_anomalies':int(strict.sum()),'HBP_rows':int(hbp.sum()),'HBP_current_event_mismatch':int(hbpm.sum()),'HBP_final_event_mismatch':int(hbp_final.sum()),'explicit_bunt_rows':int(ex['bunt_explicit'].sum()),'inplay_bunt_text_rows':int(ex['inplay_bunt_text_flag'].sum()),'FA_rows':int(raw.pitch_type.eq('FA').sum())}
    SUMMARY.append(summary);print('COMPLETE',summary,flush=True)
    writej('validation_partial.json',CHECKS);writej('summary_partial.json',SUMMARY)
    del raw,saved,ex,group,prev,ident,details,scoretab,hbpd,ctab;gc.collect()

for rel,e in EVIDENCE.items():
    if 'matches_recorded' in e:check('hashes',rel,e['matches_recorded'])
CHECKS.extend([{'dataset':'2026','item':'SWING_model_evaluation','status':'NOT_RUN','scope':'Only raw label/measurement lineage; no model evaluation or fitted prediction generated.'},{'dataset':'all','item':'latent_intent_check_swing_and_realtime_perception','status':'NOT_VERIFIABLE','scope':'No pitch video, independent adjudication, intent or real-time perception data were acquired.'},{'dataset':'all','item':'unrecorded_pitch_or_game_reconstruction','status':'NOT_VERIFIABLE','scope':'All local raw files and saved schedule checked; unavailable physical actions between records are not reconstructed.'}])
writej('validation.json',{'started_at_utc':START,'completed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'tolerances':protocol['tolerances_before_new_comparisons'],'scope':'Full raw CSV rows for 2024/2025 development, 2023 and 2026 pitch external. 2026 SWING labels only, no model evaluation. No production functions imported.','summary':SUMMARY,'checks':CHECKS})
csv('check_results.csv',CHECKS);csv('summary.csv',SUMMARY)
observe(Path(__file__),role='independent_review_code')
for p in OUT.iterdir():
    if p.is_file() and p.name!='evidence_manifest.json':observe(p,role='output' if p.suffix!='.py' else 'independent_review_code')
writej('evidence_manifest.json',{'started_at_utc':START,'completed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'command':f'"{sys.executable}" -B "{Path(__file__)}"','environment':{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'dont_write_bytecode':sys.dont_write_bytecode},'execution_class':'independent_reconstruction_from_existing_raw_and_compare_stored_inputs_scores','production_functions_called':False,'records':list(EVIDENCE.values())})
print('DONE',len(CHECKS),'checks',sum(c['status']=='FAIL' for c in CHECKS),'FAIL',flush=True)
