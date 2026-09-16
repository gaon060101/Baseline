"""Review-only baseline and end-of-review preservation check; never writes outside this directory."""
from pathlib import Path
import argparse, datetime, hashlib, json, os, sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
AN=ROOT/'columns/001-ball-count/analysis'
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def files_under(p):
    return [x for x in p.rglob('*') if x.is_file() and '__pycache__' not in x.parts]
def tracked():
    found=set()
    for name in ['AGENTS.md','README.md','guides/analysis.md','guides/writing.md','models/registry.md','columns/001-ball-count/column.md','columns/001-ball-count/sources.md']:
        found.add(ROOT/name)
    found.update(files_under(ROOT/'models/bcap'))
    found.update(files_under(ROOT/'models/bcai'))
    for p in (AN/'runs').glob('bcap_*'):
        found.update(files_under(p))
        m=read(p/'manifest.json')
        for item in m.get('inputs',[]):found.add(ROOT/item['path'])
    for pattern in ['bcap_execution*','bcap_document*','handoff_bcap_review*','bcap_v010*','bcap_original_handoff*','bcap_preparation*','bcap_implementation_review*','bcap_report*','bcap_primary_report*','bcap_final_validation*']:
        for p in AN.glob(pattern):
            found.update(files_under(p) if p.is_dir() else [p])
    for p in [AN/'bcap_preparation_20260909_r01/preparation_audit.json']+list((AN/'runs').glob('bcap_*/artifacts/preparation/preparation_audit.json')):
        for item in read(p)['inputs']:found.add(ROOT/item['path'])
    return sorted((p for p in found if p.is_file() and HERE not in p.parents),key=str)
def metadata_inventory():
    rows=[]
    for base,dirs,files in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in {'.git','.codex','.agents','__pycache__'} and Path(base)/d!=HERE]
        for name in files:
            p=Path(base)/name;s=p.stat()
            rows.append({'path':rel(p),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns})
    return sorted(rows,key=lambda r:r['path'])
def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['before','after']);a=p.parse_args()
    out=HERE/('preservation_'+a.phase+'.json');assert not out.exists()
    started=now()
    if a.phase=='before':
        rows=[]
        for f in tracked():
            s=f.stat();rows.append({'path':rel(f),'sha256':sha(f),'bytes':s.st_size,'mtime_ns':s.st_mtime_ns})
        result={'phase':'before','started_at_utc':started,'finished_at_utc':now(),'hashed_files':rows,'existing_tree_metadata':metadata_inventory(),'scope':'Hashes for BCAP/linked model/input/record files; metadata inventory of other existing workspace files. No claim of pre-production preservation from current hashes.'}
    else:
        previous=read(HERE/'preservation_before.json');errors=[];checked=[]
        for r in previous['hashed_files']:
            f=ROOT/r['path'];actual=sha(f) if f.is_file() else None;ok=actual==r['sha256']
            checked.append({'path':r['path'],'sha256_after':actual,'matches_start':ok})
            if not ok:errors.append(r['path'])
        old={x['path']:x for x in previous['existing_tree_metadata']};current={x['path']:x for x in metadata_inventory()}
        changes=[{'path':n,'before':old.get(n),'after':current.get(n)} for n in sorted(set(old)|set(current)) if old.get(n)!=current.get(n)]
        result={'phase':'after','started_at_utc':started,'finished_at_utc':now(),'status':'PASS' if not errors and not changes else 'FAIL','hash_mismatches':errors,'outside_review_metadata_changes':changes,'checked_hashes':checked,'scope':'New review preservation only; initial versus final current filesystem. Bytecode and app/git internal metadata excluded.'}
    result.update(command=[sys.executable]+sys.argv,code_sha256=sha(Path(__file__).resolve()))
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'phase':a.phase,'status':result.get('status','BASELINE_CAPTURED'),'files':len(result.get('hashed_files',result.get('checked_hashes',[])))},ensure_ascii=False))
if __name__=='__main__':main()
