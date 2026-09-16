# BCAP 별도 검수 인계 — 실제 구현·평가 완료 범위

## 최신 인계 — 2026-09-14 칼럼 사용 전 제한적 검수

[제한적 검수 결과·칼럼용 결론 문단](bcap_column_light_review.md) · [별도 검산 코드](bcap_column_light_review_20260914__r01/check_saved_results.py) · [출력·입력 해시](bcap_column_light_review_20260914__r01/checks.json). 기존 독자 보고서와 CSV를 대조하고 S/B 0-2·1-2의 저장 예측값에서 Q·Δ·기존 경기 군집 구간을 원 생성 함수 없이 재현했다. 분리·라벨·전처리·튜닝·수렴은 직접 대조한 범위와 기존 기록만 확인한 범위를 구분했다. 확인 범위에서 중대한 오류는 발견하지 못했으며, 인과적인 행동 지시 표현을 고쳐 **개발자료의 패턴을 소개하는 칼럼으로 사용 가능**하다.

모델·행동·판정 기준은 변경하지 않았고 재학습·부트스트랩·외부 연도·원자료 전면 감사는 하지 않았다. 네 모델은 EXPERIMENTAL 유지, 외부 검증 미실시다. V1 이력을 V2 검증으로 전용하거나 이번 검수를 V2 전체 독립 검증 완료로 부르지 않는다. 이전 인계·증거·기존 보고서는 아래와 원래 경로에 보존했다. 계산 완료: UTC `2026-09-14T02:40:29.024402+00:00`.

## 최신 인계 — FB/NFB와 포심/비포심 추가 비교 완료

UTC 2026-09-11T17:56:49.616639+00:00. **2024·2025 개발 비교 완료, 외부 검증 미실시 — EXPERIMENTAL**. 사용자 요청은 기존 FB/NFB를 재사용하고 FF/non-FF만 추가 학습하여 자체 및 공통 표본에서12카운트 우열 또는 불명확의 이유를 판단하는 것이었다. 두 분류 비교·보고서를 완료했으며 추가 모델 개선/외부 검증을 자동으로 이어가지 않는다.

[중심 한국어 HTML 보고서](bcap_pitch_classification_20260912__r01/report.html) · [동일 보고서 Markdown](bcap_pitch_classification_20260912__r01/report.md) · [12카운트 비교표](runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/comparison_12counts.csv) · [48개 주요 값·판정 이유](runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/primary_values.csv) · [연도2/fold3 내부 탐색](runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/year_fold_values.csv) · [구종 구성](runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/pitch_composition.csv) · [재현 명령](bcap_pitch_classification_20260912__r01/reproduction.md)

모델: BCAP-PITCH-FF-v0.1.0(EXPERIMENTAL). FF만1, non-FF=SI·FC·SL·CH·ST·CU·FS·KC·SV·FA·EP·KN·FO·CS·SC만0이다. 미상/PO/결측 및 기존 PA 제외는 넣지 않는다. 포심/비포심이며 패스트볼/변화구가 아니다. 기존 결과변수·14개 투구 전 특징·직전FB/NFB·투타 축소·규제100/1000/1000·같은 경기3fold와 훈련 내부Platt를 유지했다. 새A의 propensity/두 결과모형만 새로 학습했으며 기존 FB 점수를 새A로 재해석하지 않았다.

- [새 FF 학습 실행](runs/bcap_pitch_ff__mlb_2024_2025__20260912__r01/manifest.json): COMPLETE. 적격1,415,566·지지1,271,802행, 적합/보정12개 로그 모두 수렴. 실제fold nuisance·사전·계수·calibration자료/행ID·훈련 경기·행별scores와분할 보존.
- [두 분류 저장 점수 재집계 실행](runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/manifest.json): COMPLETE. 기존FB 지지1,395,443행, 공통1,268,736행. 기존 FB12개 Q/Δ/SE/219구간은 저장 점수 재집계에서1e-12 이내 일치. 재학습0회.
- [입력 준비](bcap_pitch_classification_20260912__r01/preparation.json), [새 학습 기본 확인](runs/bcap_pitch_ff__mlb_2024_2025__20260912__r01/artifacts/basic_checks.json), [재집계 기본 확인](runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/basic_checks.json): 모두PASS. 별도 전면 독립 검수로 부르지 않는다.

