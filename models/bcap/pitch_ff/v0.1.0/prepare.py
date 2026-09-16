"""Reuse only the existing2024/2025 pickle and original PITCH game membership."""
from pathlib import Path
import argparse,datetime,hashlib,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[4];CODE=Path(__file__).parent
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def j(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def js(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bundle',required=True);a=ap.parse_args();b=ROOT/a.bundle;plan=j(b/'analysis_plan.json');c=j(CODE/'specification.yaml')
 assert not (b/'preparation.json').exists()
 src=ROOT/plan['source'];old=ROOT/'columns/001-ball-count/analysis/runs'/plan['old_run'];oldman=j(old/'manifest.json');source=meta(src)
 assert source['sha256']==oldman['input']['sha256']
 for x in j(b/'plan_seal.json')['files']:assert sha(ROOT/x['path'])==x['sha256']
 d=pd.read_pickle(src);checks=[]
 def ck(n,v):
  assert v,n
  checks.append({'check':n,'status':'PASS'})
 ck('only2024_2025',set(d.game_year.unique())=={2024,2025})
 key=['row_id','game_pk','at_bat_number','pitch_number']
 ck('unique_keys',not d.duplicated(key[1:]).any() and d.row_id.is_unique)
 valid=sum(c['action_codes'].values(),[])
 ck('closed_codes_for_eligible',d.loc[d.eligible_pitch,'pitch_type'].isin(valid).all())
 freq=d.assign(pitch_code=d.pitch_type.astype('string').fillna('MISSING')).groupby(['pitch_code','eligible_pitch','reason_pitch'],dropna=False,observed=True).size().rename('rows').reset_index()
 freq.to_csv(b/'input_code_eligibility.csv',index=False,encoding='utf-8-sig')
 d=d[d.eligible_pitch].copy();d['A']=d.pitch_type.eq('FF').astype(int)
 ck('legacy_action_map',np.array_equal(d.A_pitch.astype(int),d.pitch_type.isin(['FF','SI','FC']).astype(int)))
 ck('FF_action_map',np.array_equal(d.A,d.pitch_type.eq('FF').astype(int)))
 ck('PA_Y_constant',d.groupby(['game_pk','at_bat_number']).Y.nunique().eq(1).all())
 want=np.array([c['weights'][str(y)].get(r,0.) for y,r in zip(d.game_year,d.result)])
 ck('seasonal_W',np.allclose(d.Y,want,rtol=0,atol=1e-12))
 ck('pre_count_consistent',d['count'].eq(d.balls.astype(str)+'-'+d.strikes.astype(str)).all())
 mem=pd.read_csv(old/'artifacts/fold_membership.csv');ck('same_eligible_row_ids',set(d.row_id)==set(mem.row_id))
 joined=d.merge(mem[key+['fold','A']].rename(columns={'A':'old_saved_A'}),on=key,how='left',validate='one_to_one')
 ck('same_pitch_keys_and_old_labels',joined.fold.notna().all() and joined.old_saved_A.eq(joined.A_pitch).all())
 ck('one_fold_per_game',joined.groupby('game_pk').fold.nunique().eq(1).all())
 cols=list(dict.fromkeys(key+['game_date','game_year','pa_id','balls','strikes','count','pitcher','batter','pitch_type','pitch_group','zone','final_event','result','Y','A','A_pitch','eligible_pitch','known_count_exception','fold']+c['features']))
 out=joined[cols].copy();out['fold']=out.fold.astype(int)
 filename=plan['new_run'].replace('bcap_pitch_ff__mlb_2024_2025__','bcap_pitch_ff_dev_')+'.pkl'
 dest=ROOT/'columns/001-ball-count/data/processed'/filename;assert not dest.exists();out.to_pickle(dest)
 js(b/'preparation.json',{'status':'PASS','at_utc':now(),'source':source,'old_membership':meta(old/'artifacts/fold_membership.csv'),'output':meta(dest),'rows':len(out),'games':int(out.game_pk.nunique()),'checks':checks,'retained_count_exceptions':int(out.known_count_exception.sum()),'excluded_rows':1424427-len(out),'preserved':'All old inputs unchanged; new slim training input keeps keys/action/outcome/pre-pitch features and analysis metadata.'})
 print(json.dumps({'status':'PASS','rows':len(out),'output':str(dest)},ensure_ascii=True))
if __name__=='__main__':main()
