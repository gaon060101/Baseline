"""Assemble this review's already-completed independent evidence; never runs models."""
from pathlib import Path
import json,hashlib,datetime,sys,platform,re
import pandas as pd
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
def link(name,path):return f'[{name}]({Path(path).as_posix()})'
def local(name,path):return link(name,HERE/path)
def sha(p):
 with Path(p).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
components={
 'source_lineage':'lineage/final_validation.json',
 'folds_saved_fit':'folds_prediction/validation.json',
 'policy_training_intervals':'folds_prediction/policy_interval_validation.json',
 'saved_score_arithmetic':'numeric/validation.json',
 'bootstrap_aggregates':'methodology_bootstrap/bootstrap_validation.json',
 'report_tables':'methodology_bootstrap/report_tables_validation.json',
 'provenance':'provenance/validation.json',
 'review_preservation':'preservation_after.json'}
data={k:read(HERE/p) for k,p in components.items()}
num=data['saved_score_arithmetic'];summary=[]
for r in num['runs']:
 p=r['overall_learned'];summary.append(dict(run_id=r['run'],stage=r['stage'],eligible_rows=r['n'],supported_rows=r['support'],gain=p['gain'],nominal_adjusted_low=p['gain_low'],nominal_adjusted_high=p['gain_high'],grade_counts=str(r['grades'])))
pd.DataFrame(summary).to_csv(HERE/'main_results_reproduced.csv',index=False)
parts=[]
for path,kind in [('lineage/findings.csv','lineage'),('methodology_bootstrap/methodology_findings.csv','methodology'),('folds_prediction/findings.csv','folds')]:
 d=pd.read_csv(HERE/path).fillna('')
 for x in d.to_dict('records'):
  parts.append(dict(finding_id=x.get('finding_id',x.get('id')),severity=x['severity'],type=x['type'],title=x.get('title',x.get('finding')),evidence=x['evidence'],exact_rows=x.get('exact_rows','See evidence file/line and linked child report'),reproduction=x['reproduction'],impact=x['impact'],action=x['action'],revalidation=x.get('revalidation',x.get('judgment',x['action'])),new_version_run_external=x.get('new_version_run_external',x.get('new_version_and_run',x.get('new_version','')+'; '+x.get('external_reexposure',''))),source_report=str((HERE/path).as_posix()),scope_note='Known limits/evidence gaps do not imply a confirmed numerical implementation error. Severity describes the claim that is affected.'))