추가 결과 전 기준: [실행 기준](bcap_pitch_classification_20260912__r01/analysis_plan.json) · [한국어 기준](bcap_pitch_classification_20260912__r01/analysis_plan.md) · [시각·SHA256](bcap_pitch_classification_20260912__r01/plan_seal.json) · [결과 열람 이력](bcap_pitch_classification_20260912__r01/result_access_log.json). 기존219개+신규36개=255 보정으로 이번 주요48개 차이를 모두 비교했다. 기존219 구간·판정은 원본/별도열에 보존했다. 기존 결과에 노출된 개발 확장이므로 독립 사전등록/외부검증을 주장하지 않는다. 연도/fold240개는 개별명목95% 내부탐색이다.

핵심 결론: 0-0은 두 분류의 자체/공통 보정 구간이 모두 ±0.01 W 안이다. FF의 3-2는 공통 Δ +0.01699, 명목 보정 구간 [+0.00141, +0.03257] W로 비포심 방향이 두 연도와 세 fold의 점추정에서 유지되지만, 최소 0.01 W의 효과 하한을 확보한 것은 아니다. FF의 3-0은 fold별 실질 반전이 있어 불안정하다. FB의 3-1은 결과모형 +0.00685 대 AIPW −0.01165 W로 부호가 다르고 보정 구간이 0을 포함한다.

FB의 3-0은 통합 차이가 계속 남는다(자체 +0.06821 W). 새 판정의 보류는 자체 fold0의 NFB ESS 193.76, 공통 fold0/2의 ESS 176.04/187.27이 기준 200에 미달했기 때문이다. 모든 연도/fold의 점추정은 여전히 양수다. subgroup_sign_consistent=False는 코드상 ‘다섯 집단 모두 지원 + 같은 부호’를 충족하지 못했다는 뜻이며, 실제 부호 반전으로 읽지 않아야 한다. 단순 평균은 FB 쪽, 모형/AIPW는 NFB 쪽으로 갈리므로 보정 의존성도 함께 제시했다.

완료와 한계: 현재 자료와 설계로 대부분 카운트의 투구 계열 우열을 충분히 구분하지 못했다. 제한된 3-2 개발 단서는 보존하며 요청 범위에서 종료한다. 선수 보정은 의도·품질·컨디션과 사후 선택을 제거하지 못했고, 구간은 고정 점수의 경기 의존성만 반영한다. 재학습 불확실성·경기 간 선수 의존성·실제 95% 포함률·외부 재현·실제 지시 효과는 미검증이다. 타자/SB, 기존 정제본/모델/완료 실행/봉인을 덮어쓰지 않았고 새로운 2023/2026 접근·KBO·bootstrap·추가 seed·광범위 탐색·Drive/게시를 하지 않았다.

후속 작업은 이 인계의 현재 결과와추가요청범위를구분해서시작한다. [이번 문서 전후 해시·백업](bcap_pitch_classification_20260912__r01/document_update.json)에공유MD수정을기록했다. 이전V2/V1인계와원증거JSON은아래이력및기존위치에보존한다.

## V2 기본 개발 인계 — 2026-09-12

**2024·2025 개발 결과 산출, 후속 검증 미실시 — EXPERIMENTAL**. 사용자 범위 변경에 따라 기존 2024·2025만으로 최소 변경 개발을 수행했다. 2023/2026 데이터 적용·외부 평가·bootstrap/반복 재학습·별도 독립 검수는 이번에 미실시다. 아래 V1 외부/독립 검산 이력을 V2 검증으로 전용하지 않는다.

[이번 제작 요청](bcap_v2_development_20260912__r01/request_original.txt) · [하나의 통합 보고서](bcap_v2_development_20260912__r01/report.html) · [최초 설계 기록](bcap_v2_development_20260912__r01/design_before_results.json) · [적합 전 최종 5구역 변경과 SHA256](bcap_v2_development_20260912__r01/design_revisions/final_choice_before_fitting.json) · [실제 기본 확인](bcap_v2_development_20260912__r01/basic_summary.json) · [재현 명령](bcap_v2_development_20260912__r01/reproduction.md) · [문서 전후 해시·보존 경로](bcap_v2_development_20260912__r01/document_update.json)

