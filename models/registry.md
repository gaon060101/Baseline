# Baseline 모델 레지스트리

## BCAP R 구현 확인 — 2026-09-28

PITCH-v0.2.0, PITCH-SB-v0.1.0, SWING-v0.2.0, PITCH-FF-v0.1.0의 2024·2025 R 재현과 2023→2015 연도별 적용을 모두 완료했다. 개발 자료는 기존 경기 분할·선택 규제값으로 새로 적합하고 보조 추정값·AIPW·지원 마스크·집계를 대조했다. 과거 연도는 새로운 R 분할을 사용한 별도 실행이다. [R 구현 안내](bcap/r/README.md) · [완료 결과 허브](../columns/001-ball-count/analysis/r_bcap_history_20260928/report.html) · [독립 구현 검토](../columns/001-ball-count/analysis/r_bcap_history_20260928/implementation_review.md). 네 모델은 EXPERIMENTAL을 유지한다. 수치 재현과 계산 완료를 과거 연도 일반화·인과 검증으로 확대하지 않는다. 2026 위치·스윙 측정 보류도 유지한다.

별도 [2026 R 보조 보고서](../columns/001-ball-count/analysis/r_supplement_20260928/report.html)에서 보존된9월7일 기준2,165경기와2025고정가중치로 BCAI 및 BCAP PITCH/FF를 계산했다. 새 R 분할이며 원 NumPy 점수 재현·미노출 외부 검증이 아니다. 검산24개와기준일을표시한PNG3개를확인했고 S/B·SWING은 측정 보류로 남겼다. 기존 모델 상태·명세는 바꾸지 않는다.

## BCAI R 구현 확인 — 2026-09-28

BCAI-OBS-v1.0.0의 정의·가중치·제외 규칙을 유지한 [R 구현](bcai/observed/v1.0.0/r/README.md)을 추가했다. [2024·2025 r02 보고서](../columns/001-ball-count/analysis/runs/bcai_r_check__mlb_2024_2025__20260928__r02/report.md)에서 364,124 유효 PA·4,859경기, 기존 점추정·분모·제외 집계가 허용 오차 1e-9 이내로 일치했다. R 난수로 다시 계산한 구간은 Python의 구간 끝점 재현으로 주장하지 않는다. R의 연도 차이 구간은 별도 후속 탐색이며 모델 상태를 승격하지 않았다. 기존 등급·보조 득점환경 지수·Ridge 출력은 이번 R 구현 대상이 아니다.

