# BCAP-PITCH-FF-v0.1.0 기본 확인과 결과 범위

## 현재 검증 범위 — 2026-09-14

**EXPERIMENTAL 유지.** 2023·2026의자체/공통지원표본12카운트외부보정비교를완료했다. 구종우열은지원·보정구간·방법민감성을함께읽으며비유의성을동등성으로해석하지않는다. 세부값·3-0/3-1/3-2판정은보고서가기준이다.

고정한 개발 규제값·학습 절차로 각 외부 연도 안에서 경기 3분할 보조 모형을 적합했다. 단일 고정 개발 예측모델의 시험이나 정책·인과 효과 검증은 아니다. 2023은 과거 연도 재현, 2026은 9월 7일까지의 개발 이후 자료다. 두 자료 모두 과거 BCAI/V1 노출 이력이 있다.

[외부 보고서](../../../../columns/001-ball-count/analysis/bcap_external_20260914__r01/final_report.html) · [계획/규제/판정](../../../../columns/001-ball-count/analysis/bcap_external_20260914__r01/plan.md) · [실행/재현](../../../../columns/001-ball-count/analysis/bcap_external_20260914__r01/reproduction.md) · [제한적 개발 검수](../../../../columns/001-ball-count/analysis/bcap_column_light_review.md). 외부적합은대상모델당연도별3fold1회,선택된개발규제값고정·외부튜닝0회다. 구간은조건부경기군집구간이며전체학습변동은미검증이다. 명세와이전완료실행은수정하지않았다.

아래는 이전 작업 시점의 기록이며 당시의 미실시 범위를 보존한다.

**2024·2025 개발 비교 완료, 외부 검증 미실시 — EXPERIMENTAL**. UTC 2026-09-11T17:56:49.616639+00:00.

입력 준비, 새 FF 3fold 학습, 저장 점수 자체/공통 집계의 기본 확인은 모두 PASS. 적합·Platt 보정 로그12건 모두 수렴했다. OOF MSE=0.235981134, Brier=0.184682519. 행동 정의와 비율이 달라 기존 FB의 Brier와 비교해 예측 개선이라고 해석하지 않는다.

확인 항목은 기존 eligible_pitch 및키·계절 W·카운트·닫힌 행동 매핑, 기존 gamefold 일치, 기존14개 입력·alpha 보존, 현재 사후 입력 배제, calibration/사전 훈련경기 한정, 새A의 투수 repertoire, 예측과AIPW 유한값 및 행별 산술, 동일 분모·부호·구종 구성 합계, 자체/공통/연도/fold 표본 합계다. 기존 FB 12카운트 Q·Δ·SE·219 구간은 저장 scores에서1e-12 이내 일치했다. FF 이외 모델을 재학습하지 않았다.

[입력 기본 확인](../../../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/preparation.json) · [학습 기본 확인](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2024_2025__20260912__r01/artifacts/basic_checks.json) · [수렴 로그](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2024_2025__20260912__r01/artifacts/fit_diagnostics.csv) · [저장 점수 집계 기본 확인](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/basic_checks.json) · [결과 전 시각·SHA256](../../../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/plan_seal.json) · [추가 결과 열람 기록](../../../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/result_access_log.json)

불확실성은 기존 경기 cluster 고정점수 명목 구간이다. 주48개 비교는 기존219개와 신규36개의 합집합을 고려해 Bonferroni255를 사용한다. 기존 FB219 결과는 원 출처로 보존했다. 연도2/fold3 보조240개는 개별 명목95% 내부 탐색이며 독립 검증이 아니다. 작은 범위·지원 부족·방법/분할 불안정·일관된 개발 방향·나머지 불확실의 사전 규칙을 적용했다.

기존 FB3-0의 통합 구간은 여전히0을 제외한다. 자체fold0, 공통fold0·2의 NFB ESS200미달 때문에 새 일관성 등급을 보류한 것이며, 기존 결과나 모든 분할의 양의 점추정을 뒤집은 것은 아니다. FF3-2는 모든 연도/fold 점추정이 양수지만 fold1의 명목 구간은0을 포함한다. 기본 계산 확인을 외부 재현·인과 검증·전체 독립 검수로 부르지 않는다.

각 FF fold의 nuisance.pkl, 계수·훈련 사전·중심화·calibration 행/점수·훈련 경기·seed, fold_membership, scores.pkl를 새 실행에 보존했다. 기존 FB 점수와 적합 객체는 기존 위치에 남겨두었다. 전체 재적합·정책 파일은 만들지 않았다. 외부 자료/2023·2026·KBO·bootstrap·추가seed·광범위 탐색·타자/SB 수정은 미실시다.