parts.append(dict(finding_id='PROV-01',severity='경미 수정',type='증거 부족',title='과거 미노출·전체 자산 과거 무변경의 포괄 인증은 불가',evidence='provenance/legacy_baseline_recheck.csv; provenance/utc_timeline.csv; models/bcap/external_seal_20260909_r01.json; bcap_execution_commands_20260909.json',exact_rows='Legacy 302 matching historical baselines; 21 without a verifiable prior baseline; final local seal 06:13:44.654276 UTC',reproduction='provenance_audit.py resolves historical JSON pointers and snapshots, recomputes SHA256, then orders stored UTC events.',impact='로컬 봉인과 사후 명령 기록을 공개 사전등록·보편적 미노출 또는 모든 자산 과거보존 증거로 해석할 수 없음.',action='기존 한계 문구 유지. 21파일은 현재 해시 목록과 과거 보존 검증을 구분. 독립 shell history와 신뢰 가능한 외부 시각 증거가 없다는 점 유지.',revalidation='현재 봉인된 핵심·주 실행·기록된 스냅샷 해시는 일치. 새 증거가 생길 때 해당 과거 주장만 재검수.',new_version_run_external='해시 재확인은 모델 변경/새 외부 평가 아님. 결과영향 변경 또는 외부 재평가는 별도 새 버전/실행/재노출 기록.',source_report=(HERE/'provenance/validation.json').as_posix(),scope_note='Known coverage limitation; no unexplained sealed-core change found.'))
pd.DataFrame(parts).to_csv(HERE/'findings.csv',index=False,encoding='utf-8-sig')
checks=[
 dict(check='raw_to_processed_to_main_scores',status='PASS',scope='150 CSV, 2784153 raw rows, 4899202 model-eligible score rows; exact Y/A/keys/features comparison',maximum_absolute_error=0,denominator='All saved source rows; not a sample'),
 dict(check='description_specific_next_count_consistency',status='FAIL',scope='6 records missed by broad producer count transition audit; source truth unresolved',finding='LINEAGE-01'),
 dict(check='six_records_physical_truth',status='NOT_VERIFIABLE',scope='No evidence distinguishing void pitch, description error, or count error. No relabeling performed.'),
 dict(check='main5_and_fixed3_AIPW_OPE_diagnostics',status=num['status'],scope=num['scope'],comparisons=num['comparisons'],maximum_absolute_error=num['max_absolute_error'],maximum_relative_error=num['max_relative_error'],denominator='4899202 main eligible rows plus 2067593 fixed developer diagnostic rows; comparisons include repeated fields/groups.'),
 dict(check='existing_final_fit_predictions',status='PASS',scope='3 external fixed-prediction files, 2067593 rows; actual final6 Ridge normal equations and final2 Platt objective/gradient',maximum_prediction_absolute_error=2.220446049250313e-16,maximum_ridge_relative_normal_residual=1.508213e-9),
 dict(check='nonfinal_fit_accuracy',status='NOT_VERIFIABLE',scope='237 nonfinal/tuning Ridge and31 nonfinal calibrator objects absent. Saved loss-based selection and split provenance checked, actual fits/losses not regenerated.'),
 dict(check='nested_partition_policy',status='PASS',scope='97 main split records,336 policy states, exact evaluation policy application'),
 dict(check='policy_training_intervals',status='PASS',scope='336 states,672 interval endpoints; resolves earlier child report nonexecution',maximum_absolute_error=data['policy_training_intervals']['maximum_absolute_error']),
 dict(check='bootstrap_saved_aggregates',status='PASS',scope='16 replicate multiplicities,432 partitions,1440 fit row counts,208 stability summary rows',comparisons=data['bootstrap_aggregates']['checks'],maximum_absolute_error=data['bootstrap_aggregates']['max_absolute_error']),
 dict(check='bootstrap_original_row_AIPW_fit',status='NOT_VERIFIABLE',scope='No saved row nuisance/score/policy/fit objects for16 replicates'),
 dict(check='all_report_tables_prose_behavior_postseal',status='PASS',scope='16 CSVs,12 count prose sections,60 behavior count rows,108 paired states,8 descriptive summaries',comparisons=data['report_tables']['checks'],maximum_absolute_error=data['report_tables']['max_absolute_error']),
 dict(check='Bonferroni_family_count',status='PASS',scope='1463 main finite delta/gain intervals <=1536; excludes fixed nuisance/individual policy values/training/known/sensitivity intervals'),
 dict(check='actual_95_coverage_and_nuisance_truth',status='NOT_VERIFIABLE',scope='No evidence establishes coverage under overlapping fitting, nuisance misspecification, cross-game dependence and near-tie learning'),
 dict(check='causal_realtime_recommendations',status='NOT_VERIFIABLE',scope='Selected completed PA, hidden state/action versions and SWING hindsight perception remain unidentified; no recommendation'),
 dict(check='SWING2026_evaluation',status='NOT_RUN',scope='WITHHELD_MEASUREMENT_NONCOMPARABILITY; saved outcome_evaluations=0; no substitute model'),
 dict(check='new_model_refitting',status='NOT_RUN',scope='No new development or external fits in this review'),
 dict(check='new_external_model_evaluation',status='NOT_RUN',scope='Only saved results reviewed and existing-fit predictions recreated; no policy reoptimization on external outcomes'),
 dict(check='sealed_core_and_historical_provenance',status=data['provenance']['status'],scope='1661 resolved hash references,340 logical checks,302 legacy baselines match,21 unverified historical coverage'),
 dict(check='review_write_boundary',status=data['review_preservation']['status'],scope='617 baseline files rehashed; no outside-review metadata changes excluding app/git/bytecode internals')]
verdicts=[]
for model in ['BCAP-PITCH-v0.1.0','BCAP-SWING-v0.1.0']:
 verdicts.append(dict(model=model,stored_status='EXPERIMENTAL',overall='명시 범위 내 사용 가능 — 선택된 관찰 의사결정 행의 탐색 진단 수치·계보·보존 최종 적합 재현성',numerical_implementation='명시 범위 내 사용 가능; 주 저장 점수 산술과 보존 final 객체 재생성 범위',statistical_interpretation='증거 부족으로 판정 보류 — 인과 행동가치·명목 구간의 실제 포함률·제한 nuisance의 목표 정확성',report_and_audit='수정 후 재검수 — description별 카운트 감사 누락 및 검증 범위/구간 표현 보완',actionable_recommendation='증거 부족으로 판정 보류; UNCERTAIN/NO_SUPPORT 및 추천 공란 유지',external_scope='2023·2026-09-07 기존 결과 검수' if 'PITCH' in model else '2023 기존 결과 검수;2026 전체 WITHHELD'))
validation=dict(finalized_at_utc=NOW,status='REVIEW_COMPLETE_WITH_FINDINGS',overall_not_a_blanket_PASS=True,model_verdicts=verdicts,checks=checks,component_evidence={k:dict(path=(HERE/p).as_posix(),sha256=sha(HERE/p)) for k,p in components.items()},tolerances=read(HERE/'review_protocol.json')['tolerances_before_new_comparisons'],independence='Fresh code does not import producer run/verify/bootstrap core functions. Statistical formulas follow declared specifications; final fit objects deserialized into inert containers. Existing review PASS not adopted.',existing_files_modified=False,new_fit_or_external_evaluation=False)
write(HERE/'validation.json',validation)

