# BCAP-PITCH-SB-v0.1.0 기본 확인과 검증 상태

## R 수치 재현 확인 — 2026-09-28

**EXPERIMENTAL 유지.** [새 R 실행](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_sb_r__mlb_2024_2025__20260928__r01/manifest.json)에서 기존 경기 분할과 선택 규제값으로 다시 적합했다. 보조 추정값·AIPW·지원 마스크·집계 재현 검사를 통과했다. [R 구현 안내](../../r/README.md) · [검사 기록](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_sb_r__mlb_2024_2025__20260928__r01/artifacts/checks.json) · [과거 연도 결과](../../../../columns/001-ball-count/analysis/r_bcap_history_20260928/report.html).

이는 계산 구현의 일치 확인이다. 인과성·미래 예측·구간의 실제 포함률을 검증하거나 상태를 승격한 것이 아니다. 새 과거 연도 적합은 별도 실행으로 보존하고, 기존 불변 명세·완료 실행을 유지한다. 구간은 고정 점수의 조건부 경기 군집 근사이며 보조 모형 재학습 변동은 포함하지 않는다.


## 현재 검증 범위 — 2026-09-14

**EXPERIMENTAL 유지.** 2023 S/B 0-2·1-2의 S−B는 +0.034266·+0.024117 W, 주4개 보정 구간은 [0.022304,0.046228]·[0.014006,0.034228]이다. 두 하한이0.01W를 넘고 별도 산술74항목이PASS다. 2026 S/B는 좌표 기준면·존 정의 변경으로 측정 보류다.

고정한 개발 규제값·학습 절차로 각 외부 연도 안에서 경기 3분할 보조 모형을 적합했다. 단일 고정 개발 예측모델의 시험이나 정책·인과 효과 검증은 아니다. 2023은 과거 연도 재현, 2026은 9월 7일까지의 개발 이후 자료다. 두 자료 모두 과거 BCAI/V1 노출 이력이 있다.

[외부 보고서](../../../../columns/001-ball-count/analysis/bcap_external_20260914__r01/final_report.html) · [계획/규제/판정](../../../../columns/001-ball-count/analysis/bcap_external_20260914__r01/plan.md) · [실행/재현](../../../../columns/001-ball-count/analysis/bcap_external_20260914__r01/reproduction.md) · [제한적 개발 검수](../../../../columns/001-ball-count/analysis/bcap_column_light_review.md). 외부적합은대상모델당연도별3fold1회,선택된개발규제값고정·외부튜닝0회다. 구간은조건부경기군집구간이며전체학습변동은미검증이다. 명세와이전완료실행은수정하지않았다.

아래는 이전 작업 시점의 기록이며 당시의 미실시 범위를 보존한다.

**EXPERIMENTAL — 2024·2025 개발 결과 산출, 후속 검증 미실시**. UTC 2026-09-11T17:21:55.606631+00:00.

제작 과정의 기본 확인: PASS. 적격 1,415,566행, 지지 1,399,993행, OOF 결과 MSE 0.235264943, 행동 Brier 0.234037911. 적합·보정 로그 30건 모두 수렴했다. 이 수치는 외부 예측 성능이 아니다.

[실제 확인 항목](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/basic_checks.json) · [수렴 기록](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/fit_diagnostics.csv) · [공통 입력 기본 확인](../../../../columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/preparation/preparation.json) · [코드·설정·입출력·환경·시각 manifest](../../../../columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/manifest.json)

확인 범위는 개발 시즌, 투구 키·유효 카운트·행동·최종 결과·시즌 W 연결, 닫힌 매핑/금지 입력, 경기 fold 분리, 계산 유한값과 수렴, 양 행동 같은 분모·부호·표 합계다. 기존 예외 6건 중 개발 2행은 표시 후 유지했으며 원인 감사·임의 수정은 하지 않았다. 각 항목의 구체적인 검사와 한계는 연결한 JSON/코드가 기준이다.

219개 차이에 대한 Bonferroni 보정 명목 구간을 결과 전에 정했다. 경기별 고정 점수 변동만 반영하며 nuisance/정책 재학습·경기 간 선수 의존성과 실제 구간 포함률은 미검증이다. 이 모듈의 출력 13개를 포함한 전체 가족이다. 차이 불명확과 비교 자료 부족을 나눴으며 인과 권고 등급은 부여하지 않았다.

보존: 각 평가 fold의 nuisance.pkl(양 행동 결과 계수, 사전·중심화, 행동 계수, Platt 보정 자료/행 ID), fold_membership.csv, fold_records.json, 행별 scores.pkl, 적합 로그. S/B는 훈련 내부 튜닝 Ridge 객체도 보존한다. 최종 전체 개발 재적합 모델과 정책은 만들지 않았다. 저장 객체는 해당 engine 모듈을 import할 수 있는 환경에서 복원한다.

미실시: 2023/2026 적용·외부 평가, 반복 재학습/여러 seed/bootstrap, 별도 독립 검산기·전면 방법론 검수, 기존 원본 전체 재해시. V1의 외부/독립 검수 기록을 이 버전의 통과 증거로 쓰지 않는다.