최종 사용자 선택은 상·하·좌(몸쪽)·우(바깥쪽)·가운데(존 안 전체)다. 모서리는 두 구역 보고에 들어가며 학습·전체·카운트에서는 한 행이다. 이 변경은 첫 적합 전에 기록했고 보정 가족을 219개로 고정했다. 기존 INNER/BOUNDARY/OUT nuisance 입력과 물리적 입력은 유지했으며 현재/직전 구종 범주만 FB/NFB로 단순화했다. S/B는 실제 기하 위치로 별도 정의했다.

- BCAP-PITCH-v0.2.0: COMPLETE / EXPERIMENTAL, 적격 1,415,566행, 공통 지지 1,395,443행. [manifest](runs/bcap_pitch__mlb_2024_2025__20260912__r01/manifest.json) · [기본 확인 범위](../../../models/bcap/pitch/v0.2.0/validation.md)
- BCAP-PITCH-SB-v0.1.0: COMPLETE / EXPERIMENTAL, 적격 1,415,566행, 공통 지지 1,399,993행. [manifest](runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/manifest.json) · [기본 확인 범위](../../../models/bcap/pitch_sb/v0.1.0/validation.md)
- BCAP-SWING-v0.2.0: COMPLETE / EXPERIMENTAL, 적격 1,416,043행, 공통 지지 1,355,719행. [manifest](runs/bcap_swing__mlb_2024_2025__20260912__r01/manifest.json) · [기본 확인 범위](../../../models/bcap/swing/v0.2.0/validation.md)

주요 결과: S/B에서 0-2·1-2는 B 쪽 허용 공격가치가 더 낮은 점추정이며 보정 명목 구간도 0을 제외한다. FB/NFB에서는 3-0만 보정 명목 구간이 0을 제외하며 NFB 방향이다. 타자 존 안은 12카운트 모두 Swing 쪽, 존 밖은 지원된 셀에서 Take 쪽 점추정이다. 3-0의 밖 네 구역은 자료 부족이다. 미측정 교란·사후 선택·구간의 실제 포함률이 미검증이므로 행동 지시의 인과 효과로 해석하지 않는다.

보존한 실제 모델은 세 outer fold의 nuisance 객체(사전·계수·중심화·Platt 자료), S/B 튜닝 객체, fold 행/경기 연결, scores.pkl이다. 최종 전체 재적합 모델·학습 정책은 없으며 정책 선택/평가 결과를 주장하지 않는다. 공통 준비와 세 실행의 기본 오류 확인은 PASS, 모든 적합은 수렴했다. 기존 예외 6건 중 개발 2행을 표시한 채 유지했다.

후속 검수자가 먼저 볼 부분은 보고 표의 단위·분모·5구역 중첩, S/B 실제 위치와 의도의 구분, 훈련/평가 경기 및 사전·calibration 분리, 저장 nuisance와 행별 AIPW 연결, 기본 확인의 실제 범위다. 외부 재현·재학습 불확실성과 독립 검산은 새 사용자 요청을 받아야 할 미실시 항목이다. 원 인계 증거/검증 JSON, v0.1 정의·완료 실행·봉인은 이번에 수정하지 않았다. 이번 MD 변경 전 사본은 document_backups에 보존했다. 과거 자산 전체를 다시 해시한 보존 감사라고 주장하지 않는다.

## 이하 V1 인계 이력 — 2026-09-09 기준

갱신: 2026-09-09T08:49:31.268706+00:00. Baseline 001-ball-count.

## 1. V1 당시 상태

BCAP-PITCH-v0.1.0 / BCAP-SWING-v0.1.0은 실제 제작·개발·독립 검산 후 **EXPERIMENTAL**이다. PITCH는 2023·2026-09-07까지 외부 진단, SWING은 2023 외부 진단을 완료했다. SWING 2026은 plate 기준면과 존 정의의 정합성을 확보하지 못해 전체 평가를 보류했다. 두 모델의 행동 추천은 모두 비어 있다. 실행된 비교는 UNCERTAIN/NO_SUPPORT로 구분한다. BCAP-JOINT는 전제 근거 부족으로 설계하지 않았다.

[실제 수치·16종 주요 표·카운트별 해석](bcap_v010_report_20260909.md) · [카운트별 실제·후보 행동 비율 비교](bcap_implementation_review_20260909/behavior_comparison.md) · [모델·실행 안내](../../../models/bcap/README.md) · [독립 구현 검수](bcap_implementation_review_20260909/review.md) · [새 실행 증거 목록](bcap_execution_evidence_20260909.json) · [MD 변경 감사](bcap_document_update_20260909.json)

