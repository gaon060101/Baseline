"""Read trusted local pickles and preserve values as CSV for R; no statistical fits.

Original game split records are exported verbatim into a compact membership map.
Missing values use an explicit sentinel to distinguish literal MISSING categories.
"""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COL = ROOT / 'columns/001-ball-count'
FIELDS = ['row_id','game_pk','at_bat_number','pitch_number','game_year','game_date',
          'count','pitcher','batter','final_event','result','Y','zone','pitch_group',
          'pitch_type','stand','plate_x','plate_z','sz_top','sz_bot','release_speed',
          'pfx_x','pfx_z','venue','matchup','base_state','outs_when_up','inning_bin',
          'score_bin','pitch_number_bin','prev_pitch_group','prev_description',
          'prev_release_speed_bin','eligible_pitch','eligible_pitch_sb','eligible_swing',
          'A_pitch','A_pitch_sb','A_swing','known_count_exception']

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True)
    p.add_argument('--output',required=True);p.add_argument('--reference-date',default='20260912')
    p.add_argument('--period',default='2024_2025');p.add_argument('--models',default='pitch,pitch_sb,swing,pitch_ff')
    p.add_argument('--reference-run-suffix',default='r01');a=p.parse_args()
    out=Path(a.output)
    if out.exists(): raise FileExistsError(out)
    out.mkdir(parents=True);source=Path(a.input);h=sha(source)
    d=pd.read_pickle(source)
    fields=[c for c in FIELDS if c in d.columns]
    d[fields].to_csv(out/'rows.csv',index=False,encoding='utf-8',na_rep='__BCAP_NA__')
    metadata={'role':'format transport only; no new estimates, eligibility or folds',
              'source':str(source),'source_sha256':h,'rows':len(d),'fields':fields,
              'python_pandas':pd.__version__,'references':{}}
    del d
    for model in a.models.split(','):
        run=COL/'analysis/runs'/f'bcap_{model}__mlb_{a.period}__{a.reference_date}__{a.reference_run_suffix}'
        if not run.exists(): continue
        records=json.loads((run/'artifacts/fold_records.json').read_text(encoding='utf-8-sig'))
        outer={};cal=[]
        for r in records:
            label=r['fit_id']
            if '/' not in label:
                k=int(label.replace('fold',''))
                for game in r['evaluation_games']: outer[game]=k
            elif label.endswith('/cal'):
                k=int(label.split('/')[0].replace('fold',''))
                cal.extend({'outer_fold':k,'game_pk':game} for game in r['evaluation_games'])
        pd.DataFrame([{'game_pk':g,'fold':k} for g,k in sorted(outer.items())]).to_csv(out/f'{model}_folds.csv',index=False)
        pd.DataFrame(cal).to_csv(out/f'{model}_calibration_games.csv',index=False)
        s=pd.read_pickle(run/'artifacts/scores.pkl')
        s[['row_id','p','mu0','mu1','phi0','phi1','support']].to_csv(out/f'{model}_reference_scores.csv',index=False,encoding='utf-8')
        del s
        metadata['references'][model]={'run':str(run),'manifest_sha256':sha(run/'manifest.json'),
           'split_records_sha256':sha(run/'artifacts/fold_records.json'),'scores_sha256':sha(run/'artifacts/scores.pkl')}
    assert h==sha(source),'Source changed during format transport'
    metadata['outputs']={f.name:{'sha256':sha(f),'bytes':f.stat().st_size} for f in out.iterdir() if f.is_file()}
    (out/'provenance.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'rows':metadata['rows'],'reference_models':list(metadata['references']),'source_unchanged':True}))

if __name__=='__main__':main()
