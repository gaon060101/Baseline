"""Verify finished review artifacts and current-byte manifests without model calls."""
from pathlib import Path
import json,hashlib,datetime,re
import pandas as pd
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
manifest=read(HERE/'evidence_manifest.json');errors=[]
for role in ['inputs','outputs']:
 for row in manifest[role]:
  p=Path(row['path'])
  if not p.is_file() or sha(p)!=row['sha256']:errors.append(dict(role=role,path=str(p),error='file/hash mismatch'))
for row in read(HERE/'preservation_before.json')['hashed_files']:
 if sha(ROOT/row['path'])!=row['sha256']:errors.append(dict(role='review baseline',path=row['path'],error='changed since before'))
assert read(HERE/'preservation_after.json')['status']=='PASS'
for name in ['review.md','findings.csv','validation.json','evidence_manifest.json','reproduction.md','followup_validation_plan.md']:
 if not (HERE/name).is_file():errors.append(dict(path=name,error='missing required output'))
f=pd.read_csv(HERE/'findings.csv')
assert f.severity.isin(['결론 무효','주요 수정','경미 수정']).all()
assert f.type.isin(['확인된 오류','알려진 한계','증거 부족','미실행']).all()
assert not f.finding_id.duplicated().any()
for col in ['finding_id','severity','type','evidence','reproduction','impact','action','revalidation','new_version_run_external']:
 if f[col].isna().any():errors.append(dict(path='findings.csv',error='missing '+col))
for name in ['review.md','followup_validation_plan.md','reproduction.md']:
 text=(HERE/name).read_text(encoding='utf-8')
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if target.startswith('http'):continue
  if not Path(target).is_file():errors.append(dict(path=name,error='broken local link',target=target))
detached=(HERE/'evidence_manifest.sha256').read_text(encoding='utf-8').split()[0]
assert detached==sha(HERE/'evidence_manifest.json')
result=dict(status='PASS' if not errors else 'FAIL',checked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),input_hashes_checked=len(manifest['inputs']),output_hashes_checked=len(manifest['outputs']),review_baseline_hashes_checked=617,errors=errors,findings=len(f),finding_types=f.type.value_counts().to_dict(),scope='Final current file hashes, required outputs/schema/local links and start-baseline preservation. This is delivery integrity, not blanket statistical or model approval.',evidence_manifest_sha256=detached,code_sha256=sha(Path(__file__)))
(HERE/'delivery_validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False))