## 2. 원래 인계 보존

이전 ‘구현 미착수’ 인계는 [원래 인계 스냅샷](bcap_original_handoff_20260909/handoff_bcap_review.md)으로 보존했다. [원래 증거 JSON](handoff_bcap_review_evidence.json)과 [원래 검증 JSON](handoff_bcap_review_validation.json)은 바이트를 변경하지 않았다. 기존 문서 해시가 가리키는 시점과 현재 실행 완료 시점을 구분한다. 새 기록은 새 증거 인덱스에 추가했으며 이전 인계 해시를 외부 사전 봉인이라고 재해석하지 않는다.

[기존 자산 보존 검사](bcap_implementation_review_20260909/legacy_asset_preservation.json)의 기존 증거 SHA 대조 범위는 302개 파일이다. 대상 정제본 7/7, BCAI 실행 파일 277/288, BCAI 모델 파일 11/19에서 과거 기준 해시와 일치했다. 기준 증거가 없는 20개와 과거 마이그레이션 이전 참조만 있는 1개 파일은 이번 현재 해시만으로 BCAP 직전부터의 무변경을 확인할 수 없다. 오래된 역사적 참조와 현재 파일의 차이 10개를 이번 BCAP의 변경으로 간주하지 않는다. 누락 0개·선택한 과거 기준 해시 불일치 0개이며 상세 파일·기준 선택·이전 참조의 차이는 원 JSON을 따른다. 원본 150 CSV는 이 기존 자산 검사에서 제외했고 별도 원본/봉인 해시 검사와 구분한다. 기존 트리 전체에 과거 무변경 증명이 있다고 주장하지 않는다.

진행 중 만든 [진행 기록](bcap_execution_progress_20260909.md)과 [재학습 완료 전 주 분석 1차 보고서](bcap_v010_primary_report_20260909.md)도 중간 기록으로 보존했다. 현재 인계의 최종 상태·8회 재학습 포함 결과는 본 문서와 최종 보고서가 기준이다.

원문 요구는 [보관 원문](bcap_request_original.txt), 원 요구·문제·채택 수정·근거·추정 대상 영향은 [설계 결정](../../../models/bcap/design_decisions.md), 행동 라벨·2026 측정 근거는 [측정 검토](../../../models/bcap/measurement_review.md)에 있다.

## 3. 구현한 추정 대상·상태·정책

PITCH는 현재 한 구 FB/NFB의 최종 PA 공격가치 비교이며 현재·직전 좌표를 입력하지 않는다. SWING은 번트 포함 기록상 공격 시도/판정상 Take의 사후 공 특성 조건부 진단이다. 명시적 scored HBP는 Take로 포함하지만 불명 라벨을 Take로 대치하지 않는다. 타자의 실시간 지각·구종 품질·컨디션·의도·미측정 교란은 식별되지 않았다. 같은 실제 선수·상황 행에 양 행동을 적용했으며 가상 평균 선수 예측으로 대체하지 않았다. 완료 PA·IBB·최종 결과 결측 제외는 사후 선택을 포함한다. 행별 차이를 합쳐 PA 전체 정책의 개선량으로 보고하지 않는다.

Y는 기존 OBS 계열의 시즌별 가중 최종 PA 공격가치 W이며 BCAI 상태 가치나 전이 보상을 더하지 않았다. PITCH의 Δ는 Q(FB)−Q(NFB), SWING의 Δ는 Q(번트 포함 Swing)−Q(Take)다. 투수는 작을수록, 타자는 클수록 점추정 방향이 유리하다. 개선량 부호는 PITCH=관찰−후보, SWING=후보−관찰이다. 단위는 W/선택된 현재 의사결정 행이며 공식 wOBA·득점·PA 전체 누적 개선과 다르다.

X에는 실제 투수·타자 및 허용한 상황을 넣고 양 nuisance에 작은 표본 효과 축소를 적용한다. Z는 PITCH count, SWING count×zone×FB/NFB다. 카운트 평균 AIPW Q, 행별 조건부 회귀 μ, 실제 학습한 후보 정책 d(Z)는 별개다. 평가 action_values의 방향은 평가자료 점추정이며 저장된 정책 행동과 다를 수 있다. 외부 승자를 정답 ‘최적 행동’으로 부르지 않는다.

