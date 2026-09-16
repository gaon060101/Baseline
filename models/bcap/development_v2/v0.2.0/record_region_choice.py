"""Record the user's five overlapping report regions before any V2 model fit."""
from pathlib import Path
import json,hashlib,datetime,shutil
ROOT=Path(__file__).resolve().parents[4];AN=ROOT/'columns/001-ball-count/analysis'
BUNDLE=AN/'bcap_v2_development_20260912__r01';REV=BUNDLE/'design_revisions';REV.mkdir(exist_ok=False)
rows=[]
for model,version in [('pitch','0.2.0'),('swing','0.2.0'),('pitch_sb','0.1.0')]:
 p=ROOT/f'models/bcap/{model}/v{version}/specification.yaml';backup=REV/f'{model}_initial_specification.yaml';shutil.copyfile(p,backup)
 c=json.loads(p.read_text(encoding='utf-8-sig'));before=hashlib.sha256(p.read_bytes()).hexdigest()
 c['comparison_family']=219
 c['family_scope']='PITCH13 + S/B13 + SWING193 =219 primary delta groups; each overall1/count12, SWING also count-region60/count-region-FB-NFB120. Five overlapping report regions. Bonferroni is valid for dependent contrasts if individual intervals were valid; actual coverage unverified.'
 c['uncertainty']='Reused fixed-score game cluster sandwich t(G-1), individual nominal95% plus Bonferroni219 across all displayed primary delta groups; actual coverage and full-learning uncertainty unverified.'
 c['region']='User final choice: five overlapping report sets CENTER,HIGH,LOW,INSIDE,OUTSIDE. CENTER=geometric S. HIGH z>top; LOW z<bot; INSIDE normalized_x<-17/24; OUTSIDE normalized_x>17/24. normalized_x=plate_x for R and -plate_x for L. Corners enter both horizontal and vertical reports, never duplicated in model/overall counts. Report sums may exceed100%.'
 c['region_model_inputs']='Minimum change: keep original legacy INNER/BOUNDARY/OUT swing_cell nuisance feature with coarse FB/NFB, and existing physical bins. Five report sets are postfit subsets only; no duplicate training rows or new fine geometry predictors.'
 p.write_text(json.dumps(c,ensure_ascii=False,indent=2),encoding='utf-8')
 rows.append(dict(model=model,path=p.relative_to(ROOT).as_posix(),before_sha256=before,before_snapshot=backup.relative_to(ROOT).as_posix(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(REV/'final_choice_before_fitting.json').write_text(json.dumps(dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source='User changed initial region request, finally requested high/low/left/right/center; overlap should belong to both regions.',changes=rows,no_model_fit_started=True,preparation_impact='None: shared pickle only adds previous coarse group and S/B; its earlier definition hash resolves to these initial specification snapshots.',counting='Fit and pooled/count summaries count each physical row once; region subsets overlap explicitly.',metadata_reference='Savant CSV documentation https://baseballsavant.mlb.com/csv-docs checked field conventions only; no new pitch data or external-year dataset accessed.'),ensure_ascii=False,indent=2),encoding='utf-8')
print('Five overlapping report regions and family219 recorded before fitting')
