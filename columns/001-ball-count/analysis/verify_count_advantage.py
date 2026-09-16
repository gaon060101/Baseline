from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from bcai_paths import CACHE, COLUMN, output_dir
P=output_dir(writable=True)
R=COLUMN
a=json.loads((P/'advantage_audit.json').read_text(encoding='utf-8'))
r=pd.read_csv(P/'advantage_count_results.csv').set_index('count')
e=pd.read_csv(P/'advantage_pa_outcomes.csv').set_index('count')
d=pd.read_pickle(CACHE)
d['count']=d.balls.astype(int).astype(str)+'-'+d.strikes.astype(int).astype(str)
keys=['game_pk','at_bat_number']
last=d.drop_duplicates(keys,keep='last')[keys+['game_year','events']]
reached=d[keys+['count']].drop_duplicates().merge(last,on=keys)
mapping={'single':'1B','double':'2B','triple':'3B','home_run':'HR','walk':'BB','intent_walk':'BB','hit_by_pitch':'HBP'}
reached['v']=[a['weights'][str(int(yr))].get(mapping.get(ev,''),0) for yr,ev in zip(reached.game_year,reached.events)]
excluded=reached.events.isna()|reached.events.isin(['truncated_pa','catcher_interf','intent_walk'])
good=reached[~excluded]
point=np.zeros(12)
for yr in (2024,2025):
    m=good[good.game_year.eq(yr)].groupby('count').v.mean().reindex(r.index)
    point+=100*a['season_mix'][str(yr)]*m.to_numpy()/m.loc['0-0']
assert np.allclose(point,r['index'],rtol=0,atol=1e-9)
assert np.allclose(e[['H%','BB%','HBP%','K%','OUT%','OTHER%']].sum(axis=1),100)
actual=d.pitch_name.notna()&~d.description.isin(['automatic_ball','automatic_strike'])
observed=d[actual].groupby('count').size()
existing=pd.read_csv(R/'data/processed/count_summary_2024_2025.csv').set_index('count')
assert observed.equals(existing.pitches.astype('int64'))
assert np.allclose(r.loc['0-0',['index','CI95_low','CI95_high']].astype(float),100)
assert ((r.CI95_low<=r['index'])&(r['index']<=r.CI95_high)).all()
assert ((r.simultaneous95_low<=r.CI95_low)&(r.simultaneous95_high>=r.CI95_high)).all()
for record in a['inputs']:
    f=R/record['path']
    assert hashlib.sha256(f.read_bytes()).hexdigest()==record['sha256'],str(f)
sens=[]
for mode in ['include_IBB_as_BB','missing_zero','missing_HR']:
    z=reached[~reached.events.eq('catcher_interf')].copy()
    missing=z.events.isna()|z.events.eq('truncated_pa')
    if mode=='include_IBB_as_BB':z=z[~missing]
    else:
        z=z[~z.events.eq('intent_walk')].copy()
        missing=z.events.isna()|z.events.eq('truncated_pa')
        z.loc[missing,'v']=0 if mode=='missing_zero' else z.loc[missing,'game_year'].map(lambda y:a['weights'][str(y)]['HR'])
    index=np.zeros(12)
    for yr in (2024,2025):
        m=z[z.game_year.eq(yr)].groupby('count').v.mean().reindex(r.index)
        index+=100*a['season_mix'][str(yr)]*m.to_numpy()/m.loc['0-0']
    sens.extend({'sensitivity':mode,'count':c,'index':x} for c,x in zip(r.index,index))
pd.DataFrame(sens).to_csv(P/'advantage_exclusion_sensitivity.csv',index=False,encoding='utf-8-sig')
audit=reached.assign(excluded=excluded).groupby('count').agg(all_observed_PA=('v','size'),excluded_PA=('excluded','sum')).reset_index()
audit.to_csv(P/'advantage_count_exclusions.csv',index=False,encoding='utf-8-sig')
summary={'passed':['independent PA aggregation matches index to 1e-9','event percentages total 100','all actual pitch counts match existing processed files','baseline anchored at 100','CI containment','all input SHA256 unchanged since analysis manifest'],
'max_exclusion_sensitivity_shift':float(np.max(np.abs(pd.DataFrame(sens).apply(lambda row:row['index']-r.loc[row['count'],'index'],axis=1))))}
(P/'advantage_validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