카운트별 실제·후보 행동 비율 비교는 기존 보조 산출물의 같은 공통 지지 집단에서 실제 비율·후보 비율·%p 차이·불일치율을 문서로 옮긴 봉인 뒤 표현 보완이다. 새 추정·주 검증 변경·추천 승격은 없다. 개발 행에는 해당 outer 훈련에서 학습한 정책, 외부 행에는 고정된 최종 개발 정책을 적용한 기록을 구분해 제시한다.

Ridge T learner 결과 회귀와 Ridge score·별도 20% 훈련 경기 Platt propensity를 사용했다. α 후보 100·1000의 선택·범주 사전·calibration은 해당 훈련 자료 안에서 이루어진다. 경기 outer3/inner2 구조로 정책 점수 생성과 outer OPE를 분리했다. 일반 deterministic 후보와 fallback Bernoulli(.5)를 기록하고, 보수 정책은 H(Z)=0으로 실제 메커니즘을 전 영역에서 유지한다. 보수 정책 개선량 0은 정의상 결과다.

## 4. 실행 목록·실제 수치

| 모델 | 범위 | 실행 상태 | 적격 행 | 공통 지지 행 | 전체 판정 | 완료 UTC | 실행 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PITCH | 2024·2025 개발 | COMPLETE | 1,415,566 | 1,395,402 | UNCERTAIN | 2026-09-09T06:02:44.847051+00:00 | [bcap_pitch__mlb_2024_2025__20260909__r02](runs/bcap_pitch__mlb_2024_2025__20260909__r02/manifest.json) |
| SWING | 2024·2025 개발 | COMPLETE | 1,416,043 | 1,354,516 | UNCERTAIN | 2026-09-09T06:10:20.553139+00:00 | [bcap_swing__mlb_2024_2025__20260909__r01](runs/bcap_swing__mlb_2024_2025__20260909__r01/manifest.json) |
| PITCH | 개발 전체 재학습 8회 | COMPLETE | 해당 없음 | 해당 없음 | 등급 없음 | 2026-09-09T08:23:56.047917+00:00 | [bcap_pitch__mlb_2024_2025__20260909__r03](runs/bcap_pitch__mlb_2024_2025__20260909__r03/manifest.json) |
| SWING | 개발 전체 재학습 8회 | COMPLETE | 해당 없음 | 해당 없음 | 등급 없음 | 2026-09-09T08:45:24.101853+00:00 | [bcap_swing__mlb_2024_2025__20260909__r02](runs/bcap_swing__mlb_2024_2025__20260909__r02/manifest.json) |
| PITCH | 2023 재현 | COMPLETE | 716,113 | 697,633 | UNCERTAIN | 2026-09-09T06:16:29.016396+00:00 | [bcap_pitch__mlb_2023__20260909__r01](runs/bcap_pitch__mlb_2023__20260909__r01/manifest.json) |
| SWING | 2023 재현 | COMPLETE | 716,385 | 682,953 | UNCERTAIN | 2026-09-09T06:20:48.704321+00:00 | [bcap_swing__mlb_2023__20260909__r01](runs/bcap_swing__mlb_2023__20260909__r01/manifest.json) |
| PITCH | 2026-09-07까지 | COMPLETE | 635,095 | 615,820 | UNCERTAIN | 2026-09-09T06:21:13.945174+00:00 | [bcap_pitch__mlb_2026_ytd_20260907__20260909__r01](runs/bcap_pitch__mlb_2026_ytd_20260907__20260909__r01/manifest.json) |
| SWING | 2026-09-07까지 | WITHHELD | 해당 없음 | 해당 없음 | 등급 없음 | 2026-09-09T06:15:29.151986+00:00 | [bcap_swing__mlb_2026_ytd_20260907__20260909__r01](runs/bcap_swing__mlb_2026_ytd_20260907__20260909__r01/manifest.json) |
| PITCH | 개발 최초 호출 실패 보존 | FAILED | 해당 없음 | 해당 없음 | 등급 없음 | 2026-09-09T05:53:58.356406+00:00 | [bcap_pitch__mlb_2024_2025__20260909__r01](runs/bcap_pitch__mlb_2024_2025__20260909__r01/manifest.json) |

