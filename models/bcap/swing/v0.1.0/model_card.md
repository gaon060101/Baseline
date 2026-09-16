# BCAP-SWING-v0.1.0

상태: **EXPERIMENTAL**. 갱신 시각 2026-09-09T08:49:31.268706+00:00. 실제 구현·적합·검산·명시 범위 외부 진단 완료. 행동 추천 없음.

목적: 같은 상태·사후 공 특성의 번트 포함 Swing/판정상 Take 비교. 개발 2024·2025. 2023 외부 재현 완료; 2026 위치·존 측정 정합성 부족으로 전체 평가 보류. 기존 OBS/Ridge의 검증 상태를 전용하지 않는다.

모델은 DRAFT에서 시작했다. 봉인된 specification.yaml의 status_at_definition=DRAFT는 최초 정의 시점의 역사이며 현재 카드·레지스트리의 EXPERIMENTAL과 충돌하지 않는다. 명세·코드·정책 해시는 이 문서 갱신으로 바꾸지 않았다.

PITCH는 현재 한 구 FB/NFB의 최종 PA 공격가치 비교이며 현재·직전 좌표를 입력하지 않는다. SWING은 번트 포함 기록상 공격 시도/판정상 Take의 사후 공 특성 조건부 진단이다. 명시적 scored HBP는 Take로 포함하지만 불명 라벨을 Take로 대치하지 않는다. 타자의 실시간 지각·구종 품질·컨디션·의도·미측정 교란은 식별되지 않았다. 같은 실제 선수·상황 행에 양 행동을 적용했으며 가상 평균 선수 예측으로 대체하지 않았다. 완료 PA·IBB·최종 결과 결측 제외는 사후 선택을 포함한다. 행별 차이를 합쳐 PA 전체 정책의 개선량으로 보고하지 않는다.

주 구간은 고정 OOF 점수의 경기 군집 조건부 구간과 Bonferroni 1,536 가족 범위다. 각 모델의 8회 전체 재학습은 매 반복의 전처리·튜닝·calibration·nuisance·정책 선택을 다시 수행한 안정성 진단이며 최종 개발 정책의 완전한 95% 신뢰구간이 아니다. 경기 간 선수·시리즈 의존성과 동률 근처 선택도 남는다. known/unseen·IPW·Hájek·g-computation·추가 calibration·민감도와 보조 구간은 별도 진단이다. NO_SUPPORT는 실행된 비교의 표본·공통 지지 부족, UNCERTAIN은 지원된 비교에도 식별·학습 불확실성 근거 부족을 뜻한다. 미실행·측정 보류에는 표본 판정 등급을 부여하지 않는다. 모든 추천 행동은 비어 있고 보수 정책은 전 영역에서 실제 행동을 유지한다.

X는 양 nuisance 보정 입력, Z는 정책 허용 상태다. PITCH Z는 count, SWING Z는 count×zone×FB/NFB다. 양 nuisance의 투수·타자 효과를 Ridge로 축소하며 행동별 outcome T learner와 별도 훈련 경기에서 Platt 보정한 propensity를 썼다. 경기 outer3/inner2에서 정책 학습과 평가를 분리했다. 외부 고정 개발 nuisance의 예측 성능과 외부 교차 적합 nuisance를 이용한 고정 개발 정책 OPE는 별도 산출물이다.

[봉인된 기계 명세](specification.yaml) · [실제 검증 범위](validation.md) · [설계 변경 근거](../../design_decisions.md) · [측정 근거](../../measurement_review.md) · [16종 표·카운트별 보고서](../../../../columns/001-ball-count/analysis/bcap_v010_report_20260909.md)

| 모델 | 범위 | 실행 상태 | 적격 행 | 공통 지지 행 | 전체 판정 | 실행 |
| --- | --- | --- | --- | --- | --- | --- |
| SWING | 2024·2025 개발 | COMPLETE | 1,416,043 | 1,354,516 | UNCERTAIN | [bcap_swing__mlb_2024_2025__20260909__r01](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260909__r01/manifest.json) |
| SWING | 개발 전체 재학습 8회 | COMPLETE | 해당 없음 | 해당 없음 | 등급 없음 | [bcap_swing__mlb_2024_2025__20260909__r02](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260909__r02/manifest.json) |
| SWING | 2023 재현 | COMPLETE | 716,385 | 682,953 | UNCERTAIN | [bcap_swing__mlb_2023__20260909__r01](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2023__20260909__r01/manifest.json) |
| SWING | 2026-09-07까지 | WITHHELD | 해당 없음 | 해당 없음 | 등급 없음 | [bcap_swing__mlb_2026_ytd_20260907__20260909__r01](../../../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2026_ytd_20260907__20260909__r01/manifest.json) |

새 입력 적용은 새 실행 ID를 사용한다. 결과에 영향을 주는 설계 변경은 새 버전을 만들고, 이미 본 2023·2026을 최초 독립 검증이라고 부르지 않는다. KBO·Drive·외부 게시 범위는 이번 실행에 없다.