2015~2025 전 11시즌의 BCAI 및 BCAP 네 모듈 R 계산을 완료했다. 실행별 검증 범위와 보류는 [칼럼 상태](../columns/001-ball-count/column.md#current-status) 및 새 실행 manifest를 따른다. 기존 불변 명세와 과거 실행은 보존하며 모델 상태는 바꾸지 않는다.

## 2026-09-18 후속 변경 검수 — 상태 유지

[제한적 검수](../columns/001-ball-count/analysis/runs/bcap_followup_review__mlb_2024_2025__20260918__r01/report.md): BCAI-STATE-DELTA의 저장24행 독립 산술과 BCAP-DECOMP의 새 모의 예제·입력 오류·해시 확인을 완료했다. 명시 범위에서 중대한 오류는 발견하지 못했다. STATE-DELTA는 EXPERIMENTAL, DECOMP는 DRAFT 유지이며 실제 분해 학습·불확실성·시나리오 결과는 없다. 기존 BCAP·OBS 검증 범위를 확대하거나 VALIDATED로 승격하지 않았다.


## 2026-09-17 후속 구현·간단한 확인 완료

[구현 보고서](../columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md) · [보고 실행](../columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/manifest.json). 기존 S/B-v0.1.0 추정값은 재사용했으며 정의·기존 상태를 바꾸지 않았다.

| 모델 | 현재 상태·범위 | 정의·기본 확인 | 이번 실행 |
| --- | --- | --- | --- |
| BCAI-STATE-DELTA-v0.1.0 | EXPERIMENTAL · 저장된 시즌 원 W의 상태 평균 차이 24행, 간단한 산술 확인 | [카드](bcai/state_delta/v0.1.0/model_card.md) · [명세](bcai/state_delta/v0.1.0/specification.yaml) · [확인](bcai/state_delta/v0.1.0/validation.md) | [2024·2025 계산](../columns/001-ball-count/analysis/runs/bcai_state_delta__mlb_2024_2025__20260917__r01/manifest.json) |
| BCAP-DECOMP-v0.1.0 | DRAFT · 행별 확률×조건부 W 합성 구현; 실제 MLB 학습·추정·지원·구간 미실행 | [카드](bcap/decomposition/v0.1.0/model_card.md) · [명세](bcap/decomposition/v0.1.0/specification.yaml) · [확인](bcap/decomposition/v0.1.0/validation.md) | [명시적 모의 자료 확인만](../columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r01/manifest.json) |

상태 평균 차이는 실제 전이 사건조건부 값·행동 효과가 아니다. 기존 OBS 검증 상태를 승계하지 않는다. 반응률 시나리오는 설계/지원 미확보로 수치 미산출이며 JOINT 모델을 등록하지 않았다. 기존 외부 재현 및 2026 S/B·SWING 측정 보류는 유지한다.

## BCAP 외부 패턴 재현 — 2026-09-14

**2023 네 모델·2026 구종 두 모델의 외부 패턴 재현 완료, 2026 S/B·타자는 측정 보류 — EXPERIMENTAL**. 네 대상 모델의 기존 상태는 유지한다.

[최종 보고서](../columns/001-ball-count/analysis/bcap_external_20260914__r01/final_report.html) · [실행 전 계획](../columns/001-ball-count/analysis/bcap_external_20260914__r01/plan.md) · [최신 인계](../columns/001-ball-count/analysis/handoff_bcap_review.md).

고정한 개발 규제값·학습 절차로 각 외부 연도 안에서 경기 3분할 보조 모형을 적합했다. 단일 고정 개발 예측모델의 시험이나 정책·인과 효과 검증은 아니다. 2023은 과거 연도 재현, 2026은 9월 7일까지의 개발 이후 자료다. 두 자료 모두 과거 BCAI/V1 노출 이력이 있다. 2023 S/B 0-2·1-2의 S−B는 +0.034266·+0.024117 W, 주4개 보정 구간은 [0.022304,0.046228]·[0.014006,0.034228]이다. 두 하한이0.01W를 넘고 별도 산술74항목이PASS다. 2026 S/B는 좌표 기준면·존 정의 변경으로 측정 보류다. 2023 타자 가운데12카운트 모두 스윙 쪽 점추정이며3-0·3-1은 불명확하다. 밖 지원44셀은 모두 테이크 방향,3-0 밖4셀은자료부족이다. 2026 타자는 측정 보류다.

아래는 이전 작업 시점의 기록이며 당시의 미실시 범위를 보존한다.

## 포심/비포심 추가 비교 — 2026-09-12

**2024·2025 개발 비교 완료, 외부 검증 미실시 — EXPERIMENTAL**. 기존 FB/NFB의 대체 또는 검증 승격이 아니라 별도 행동 정의의 비교 모듈이다.

| 모델 | 상태·역할 | 정의 | 실행·보고 |
| --- | --- | --- | --- |
| BCAP-PITCH-FF-v0.1.0 | EXPERIMENTAL · 포심/비포심 보정 비교 | [카드](bcap/pitch_ff/v0.1.0/model_card.md) · [불변 명세](bcap/pitch_ff/v0.1.0/specification.yaml) · [기본 확인](bcap/pitch_ff/v0.1.0/validation.md) | [FF 학습](../columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2024_2025__20260912__r01/manifest.json) · [두 분류 재집계](../columns/001-ball-count/analysis/runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/manifest.json) · [보고서](../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/report.html) |

기존 PITCH-v0.2.0의 저장 점수만 재사용하며 타자·S/B 모델과 과거 완료 실행·명세는 그대로 보존했다. 추가 결과 전255 보정·실질 차이0.01W·자체/공통 표본·중단 기준을 고정했다.

## BCAP V2 — 2026-09-12

**2024·2025 개발 결과 산출, 후속 검증 미실시**. [통합 보고서](../columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/report.html). 세부 구종 입력은 FB/NFB로 바꿨고 실제 S/B 비교를 추가했다. 최종 타자 5구역의 모서리는 보고 집합에서 중복 포함한다. 외부 검증·반복 재학습·별도 독립 검수는 미실시이며 기존 버전의 통과 기록을 전용하지 않는다. 명세의 DRAFT는 정의 시점 기록이며 카드·manifest가 현재 상태다.

| 모델 | 현재 상태 | 정의·확인 | 실행 |
| --- | --- | --- | --- |
| BCAP-PITCH-v0.2.0 | EXPERIMENTAL | [카드](bcap/pitch/v0.2.0/model_card.md) · [명세](bcap/pitch/v0.2.0/specification.yaml) · [기본 확인](bcap/pitch/v0.2.0/validation.md) | [2024·2025 개발 완료](../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260912__r01/manifest.json) |
| BCAP-PITCH-SB-v0.1.0 | EXPERIMENTAL | [카드](bcap/pitch_sb/v0.1.0/model_card.md) · [명세](bcap/pitch_sb/v0.1.0/specification.yaml) · [기본 확인](bcap/pitch_sb/v0.1.0/validation.md) | [2024·2025 개발 완료](../columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/manifest.json) |
| BCAP-SWING-v0.2.0 | EXPERIMENTAL | [카드](bcap/swing/v0.2.0/model_card.md) · [명세](bcap/swing/v0.2.0/specification.yaml) · [기본 확인](bcap/swing/v0.2.0/validation.md) | [2024·2025 개발 완료](../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260912__r01/manifest.json) |

아래는 기존 모델 등록 이력이다.

모델 정의의 기준 위치는 models/, 칼럼별 실행의 기준 기록은 analysis/runs/<run_id>/manifest.json이다. 실행과 설계·검증의 의미를 분리한다. 운영 규칙은 [분석 지침](../guides/analysis.md), 구현과 재현은 [BCAI 안내](bcai/README.md)를 따른다.

| 항목 | 관찰 모델 | Ridge 탐색 모델 |
| --- | --- | --- |
| 모델 ID | BCAI-OBS-v1.0.0 | BCAI-RIDGE-v0.1.0 |
| 정식 명칭 | Ball Count Advantage Index Observed | Ball Count Advantage Index Ridge Adjusted |
| 한글 명칭 | 볼카운트 관찰 유불리 지수 | 볼카운트 Ridge 보정 유불리 지수 |
| 버전 | 1.0.0 | 0.1.0 |
| 상태 | VALIDATED | EXPERIMENTAL |
| 목적 | 칼럼의 주 유불리 측정 | 관찰 지수의 보정 민감도 점검 |
| 추정 대상 | 도달 PA의 시즌별 상대 평균 가중 공격가치 I(c) | 시작 상황을 교차 적합 잔차화한 상대 진단 J(c) |
| 기준점 | 시즌별 유효 PA의 0-0 평균; I(0-0)=100 | 시즌별 0-0 평균 잔차; J(0-0)=100 |
| 주요 입력 | PA·투구 키, 투구 전 count, 최종 event, 시즌 가중치 | OBS 입력 + 시작 타자/투수/좌우/구장/점수/주자/아웃/이닝/시즌 |
| 모델 카드 | [OBS](bcai/observed/v1.0.0/model_card.md) | [Ridge](bcai/ridge/v0.1.0/model_card.md) |
| 코드 위치 | [공동 계산](../columns/001-ball-count/analysis/analyze_count_advantage.py) | 같은 코드의 oof_ridge·잔차 지수 부분 |
| 검증 문서 | [OBS 검증](bcai/observed/v1.0.0/validation.md) | [Ridge 진단](bcai/ridge/v0.1.0/validation.md) |
| 사용한 칼럼 | [001](../columns/001-ball-count/column.md) | [001](../columns/001-ball-count/column.md) |
| 실행 결과 위치 | [bcai_obs__mlb_2024_2025__20260907__r01](../columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/README.md) | [bcai_ridge__mlb_2024_2025__20260907__r01](../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2024_2025__20260907__r01/README.md) |
| 이전·후속 버전 | 최초 등록; 이전 없음·후속 없음 | 최초 등록; 후속 BCAI-RIDGE-v0.2.0 (아래) |

Ridge는 OBS의 민감도 동반 모델이며 이전·후속 버전 관계가 아니다. VALIDATED는 해당 관찰 계산의 검증 범위이지 인과성·미래 예측·KBO 일반화 인증이 아니다. 현재 공동 CSV·audit는 OBS 실행 artifacts에 단일 보관하고, Ridge manifest의 열/JSON 선택자로 명확히 분리한다.

## 후속 Ridge 모델 — 2026-09-09 기록

| 항목 | 내용 |
| --- | --- |
| 모델 ID·버전 | BCAI-RIDGE-v0.2.0 · 0.2.0 |
| 상태 | EXPERIMENTAL · 수치 수렴·두 외부 스냅샷 평가 완료, 예측 개선은 제한적 |
| 이전 버전 | BCAI-RIDGE-v0.1.0 보존; OBS의 대체 아님 |
| 추정 대상·기준 | 시작 선수·상황 잔차화 J(c), J(0-0)=100 유지 |
| 주요 변경 | 선수/구장 공통 효과, 훈련 fold 기준 정규화, 경기 단위 중첩 CV, 엄격 수렴 PCG |
| α | 개발 CV 최소 MSE 규칙으로300; 1-SE는 비교만 수행 |
| 정의 | [모델 카드](bcai/ridge/v0.2.0/model_card.md), [명세](bcai/ridge/v0.2.0/specification.yaml) |
| 검증·코드 | [검증](bcai/ridge/v0.2.0/validation.md), [개발](bcai/ridge/v0.2.0/ridge_v02.py), [외부](bcai/ridge/v0.2.0/external_validation.py) |
| 개발 완료 | [2024·2025 r02](../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2024_2025__20260908__r02/manifest.json) |
| 수치 추가 확인 | [고정 모델 r03](../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2024_2025__20260908__r03/manifest.json) |
| 외부 재현 | [2023](../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2023__20260908__r01/manifest.json) |
| 외부 시간 순방향 | [2026-09-07까지](../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2026_ytd_20260907__20260909__r01/manifest.json) |
| 전체 비교 | [001 검증 보고서](../columns/001-ball-count/analysis/ridge_v02_validation_report.md) |

개발207개 적합 전부 수렴, 최종α300. 상수 대비 MSE 개선: 개발0.428%,2023 0.179%,2026 0.205%. 두 외부 모두0-2 최저·3-0 최고. 기존 실패 실행(개발 호출 오류,2026 최초 확보 누락)은 FAILED로 보존했다.2026은 평가 전에 누락된11경기만 보충해 최초1회 평가했으며 모델·평가 코드는 변경하지 않았다. 수집 어댑터 기록은 완료 실행의 manifest_extension.json에 있다. 모델 상태를 높은 예측력이나 선택 편향 제거의 인증으로 해석하지 않는다.


## BCAP 실제 구현·평가 반영 — 2026-09-09

| 모델 | 현재 상태 | 추정 대상 | 개발·외부 범위 | 정의·검증 |
| --- | --- | --- | --- | --- |
| BCAP-PITCH-v0.1.0 | EXPERIMENTAL · 추천 없음 | 같은 실제 상태에서 현재 한 구 FB/NFB 최종 PA W 비교 | 2024·2025 개발; 2023·2026-09-07 진단; 8회 재학습 안정성 | [카드](bcap/pitch/v0.1.0/model_card.md) · [명세](bcap/pitch/v0.1.0/specification.yaml) · [검증](bcap/pitch/v0.1.0/validation.md) |
| BCAP-SWING-v0.1.0 | EXPERIMENTAL · 추천 없음 | 사후 공 특성 조건부 번트 포함 Swing/판정상 Take의 현재 한 구 W 비교 | 2024·2025 개발; 2023 진단; 2026 전체 보류; 8회 재학습 안정성 | [카드](bcap/swing/v0.1.0/model_card.md) · [명세](bcap/swing/v0.1.0/specification.yaml) · [검증](bcap/swing/v0.1.0/validation.md) |

BCAP-JOINT는 식별·순차 정보·SWING 외부 근거가 충분하지 않아 설계하지 않았다. 봉인 명세의 status_at_definition=DRAFT는 최초 등록 이력이며 현재 카드의 EXPERIMENTAL이 실행 후 상태다. 이 상태는 인과 추천·실시간 배포·전체 PA 개선의 검증을 뜻하지 않는다. [모델/실행 목록](bcap/README.md) · [실제 보고서](../columns/001-ball-count/analysis/bcap_v010_report_20260909.md) · [입출력·명령·열람 증거](../columns/001-ball-count/analysis/bcap_execution_evidence_20260909.json).