| 모델 | 평가 | Q0 | Q1 | Δ=Q1−Q0 W | Δ 조건부 동시95% | 후보 정책 개선량 W | 개선량 조건부 동시95% | 지지 비율 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| PITCH | development_2024_2025 | 0.3009 | 0.3009 | -0.0000 | [-0.0037, 0.0037] | 0.0010 | [-0.0007, 0.0027] | 98.6% |
| SWING | development_2024_2025 | 0.2846 | 0.2600 | -0.0246 | [-0.0286, -0.0206] | 0.0256 | [0.0242, 0.0270] | 95.7% |
| PITCH | external_2023 | 0.3058 | 0.3071 | 0.0013 | [-0.0041, 0.0066] | 0.0014 | [-0.0009, 0.0037] | 97.4% |
| SWING | external_2023 | 0.2912 | 0.2636 | -0.0276 | [-0.0330, -0.0222] | 0.0264 | [0.0244, 0.0284] | 95.3% |
| PITCH | external_2026 | 0.3016 | 0.3028 | 0.0012 | [-0.0045, 0.0068] | 0.0019 | [-0.0005, 0.0043] | 97.0% |

카운트와 셀의 분모·가치·구간·등급·external 비교는 주 보고서와 16종 CSV를 따른다. 최초 PITCH r01은 입력 경로 처리 오류로 적합 전 실패한 기록을 FAILED로 보존했고 새 r02에서 수행했다. 실패 당시 manifest의 코드 해시와 일치하는 [실패 실행 원 코드 사본](runs/bcap_pitch__mlb_2024_2025__20260909__r01/artifacts/run_failed_source.py)과 [추가 provenance](runs/bcap_pitch__mlb_2024_2025__20260909__r01/provenance_extension_20260909.json)에 현재 코드와의 경로 보정·스냅샷 보존 차이를 기록했다. 원 실패 manifest는 바꾸지 않았다. r03(PITCH)과 r02(SWING)는 버전 교체가 아닌 8회 전체 재학습 민감도 실행이다.

## 5. 외부 봉인과 열람 이력

최종 봉인: [external_seal_20260909_r01.json](../../../models/bcap/external_seal_20260909_r01.json). UTC 2026-09-09T06:13:44.654276+00:00, SHA256 `0fa8f05f2c2d75bc08d40433317890281c2007467520d365b5482c560d5e1105`. 정의·코드·최종 개발 nuisance/정책·hyperparameter와 사전 보조 범위를 고정했다. 기존 외부 원본의 파일 해시는 최종 봉인에 기록했다. 문서 갱신 시 모든 sealed files 해시를 재확인하며 원본 전체 재해시는 별도 check_artifacts 검사의 역할이다.

2023·2026은 기존 BCAI/Ridge에서 이미 사용했다. 이번 BCAP 결과 접근 시각만 별도 남기며 완전히 미관측 데이터라고 주장하지 않는다. 외부 고정 개발 nuisance의 예측 성능과 외부 경기 교차 적합 nuisance로 평가한 고정 개발 정책가치를 구분한다. 외부 propensity를 개발에서 그대로 맞다고 가정하지 않고, 외부 nuisance의 알고리즘·α는 개발 고정값을 사용했다. 외부 정책 학습·외부 튜닝·외부 결과에 따른 모델 재설계는 하지 않았다.

| 실행 | 이번 작업 최초 BCAP 외부 행 접근 UTC | 완료 UTC | 모델 결과 평가 횟수 |
| --- | --- | --- | --- |
| bcap_pitch__mlb_2023__20260909__r01 | 2026-09-09T06:14:39.518503+00:00 | 2026-09-09T06:16:29.016396+00:00 | 1 |
| bcap_swing__mlb_2023__20260909__r01 | 2026-09-09T06:17:36.283411+00:00 | 2026-09-09T06:20:48.704321+00:00 | 1 |
| bcap_pitch__mlb_2026_ytd_20260907__20260909__r01 | 2026-09-09T06:18:57.081644+00:00 | 2026-09-09T06:21:13.945174+00:00 | 1 |
| bcap_swing__mlb_2026_ytd_20260907__20260909__r01 | 모델 평가 접근 없음; WITHHELD | 2026-09-09T06:15:29.151986+00:00 | 0 |

