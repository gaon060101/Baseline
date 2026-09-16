"""Follow-up of new source-count exceptions and measurement selection; no model calls."""
from pathlib import Path
import sys,json,hashlib,datetime as dt,platform
import numpy as np,pandas as pd
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[4];RUNS=ROOT/'columns/001-ball-count/analysis/runs'
START=dt.datetime.now(dt.timezone.utc).isoformat();EVID=[];CHECKS=[]
KEY=['game_pk','at_bat_number','pitch_number']
IDS=['bcap_pitch__mlb_2024_2025__20260909__r02','bcap_swing__mlb_2024_2025__20260909__r01','bcap_pitch__mlb_2023__20260909__r01','bcap_swing__mlb_2023__20260909__r01','bcap_pitch__mlb_2026_ytd_20260907__20260909__r01']
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def meta(p,role='input'):
    p=Path(p);e={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size,'role':role};EVID.append(e);return p
def jr(p):return json.loads(meta(p).read_text(encoding='utf-8-sig'))
def csv(n,d):d.to_csv(OUT/n,index=False,encoding='utf-8-sig')
def wj(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
parts=[]
for ds in ['dev','2023','2026']:
    d=pd.read_csv(meta(OUT/(ds+'__sequence_and_switch_cases.csv')))
    a=d[d.strict_description_count_anomaly].copy();a['dataset']=ds;parts.append(a)
an=pd.concat(parts,ignore_index=True);csv('all_strict_count_exceptions.csv',an)
full=[]
for src,g in an.groupby('_source_file'):
    d=pd.read_csv(meta(ROOT/src),low_memory=False)
    selected=set(map(tuple,g[KEY[:2]].to_numpy()))
    mask=pd.MultiIndex.from_frame(d[KEY[:2]]).isin(selected)
    sub=d.loc[mask,KEY+['game_date','balls','strikes','description','events','type','pitch_type','des']].copy()
    sub['_source_file']=src;sub['_source_record']=np.flatnonzero(mask)+1;full.append(sub)
csv('all_strict_count_exceptions_full_PA.csv',pd.concat(full).sort_values(KEY))
special=[];effects=[];features=[];selection=[];laggroups=[]
for rid in IDS:
    man=jr(RUNS/rid/'manifest.json');variant=man['configuration']['variant'];p=ROOT/man['inputs'][0]['path'];d=pd.read_pickle(meta(p))
    elig=d['eligible_'+variant];take=d.loc[elig].copy().reset_index(drop=True);s=pd.read_pickle(meta(RUNS/rid/'artifacts/scores.pkl'))
    assert take[KEY].equals(s[KEY])
    for label,mask in [('HBP',take.description.eq('hit_by_pitch')),('explicit_bunt',take.bunt_explicit),('inplay_bunt_text',take.inplay_bunt_text_flag),('FA_Other',take.pitch_type.eq('FA')),('all',pd.Series(True,index=take.index))]:
        sub=pd.DataFrame({'game_year':take.game_year,'A':s.A,'measurement_support':s.measurement_support,'repertoire':s.repertoire,'propensity_in_bounds':s.p.between(.05,.95),'support':s.support})[mask]
        sub['run_id']=rid;sub['subgroup']=label
        special.append(sub.groupby(list(sub.columns),dropna=False).size().rename('rows').reset_index())
    # Count-row exception impact: saved-score contributions only, no correction/retraining.
    exc_keys=pd.MultiIndex.from_frame(an[KEY]);emask=pd.MultiIndex.from_frame(s[KEY]).isin(exc_keys)
    e=s.loc[emask].copy();e.insert(0,'run_id',rid);effects.append(e)
    for yr,g in s.groupby('game_year'):
        idx=g.index;keep=g.support;emaskg=emask[idx]&keep
        selection.append({'run_id':rid,'game_year':yr,'supported_rows':int(keep.sum()),'exception_rows_supported':int(emaskg.sum()),'stored_phi_delta_mean':float((g.phi1-g.phi0)[keep].mean()),'stored_phi_delta_mean_after_omitting_exception_rows':float((g.phi1-g.phi0)[keep&~emask[idx]].mean()),'scope':'same fitted scores, changed descriptive target only; not corrected-model sensitivity'})
    # Strict lag of automatic records remains a pre-current state in eligible successors.
    for kind,m in [('previous_automatic',take.prev_description.isin(['automatic_ball','automatic_strike'])),('previous_pitchout',take.prev_description.isin(['pitchout','swinging_pitchout','foul_pitchout']))]:
        laggroups.append({'run_id':rid,'kind':kind,'eligible_successors':int(m.sum()),'supported_successors':int((m&s.support).sum())})
    forbidden={'description','events','final_event','result','Y','launch_speed','launch_angle','des','inplay_bunt_text_flag'}
    if variant=='pitch':forbidden|={'pitch_type','release_speed','A_swing','plate_x','plate_z','zone','swing_cell','pfx_x','pfx_z','prev_plate_x','prev_plate_z','prev_zone'}
    declared=man['configuration']['features'];bad=sorted(set(declared)&forbidden)
    CHECKS.append({'item':'forbidden_features:'+rid,'status':'PASS' if not bad else 'FAIL','features':declared,'forbidden_present':bad,'scope':'Manifest/frozen implementation feature allowlist; actual design object fields checked by model/fold reviewer'})
    for f in declared:features.append({'run_id':rid,'model':variant,'feature':f,'lineage':'post-measured current ball proxy' if variant=='swing' and f in ['pitch_type','release_speed_bin','pfx_x_bin','pfx_z_bin','plate_x_bin','relative_z_bin','swing_cell'] else 'strictly previous same-PA raw record' if f.startswith('prev_') else 'current pre-pitch identifier/context'})
    frozen=RUNS/rid/'artifacts/frozen_data.py';current=ROOT/'models/bcap/data.py'
    if frozen.exists():CHECKS.append({'item':'frozen_data_code_matches_current:'+rid,'status':'PASS' if sha(meta(frozen))==sha(meta(current)) else 'FAIL'})
    del d,take,s
csv('special_subgroup_measurement_selection.csv',pd.concat(special,ignore_index=True));csv('exception_saved_score_rows.csv',pd.concat(effects,ignore_index=True));csv('exception_descriptive_omission.csv',pd.DataFrame(selection));csv('lag_of_excluded_records.csv',pd.DataFrame(laggroups));csv('feature_lineage.csv',pd.DataFrame(features))
CHECKS.extend([{'item':'description-specific_count_consistency','status':'FAIL','mismatch_rows':len(an),'scope':'6 recorded nonterminal ball rows fail expected next-count rule; this is a source/measurement exception, not raw-to-processed transformation mismatch. Existing broad delta checker permits unchanged counts and does not detect these.'},{'item':'true_adjudication_of_six_count_exceptions','status':'NOT_VERIFIABLE','scope':'Existing local records do not establish whether a ball was nullified, mislabelled or followed by erroneous count. No new play/video data acquired.'},{'item':'corrected_model_sensitivity_to_exceptions','status':'NOT_RUN','scope':'No input correction or model refit; only stored-score mean omission reported, never corrected-model estimates.'}])
wj('supplement_validation.json',{'started_at_utc':START,'completed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'checks':CHECKS})
meta(Path(__file__),'independent_review_code')
for p in OUT.iterdir():
    if p.is_file() and p.name not in ['supplement_evidence_manifest.json']:meta(p,'review_output' if p.suffix!='.py' else 'independent_review_code')
wj('supplement_evidence_manifest.json',{'command':f'"{sys.executable}" -B "{Path(__file__)}"','started_at_utc':START,'completed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'environment':{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'pandas':pd.__version__,'dont_write_bytecode':sys.dont_write_bytecode},'execution_class':'follow-up existing-raw exception inspection and reaggregation of stored summaries/scores','model_functions_called':False,'records':EVID})
print('supplement_complete',len(an),'strict count exceptions',flush=True)
