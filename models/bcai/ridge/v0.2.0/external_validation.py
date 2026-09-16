"""Frozen external acquisition/evaluation. Does not fit any model or choose hyperparameters."""
from pathlib import Path
import sys,json,urllib.request,urllib.parse,time,io,datetime,argparse
from concurrent.futures import ThreadPoolExecutor
import ridge_v02 as m
import numpy as np
import pandas as pd
F=m.MODEL
def fetch(url):
    for attempt in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Baseline user-requested baseball analysis CSV download'})
            with urllib.request.urlopen(req,timeout=120) as resp:return resp.read()
        except Exception:
            if attempt==2:raise
            time.sleep(2*(attempt+1))
def acquire(year,raw,cutoff):
    raw.mkdir(parents=True,exist_ok=True)
    schedule_url=f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={year}-01-01&endDate={cutoff}&gameTypes=R'
    sp=raw/f'schedule_{year}.json'
    if not sp.exists():sp.write_bytes(fetch(schedule_url))
    sch=json.loads(sp.read_text(encoding='utf-8-sig'))
    games=[g for day in sch['dates'] for g in day['games'] if g['gameType']=='R' and g['status']['abstractGameState']=='Final' and g['status'].get('detailedState')!='Cancelled' and g['officialDate']<=cutoff]
    expected={g['gamePk'] for g in games};days=sorted({g['officialDate'] for g in games})
    if not days:raise RuntimeError(f'No completed games returned for {year}')
    lo=datetime.date.fromisoformat(days[0]);hi=datetime.date.fromisoformat(days[-1]);jobs=[]
    while lo<=hi:
        end=min(lo+datetime.timedelta(days=4),hi);jobs.append((lo,end));lo=end+datetime.timedelta(days=1)
    print(year,'schedule games',len(expected),'last date',days[-1],flush=True)
    def chunk(bounds):
        a,b=bounds;p=raw/f'statcast_{a}_{b}.csv'
        params=dict(all='true',type='details',hfGT='R|',hfSea=f'{year}|',player_type='pitcher',game_date_gt=str(a),game_date_lt=str(b),group_by='name',min_pitches=0,min_results=0,sort_col='pitches',sort_order='desc')
        url='https://baseballsavant.mlb.com/statcast_search/csv?'+urllib.parse.urlencode(params)
        data=p.read_bytes() if p.exists() else fetch(url)
        frame=pd.read_csv(io.BytesIO(data),usecols=lambda c:c in set(m.OLD['input_fields']['pitch']+m.OLD['input_fields']['context']+['game_date','game_type']),low_memory=False)
        if 'game_pk' not in frame:raise RuntimeError(f'Invalid CSV {url}')
        if len(frame)>=25000:
            if a==b:raise RuntimeError('Daily cap')
            mid=a+(b-a)//2;return chunk((a,mid))+chunk((mid+datetime.timedelta(days=1),b))
        if len(frame):
            assert frame.game_type.eq('R').all() and frame.game_date.between(str(a),str(b)).all()
        if not p.exists():p.write_bytes(data)
        return [(frame,dict(**m.meta(p),rows=len(frame),url=url))]
    pieces=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        for idx,res in enumerate(pool.map(chunk,jobs)):
            pieces.extend(res)
            if idx%10==0:print(year,'download batches',idx+1,'/',len(jobs),flush=True)
    data=pd.concat([x[0] for x in pieces],ignore_index=True)
    found=set(data.game_pk.unique());extra=found-expected;missing=expected-found
    # Snapshot excludes in-progress/suspended games present in raw response.
    filtered=data[data.game_pk.isin(expected)].copy()
    dup=int(filtered.duplicated(['game_pk','at_bat_number','pitch_number']).sum())
    audit=dict(year=year,cutoff=cutoff,snapshot_at=m.now(),schedule_url=schedule_url,schedule=m.meta(sp),expected_games=len(expected),raw_rows=len(data),included_rows=len(filtered),included_games=int(filtered.game_pk.nunique()),missing_games=sorted(missing),extra_response_games_excluded=sorted(extra),duplicate_pitch_keys=dup,first_game_date=days[0],last_game_date=days[-1],files=[x[1] for x in pieces])
    m.writejson(raw/'acquisition_audit.json',audit)
    if missing or dup:raise RuntimeError(f'Data validation failed missing={len(missing)} duplicates={dup}')
    return filtered,sch,audit

def nominal(v):
    return '타자 매우 유리' if v>=115 else '타자 유리' if v>=105 else '투수 매우 유리' if v<=85 else '투수 유리' if v<=95 else '중립'

