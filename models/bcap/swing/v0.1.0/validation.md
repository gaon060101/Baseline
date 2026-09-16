# BCAP-SWING-v0.1.0 검증

상태: **EXPERIMENTAL**. 실제 기록 기준 2026-09-09T08:49:31.268706+00:00. 적합·독립 수치 검산과 명시한 외부 진단을 완료했다. 인과 효과·실시간 정책·행동 추천은 검증되지 않았다.

| 모델 | 범위 | 실행 상태 | 적격 행 | 공통 지지 행 | 전체 판정 | 완료 UTC | 실행 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SWING | 2024·2025 개발 | COMPLETE | 1,416,043 | 1,354,516 | UNCERTAIN | 2026-09-09T06:10:20.553139+00:00 | [bcap_swing__mlb_2024_2025__20260909__r01](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260909__r01/manifest.json) |
| SWING | 개발 전체 재학습 8회 | COMPLETE | 해당 없음 | 해당 없음 | 등급 없음 | 2026-09-09T08:45:24.101853+00:00 | [bcap_swing__mlb_2024_2025__20260909__r02](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260909__r02/manifest.json) |
| SWING | 2023 재현 | COMPLETE | 716,385 | 682,953 | UNCERTAIN | 2026-09-09T06:20:48.704321+00:00 | [bcap_swing__mlb_2023__20260909__r01](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2023__20260909__r01/manifest.json) |
| SWING | 2026-09-07까지 | WITHHELD | 해당 없음 | 해당 없음 | 등급 없음 | 2026-09-09T06:15:29.151986+00:00 | [bcap_swing__mlb_2026_ytd_20260907__20260909__r01](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2026_ytd_20260907__20260909__r01/manifest.json) |

## 수치·자료 분리 검사

| 실행 | 적합/보정 기록 수 | 분할 기록 수 | 자기 훈련/평가 교집합 | 전부 수렴 | 기록 |
| --- | --- | --- | --- | --- | --- |
| bcap_swing__mlb_2024_2025__20260909__r01 | 120 | 35 | 0 | True | [수렴](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260909__r01/artifacts/fit_diagnostics.csv) |
| bcap_swing__mlb_2023__20260909__r01 | 12 | 9 | 0 | True | [수렴](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2023__20260909__r01/artifacts/fit_diagnostics.csv) |

독립 검산은 주 실행기의 AIPW 행 점수를 가져다 평균하는 데 그치지 않고 별도 OPE 식을 통해 부호·분모·단위·키·fold 및 개발 정책 학습과 상위 holdout 분리를 대조한다. 상세 허용오차·최대 차이는 다음 원 기록을 따른다.

- [swing_development_complete_validation.json](../../../../columns/001-ball-count/analysis/bcap_implementation_review_20260909/swing_development_complete_validation.json): PASS
- [swing_2023_external_validation.json](../../../../columns/001-ball-count/analysis/bcap_implementation_review_20260909/swing_2023_external_validation.json): PASS

전체 재학습 8회에서 저장 복제 키·집계·최종 안정성 요약의 독립 대조는 [bootstrap 최종 독립 검산](../../../../columns/001-ball-count/analysis/bcap_implementation_review_20260909/bootstrap_final_validation.json)에서 PASS를 확인했다. 이는 저장 산출물 재구성 검산이며 완전한 학습 신뢰구간이나 추천 승격의 근거가 아니다.

## 불확실성·정책 판정

주 구간은 고정 OOF 점수의 경기 군집 조건부 구간과 Bonferroni 1,536 가족 범위다. 각 모델의 8회 전체 재학습은 매 반복의 전처리·튜닝·calibration·nuisance·정책 선택을 다시 수행한 안정성 진단이며 최종 개발 정책의 완전한 95% 신뢰구간이 아니다. 경기 간 선수·시리즈 의존성과 동률 근처 선택도 남는다. known/unseen·IPW·Hájek·g-computation·추가 calibration·민감도와 보조 구간은 별도 진단이다. NO_SUPPORT는 실행된 비교의 표본·공통 지지 부족, UNCERTAIN은 지원된 비교에도 식별·학습 불확실성 근거 부족을 뜻한다. 미실행·측정 보류에는 표본 판정 등급을 부여하지 않는다. 모든 추천 행동은 비어 있고 보수 정책은 전 영역에서 실제 행동을 유지한다.

PITCH는 현재 한 구 FB/NFB의 최종 PA 공격가치 비교이며 현재·직전 좌표를 입력하지 않는다. SWING은 번트 포함 기록상 공격 시도/판정상 Take의 사후 공 특성 조건부 진단이다. 명시적 scored HBP는 Take로 포함하지만 불명 라벨을 Take로 대치하지 않는다. 타자의 실시간 지각·구종 품질·컨디션·의도·미측정 교란은 식별되지 않았다. 같은 실제 선수·상황 행에 양 행동을 적용했으며 가상 평균 선수 예측으로 대체하지 않았다. 완료 PA·IBB·최종 결과 결측 제외는 사후 선택을 포함한다. 행별 차이를 합쳐 PA 전체 정책의 개선량으로 보고하지 않는다.

SWING의 2026 위치·존 정합성이 확보되지 않았으므로 대리 분석으로 채우지 않고 WITHHELD로 남겼다. 이것은 외부 성과가 나빠 실패한 결과나 표본 NO_SUPPORT 판정이 아니다.

[독립 검수 의견·보조 진단](../../../../columns/001-ball-count/analysis/bcap_implementation_review_20260909/review.md) · [실행·코드·입출력 해시·명령 증거](../../../../columns/001-ball-count/analysis/bcap_execution_evidence_20260909.json) · [주 결과 보고서](../../../../columns/001-ball-count/analysis/bcap_v010_report_20260909.md)