rows=[]
for r in summary:
 if r['stage']!='main':continue
 model='SWING' if 'swing' in r['run_id'] else 'PITCH';period='2024·2025 개발' if '2024_2025' in r['run_id'] else '2023' if '2023' in r['run_id'] else '2026-09-07까지'
 rows.append(f"| {model} | {period} | {r['eligible_rows']:,} | {r['supported_rows']:,} | {r['gain']:+.6f} | [{r['nominal_adjusted_low']:+.6f}, {r['nominal_adjusted_high']:+.6f}] |")
table='\n'.join(rows)
report=f'''# BCAP 독립 검수 보고서 — 2026-09-09

두 모델의 **저장된 관찰 진단 수치는 독립 재현됐다. 행동 권고의 타당성은 증거 부족으로 판정 보류한다.** 원자료의 description과 다음 카운트가 맞지 않는 6행을 기존 감사가 놓친 점은 수정이 필요하다. 모델 자체의 원행 AIPW·정책가치 산술 오류는 발견하지 못했다. 이 문장은 인과성·실시간 정책·전체 PA 개선의 인증이 아니다.

검수는 새 폴더에만 기록했다. 기존 코드·명세·실행·봉인·정제본·보고서·README·column·sources를 수정하지 않았다. 제작 당시 대화 대신 현재 파일과 기록된 계보를 읽고 새 코드를 실행했다. 최종 집계 시각은 {NOW}이다. {local('검수 요청 원문','request_original.txt')}, {local('사전 허용오차·범위','review_protocol.json')}, {local('검사별 판정','validation.json')}, {local('발견 사항 전체','findings.csv')}를 함께 보관한다.

## 모델별 판정

| 모델 | 구현·저장 수치 | 통계적 해석 | 행동 권고 | 외부 범위 |
| --- | --- | --- | --- | --- |
| BCAP-PITCH-v0.1.0 | 명시 범위 내 사용 가능: 계보·주 산술·보존 final 적합 재현 | 선택된 행의 탐색 통계량으로 제한. 인과 효과·실제 95% 포함률은 판정 보류 | 판정 보류, 추천 없음 | 2023·2026-09-07 기존 결과 검수 |
| BCAP-SWING-v0.1.0 | 명시 범위 내 사용 가능: 같은 검수 범위 | 사후 공 특성·번트 포함 판정상 시도 진단. 실시간·인과 해석은 판정 보류 | 판정 보류, 추천 없음 | 2023 기존 결과 검수; 2026 WITHHELD |

두 모델의 기존 EXPERIMENTAL 상태는 유지한다. **수정 후 재검수**의 대상은 카운트 감사의 누락과 검증 범위·구간 표현이다. 중간 적합 객체가 없어 모든 nuisance 적합의 정확성을 독립 인증하지 못한 범위도 남는다. 알려진 한계와 증거 부족을 확인된 수치 오류로 합치지 않았다. 현재 RECOMMENDED/LEAN은 없고, 평가된 그룹은 UNCERTAIN/NO_SUPPORT다. SWING 2026은 등급 없는 측정 보류다. BCAP-JOINT·Nash·전체 PA 정책은 검증하지 않았다.

## 주요 발견과 제작 작업에 돌려보낼 요청

1. **LINEAGE-01 — 경미 수정·확인된 감사 오류.** {link('data.py',ROOT/'models/bcap/data.py')}:224–236의 일반 전이 규칙은 볼·스트라이크 모두 0 증가를 허용한다. 독립 description별 검사에서는 ball 5행과 swinging_strike 1행 뒤 카운트가 그대로인 예외를 찾았다. 키는 `(746664,63,6)`, `(778541,42,6)`, `(716482,85,8)`, `(718506,27,7)`, `(718708,65,5)`, `(824212,43,3)`이다. 원자료와 정제본은 일치하며, 실제 무효구인지 기록 오류인지는 확인하지 못했다. {local('예외와 원본 레코드 위치','lineage/all_strict_count_exceptions.csv')}와 {local('해당 PA 전체','lineage/all_strict_count_exceptions_full_PA.csv')}에 증거가 있다. 예외 감사를 추가하고 검증 범위를 바로잡아야 한다. 근거 없이 라벨을 바꾸면 안 된다.
2. **F-FOLD-01·MB04 — 주요 수정·증거 부족.** 보존 final 모델의 실제 예측은 검산했지만 nonfinal/tuning Ridge 237개와 calibrator 31개의 객체는 없다. 재학습 16회에도 원행 nuisance·점수·정책·적합 객체가 없다. 검증 문서는 저장 점수 산술, 로그 확인, 실제 객체 재생성을 나누어 표시해야 한다. 해당 결과 전체를 ‘원자료부터 전 적합 독립 재현’으로 부르면 안 된다. 저장 범위를 보완하는 후속 계획은 {local('후속 검증 계획','followup_validation_plan.md')}에 있다.
3. **MB01·MB03 — 주요 수정·증거 부족.** 구간 산술과 Bonferroni 가족 크기는 맞지만, 겹치는 nuisance·정책 훈련, 함수족 오지정, 경기 간 선수·시리즈 의존성, 동률 근처 선택 아래의 실제 95% 포함률은 검증되지 않았다. ‘고정 점수 경기 변동에 기반한 명목 근사 구간, 실제 포함률 미검증’으로 명시해야 한다. 주변 calibration·수렴·ESS만으로 목표 행동가치의 정확성을 인증할 수 없다.
4. **MB02·MB05·LINEAGE-02 — 주요 수정·알려진 한계.** 완료 PA·IBB·결과 결측 제외와 공통 지지는 선택된 집단을 만든다. 관찰된 선택집단의 조건부 결과 관계와 가상 한 구 개입 효과를 별도 목표로 써야 한다. SWING의 좌표·움직임·구속은 사후 측정 대리값이다. 번트 포함 공격 시도와 판정상 Take를 일반 full swing/운동학적 무동작으로 해석할 수 없다. 현재 문서는 이 제한을 대체로 인정하며, 이번 발견은 제한된 산술 자체를 무효화하지 않는다.
5. **LINEAGE-03·MB06·PROV-01 — 경미 수정 또는 증거 범위 제한.** NFB에는 FA=`Other`가 포함되므로 ‘물리적으로 모두 확정된 비속구’가 아니다. PITCH의 좌표 제외도 2026 판정 환경 변화가 이전 description·현재 count·Y에 미치는 경로를 제거하지 않는다. 로컬 봉인은 공개 사전등록이나 보편적 과거 미노출의 증명이 아니다.

예외 현재행만 저장 점수에서 생략하면 모델×시즌 전체 Δ 이동의 최대 절대값은 `1.307024e-6 W`다. 이는 추가 기술 재합산이며 라벨·지연 입력·모형·정책을 교정해 재학습한 효과나 영향 상한이 아니다. 수치를 실제 변경하려면 새 설계 버전·새 실행·외부 재노출 기록이 필요하다. 현재 검수에서는 모델을 고치지 않았다.

## 믿을 수 있는 재현 범위와 주요 수치

원본 **150 CSV·2,784,153행·714,990 PA·9,454경기**를 전수 재구성했다. 주 5개 scores의 **4,899,202행**에서 Y/A·키·시즌·선수·count·입력 계보 불일치가 없었다. 득점 65,191행을 포함해 bat_score_diff는 투구 전 점수와 일치했다. 시즌 가중치는 OBS 원 W이며 2026에는 2025 가중치를 고정했다. BCAI 상태 지수나 전이 보상을 더하지 않았다. 자세한 모델·시즌·행동·제외사유 표는 {local('원자료 계보 보고','lineage/review.md')}에 연결했다.

행별 AIPW는 저장 phi를 평균하는 방식으로 대신하지 않고 Y/A/p/μ에서 복원했다. OPE는 factual residual을 사용하는 별도 표현으로 계산했다. d는 개발 outer별 정책 또는 외부의 고정 최종 개발 정책에서 복원했다. 항상0/1·학습 후보·Bernoulli(.5)·관찰 메커니즘·보수 정책은 동일 지지 행을 사용한다. 보수 정책의 H=0 기여는 Y이고 이득0은 정의상 결과다. fallback .5와 관찰 메커니즘 유지는 다르다.

다음은 학습 후보와 관찰 메커니즘의 저장 진단 차이를 독립 재현한 값이다. 단위는 **W/선택된 현재 의사결정 행**이다. PITCH의 양수는 관찰Y−정책가치, SWING의 양수는 정책가치−관찰Y다. 행별 값을 합쳐 PA 전체 이득으로 읽을 수 없다.

| 모델 | 기간 | 적격 행 | 공통 지지 행 | 후보 gain | 명목 Bonferroni 보정 구간 |
| --- | --- | ---: | ---: | ---: | --- |
{table}

PITCH의 세 구간은 0을 포함한다. SWING의 양수 점추정과 0 위 구간도 인과적·실시간 개선 근거로 승격하지 않는다. 양 모델 8회 재학습 집계에서 PITCH 전체 gain은 −0.00137650~+0.00153482 W, SWING은 +0.02469531~+0.02603555 W였다. 각각 양수 6/8·8/8이며, 중첩 학습 절차의 안정성 진단이다. 최종 고정 정책의 완전한 95% 구간은 아니다.

주 실행5와 외부 고정 예측 진단3을 합친 산술 검산은 48,845,813개 원소/필드 비교에서 불일치0이었다. 최대 절대오차는 값 `1.42109e-14`, SE/구간 `3.88578e-16`, ESS `1.74623e-10`으로 각각 사전 허용오차 안이다. 전체 최대 상대오차는 `1.32487e-11`이다. 비교 개수는 반복 필드·집단 검사를 포함하며 독립된 통계 실험 수가 아니다. 키·정수·정책·표지의 허용 불일치는0이다. 빈 지지는 같은 키의 NaN으로 유지했고 0으로 채우지 않았다. {local('비교별 오차·분모','numeric/comparisons.csv')}, {local('불일치 파일','numeric/mismatches.csv')}, {local('재현 결과','main_results_reproduced.csv')}를 제공한다.

## 학습·정책·지지와 적합 정확성

97개 주 분할 기록과 모든 상위 outer/inner holdout 배제를 독립 재구성했다. 336개 정책 상태의 Δ·N·경기 수·행동과 평가행 적용이 일치한다. 해당 훈련용 구간672끝점도 최대 절대차2.22e-16으로 일치했다. Q는 공통 행의 평균 φ, μ는 X별 근사 결과 회귀, d는 훈련에서 선택한 Z별 정책이다. X에는 실제 선수·상황, Z에는 PITCH count 또는 SWING count×zone×구종군이 쓰인다. 가상 평균 선수 한 명으로 표준화하지 않는다.

개발 final 객체에서 외부3의 2,067,593행 예측을 재생성했다. raw score·μ0·μ1 최대차0, p 최대차2.22e-16이며 사전·known/repertoire/measurement/support도 일치했다. 실제 final Ridge6개의 중심화 정상방정식 상대잔차 최대1.50821e-9는 명세 한도1e-7을 만족했다. final Platt2개의 목적함수와 gradient도 실제 훈련행에서 확인했다. 실제 계수 검산과 저장 로그만의 확인은 {local('적합·분할 보고','folds_prediction/review.md')}에서 구분한다. 그 보고의 훈련 구간 ‘미재계산’ 항목은 {local('후속 구간 검산','folds_prediction/policy_interval_addendum.md')}으로 해소됐다.

지원 마스크·행동별 ESS·경기 수·집중도·propensity 분위·calibration·극단 가중치·known/unseen·제외사유와 민감도는 독립 복원했다. `.05≤p≤.95`, 훈련 선수 양 행동30회, SWING 유효 측정 조건을 양 행동·모든 정책에 공통 적용했다. 그룹 N500·ESS200·행동별100경기·포함률.5·최대경기비중.05는 구현상 일치하지만 통계적 충분성 정리는 아니다. 선수 절편 축소와 넓은 repertoire가 상황별 positivity나 숨은 의도를 해결하지 않는다.

trimming별 대상 집단은 달라지고, primary와 같은 행에 clip .1을 적용한 비교는 가중치만 바뀐다. 첫 count 방문은 적격 행 정렬에서 먼저 정하고 지원 마스크와 결합한다. 경기 군집은 PA 내부 반복을 포함하지만 경기 간 의존성까지 해결하지 않는다. 실제 주 보정 가족은 Δ209+정책gain1,254=1,463≤1,536이며 정책 value 개별구간·고정개발진단·훈련·known/unseen·민감도 구간 전체의 동시보장이 아니다.

SWING HBP는 개발 적격3,948 중 지원2,220,2023 적격2,112 중 지원1,259다. raw HBP7,944의 description·현재/최종events 연결은 일치하지만 최종 지지집단 대표성은 다르다. action0/1의 명확한 라벨과 선택 편향은 별도 문제다. 원 요구와 수정 설계의 25쟁점 대조는 {local('원 요구→문제→수정→판단 표','methodology_bootstrap/requirements_decisions_review.csv')}를 따른다.

## 외부 평가·봉인·시점

외부의 고정 개발 nuisance 예측과 외부 경기 교차 적합 nuisance를 쓴 고정 정책 OPE를 구분했다. 전자는 보존 final 객체에서 재생성했고, 후자는 저장 점수와 외부 훈련 분할·정책 고정을 검산했다. 공통 지지 행도 PITCH2023 635,421 대697,633, SWING2023 630,906 대682,953, PITCH2026 561,233 대615,820으로 다르다. 이를 같은 대상의 직접 성능 개선으로 비교할 수 없다. known/unseen은 개발 최종 선수 목록 기준이다.

최종 로컬 봉인은 **06:13:44.654276 UTC**이며 현재 핵심·최종 정책·모델 해시와 일치한다. 기록된 BCAP 외부 첫 열람은 PITCH2023 **06:14:39.518503**, SWING2023 **06:17:36.283411**, PITCH2026 **06:18:57.081644 UTC**로 이후다. 2023·2026은 이미 BCAI/Ridge에 쓰인 자료이며, 이번 검수도 저장 BCAP 결과를 재열람한 사후 검수다. 새 모델·정책을 외부에 평가하지 않았다. {local('전체 UTC 순서','provenance/utc_timeline.csv')}와 {local('해시 대조','provenance/hash_comparisons.csv')}가 있다.

PITCH 실패r01의 기록된 source는 보존 run_failed_source.py로 해석했다. 성공 엔진과 차이는 입력 경로 정규화와 frozen 파일 저장뿐이었다. `status_at_definition=DRAFT`와 현재 EXPERIMENTAL은 시점이 다르다. 봉인후 방향/상관 집계06:27:25와 행동표현08:34:45는 별도 기술 비교다. 문서 갱신08:49:31 뒤 최종 감사08:50:00이 생성되어 ‘감사 예정’ 문구는 당시 기록으로 설명된다. 과거 input 해시는 명시된 변경전 백업으로 확인했으며 현재 파일과 단순 비교한 초기 탐지 목록도 보존했다. 설명을 면책으로 채택한 것이 아니라 각 보존본 해시와 실제 diff를 대조한 결과다.

SWING2026은 WITHHELD·평가0·대체모델 없음이다. 2026 plate_x/z 기준면과 sz_top/bot 정의 변경은 [Savant 공식 필드 정의](https://baseballsavant.mlb.com/csv-docs)와 대조했다. 위치 교량이 없어 평가 보류가 타당하다. 이를 NO_SUPPORT나 외부 성과 실패로 바꾸지 않았다. 관련 방법론·공식 근거는 {local('방법론 검토','methodology_bootstrap/methodology_review.md')}에 있다.

## 보고서·보존·미검증 범위

16종 CSV·12카운트 본문을 원 실행에 대조했다. 행동표60행은 같은 지원 행에서 관찰A와 복원d로 행동률·%p·기대 불일치율을 계산해 맞았다. 확률 정책의 불일치는 `A(1−d)+(1−A)d`의 평균이다. 평가 Δ의 candidate_direction과 학습 행동도 구분했다. 봉인후108쌍·8요약의 방향/상관을 독립 재합산했으며 추천으로 승격할 근거는 아니다. {local('보고표 검수','methodology_bootstrap/report_tables_validation.json')}에 범위와 오차를 남겼다.

과거 자산323개 중302개는 과거 근거의 해시와 지금도 일치한다(이 중2개는 역사적 참조와 일치). 20개는 사전 해시가 없고1개는 불일치하는 역사적 해시만 있어 과거 보존 미검증이다. 과거 참조 차이10건은 출처·시점으로 분리했다. 원본154파일(CSV150+schedule4)은 별도 입력 해시 경로로 확인했다. 새 검수 시작/종료의617파일 해시와 검수폴더 밖 metadata는 모두 보존됐다. 현재 해시만으로 그 이전 모든 시점의 무변경을 주장하지 않는다.

이번에 실행하지 않은 것은 모델 재학습·새 외부 평가·SWING2026 평가다. 증거가 없어 검증하지 못한 것은 중간 nuisance의 실제 적합,16회 원행 bootstrap,실제 판정/지각,인과 식별과 목표 추정 정확성·구간 포함률이다. 미실행과 증거 부족, 표본 부족과 측정 보류를 합치지 않았다.

## 다음 검수자가 먼저 확인할 항목

1. {local('카운트 예외6행','lineage/all_strict_count_exceptions.csv')}와 원 PA 문맥으로 무효구·오표기·카운트 오류 여부를 판단한다. 현 자료만으로 안 되면 필요한 판정 증거를 지정한다.
2. {local('발견 사항','findings.csv')}의 MB01/F-FOLD-01/MB04를 보고 구간·객체 재현의 검증 범위가 정확히 표현되는지 확인한다. 현재 수치가 재현된다는 사실과 실제 효과 정확성을 구분한다.
3. {local('기계 판정','validation.json')}과 {local('최종 증거 목록','evidence_manifest.json')}에서 scope·분모·해시를 확인한다. {local('재현 명령','reproduction.md')}은 새 검수 폴더에서만 사용한다.

이번 산출물은 이 새 검수 폴더의 보고서·발견 CSV·검증 JSON·증거 manifest·독립 코드와 비교표다. 기존 README·인계·카드·모델 버전은 수정하지 않았다. 제작 작업에 돌려줄 수정은 {local('후속 검증 계획','followup_validation_plan.md')}에 구체화했다.
'''
(HERE/'review.md').write_text(report,encoding='utf-8')

