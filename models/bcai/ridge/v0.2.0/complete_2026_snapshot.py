"""Acquisition-only repair of 11 missing Sept 7 games. Frozen evaluator/model unchanged.
2026 failed before evaluation (evaluation_passes=0); this runs its first evaluation.
"""
from pathlib import Path
import json,io,urllib.parse
import pandas as pd
import external_validation as ev
import ridge_v02 as m
OLD=m.COL/'data/raw/mlb/2026/snapshot_20260908_ridge_v02'
NEW=m.COL/'data/raw/mlb/2026/supplement_20260909_ridge_v02'
def repaired_acquisition(year,raw,cutoff):
    assert year==2026 and cutoff=='2026-09-07'
    audit=json.loads((OLD/'acquisition_audit.json').read_text(encoding='utf-8'))
    expected_missing=set(audit['missing_games']);assert len(expected_missing)==11
    prior=json.loads((m.ANAL/'runs/bcai_ridge__mlb_2026_ytd_20260907__20260908__r01/manifest.json').read_text(encoding='utf-8'))
    assert prior['status']=='FAILED' and prior['evaluation_passes']==0
    NEW.mkdir(parents=True,exist_ok=True)
    # Same cutoff/schedule. Do not change historical bytes; only add missing game IDs.
    supplement=NEW/'statcast_2026-09-07_missing_games.csv'
    params=dict(all='true',type='details',hfGT='R|',hfSea='2026|',player_type='pitcher',game_date_gt='2026-09-07',game_date_lt='2026-09-07',group_by='name',min_pitches=0,min_results=0,sort_col='pitches',sort_order='desc')
    url='https://baseballsavant.mlb.com/statcast_search/csv?'+urllib.parse.urlencode(params)
    if not supplement.exists():supplement.write_bytes(ev.fetch(url))
    columns=set(m.OLD['input_fields']['pitch']+m.OLD['input_fields']['context']+['game_date','game_type'])
    add=pd.read_csv(supplement,usecols=lambda c:c in columns,low_memory=False)
    assert len(add)<25000 and add.game_date.eq('2026-09-07').all() and add.game_type.eq('R').all()
    add=add[add.game_pk.isin(expected_missing)].copy()
    assert set(add.game_pk)==expected_missing,'Missing games still unavailable; no evaluation'
    parts=[]
    for rec in audit['files']:
        f=m.ROOT/rec['path'];assert m.sha(f)==rec['sha256'];parts.append(pd.read_csv(f,usecols=lambda c:c in columns,low_memory=False))
    data=pd.concat(parts+[add],ignore_index=True)
    sch=json.loads((OLD/'schedule_2026.json').read_text(encoding='utf-8-sig'))
    expected={g['gamePk'] for day in sch['dates'] for g in day['games'] if g['gameType']=='R' and g['status']['abstractGameState']=='Final' and g['status'].get('detailedState')!='Cancelled' and g['officialDate']<=cutoff}
    assert set(data.game_pk)==expected
    assert not data.duplicated(['game_pk','at_bat_number','pitch_number']).any()
    current=dict(audit,snapshot_at=m.now(),raw_rows=len(data),included_rows=len(data),included_games=len(expected),missing_games=[],duplicate_pitch_keys=0,
                 original_snapshot=m.meta(OLD/'acquisition_audit.json'),supplement_reason='Eleven 2026-09-07 completed games absent in initial Statcast acquisition; no 2026 metrics previously evaluated',
                 files=audit['files']+[dict(**m.meta(supplement),rows=len(add),url=url)],supplement_game_ids=sorted(expected_missing))
    m.writejson(NEW/'acquisition_audit.json',current)
    return data,sch,current
if __name__=='__main__':
    # Adapter replaces acquisition only; prediction, weights, normalization, metrics stay byte-identical.
    ev.acquire=repaired_acquisition
    ev.evaluate(2026,'bcai_ridge__mlb_2024_2025__20260908__r02','bcai_ridge__mlb_2026_ytd_20260907__20260909__r01')
