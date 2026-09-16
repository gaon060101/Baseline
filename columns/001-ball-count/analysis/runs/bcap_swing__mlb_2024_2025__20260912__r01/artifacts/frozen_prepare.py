"""Minimal V2 preparation from the existing 2024/25 pickle. No raw acquisition/audit."""
from pathlib import Path
import json,hashlib,datetime,sys
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[4];COL=ROOT/'columns/001-ball-count';AN=COL/'analysis'
KEY=['game_pk','at_bat_number','pitch_number']
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return dict(path=Path(p).relative_to(ROOT).as_posix(),sha256=sha(p),bytes=Path(p).stat().st_size)
def js(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x)),encoding='utf-8')
def main():
 day=datetime.datetime.now().strftime('%Y%m%d');bundle=AN/f'bcap_v2_development_{day}__r01'
 source=COL/'data/processed/bcap_dev_v010_20260909_r01.pkl';out=COL/f'data/processed/bcap_dev_v2_{day}__r01.pkl'
 audit=bundle/'preparation';assert not out.exists() and not audit.exists();audit.mkdir()
 start=now();d=pd.read_pickle(source);checks=[]
 def check(name,ok,detail=None):
  checks.append(dict(check=name,status='PASS' if bool(ok) else 'FAIL',detail=detail))
  if not ok:raise AssertionError(name)
 check('development_years_only',set(d.game_year.unique())=={2024,2025})
 check('unique_complete_pitch_keys',not d[KEY].isna().any().any() and not d.duplicated(KEY).any())
 check('valid_count',d.balls.between(0,3).all() and d.strikes.between(0,2).all())
 check('count_labels',d['count'].astype(str).eq(d.balls.astype(str)+'-'+d.strikes.astype(str)).all())
 check('PA_Y_constant',d.groupby('pa_id',observed=True).Y.nunique().le(1).all())
 spec=json.loads((ROOT/'models/bcap/pitch/v0.2.0/specification.yaml').read_text(encoding='utf-8'))
 # Basic Y check uses retained terminal events and original OBS classification; no raw reconstruction.
 obs=json.loads((ROOT/'models/bcai/observed/v1.0.0/specification.yaml').read_text(encoding='utf-8-sig'))
 eventmap={e:k for k,v in obs['result_classification'].items() for e in v}
 last=d.drop_duplicates('pa_id',keep='last').set_index('pa_id')
 final=d.pa_id.map(last.events.astype('string'))
 check('terminal_event_link',final.fillna('MISSING').eq(d.final_event.astype('string').fillna('MISSING')).all())
 expected_result=final.map(eventmap)
 check('result_classification',expected_result.astype('string').fillna('MISSING').eq(d.result.astype('string').fillna('MISSING')).all())
 yy=np.array([spec['weights'][str(y)].get(str(r),0.) if ok else np.nan for y,r,ok in zip(d.game_year,d.result,d.eligible_pa)])
 check('season_W_no_extra_reward',np.allclose(d.Y,yy,rtol=0,atol=0,equal_nan=True))
 fb=spec['actions']['FB'];nfb=spec['actions']['NFB']
 coarse={**{x:'FB' for x in fb},**{x:'NFB' for x in nfb}}
 group=d.pitch_type.astype('string').map(coarse).fillna('UNCLASSIFIED')
 check('current_closed_pitch_mapping',group.astype(str).eq(d.pitch_group.astype(str)).all())
 d['prev_pitch_group']=d.prev_pitch_type.astype('string').map({**coarse,'START':'START','MISSING_PREVIOUS':'MISSING_PREVIOUS'}).fillna('UNCLASSIFIED').astype('category')
 check('no_fine_lag_categories',set(d.prev_pitch_group.astype(str))<= {'FB','NFB','START','MISSING_PREVIOUS','UNCLASSIFIED'})
 for m in ['pitch','swing']:
  a=d.loc[d['eligible_'+m],'A_'+m]
  check(m+'_complete_binary_action',a.notna().all() and a.isin([0,1]).all())
 check('pitch_action_definition',d.loc[d.eligible_pitch,'A_pitch'].eq(d.loc[d.eligible_pitch,'pitch_group'].eq('FB').astype(int)).all())
 swingmap={**{x:1 for x in spec['actions']['Swing']},**{x:0 for x in spec['actions']['Take']}}
 check('swing_action_definition',d.loc[d.eligible_swing,'A_swing'].eq(d.loc[d.eligible_swing,'description'].astype('string').map(swingmap)).all())
 geometry=d[['plate_x','plate_z','sz_top','sz_bot']].to_numpy(dtype=float)
 valid=np.isfinite(geometry).all(axis=1)&d.sz_top.gt(d.sz_bot).to_numpy()
 inside=d.plate_x.abs().le(17/24)&d.plate_z.ge(d.sz_bot)&d.plate_z.le(d.sz_top)
 d['A_pitch_sb']=pd.array(np.where(valid,inside.astype(int),np.nan),dtype='Int8')
 d['eligible_pitch_sb']=d.eligible_pitch & valid
 d['reason_pitch_sb']=np.where(~d.eligible_pitch,d.reason_pitch.astype(str),np.where(~valid,'invalid_geometry','included'))
 check('SB_complete_binary_action',d.loc[d.eligible_pitch_sb,'A_pitch_sb'].notna().all())
 check('SB_boundary_legacy_separate',d.loc[d.zone.eq('BOUNDARY') & d.eligible_pitch_sb,'A_pitch_sb'].nunique()==2)
 # Existing unresolved anomalies are flags only; no new wide sequence audit or corrections.
 known={(746664,63,6),(778541,42,6)}
 d['known_count_exception']=pd.MultiIndex.from_frame(d[KEY]).isin(known)
 check('known_development_exception_rows',int(d.known_count_exception.sum())==2)
 d.loc[d.known_count_exception,KEY+['count','description','A_pitch','A_swing','A_pitch_sb']].to_csv(audit/'known_exceptions_retained.csv',index=False)
 flow=[]
 for model in ['pitch','pitch_sb','swing']:
  for year,g in d.groupby('game_year',observed=True):
   for reason,z in g.groupby('reason_'+model,observed=True,dropna=False):flow.append(dict(model=model,year=int(year),reason=str(reason),rows=len(z),PA=z.pa_id.nunique(),games=z.game_pk.nunique()))
 pd.DataFrame(flow).to_csv(audit/'selection_counts.csv',index=False)
 pd.crosstab(d.loc[d.eligible_pitch_sb,'zone'],d.loc[d.eligible_pitch_sb,'A_pitch_sb']).to_csv(audit/'SB_by_legacy_zone.csv')
 d.to_pickle(out)
 result=dict(status='PASS',started_at_utc=start,finished_at_utc=now(),scope='Basic reused development-pickle checks; no raw source audit or independent verifier',years=[2024,2025],rows=len(d),games=d.game_pk.nunique(),PA=d.pa_id.nunique(),eligible={m:int(d['eligible_'+m].sum()) for m in ['pitch','pitch_sb','swing']},checks=checks,input=meta(source),output=meta(out),code=meta(Path(__file__)),definitions=[meta(ROOT/'models/bcap/pitch/v0.2.0/specification.yaml'),meta(ROOT/'models/bcai/observed/v1.0.0/specification.yaml')],known_exceptions='Six known historically; two belong to2024/25 and retained. No external records opened, no cause investigation.',not_run=['external data','raw-file rehash audit','full independent review','refits or bootstrap'])
 js(audit/'preparation.json',result);print(json.dumps({k:result[k] for k in ['status','rows','games','eligible']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