followup=f'''# 제작 작업에 돌려보낼 수정과 후속 검증

이번 검수는 수정·재학습을 실행하지 않았다. 기존 수치 오류가 확인되지 않아 전체 개발/외부 명령을 다시 돌릴 근거는 없다. 선행 작업은 검증 문구와 6개 원자료 예외의 판정이다.

| 단계 | 목적·대상 | 실행/비용 계획 | 버전·외부 영향 |
| --- | --- | --- | --- |
| 1 | description별 기대 다음 count 감사와6예외 문맥·무효구 여부 정리 | 새 감사 코드/출력만. 기존 CSV·라벨 변경 금지. 원본 필드로 원인 확인이 안 되면 판정/이벤트 보충 증거 필요로 남김 | 감사 문구만 수치불변이면 Patch. 입력/선택 수정은 Minor 이상, 목표/핵심공식 변경은 Major. 기존 봉인은 보존 |
| 2 | 통계적 선택집단 목표와 가상개입 목표를 분리; 구간을 명목 근사·실제 포함률 미검증으로 표시 | model card/spec의 후속버전 문서·validation·보고·인계 정합. 중간fit/원행bootstrap 미보존 구분. HBP선택·FA/Other 명시 | 수치불변 설명은 Patch 기록. 정의를 실제 변경하면 해당 Major/Minor 새버전 |
| 3, 조건부 | 전 적합 재현이 필요할 때 개발 outer0 평가 nuisance와 inner0 nuisance부터 복원 | 동일 v0.1.0 고정 seed/자료로 PITCH/SWING 각1쌍. 객체·사전·calibration입력·훈련키해시·row예측·잔차 보존. 기존 전체 개발 약8분/13분은 참고값이며 소범위 비용은 실행전 새추정 | 2026-09-09 기준 후보 미사용ID PITCH `bcap_pitch__mlb_2024_2025__20260909__r04`, SWING `bcap_swing__mlb_2024_2025__20260909__r03`. 실제 시작 날짜·미사용 여부 재확인. 동일설계 재현은 새실행이며 모델버전 유지 가능 |
| 4, 조건부 | bootstrap 원행/행별정책까지 인증이 필요한 경우 개발 반복1부터 저장 확장 | 기존8회 벽시계 약2시간20분/2시간34분. 새 반복1의 실제비용을 측정한 뒤 확대. raw Y/A/p/μ/φ/d/support/원game/복제키·정책·객체 보존 | 새실행ID. 개발만 재현하면 새 외부 평가 아님. 8회집계PASS로 누락원행을 채우지 않음 |
| 5, 별도 설계 | 정확한 행동가치/구간/실시간 권고가 필요한 경우 | 개발 자료에서 후보함수족·정책관련 calibration/잔차·상황별지지·숨은상태/선택/행동버전 설계. 고정최종정책 가치와 학습알고리즘 성능 중 추론목표를 정하고 의존성/동률 포함률을 검증 | 모델 설계 변경 버전과 새실행. 2023/26 재사용은 새 외부 재노출이며 최초독립외부검증이라 부르지 않음 |
| SWING2026 | 위치·존 측정 교량이 갖춰질 때만 별도 검토 | 현재평가0 유지. 동일측정량 연결의 자료·변환검증이 먼저 필요. 위치없는 대체모형으로 주검증을 대신하지 않음 | 추후실행 전 새고정명세·코드·정책·해시·시각/노출계획 필요 |

재학습 확장 여부의 기준은 검수 범위다. 저장된 탐색 진단의 재현성만 사용하는 경우1~2단계가 우선이고, 전 적합 정확성의 독립 인증을 요구할 때3~4단계를 수행한다. 단순히 오래 실행하면 인과 식별이 생기지는 않는다. 계산 결과에 영향을 주는 수정은 {link('프로젝트 버전 규칙',ROOT/'guides/analysis.md')}:31–36을 따른다.
'''
(HERE/'followup_validation_plan.md').write_text(followup,encoding='utf-8')

