"""Read-only result/seal/input preservation audit; writes one new audit JSON."""
from pathlib import Path
import argparse,json,hashlib,datetime,re
ROOT=Path(__file__).resolve().parents[2];AN=ROOT/'columns/001-ball-count/analysis'
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def check(args):
    out=Path(args.output);assert not out.exists()
    errors=[];files=[];runs=[]
    evidence=read(AN/'handoff_bcap_review_evidence.json')
    snapshots={'columns/001-ball-count/analysis/handoff_bcap_review.md':'handoff_bcap_review.md','columns/001-ball-count/sources.md':'sources.md','models/registry.md':'registry.md'}
    for item in evidence['files']:
        original=ROOT/item['path'];p=original
        if item['path'] in snapshots:p=AN/'bcap_original_handoff_20260909'/snapshots[item['path']]
        ok=p.is_file() and sha(p)==item['sha256'];files.append(dict(kind='original_handoff_evidence',path=str(p),ok=ok))
        if not ok:errors.append('Original evidence changed: '+item['path'])
    for runid in args.runs:
        r=AN/'runs'/runid;m=read(r/'manifest.json');runs.append(dict(run_id=runid,status=m['status'],model_id=m['model_id']))
        for item in m.get('inputs',[])+m.get('outputs',[]):
            p=ROOT/item['path'];ok=p.is_file() and sha(p)==item['sha256'];files.append(dict(kind='manifest_asset',path=item['path'],ok=ok))
            if not ok:errors.append('Manifest hash mismatch: '+item['path'])
    seal=read(args.seal)
    for item in seal['files']+seal.get('external_input_hashes_before_action_result_access',[]):
        p=ROOT/item['path'];ok=p.is_file() and sha(p)==item['sha256'];files.append(dict(kind='external_seal',path=item['path'],ok=ok))
        if not ok:errors.append('Seal mismatch: '+item['path'])
    prep=[AN/'bcap_preparation_20260909_r01/preparation_audit.json']
    prep += list((AN/'runs').glob('bcap_*/artifacts/preparation/preparation_audit.json'))
    done=set()
    for p in prep:
        for item in read(p)['inputs']:
            if item['path'] in done:continue
            done.add(item['path']);q=ROOT/item['path'];ok=q.is_file() and sha(q)==item['sha256'];files.append(dict(kind='raw_source_preservation',path=item['path'],ok=ok))
            if not ok:errors.append('Raw source changed: '+item['path'])
    linkdocs=[ROOT/'README.md',ROOT/'models/registry.md',ROOT/'columns/001-ball-count/column.md',ROOT/'columns/001-ball-count/sources.md',AN/'handoff_bcap_review.md']+list((ROOT/'models/bcap').rglob('*.md'))
    links=[]
    for p in linkdocs:
        for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8-sig')):
            if '://' in target or target.startswith('#'):continue
            t=target.split('#')[0].strip('<>');dest=(p.parent/t).resolve();ok=dest.exists();links.append(dict(document=str(p.relative_to(ROOT)),target=t,ok=ok))
            if not ok:errors.append('Broken link '+str(p)+' -> '+target)
    result=dict(checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS' if not errors else 'FAIL',errors=errors,runs=runs,files=files,raw_files_rehashed=len(done),links=links,scope='Hashes, preservation and local links; no statistical fitting or causal identification')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:result[k] for k in ['status','errors','raw_files_rehashed']},ensure_ascii=False))
    if errors:raise SystemExit(1)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seal',required=True);p.add_argument('--runs',nargs='+',required=True);p.add_argument('--output',required=True);check(p.parse_args())
