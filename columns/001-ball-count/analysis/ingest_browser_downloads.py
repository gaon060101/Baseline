import csv,json,hashlib,shutil
from pathlib import Path
root=Path('columns/001-ball-count')
raw=root/'data/raw/mlb/2025'
items=[]
for p in Path('C:/Users/백창현/Downloads').glob('savant_data*.csv'):
    with p.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if not rows or not rows[0].get('game_date','').startswith('2025'):continue
    if len(rows)>=25000:continue
    dates=sorted({r['game_date'] for r in rows})
    target=raw/f'statcast_{dates[0]}_{dates[-1]}.csv'
    if not target.exists():shutil.copyfile(p,target)
    items.append({'file':target.name,'rows':len(rows),'bytes':target.stat().st_size})
(root/'analysis/download_2025_status.json').write_text(json.dumps({'status':'partial','files':items},indent=2),encoding='utf-8')
print(json.dumps(items))