commands=[]
for script,role in [('inventory.py before','review baseline'),('lineage/independent_lineage.py','raw reconstruction'),('lineage/supplement_lineage.py','source exceptions and saved-score reaggregation'),('lineage/finalize_lineage_review.py','lineage evidence finalization'),('folds_prediction/review_folds_prediction.py','saved-fit recreation and partition/policy reconstruction'),('folds_prediction/supplement_saved_fit.py','saved-fit missing and unknown behavior'),('folds_prediction/policy_intervals_review.py','saved Y/A/nuisance training interval reconstruction'),('methodology_bootstrap/bootstrap_audit.py','existing aggregate/resampling reaggregation'),('numeric_audit.py','saved Y/A/nuisance AIPW/OPE reconstruction'),('provenance_audit.py','resolved hashes and timestamps'),('methodology_bootstrap/report_tables_audit.py','existing tables and behavior reaggregation'),('inventory.py after','review boundary preservation'),('finalize_review.py','review evidence assembly')]:
 name,*args=script.split();commands.append(dict(command=[sys.executable,'-B',str(HERE/name)]+args,role=role,record_type='Reconstructed from this review tool/script invocations and component logs; not independent shell history'))
write(HERE/'execution_records.json',dict(recorded_at_utc=NOW,commands=commands,attempt_notes=['Initial SciPy sandbox import denied; numerical and policy interval audits succeeded after ordinary escalation. No old library/file changed.','Provenance first pass listed historical/current hash differences; explicit archived failed source and pre-update document backups resolved them. First pass retained; one review-only None backup TypeError was fixed before final run.','Policy interval review first attempt used incorrect final score filename; review-only source fix and attempt artifacts preserved in folds_prediction.'],not_executed=['producer develop/external','model refitting','new external model evaluation','SWING2026 evaluation','new raw collection']))
execution='\n\n'.join(f"{x['role']}:\n```powershell\n& '{x['command'][0]}' -B '{x['command'][2]}'"+(' '+ ' '.join(x['command'][3:]) if len(x['command'])>3 else '')+'\n```' for x in commands)
(HERE/'reproduction.md').write_text(f'''# 독립 검수 재현 명령

아래는 이번 검수에서 사용한 명령 기록이다. 기존 생산 run.py develop/external은 실행하지 않는다. 완료된 검수 결과도 보존해야 하므로 재검수 때에는 같은 analysis 부모 아래 새 미사용 검수 폴더를 만들고 코드와 review_protocol.json의 새 선언본을 옮긴 뒤 아래 경로를 새 폴더로 치환한다. 초기 출력 JSON/CSV를 복사해 재사용하지 않는다. 코드의 ROOT/HERE 상대 깊이는 유지한다. `inventory.py`는 기존 before/after가 있으면 중단한다. 일부 보조 감사는 앞 단계의 새 산출물에 의존한다.

현재 환경은 Python {platform.python_version()}, NumPy {np.__version__}, pandas {pd.__version__}, Windows다. scipy.stats.t만 기존 runtime_ridge_v02 라이브러리에서 읽으며 샌드박스 접근 제한 시 정식 승인이 필요할 수 있다. 외부 원본 수집·재학습은 없다. 각 구성품 증거 manifest에 실제 시각·입출력 해시가 있다.

{execution}

하위 source_audit.py/write_review.py 등 증거·문서 조립 보조 명령은 해당 하위 execution log/manifest를 따른다. 이번 최종 보고서는 저장 산술과 원자료 계보·기존fit 예측을 분리하며, 명령의 성공만으로 더 넓은 통계적 주장을 인증하지 않는다.
''',encoding='utf-8')