2026은 2025 결과 가중치를 고정했다. PITCH 입력은 위치를 쓰지 않는다. SWING은 front/middle plate와 operator/ABS zone 간 검증된 교량 자료가 없어 전체 평가를 보류했으며 위치를 뺀 대리 분석으로 주 검증을 대체하지 않았다. 외부 결과 뒤 설계를 바꾸면 새 버전·새 실행과 재노출 이력을 남겨야 한다.

## 6. 검증과 남은 한계

주 구간은 고정 OOF 점수의 경기 군집 조건부 구간과 Bonferroni 1,536 가족 범위다. 각 모델의 8회 전체 재학습은 매 반복의 전처리·튜닝·calibration·nuisance·정책 선택을 다시 수행한 안정성 진단이며 최종 개발 정책의 완전한 95% 신뢰구간이 아니다. 경기 간 선수·시리즈 의존성과 동률 근처 선택도 남는다. known/unseen·IPW·Hájek·g-computation·추가 calibration·민감도와 보조 구간은 별도 진단이다. NO_SUPPORT는 실행된 비교의 표본·공통 지지 부족, UNCERTAIN은 지원된 비교에도 식별·학습 불확실성 근거 부족을 뜻한다. 미실행·측정 보류에는 표본 판정 등급을 부여하지 않는다. 모든 추천 행동은 비어 있고 보수 정책은 전 영역에서 실제 행동을 유지한다.

독립 검산 기록:

- [pitch_development_complete_validation.json](bcap_implementation_review_20260909/pitch_development_complete_validation.json): PASS; 2026-09-09T06:04:14.709677+00:00
- [swing_development_complete_validation.json](bcap_implementation_review_20260909/swing_development_complete_validation.json): PASS; 2026-09-09T06:11:47.947409+00:00
- [pitch_2023_external_validation.json](bcap_implementation_review_20260909/pitch_2023_external_validation.json): PASS; 2026-09-09T06:17:09.674258+00:00
- [swing_2023_external_validation.json](bcap_implementation_review_20260909/swing_2023_external_validation.json): PASS; 2026-09-09T06:23:37.085459+00:00
- [pitch_2026_external_validation.json](bcap_implementation_review_20260909/pitch_2026_external_validation.json): PASS; 2026-09-09T06:23:36.847122+00:00
- [action_lineage_validation.json](bcap_implementation_review_20260909/action_lineage_validation.json): PASS (원자료 행동·입력 계보 또는 투구 전 점수 시점 검사)
- [score_timing_validation.json](bcap_implementation_review_20260909/score_timing_validation.json): PASS (원자료 행동·입력 계보 또는 투구 전 점수 시점 검사)
- [bootstrap_final_validation.json](bcap_implementation_review_20260909/bootstrap_final_validation.json): PASS; 두 모델 각각 완료 8회 저장 복제 키·집계·안정성 요약을 독립 대조. 전체 학습 신뢰구간 검증·추천 승격 없음.

독립 검산은 AIPW/OPE 부호·W 단위·같은 분모·키·fold 교집합·금지 입력·학습 정책을 검사했다. 행동·입력 계보 재구성과 투구 전 점수 시점을 별도 검사했으며 행동 선택의 인과 식별·실시간 유용성 검증을 대신하지 않는다. 투타 개인 효과를 두 nuisance에 포함해도 선수×행동 품질과 목표 위치·예상·컨디션 교란이 남는다.

외부 방향 일치·상관의 [사후 기술 비교](bcap_implementation_review_20260909/postseal_descriptive_comparison/comparison_manifest.json)와 [요약 CSV](bcap_implementation_review_20260909/postseal_descriptive_comparison/direction_and_correlation_summary.csv)는 봉인 뒤 기존 결과를 본 상태에서 작성한 집계다. 주 명세·추정 대상·정책·등급은 변경하지 않았고, 각 시즌의 서로 다른 실제 지지 집단을 비교한다. 사전 고정 주 검증 또는 최적 정책의 정답 일치로 해석하지 않으며, 추천 등급을 올리지 않는다.

해결되지 않은 항목과 필요한 증거:

