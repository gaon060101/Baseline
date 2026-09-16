# BCAI-OBS-v1.0.0

Ball Count Advantage Index Observed · 볼카운트 관찰 유불리 지수  
상태: VALIDATED · 칼럼의 주 분석 모델. 검증 범위는 아래 실행과 구현 점검이며 인과성·KBO·미래 일반화의 보증이 아니다.

## 목적과 질문

“투구 전 카운트 c에 도달한 타석은 시작점보다 어느 정도의 최종 가중 공격가치를 남겼는가?” 실제 도달 집단의 관찰 평균을 비교한다.

## 공식과 변수

- W_i = Σ_e w_{e,y} 1(event_i=e). e는 1B, 2B, 3B, HR, 비고의 BB, HBP. K·OUT·OTHER=0.
- R_ic: PA i에서 카운트 c가 관측되면 1. N_yc=Σ_i R_ic.
- V_yc=Σ_i R_ic W_i/N_yc. V_y0는 시즌별 0-0 평균. q_y=N_y0/Σ_y N_y0.
- I(c)=100×Σ_y q_y V_yc/V_y0.
- 보조 100D(c)=100×Σ_y q_y(V_yc−V_y0)/scale_y.
- E(c)=100+100×Σ_y q_y(V_yc−V_y0)/(scale_y×R/PA_y). E에 I의 등급을 적용하지 않는다.

가중치·기준 평균·혼합비의 실행별 정확한 값은 [실행 manifest](../../../../columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/manifest.json)의 parameters, 분류와 경계 포함 규칙은 [명세](specification.yaml)에 있다. YAML은 JSON 호환 YAML 1.2 문서이며 코드가 자동 읽는 설정은 아니다.

## 결과 해석

100은 관측 시작점 평균이지 50:50 승률이 아니다. I=120은 가중 공격가치가 시작점 대비 20% 높다는 뜻이다. 연속 지수·구간이 우선이고 ±5/15는 설명용 경계다. 명목 grade와 동시 구간 기반 confirmed_grade를 구분한다. 95<I<105만 명목 중립이며 정확한 경계 포함과 순차 판정은 명세를 따른다.

## 적용 범위와 제외 기준

현재 검증 실행은 MLB 2024·2025 정규시즌. 다른 리그에는 필드·분모·자체 가중치 검증이 선행되어야 한다. 마지막 기록이 결측, 고의볼넷, 타격방해, truncated, 미분류 event, 시작 0-0 미관측이면 제외한다. 희생번트는 포함하여 공식 wOBA와 분모가 다르다. OTHER는 실책 출루·아웃 없는 야수선택으로 아웃이 아니다. 원본 중복 투구 키는 오류로 중단하고 PA×count는 한 번만 집계한다. 자동 판정도 count 관측에 포함하나 실제 구종 설명 표에서는 제외한다.

## 불확실성 계산법

시즌 내 경기 단위 2,000회 복원추출, seed 20260907, q와 외부 가중치 고정. 같은 추출을 모든 count에 공유하고 매번 0-0 평균 재계산. 개별 CI는 2.5/97.5 백분위. 동시 CI는 11개 비기준 count의 |(I_boot−I)/SE| 최대값의 95백분위를 임계값으로 I±임계값×SE, SE의 ddof=1. 0-0=[100,100]. 쌍 차이 구간은 개별 비교이며 66쌍 동시 보장이 아니다.

## 검증 결과

유효 364,124 PA·4,859경기. 독립 재집계 1e-9 이내 일치 등 기존 6개 검증 통과. 0-2 63.99, 3-0 175.40. [검증 문서](validation.md)와 원 결과를 따른다. 이번 구조 변경에서는 모델을 다시 적합하지 않았다.

## 알려진 한계와 사용하면 안 되는 해석

도달 집단 선택 편향, 미측정 교란, 경기 간 동일 선수 의존성, 가중치 추정 오차가 남는다. 득점·승률 증가, 최적 구종·초구 공략의 인과효과, 절대 리그 실력, 공식 wOBA/wRC+/RE24, 미래 예측이라고 쓰지 않는다. Ridge 이동이 작아도 이 한계가 제거되지 않는다. 이전 기본 표의 366,231 PA와 분석 분모를 섞지 않는다.

## 관련 코드와 결과

- [공동 계산 코드](../../../../columns/001-ball-count/analysis/analyze_count_advantage.py): OBS와 Ridge를 함께 계산하는 기존 구현. 독립 OBS 전용 실행기로 오인하지 않는다.
- [검증 코드](../../../../columns/001-ball-count/analysis/verify_count_advantage.py), [보고서 생성 코드](../../../../columns/001-ball-count/analysis/write_advantage_report.py).
- [실행 결과](../../../../columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/README.md), [상세 보고서](../../../../columns/001-ball-count/analysis/count_advantage_2024_2025.md), [인계](../../../../columns/001-ball-count/analysis/handoff_count_advantage.md).