# Collect existing input evidence referenced by child records and preservation baseline.
inputs=set(ROOT/r['path'] for r in read(HERE/'preservation_before.json')['hashed_files'])
def harvest(obj):
 if isinstance(obj,dict):
  p=obj.get('path')
  if isinstance(p,str) and isinstance(obj.get('sha256'),str):
   pp=Path(p);pp=pp if pp.is_absolute() else ROOT/pp
   if pp.is_file() and HERE not in pp.parents:inputs.add(pp)
  for v in obj.values():harvest(v)
 elif isinstance(obj,list):
  for v in obj:harvest(v)
for f in list(HERE.rglob('*.json')):
 if f.name=='evidence_manifest.json' and f.parent==HERE:continue
 try:harvest(read(f))
 except (ValueError,KeyError):pass
inputrows=[dict(path=p.as_posix(),sha256=sha(p),bytes=p.stat().st_size,role='review input/current digest; historical comparison coverage is separate') for p in sorted(inputs)]
outputrows=[dict(path=p.as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(HERE.rglob('*')) if p.is_file() and p not in [HERE/'evidence_manifest.json',HERE/'evidence_manifest.sha256',HERE/'delivery_validation.json']]
manifest=dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Final current-byte inventory of independent review inputs/code/outputs. Child logs/manifests retain earlier execution stages. No blanket pre-production preservation claim.',environment=dict(python=sys.version,executable=sys.executable,platform=platform.platform(),numpy=np.__version__,pandas=pd.__version__,dont_write_bytecode=sys.dont_write_bytecode),commands=commands,inputs=inputrows,outputs=outputrows,model_refits=0,new_external_model_evaluations=0,SWING2026_evaluations=0,code=[r for r in outputrows if r['path'].endswith('.py')],self_hash='Excluded from own output inventory to avoid a recursive digest; detached evidence_manifest.sha256 records it.',preservation_check=(HERE/'preservation_after.json').as_posix())
write(HERE/'evidence_manifest.json',manifest)
(HERE/'evidence_manifest.sha256').write_text(sha(HERE/'evidence_manifest.json')+'  evidence_manifest.json\n',encoding='utf-8')
print(json.dumps(dict(status=validation['status'],findings=len(parts),components=len(components),input_files=len(inputrows),output_files=len(outputrows)),ensure_ascii=False))