def evaluate(year,devrun,runid):
    dev=m.ANAL/'runs'/devrun/'artifacts';freeze=json.loads((dev/'freeze.json').read_text(encoding='utf-8'))
    for rec in freeze['files']:assert m.sha(m.ROOT/rec['path'])==rec['sha256'],'Frozen input changed'
    run=m.ANAL/'runs'/runid
    if run.exists():raise FileExistsError('External run IDs are immutable; new run needs explicit reason')
    art=run/'artifacts';art.mkdir(parents=True)
    cutoff='2023-12-31' if year==2023 else freeze['external_snapshot_cutoff']
    state=json.loads((dev/'frozen_model.json').read_text(encoding='utf-8'))
    manifest=dict(run_id=runid,model_id='BCAI-RIDGE-v0.2.0',version='0.2.0',model_status='EXPERIMENTAL',role='external_reproduction' if year==2023 else 'external_forward_time',status='ACQUIRING',run_date=datetime.date.today().isoformat(),started_at=m.now(),cutoff=cutoff,development_run=devrun,model_freeze=m.meta(dev/'freeze.json'),frozen_model=m.meta(dev/'frozen_model.json'),code=[m.meta(Path(__file__)),m.meta(F/'ridge_v02.py')],environment=m.environment(),external_data_used_for_tuning=False,evaluation_passes=0)
    m.writejson(run/'manifest.json',manifest)
    try:
        raw=m.COL/f'data/raw/mlb/{year}/snapshot_20260908_ridge_v02'
        data,sch,acq=acquire(year,raw,cutoff)
        p,reach,audit=m.make_pa(data,[sch])
        manifest.update(status='EVALUATING',evaluation_started_at=m.now(),evaluation_passes=1);m.writejson(run/'manifest.json',manifest)
        pred=np.full(len(p),state['intercept']);flags={};past={};beta=np.array(state['beta']);mean=np.array(state['design']['mean']);counts=np.array(state['design']['training_counts'])
        for feature,levels,(lo,hi) in zip(state['features'],state['design']['maps'],state['design']['blocks']):
            encoded=p[feature].fillna('missing').astype(str).map(levels);known=encoded.notna().to_numpy();idx=encoded.fillna(0).astype(int).to_numpy()
            pred[known]+=beta[idx[known]]-mean[lo:hi]@beta[lo:hi];flags[feature]=~known;past[feature]=np.where(known,counts[idx],0)
        scale=np.full(len(p),state['external_base']);pred*=scale
        metrics=m.score(p,pred,scale);table=m.index_table(p,reach,pred);m.csv(art/'count_indices.csv',table)
        subgroups=[]
        for feature in state['features']:
            for label,mask in [('known',~flags[feature]),('unseen',flags[feature])]:
                if mask.any():subgroups.append(dict(feature=feature,group=label,share_pct=float(100*mask.mean()),**m.score(p.loc[mask],pred[mask],scale[mask])))
        both=~(flags['batter']|flags['pitcher'])
        for label,mask in [('both_players_known',both),('at_least_one_unseen_player',~both)]:
            if mask.any():subgroups.append(dict(feature='players_combined',group=label,share_pct=float(100*mask.mean()),**m.score(p.loc[mask],pred[mask],scale[mask])))
        m.csv(art/'unseen_performance.csv',subgroups);m.csv(art/'scores.csv',[metrics])
        baseline=pd.read_csv(dev/'count_indices.csv');base=baseline[baseline.period.eq('combined')].set_index('count');current=table[table.period.eq('combined')].copy()
        current['development_J']=current['count'].map(base.J);current['development_I']=current['count'].map(base.I)
        current['J_rank']=current.J.rank();current['development_J_rank']=current.development_J.rank()
        current['same_J_direction']=np.sign((current.J-100).round(8))==np.sign((current.development_J-100).round(8))
        current['J_nominal_band']=current.J.map(nominal);current['development_J_nominal_band']=current.development_J.map(nominal);current['same_nominal_band']=current.J_nominal_band==current.development_J_nominal_band
        m.csv(art/'reproduction.csv',current)
        checks=dict(minimum_J=current.loc[current.J.idxmin(),'count'],maximum_J=current.loc[current.J.idxmax(),'count'],same_direction_count=int(current.same_J_direction.sum()),same_nominal_band_count=int(current.same_nominal_band.sum()),rank_spearman=float(current.J_rank.corr(current.development_J_rank)),max_abs_shift=float(current['shift'].abs().max()))
        m.writejson(art/'sample_audit.json',audit);m.writejson(art/'acquisition_audit.json',acq);m.writejson(art/'reproduction_summary.json',checks)
        output=p[['game_pk','at_bat_number','game_year','value']].assign(prediction_W=pred)
        for feature in state['features']:output[f'unseen_{feature}']=flags[feature];output[f'train_N_{feature}']=past[feature]
        m.csv(art/'predictions.csv',output)
        manifest.update(status='COMPLETE',completed_at=m.now(),sample=audit,data_period={'first':acq['first_game_date'],'last':acq['last_game_date']},inputs=acq['files']+[acq['schedule']],weights=m.WEIGHTS[year],baseline={'training_fixed':state['external_base'],'evaluation_season':float(p.value.mean())},features=state['features'],selected_alpha=state['selected_alpha'],solver='frozen inference only; no fitting',tolerance=1e-7,max_iterations=5000,convergence='see development manifest; no external fit',exclusions=m.OLD['exclusions'],metrics=metrics,reproduction=checks,artifacts=[m.meta(f) for f in sorted(art.glob('*')) if f.is_file()])
        m.writejson(run/'manifest.json',manifest);print(year,'EXTERNAL COMPLETE',metrics,checks,flush=True)
    except Exception as exc:
        manifest.update(status='FAILED',error=str(exc),failed_at=m.now());m.writejson(run/'manifest.json',manifest);raise

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--year',type=int,choices=[2023,2026],required=True);ap.add_argument('--development-run',required=True);ap.add_argument('--run-id',required=True);args=ap.parse_args();evaluate(args.year,args.development_run,args.run_id)