1. 인과적 행동 추천: 선수별 실행 가능한 구종군, 의도·구종 품질·상태·타자 지각의 측정 및 교환가능성/선택 식별 근거가 필요하다.
2. SWING 실시간 정책: 결정을 내릴 때 실제 가용했던 시간별 지각 대리값과 측정 지연·오차 검증이 필요하다.
3. 2026 SWING: 같은 투구 구·신 좌표와 두 존 정의의 짝지은 교량 자료 및 사전 오차 기준이 필요하다.
4. 전체 학습95% 구간: 충분한 재학습 반복과 동률 민감 정책 추론, 경기 간 선수·시리즈 의존성을 다루는 별도 설계가 필요하다. 8회 범위는 대체 증거가 아니다.
5. NO_SUPPORT 셀: 해당 행동별 표본·경기·ESS·공통 지지 확보가 먼저이며 일반 선수군 외삽으로 메우지 않는다.
6. 전체 PA·JOINT: 바뀐 행동의 미래 상태 분포·상대 반응을 포함한 순차 식별·평가를 별도 설계해야 한다.

## 7. 파일·입출력·명령·다음 검수

모델 정의는 models/bcap/<variant>/v0.1.0, 실제 실행은 해당 run manifest/artifacts, 새 정제본은 기존 data/processed의 bcap 이름 파일이다. 이전 원본·정제본·BCAI 모델·실행은 보존했다. 정제 감사의 사유별 제외·문자열·구종 맵·키·측정 검사와 raw/input/code/config/output 해시를 [새 실행 증거 JSON](bcap_execution_evidence_20260909.json)에서 모두 연결한다. 실제 작업의 도구 호출 명령은 [사후 명령 기록](bcap_execution_commands_20260909.json)에서 출처·UTC·manifest 해시와 함께 확인한다. 독립 shell history 회수와 구분하며, 명령이 누락되어 manifest에서 복원한 경우에는 별도 kind로 표시한다. 각 run에 후속 provenance/manifest extension이 있으면 새 증거 목록에 함께 보존한다.

문서 갱신 뒤 실행하는 최종 보존·해시·내부 링크 검사의 실제 결과는 [최종 보존·해시·링크 검사 폴더](bcap_final_validation_20260909)의 `validation.json`에서 확인한다. 이 문서 생성 시점에는 예정 출력이며 PASS를 선제적으로 단정하지 않는다. 최종 감사 이후 문서를 바꾸면 새로운 감사가 필요하다.

후처리 재현 예시(모델 적합·데이터 수집 없이 기존 완료 집계에서 새 보고 사본 생성; 아래 목적지가 이미 있으면 새 이름 사용):

```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\백창현\Desktop\Baseline\models\bcap\build_report.py' '--pitch-dev' 'bcap_pitch__mlb_2024_2025__20260909__r02' '--swing-dev' 'bcap_swing__mlb_2024_2025__20260909__r01' '--pitch-2023' 'bcap_pitch__mlb_2023__20260909__r01' '--swing-2023' 'bcap_swing__mlb_2023__20260909__r01' '--pitch-2026' 'bcap_pitch__mlb_2026_ytd_20260907__20260909__r01' '--swing-2026' 'bcap_swing__mlb_2026_ytd_20260907__20260909__r01' '--pitch-bootstrap' 'bcap_pitch__mlb_2024_2025__20260909__r03' '--swing-bootstrap' 'bcap_swing__mlb_2024_2025__20260909__r02' '--output-dir' 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_report_recheck_20260909T084931Z' '--report' 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_report_recheck_20260909T084931Z.md'
```

행별 독립 검산을 다시 수행할 때는 verify_bcap.py의 --rows/--model/--summary/--folds/--config에 해당 실행 artifacts를 지정하고 --output에 새 JSON 경로를 쓴다. 기존 명령의 run ID로 다시 적합하면 보존 규칙에 따라 중단되므로 새 분석 실행은 반드시 새 ID를 사용한다.

검수 순서: (1) 원 인계 증거 보존과 최종 봉인 해시, (2) 실제 실행·정제 입력/출력 해시, (3) 시간 순서와 행동 라벨·사후 선택, (4) outer/inner/tuning/calibration/정책 평가 경기 분리, (5) 독립 수치 검산과 16종 표의 분모·부호, (6) 외부 고정 예측/OPE 분리와 열람 시각, (7) 실제 지지 등급·전체 학습 불확실성·2026 측정 보류, (8) 카운트 해석과 문서 상태의 일치.

KBO 수집·분석, Drive 업로드, 공동 Docs 수정, 외부 게시·전송은 이번 작업에서 하지 않았다. 로컬 MD 갱신이 기존 드라이브 공유 사본에 자동 반영되지 않는다. 기존 자료를 다시 수집하지 않았다.
