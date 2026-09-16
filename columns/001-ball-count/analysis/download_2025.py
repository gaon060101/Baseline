import csv, io, json, time, hashlib, urllib.request, urllib.parse, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import date, timedelta, datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw/mlb/2025'
RAW.mkdir(parents=True, exist_ok=True)
LOG = ROOT / 'analysis/download_2025_status.json'
manifest = []
lock = threading.Lock()

def fetch(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent':'Baseline baseball research (CSV download)'})
            with urllib.request.urlopen(request, timeout=180) as response:
                return response.read()
        except Exception:
            if attempt == 2: raise
            time.sleep(10 * (attempt + 1))

schedule_path = RAW / 'schedule_2025.json'
schedule_url = 'https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2025-01-01&endDate=2025-12-31&gameTypes=R'
if not schedule_path.exists(): schedule_path.write_bytes(fetch(schedule_url))
schedule = json.loads(schedule_path.read_text('utf-8'))
games = [g for d in schedule['dates'] for g in d['games'] if g['gameType'] == 'R' and g['status']['abstractGameState'] == 'Final']
expected = {str(g['gamePk']) for g in games}
days = sorted({g['officialDate'] for g in games})
start, last = date.fromisoformat(days[0]), date.fromisoformat(days[-1])
print(f'Schedule: {len(expected)} completed games; {start} to {last}', flush=True)
for p in sorted(RAW.glob('statcast_*.csv')):
    with p.open(encoding='utf-8-sig', newline='') as f: prior=list(csv.DictReader(f))
    if not prior: continue
    dates=sorted({r['game_date'] for r in prior})
    manifest.append(dict(file=p.name,start=dates[0],end=dates[-1],rows=len(prior),bytes=p.stat().st_size,
                         url='https://baseballsavant.mlb.com/statcast_search',sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
if manifest: start=date.fromisoformat(max(x['end'] for x in manifest))+timedelta(days=1)

def chunk(a, b):
    path = RAW / f'statcast_{a}_{b}.csv'
    params = dict(all='true', type='details', hfGT='R|', hfSea='2025|', player_type='pitcher',
                  game_date_gt=str(a), game_date_lt=str(b), group_by='name', min_pitches=0,
                  min_results=0, sort_col='pitches', sort_order='desc')
    url = 'https://baseballsavant.mlb.com/statcast_search/csv?' + urllib.parse.urlencode(params)
    data = path.read_bytes() if path.exists() else fetch(url)
    reader = csv.DictReader(io.StringIO(data.decode('utf-8-sig')))
    if not reader.fieldnames or 'game_pk' not in reader.fieldnames: raise RuntimeError(f'Invalid CSV {a}: {data[:100]!r}')
    rows = list(reader)
    if len(rows) >= 25000:
        if a == b: raise RuntimeError(f'Daily row cap {a}')
        mid = a + (b-a)//2
        chunk(a, mid); chunk(mid + timedelta(days=1), b)
        return
    if any(r['game_type'] != 'R' or not str(a) <= r['game_date'] <= str(b) for r in rows):
        raise RuntimeError(f'Unexpected dates/types {a}')
    if not path.exists(): path.write_bytes(data)
    with lock:
        manifest.append(dict(file=path.name, start=str(a), end=str(b), rows=len(rows), bytes=len(data), url=url,
                             sha256=hashlib.sha256(data).hexdigest()))
        LOG.write_text(json.dumps(dict(status='downloading', files=manifest), indent=2), encoding='utf-8')
    print(f'{a}..{b}: {len(rows):,} rows; files={len(manifest)}', flush=True)
    time.sleep(1)

jobs=[]
while start <= last:
    end = min(start + timedelta(days=4), last)
    jobs.append((start,end)); start = end + timedelta(days=1)
with ThreadPoolExecutor(max_workers=3) as pool:
    futures=[pool.submit(chunk,a,b) for a,b in jobs]
    for future in futures: future.result()

keys, found, pas, counts = set(), set(), set(), {}
duplicates = 0
total = 0
for item in manifest:
    with (RAW / item['file']).open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            total += 1
            key = (r['game_pk'], r['at_bat_number'], r['pitch_number'])
            if key in keys: duplicates += 1
            keys.add(key); found.add(r['game_pk']); pas.add(key[:2])
            c = r['balls']+'-'+r['strikes']; counts[c] = counts.get(c, 0)+1
result = dict(status='complete' if not expected-found and duplicates == 0 else 'needs_review',
              retrieved_at=datetime.now(timezone.utc).isoformat(), rows=total, games=len(found),
              plate_appearances=len(pas), duplicate_pitch_keys=duplicates, counts=counts,
              missing_schedule_games=sorted(expected-found), extra_games=sorted(found-expected),
              bytes=sum(x['bytes'] for x in manifest), schedule_url=schedule_url, files=manifest)
LOG.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='files'}), flush=True)
