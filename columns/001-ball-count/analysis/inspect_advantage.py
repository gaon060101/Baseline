from pathlib import Path
import pandas as pd
R=Path(__file__).resolve().parents[1]
cols=['game_pk','at_bat_number','pitch_number','game_year','game_date','balls','strikes','events','batter','pitcher','stand','p_throws','home_team','on_1b','on_2b','on_3b','outs_when_up','inning','bat_score_diff','description','pitch_name','type']
parts=[]
for year in (2024,2025):
    for f in sorted((R/f'data/raw/mlb/{year}').glob('statcast_*.csv')):
        parts.append(pd.read_csv(f,usecols=cols,low_memory=False))
d=pd.concat(parts,ignore_index=True).sort_values(['game_pk','at_bat_number','pitch_number'])
print('rows',len(d),'duplicates',d.duplicated(['game_pk','at_bat_number','pitch_number']).sum(),flush=True)
print(d.events.value_counts(dropna=False).to_string(),flush=True)
d.to_pickle(R/'analysis/advantage_input_cache.pkl')
print('cached',flush=True)
