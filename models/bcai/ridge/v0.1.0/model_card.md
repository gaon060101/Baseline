# BCAI-RIDGE-v0.1.0

Ball Count Advantage Index Ridge Adjusted · 볼카운트 Ridge 보정 유불리 지수  
상태: EXPERIMENTAL · 관찰 지수의 탐색적 민감도 모델. OBS의 후속 대체 모델이 아니다.

## 목적과 답하는 질문

“시작 시점 선수·상황의 예상 기본값을 잔차화하면 관찰 지수가 얼마나 이동하는가?” 선택 편향 제거 여부를 입증하거나 미래 성적을 예측하는 질문이 아니다.

## 공식과 변수 정의

W, V_y0, q_y, PA 도달 정의는 [OBS 명세](../../observed/v1.0.0/specification.yaml)를 참조한다.
z_i=W_i/V_y0; m̂_{−fold}(X_i)=절편+Σ_j β_j[X_ij]; e_i=z_i−m̂_{−fold}(X_i).
J(c)=100+100×Σ_y q_y[mean(e|y,c)−mean(e|y,0-0)].
훈련 목적은 Σ(z−m̂)^2+αΣβ²이며 절편은 비벌점이다. PA 첫 기록의 타자×시즌·투수×시즌·좌우·실제 구장×시즌·점수 차·8개 주자 상태·아웃·10회 이상 통합 이닝·시즌을 사용한다. score_bin은 (-∞,-4],(-4,-1],(-1,0],(0,3],(3,∞)이다.

경기 단위 무작위 5분할 교차 적합. 같은 경기는 한 fold에만 배정한다. 전체 표본의 V_y0로 정규화하며 fold별 기준은 아니다. 전체 표본 범주 인코딩, 훈련에 없는 수준 효과는 0. RNG는 OBS 부트스트랩 이후 상태를 이어 사용하므로 Ridge만 따로 seed를 재설정하면 과거 fold를 재현하지 못한다. α=20/100/500을 모두 공개하며 중심 α100은 최적화된 값이 아니다. [명세](specification.yaml)에 변환과 반복 조건을 보존했다.

## 결과 해석과 적용 범위

J(0-0)=100으로 잔차 중심을 고정한 진단 지수다. OBS와의 지수 포인트 차이를 비교한다. 보정값에 OBS의 grade·신뢰구간을 붙이지 않는다. 현재 MLB 2024·2025 표본 내부 교차 적합만 수행했고 시간외·KBO 검증은 없다.

## 제외 기준

[OBS](../../observed/v1.0.0/model_card.md)와 같은 364,124 PA. 마지막 결과·0-0·중복 처리 규칙 공유. 문맥은 타석 시작 선수와 상황으로, 타석 도중 교체에도 시작 효과를 쓴다.

## 불확실성 계산법

모형 재적합 신뢰구간은 미산출. α별 점추정·교차 적합 MSE·수렴 진단만 제공한다. OBS 부트스트랩은 J의 불확실성이 아니다.

## 검증 결과

α100 최대 이동 1.77포인트. OOF MSE 2.7048340310431147, 상수 기준 MSE 2.712496201602141, 개선 약 0.28%. 모든 15개 적합은 150회 한도, 1e-7 정지 기준 미충족. 전체 최대 최종 변화 1.0800681081502006e-05. [검증 문서](validation.md)에 정확한 α별 진단을 연결한다.

## 알려진 한계와 사용하면 안 되는 해석

수렴 기준 미달·설명력 제한·누락 교란·상호작용 미반영·희귀 수준·도달 선택 편향이 남는다. 완성된 인과 모형, 미래 예측 모형, 공통 집단으로 완전히 표준화한 반사실, IPW 추정으로 분류하지 않는다. 작은 이동을 교란 제거의 증거라고 쓰지 않는다.

## 관련 코드와 결과

- [공동 계산 코드](../../../../columns/001-ball-count/analysis/analyze_count_advantage.py)의 oof_ridge와 adjusted 계산.
- [Ridge 실행](../../../../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2024_2025__20260907__r01/README.md), [실행 manifest](../../../../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2024_2025__20260907__r01/manifest.json).
- 원 CSV의 adjusted_index_alpha20/100/500과 audit.model만 Ridge 산출로 해석한다. 나머지 index·CI·grade는 OBS 소유다.
- [상세 보고서](../../../../columns/001-ball-count/analysis/count_advantage_2024_2025.md), [인계](../../../../columns/001-ball-count/analysis/handoff_count_advantage.md).
