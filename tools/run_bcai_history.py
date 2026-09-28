"""Acquire/transport authorized seasons, then call R. No statistical estimation in Python."""
import argparse, csv, datetime as dt, hashlib, http.client, io, json, os, subprocess, time, urllib.request, urllib.parse, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
COL=ROOT/'columns/001-ball-count'
BUNDLE=COL/'analysis/r_history_20260928'
FIELDS=['game_pk','at_bat_number','pitch_number','game_year','game_date','balls','strikes','events']
def meta(p):
    with p.open('rb') as f: h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=p.relative_to(ROOT).as_posix(),sha256=h,bytes=p.stat().st_size)
def save(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Baseline user-requested historical baseball research'}),timeout=90) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (401,403,429): raise
            if attempt==2: raise
            time.sleep(2*(attempt+1))
        except (TimeoutError,ConnectionError,http.client.IncompleteRead,urllib.error.URLError):
            if attempt==2: raise
            time.sleep(2*(attempt+1))
def obtain(year,workers=2):
    if year==2023:
        folder=COL/'data/raw/mlb/2023/snapshot_20260908_ridge_v02'
        files=sorted(folder.glob('statcast_*.csv')); schedule=folder/'schedule_2023.json'
        if not files or not schedule.exists(): raise RuntimeError('Existing 2023 input missing; do not recollect silently')
        return files,schedule
    folder=COL/f'data/raw/mlb/{year}/snapshot_20260928_r_history'
    folder.mkdir(parents=True,exist_ok=True)
    schedule=folder/f'schedule_{year}.json'
    surl=f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={year}-01-01&endDate={year}-12-31&gameTypes=R'
    if not schedule.exists(): schedule.write_bytes(get(surl))
    sch=json.loads(schedule.read_text(encoding='utf-8-sig'))
    games=[g for day in sch['dates'] for g in day['games'] if g['gameType']=='R' and g['status']['abstractGameState']=='Final' and g['status'].get('detailedState')!='Cancelled']
    dates=sorted(g['officialDate'] for g in games)
    if not dates: raise RuntimeError('No final regular-season schedule')
    jobs=[]; a=dt.date.fromisoformat(dates[0]); last=dt.date.fromisoformat(dates[-1])
    while a<=last:
        b=min(a+dt.timedelta(days=4),last);jobs.append((a,b));a=b+dt.timedelta(days=1)
    def chunk(pair):
        a,b=pair;p=folder/f'statcast_{a}_{b}.csv'
        params=dict(all='true',type='details',hfGT='R|',hfSea=f'{year}|',player_type='pitcher',game_date_gt=str(a),game_date_lt=str(b),group_by='name',min_pitches=0,min_results=0,sort_col='pitches',sort_order='desc')
        url='https://baseballsavant.mlb.com/statcast_search/csv?'+urllib.parse.urlencode(params)
        data=p.read_bytes() if p.exists() else get(url)
        frame=pd.read_csv(io.BytesIO(data),usecols=lambda c:c in FIELDS+['game_type'])
        if not set(FIELDS+['game_type'])<=set(frame): raise RuntimeError(f'Invalid Statcast CSV {year} {a}')
        if len(frame)>=25000:
            if a==b: raise RuntimeError('Daily result limit')
            mid=a+(b-a)//2
            return chunk((a,mid))+chunk((mid+dt.timedelta(days=1),b))
        if len(frame) and (not frame.game_type.eq('R').all() or not frame.game_date.between(str(a),str(b)).all()): raise RuntimeError('Unexpected date/game type')
        if not p.exists(): p.write_bytes(data)
        return [dict(**meta(p),rows=len(frame),url=url)]
    parts=[]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i,result in enumerate(pool.map(chunk,jobs)):
            parts.extend(result)
            save(folder/'acquisition_progress.json',dict(year=year,status='ACQUIRING',completed_chunks=i+1,total_chunks=len(jobs),files=parts))
            if i%5==0: print(year,'download',i+1,'/',len(jobs),flush=True)
    save(folder/'acquisition.json',dict(status='DOWNLOADED_NOT_YET_COVERAGE_CHECKED',year=year,schedule_url=surl,schedule=meta(schedule),files=parts))
    return [ROOT/x['path'] for x in parts],schedule
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--years',nargs='+',type=int,required=True);ap.add_argument('--rscript',required=True)
    ap.add_argument('--download-workers',type=int,choices=[1,2],default=2)
    ap.add_argument('--progress-file',type=Path,default=BUNDLE/'progress.json')
    args=ap.parse_args();progress_path=args.progress_file
    if not progress_path.is_absolute():progress_path=ROOT/progress_path
    if not progress_path.resolve().is_relative_to(BUNDLE.resolve()):ap.error('Progress file must stay in history analysis bundle')
    weight_table=pd.read_csv(BUNDLE/'weights.csv'); summary=[]
    env=os.environ.copy()
    for k in ('LANG','LC_ALL','LC_CTYPE'):env.pop(k,None)
    for year in args.years:
        record=dict(year=year,status='STARTED');summary.append(record);save(progress_path,summary)
        try:
            files,schedule=obtain(year,args.download_workers)
            outdir=COL/f'data/processed/r_history_20260928/{year}'
            outdir.mkdir(parents=True,exist_ok=True)
            inp=outdir/'pitches.csv'; prov=outdir/'pitches.provenance.json'
            if not inp.exists():
                frames=[pd.read_csv(f,usecols=FIELDS,low_memory=False) for f in files]
                d=pd.concat(frames,ignore_index=True)
                if d.duplicated(['game_pk','at_bat_number','pitch_number']).any(): raise RuntimeError('Duplicate historical pitch keys')
                d.to_csv(inp,index=False,encoding='utf-8-sig')
                save(prov,dict(role='format transport; no PA aggregation',source_files=[meta(f) for f in files],output=meta(inp),rows=len(d)))
                del frames,d
            else:
                if not prov.exists() or meta(inp)['sha256']!=json.loads(prov.read_text(encoding='utf-8'))['output']['sha256']: raise RuntimeError('Unverified preexisting transport')
            runid=f'bcai_history__mlb_{year}__20260928__r01';run=COL/'analysis/runs'/runid
            if (run/'manifest.json').exists():
                existing=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
                if existing['status']=='COMPLETE':record.update(status='COMPLETE_EXISTING',run=runid);continue
                raise RuntimeError('Prior non-complete run exists; choose a new run ID manually')
            run.mkdir(exist_ok=True)
            w=weight_table[weight_table.year.eq(year)].to_dict('records')
            if len(w)!=1:raise RuntimeError('Weight year unavailable')
            cfg=dict(run_id=runid,model_id='BCAI-OBS-v1.0.0',version='1.0.0',input_csv=[inp.relative_to(ROOT).as_posix()],
                input_provenance=[prov.relative_to(ROOT).as_posix()],years=[year],seasons=[dict(year=year,cutoff=f'{year}-12-31',scope='full_regular_season',schedule=schedule.relative_to(ROOT).as_posix())],
                weights=w,weights_source=(BUNDLE/'weights.csv').relative_to(ROOT).as_posix(),bootstrap_replicates=2000,seed=20260928,
                comparisons=[],tolerance=1e-9,data_source='MLB Baseball Savant; archived Statcast',source_notes='columns/001-ball-count/sources.md')
            save(run/'config.json',cfg)
            with (run/'execution.log').open('w',encoding='utf-8') as log:
                subprocess.run([args.rscript,'--vanilla','models/bcai/observed/v1.0.0/r/run.R',str(run/'config.json')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
            record.update(status='COMPLETE',run=runid);print(year,'R COMPLETE',flush=True)
        except Exception as e:
            record.update(status='FAILED',error=str(e));print(year,'FAILED',str(e),flush=True)
            if isinstance(e,urllib.error.HTTPError) and e.code in (401,403,429):
                record['stop_reason']='Access refusal; no bypass or bulk retry';save(progress_path,summary);break
        finally:save(progress_path,summary)
if __name__=='__main__':main()
