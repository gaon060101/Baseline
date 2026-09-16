# 보고서·표·행동 비율·외부 기술 비교 독립 검수

**명시 범위 내 사용 가능.** 원 실행 집계를 전달하는 16개 CSV, 본문의 12카운트 개발·외부 설명 및 SWING 셀 표에서 수치 연결 오류를 발견하지 못했다. 봉인 후 행동 비율 문서는 동일 지원 행에서 계산한 실제 비율·후보 비율·퍼센트포인트 차이·기대 불일치율을 올바르게 표시한다. 외부 상관·방향 비교는 서로 다른 시즌 지원 집단의 상태별 관찰 진단이며 정책의 인과적 타당성 또는 외부 최적행동의 정답과 구분되어 있다.

`report_tables_audit.py`는 build_report.py, supplement_diagnostics.py, compare_existing_estimates.py의 계산 함수를 호출하지 않는다. 기존 코드는 정의를 확인하는 읽기 대상으로만 사용했다. 16개 표와 해당 원 CSV/JSON의 직접 대조, 정책 확률과 행동률의 독립 복원, 별도 상관 계산을 수행했다. 허용오차는 review_protocol.json에 따라 수치 종류별로 적용했으며 문장의 숫자는 출력된 소수 자릿수에서 대조했다.

| 검사 | 범위 | 결과 |
| --- | --- | --- |
| report_manifest | 16표 존재·행수·기록된 input/output SHA256 | 일치 |
| 표1 | OBS 원 지수·CI·등급과 Ridge combined J·N·shift | 일치; OBS CI가 Ridge/BCAP로 복사되지 않음 |
| 표2–9 | 개발 카운트·셀의 원 action 수치, 비율 여집합, 평가 방향, 최종 정책 p1 | 일치 |
| 표10 | 주 5개 실행 여섯 정책 가치·gain·단위·지지 분모, SWING 보류 행 | 일치 |
| 표11–12 | 원 propensity/calibration/support/fit/metrics 및 known/unseen, 고정 개발 예측 진단 분리 | 일치 |
| 표13–14 | 외부 action·정책 결합값, 외부 CF vs fixed-development metrics, WITHHELD 행 | 일치 |
| 표15 | 원 sensitivity 및 두 모델 bootstrap summary | 일치 |
| 표16 | 원 UNCERTAIN/NO_SUPPORT 행, WITHHELD, full-learning 구간미산출2건, JOINT미설계 | 일치 |
| 본문 | 12카운트의 OBS/Ridge, 개발24문장, 완료 외부36문장, 모든 개발SWING셀 표 수치 | 인쇄 정밀도에서 일치 |
| 행동 문서 | 5개 실행×12카운트=60행, 실제/후보 행동비율·%p·기대불일치·PA·경기 | 저장 A/support와 해당 outer/최종 정책에서 독립 복원 후 원 보조표·문장과 일치 |
| 봉인 후 비교 | 108개 count/cell paired 행 및 8개 방향·Pearson·Spearman 요약 | 원 실행 Δ·등급·최종정책에서 독립 계산해 일치 |

총 98,357개 셀/구조/표시 비교, 실패 0. 최대 절대오차는 2.9103830456733704e-11이며 ESS 등의 CSV 재표현 차이로 허용오차 안이다. 미산출 NaN은 양쪽 미산출로 대조했고 0으로 대치하지 않았다. 결과는 `report_tables_validation.json`, 상세 비교는 `report_tables_comparisons.csv`, 독립 행동 비율은 `behavior_independent_rates.csv`, 입출력 해시는 `report_tables_evidence_manifest.json`에 저장했다.

행동 비교의 개발 후보는 각 outer 훈련에서 학습한 정책이고 외부 후보는 개발 최종 정책이다. `d`를 평가 효과에서 다시 고르지 않고 저장 정책과 평가 fold에서 재구성했으며, scores의 policy_p1과 모든 행에서 일치했다. 기대 불일치율은 A=1이면 1−d, A=0이면 d의 평균으로 계산했다. 보수 정책은 관찰 행위 유지이므로 실제 비율과 같고 불일치 0이다.

주 다중비교 가족은 Δ 209개+6정책 gain 1,254개=1,463개로 상한 1,536 안이다. value의 CI95는 개별구간이고 주 가족을 전체 출력으로 확장하지 않았다. 외부 상관은 상태별 무가중값이며 Spearman에는 평균 동률 순위를 사용했다. 2023/2026 지원 집단은 서로 다르며 외부 방향과 저장 정책 행동의 일치율은 최적정책 정답률이 아니다. SWING 카운트 평균에는 한 개의 정책 행동이 없으므로 이 비교를 N/A로 둔 처리도 맞다.

이 검사는 **원 실행 값의 보고 전달과 별도 행동 비율/상관 산술**을 확인했다. 원행 Y/A 계보, nuisance 적합의 정확성, 통계적 식별 및 95% 포함률은 별도 범위다. 원 결과 자체의 정확성을 표 복사 일치로 대신하지 않는다. 신규 raw 자료·정책 학습·외부 모델 평가를 실행하지 않았다.
