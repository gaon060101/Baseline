"""Register completed development results; preserve previous documentation bytes."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,sys

ROOT=Path(__file__).resolve().parents[4]
AN=ROOT/'columns/001-ball-count/analysis'
DAY='20260912'
B=AN/f'bcap_v2_development_{DAY}__r01'
CODE=Path(__file__).parent
MODELS=['pitch','pitch_sb','swing']
VERSION={'pitch':'0.2.0','pitch_sb':'0.1.0','swing':'0.2.0'}
STATUS='2024·2025 개발 결과 산출, 후속 검증 미실시'
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()

def readj(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def js(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def link(base,p,label):return f'[{label}]({Path(os.path.relpath(p,base.parent)).as_posix()})'
def top(text,section):
 first,rest=text.split('\n',1)
 return first+'\n\n'+section.strip()+'\n\n'+rest.lstrip('\n')

assert not (B/'document_update.json').exists(),'Documentation registration already completed.'
man={};runs={};checks={}
for m in MODELS:
 runs[m]=AN/'runs'/f'bcap_{m}__mlb_2024_2025__{DAY}__r01'
 man[m]=readj(runs[m]/'manifest.json');checks[m]=readj(runs[m]/'artifacts/basic_checks.json')
 assert man[m]['status']=='COMPLETE' and man[m]['model_status']=='EXPERIMENTAL'
 assert checks[m]['status']=='PASS' and man[m]['metrics']['all_fit_converged']

updates=[]
def write(path,text):
 path=Path(path);before=meta(path) if path.exists() else None
 if before:
  backup=B/'document_backups'/path.relative_to(ROOT)
  assert not backup.exists();backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup)
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
 updates.append({'before':before,'after':meta(path),'backup':backup.relative_to(ROOT).as_posix() if before else None})

descriptions={
 'pitch':'같은 투구 전 선수·상황 분포의 FB/NFB 보정 최종 PA 공격가치. 투수에게 낮은 값이 점추정상 유리하다. 현재 실제 위치·S/B·Swing·구속·움직임은 입력하지 않는다.',
 'pitch_sb':'실제 존 안 S/존 밖 B의 보정 최종 PA 공격가치. 공 중심이 |plate_x|≤17/24피트, sz_bot≤plate_z≤sz_top이면 S다. 현재 좌표·존·스윙·구속·움직임은 입력하지 않으며 현재 FB/NFB를 보정한다. 판정 또는 투수 의도 비교가 아니다.',
 'swing':'같은 선수·상황·사후 측정 공 특성에서 번트 포함 공격 시도 Swing/판정상 Take의 보정 최종 PA 공격가치. 실시간 지각 자료나 실행 가능한 정책을 학습한 것은 아니다.'}
findings={
 'pitch':'점추정은 FB 6카운트, NFB 6카운트. 219개 차이의 Bonferroni 명목 구간이 0을 제외한 카운트는 3-0뿐이며 NFB 쪽 허용 공격가치가 낮다.',
 'pitch_sb':'점추정은 S 10카운트, B 2카운트. B 쪽 허용 공격가치가 낮은 0-2와 1-2의 S−B는 각각 +0.02783 W, +0.02137 W다. 0-1을 제외한 11카운트에서 보정 명목 구간이 0을 제외한다. 목표 위치 변경의 인과 효과로 해석하지 않는다.',
 'swing':'가운데(존 안)는 12카운트 모두 Swing 쪽 점추정, 11개에서 보정 명목 구간이 0을 제외한다. 바깥 네 구역의 지지 기준 통과 셀은 모두 Take 쪽 점추정이다. 3-0의 존 밖 네 구역은 비교 자료 부족이다. FB/NFB 양쪽이 지원되는 50/60개 카운트×구역에서는 방향 반전이 없다. 구종 효과 또는 동등성 검정은 아니다.'}

for m in MODELS:
 folder=ROOT/f'models/bcap/{m}/v{VERSION[m]}'
 card=folder/'model_card.md';val=folder/'validation.md';mm=man[m]['metrics']
 tuning='새 S/B의 훈련 자료 안에서 기존 100/1000 후보만 비교했다.' if m=='pitch_sb' else '기존 개발 α를 p=100, 결과=1000으로 고정했다.'
 region='\n\n보고 구역은 상·하·좌(몸쪽)·우(바깥쪽)·가운데(존 안 전체)의 5개 중첩 집합이다. 모서리는 2개 구역에 포함하며 학습·전체·카운트 집계는 공당 1행이다. 좌타자는 좌우를 정규화한다. 기존 INNER/BOUNDARY/OUT 보정 범주와 물리적 입력은 유지했고, 5구역은 보고 부분집단에만 사용한다.' if m=='swing' else ''
 write(card,f'''# {man[m]['model_id']}

상태: **EXPERIMENTAL — {STATUS}**. 갱신 UTC {NOW}.

{descriptions[m]} 결과는 기존 OBS의 시즌별 가중 최종 PA 공격가치 W이며 상태 가치·전이 보상을 더하지 않는다. 양 행동은 동일한 실제 공통 지지 행에 평균화한다. 단위는 W/선택된 현재 의사결정 행이다. 행별 차이를 PA 전체 정책 개선으로 합산하지 않는다.

현재·직전 구종 범주는 FB(FF/SI/FC)와 닫힌 NFB 목록만 사용한다. 세부 원본 코드는 매핑·보존용이며 미분류를 NFB로 채우지 않는다. 투수·타자 축소 효과를 결과/행동 nuisance 양쪽에 포함한다. 경기 단위 3fold OOF AIPW 1회와 훈련 경기 안 전처리·사전·Platt 보정을 사용한다. {tuning} 정책은 학습하지 않았다.{region}

개발 적격 {mm['n']:,}행, 공통 지지 {mm['support']:,}행({mm['coverage']:.2%}), {mm['games']:,}경기. {findings[m]}

수치 수렴·기본 오류 확인을 통과했으며 외부 평가·bootstrap·전체 재학습 불확실성·별도 독립 검수는 미실시다. 완료 PA/IBB/결측/지지 제외와 미측정 의도·품질·컨디션·지각·경기 간 선수 의존성이 남는다. 구간은 고정 점수 경기 의존성에 대한 명목 근사이며 실제 95% 포함률은 미검증이다. 행동 추천으로 승격하지 않는다.

{link(card,folder/'specification.yaml','결과 전 명세')} · {link(card,val,'기본 확인·검증 범위')} · {link(card,runs[m]/'manifest.json','완료 실행')} · {link(card,B/'report.html','통합 개발 보고서')} · {link(card,B/'reproduction.md','재현 명령')}

명세의 status_at_definition=DRAFT는 정의 당시 기록이다. 결과 전 고정한 명세를 수정하지 않았으며 현재 상태는 이 카드·검증 문서·완료 manifest에 기록한다. PITCH/SWING v0.2.0은 기존 v0.1.0의 입력 변경 후속 버전이고, 새 S/B v0.1.0은 별도 비교 모듈의 최초 버전이다. 기존 모델·실행의 검증 상태는 V2에 전용하지 않는다.
''')
 write(val,f'''# {man[m]['model_id']} 기본 확인과 검증 상태

**EXPERIMENTAL — {STATUS}**. UTC {NOW}.

제작 과정의 기본 확인: PASS. 적격 {mm['n']:,}행, 지지 {mm['support']:,}행, OOF 결과 MSE {mm['MSE']:.9f}, 행동 Brier {mm['Brier']:.9f}. 적합·보정 로그 {mm['fit_logs']}건 모두 수렴했다. 이 수치는 외부 예측 성능이 아니다.

{link(val,runs[m]/'artifacts/basic_checks.json','실제 확인 항목')} · {link(val,runs[m]/'artifacts/fit_diagnostics.csv','수렴 기록')} · {link(val,B/'preparation/preparation.json','공통 입력 기본 확인')} · {link(val,runs[m]/'manifest.json','코드·설정·입출력·환경·시각 manifest')}

확인 범위는 개발 시즌, 투구 키·유효 카운트·행동·최종 결과·시즌 W 연결, 닫힌 매핑/금지 입력, 경기 fold 분리, 계산 유한값과 수렴, 양 행동 같은 분모·부호·표 합계다. 기존 예외 6건 중 개발 2행은 표시 후 유지했으며 원인 감사·임의 수정은 하지 않았다. 각 항목의 구체적인 검사와 한계는 연결한 JSON/코드가 기준이다.

219개 차이에 대한 Bonferroni 보정 명목 구간을 결과 전에 정했다. 경기별 고정 점수 변동만 반영하며 nuisance/정책 재학습·경기 간 선수 의존성과 실제 구간 포함률은 미검증이다. 이 모듈의 출력 {mm['displayed_delta_groups']}개를 포함한 전체 가족이다. 차이 불명확과 비교 자료 부족을 나눴으며 인과 권고 등급은 부여하지 않았다.

보존: 각 평가 fold의 nuisance.pkl(양 행동 결과 계수, 사전·중심화, 행동 계수, Platt 보정 자료/행 ID), fold_membership.csv, fold_records.json, 행별 scores.pkl, 적합 로그. S/B는 훈련 내부 튜닝 Ridge 객체도 보존한다. 최종 전체 개발 재적합 모델과 정책은 만들지 않았다. 저장 객체는 해당 engine 모듈을 import할 수 있는 환경에서 복원한다.

미실시: 2023/2026 적용·외부 평가, 반복 재학습/여러 seed/bootstrap, 별도 독립 검산기·전면 방법론 검수, 기존 원본 전체 재해시. V1의 외부/독립 검수 기록을 이 버전의 통과 증거로 쓰지 않는다.
''')

p=ROOT/'README.md';text=p.read_text(encoding='utf-8-sig')
text=text.replace('MLB OBS·Ridge v0.2 외부 검증 완료 · BCAP 실제 개발·외부 진단 완료·추천 보류(2026 SWING 보류) · KBO 미착수','BCAP V2 2024·2025 개발 결과 산출·후속 검증 미실시(EXPERIMENTAL) · 기존 OBS/Ridge·BCAP V1 기록 보존 · KBO 미착수',1)
text=text.replace('│     ├─ pitch/v0.1.0/ / swing/v0.1.0/  # 카드·불변 명세·검증','│     ├─ pitch/v0.1.0/ / swing/v0.1.0/  # 기존 카드·불변 명세·검증\n│     ├─ pitch/v0.2.0/ / swing/v0.2.0/ / pitch_sb/v0.1.0/  # V2 개발\n│     ├─ development_v2/v0.2.0/  # V2 준비·실행·보고·문서 연결')
text=text.replace('│     │  ├─ bcap_report_20260909_r01/  # 16종 CSV·보고 manifest','│     │  ├─ bcap_report_20260909_r01/  # 16종 CSV·보고 manifest\n│     │  ├─ bcap_v2_development_20260912__r01/  # V2 통합 보고·CSV·변경 기록')
text=text.replace('## 다음 작업\n','## 다음 작업\n\n2026-09-12: '+link(p,B/'report.html','BCAP V2 통합 개발 보고서')+'를 완료했다. '+STATUS+'이며 세 모듈 모두 EXPERIMENTAL이다. 타자 상·하·좌·우·가운데 5구역의 모서리 중복은 보고 표에만 반영했다. 외부 검증·반복 재학습·별도 독립 검수는 후속 요청 범위다. 아래 2026-09-09 기록은 V1 이력이다.\n',1)
write(p,text)

p=ROOT/'columns/001-ball-count/column.md';text=p.read_text(encoding='utf-8-sig')
text=text.replace('- 상태: MLB OBS·Ridge v0.2 외부 검증 완료 · BCAP 실제 개발·외부 진단 완료·추천 보류(2026 SWING 보류) · KBO 미착수','- 상태: BCAP V2 '+STATUS+'(EXPERIMENTAL) · 기존 OBS/Ridge·V1 기록 보존 · KBO 미착수',1)
section='''## 최신 개발 — BCAP V2, 2026-09-12

'''+link(p,B/'report.html','통합 개발 보고서')+' · '+link(p,B/'reproduction.md','재현 명령')+' · '+link(p,B/'basic_summary.json','기본 확인')+' · '+link(p,AN/'handoff_bcap_review.md','갱신 인계')+'''

기존 2024·2025만 재사용했다. PITCH/SWING-v0.2.0, 새 PITCH-SB-v0.1.0은 모두 EXPERIMENTAL이며 개발 계산을 완료했다. 실제 존 밖 B의 허용 공격가치가 더 낮은 점추정은 0-2·1-2, 타자 가운데(존 안 전체)는 12카운트 모두 Swing 쪽 점추정이다. 밖 네 구역의 기준 통과 셀은 Take 쪽이며 3-0의 밖 구역은 자료 부족이다. 수치·단위·구간·분모와 FB/NFB별 차이는 보고서를 따른다.

최종 사용자 구역은 상·하·좌(몸쪽)·우(바깥쪽)·가운데 5개다. 모서리는 두 구역에 포함하지만 학습·전체 집계는 공당 한 행이다. 3fold OOF AIPW·훈련 안 사전/보정과 기본 오류 확인을 수행했고 모든 적합이 수렴했다. 학습 정책·외부 평가·반복 재학습·독립 검수·KBO·업로드는 이번에 실행하지 않았다. 아래 외부 검증/독립 검산 결과는 기존 버전의 이력이다.

'''
text=text.replace('## 최신 모델 검증 — 2026-09-09',section+'## 기존 모델 검증 — 2026-09-09',1);write(p,text)

p=ROOT/'models/registry.md';rows=[]
for m in MODELS:
 folder=ROOT/f'models/bcap/{m}/v{VERSION[m]}'
 rows.append('| '+man[m]['model_id']+' | EXPERIMENTAL | '+link(p,folder/'model_card.md','카드')+' · '+link(p,folder/'specification.yaml','명세')+' · '+link(p,folder/'validation.md','기본 확인')+' | '+link(p,runs[m]/'manifest.json','2024·2025 개발 완료')+' |')
section='## BCAP V2 — 2026-09-12\n\n**'+STATUS+'**. '+link(p,B/'report.html','통합 보고서')+'. 세부 구종 입력은 FB/NFB로 바꿨고 실제 S/B 비교를 추가했다. 최종 타자 5구역의 모서리는 보고 집합에서 중복 포함한다. 외부 검증·반복 재학습·별도 독립 검수는 미실시이며 기존 버전의 통과 기록을 전용하지 않는다. 명세의 DRAFT는 정의 시점 기록이며 카드·manifest가 현재 상태다.\n\n| 모델 | 현재 상태 | 정의·확인 | 실행 |\n| --- | --- | --- | --- |\n'+'\n'.join(rows)+'\n\n아래는 기존 모델 등록 이력이다.'
write(p,top(p.read_text(encoding='utf-8-sig'),section))

p=ROOT/'models/bcap/README.md'
section='## 최신 개발 V2 — 2026-09-12\n\n**'+STATUS+' — EXPERIMENTAL**. '+link(p,B/'report.html','통합 결과 보고서')+' · '+link(p,B/'reproduction.md','실행 명령')+' · '+link(p,B/'basic_summary.json','기본 확인')+'.\n\n'+ ' · '.join(link(p,ROOT/f'models/bcap/{m}/v{VERSION[m]}/model_card.md',man[m]['model_id']) for m in MODELS)+'. 실제 사용한 fold 적합 객체와 분할·행별 점수를 새 실행에 보존했다. 2024·2025만 계산했고 외부/재학습/독립 검수는 수행하지 않았다. 타자 5구역은 상·하·좌(몸쪽)·우(바깥쪽)·가운데(존 안 전체), 모서리는 두 구역에 포함된다.\n\n## 기존 V1 구현·검증 이력'
write(p,top(p.read_text(encoding='utf-8-sig'),section))

p=ROOT/'columns/001-ball-count/sources.md'
section='## BCAP V2 개발 자료 재사용 — 2026-09-12\n\n'+link(p,ROOT/'columns/001-ball-count/data/processed/bcap_dev_v010_20260909_r01.pkl','기존 2024·2025 정제본')+'의 1,424,427행·4,859경기를 재사용했다. '+link(p,ROOT/'columns/001-ball-count/data/processed/bcap_dev_v2_20260912__r01.pkl','새 V2 정제본')+'에 직전 FB/NFB·실제 S/B·기존 카운트 예외 표시만 추가했다. 원본 재수집·기존 정제본 덮어쓰기와 2023/2026 데이터 적용은 없었다. '+link(p,B/'preparation/preparation.json','입출력 해시·기본 확인')+' · '+link(p,B/'report.html','개발 보고서')+'.\n\nS/B와 타자 5개 보고 구역은 2024·2025의 plate_x/z 및 sz_bot/top을 이용한 공 중심 기하 기준이다. 좌우는 타자 방향을 반영한 몸쪽/바깥쪽, 모서리는 두 구역 포함이다. [Savant 공식 CSV 필드 설명](https://baseballsavant.mlb.com/csv-docs)의 좌표 설명만 확인했고 신규 투구 데이터를 수집하지 않았다. 기존 출처·이용 조건 이력은 아래에 보존한다. 이번 버전의 상태는 '+STATUS+'다.'
write(p,top(p.read_text(encoding='utf-8-sig'),section))

p=AN/'handoff_bcap_review.md'
section='''## 최신 인계 추가 — BCAP V2 개발 완료, 2026-09-12

**'''+STATUS+''' — EXPERIMENTAL**. 사용자 범위 변경에 따라 기존 2024·2025만으로 최소 변경 개발을 수행했다. 2023/2026 데이터 적용·외부 평가·bootstrap/반복 재학습·별도 독립 검수는 이번에 미실시다. 아래 V1 외부/독립 검산 이력을 V2 검증으로 전용하지 않는다.

'''+link(p,B/'request_original.txt','이번 제작 요청')+' · '+link(p,B/'report.html','하나의 통합 보고서')+' · '+link(p,B/'design_before_results.json','최초 설계 기록')+' · '+link(p,B/'design_revisions/final_choice_before_fitting.json','적합 전 최종 5구역 변경과 SHA256')+' · '+link(p,B/'basic_summary.json','실제 기본 확인')+' · '+link(p,B/'reproduction.md','재현 명령')+' · '+link(p,B/'document_update.json','문서 전후 해시·보존 경로')+'''

최종 사용자 선택은 상·하·좌(몸쪽)·우(바깥쪽)·가운데(존 안 전체)다. 모서리는 두 구역 보고에 들어가며 학습·전체·카운트에서는 한 행이다. 이 변경은 첫 적합 전에 기록했고 보정 가족을 219개로 고정했다. 기존 INNER/BOUNDARY/OUT nuisance 입력과 물리적 입력은 유지했으며 현재/직전 구종 범주만 FB/NFB로 단순화했다. S/B는 실제 기하 위치로 별도 정의했다.

'''+ '\n'.join('- '+man[m]['model_id']+': COMPLETE / EXPERIMENTAL, 적격 '+f"{man[m]['metrics']['n']:,}"+'행, 공통 지지 '+f"{man[m]['metrics']['support']:,}"+'행. '+link(p,runs[m]/'manifest.json','manifest')+' · '+link(p,ROOT/f'models/bcap/{m}/v{VERSION[m]}/validation.md','기본 확인 범위') for m in MODELS)+'''

주요 결과: S/B에서 0-2·1-2는 B 쪽 허용 공격가치가 더 낮은 점추정이며 보정 명목 구간도 0을 제외한다. FB/NFB에서는 3-0만 보정 명목 구간이 0을 제외하며 NFB 방향이다. 타자 존 안은 12카운트 모두 Swing 쪽, 존 밖은 지원된 셀에서 Take 쪽 점추정이다. 3-0의 밖 네 구역은 자료 부족이다. 미측정 교란·사후 선택·구간의 실제 포함률이 미검증이므로 행동 지시의 인과 효과로 해석하지 않는다.

보존한 실제 모델은 세 outer fold의 nuisance 객체(사전·계수·중심화·Platt 자료), S/B 튜닝 객체, fold 행/경기 연결, scores.pkl이다. 최종 전체 재적합 모델·학습 정책은 없으며 정책 선택/평가 결과를 주장하지 않는다. 공통 준비와 세 실행의 기본 오류 확인은 PASS, 모든 적합은 수렴했다. 기존 예외 6건 중 개발 2행을 표시한 채 유지했다.

후속 검수자가 먼저 볼 부분은 보고 표의 단위·분모·5구역 중첩, S/B 실제 위치와 의도의 구분, 훈련/평가 경기 및 사전·calibration 분리, 저장 nuisance와 행별 AIPW 연결, 기본 확인의 실제 범위다. 외부 재현·재학습 불확실성과 독립 검산은 새 사용자 요청을 받아야 할 미실시 항목이다. 원 인계 증거/검증 JSON, v0.1 정의·완료 실행·봉인은 이번에 수정하지 않았다. 이번 MD 변경 전 사본은 document_backups에 보존했다. 과거 자산 전체를 다시 해시한 보존 감사라고 주장하지 않는다.

## 이하 V1 인계 이력 — 2026-09-09 기준
'''
text=p.read_text(encoding='utf-8-sig').replace('## 1. 현재 상태','## 1. V1 당시 상태',1)
write(p,top(text,section))

js(B/'document_update.json',{'at_utc':NOW,'scope':'V2 development documentation registration; not independent review','status':STATUS,'command':f'{sys.executable} -B {Path(__file__).as_posix()}','code':meta(Path(__file__)),'changes':updates,'old_evidence_and_models':'No old evidence JSON/specifications/runs/seals edited; no whole legacy audit run','outputs_scope':'Only new cards/validation and six shared Markdown entry documents updated'})
print(json.dumps({'status':'COMPLETE','documents_updated':len(updates),'record':str(B/'document_update.json')},ensure_ascii=True))
