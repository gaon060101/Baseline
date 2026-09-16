# BCAP 훈련 분리·정책 복원·기존 적합 객체 독립 검수

검사 시간: 2026-09-09T09:10:29.843874+00:00 ~ 2026-09-09T09:15:00.884650+00:00. 이 하위 보고서는 전체 검수의 훈련/평가 분리, 정책 학습 자료, 저장 final nuisance의 정확한 재현만 담당한다. 원자료 선택·행동 정의·주 AIPW/OPE 집계·통계 방법론의 종합 판정은 상위 보고서를 따른다.

## 판정과 실제 수행 범위

분할표·정책 학습/적용 및 보존된 개발 최종 적합 객체의 외부 예측 재현은 **명시 범위 내 사용 가능**이다. 검사 1,513건 PASS, 0건 FAIL, 5건 NOT_VERIFIABLE이다. 추가 결측/unknown 코드 확인 48건에서 FAIL은 없다. PASS 개수는 세분화한 검사 수이며 독립된 실험 횟수나 통계적 보장의 크기가 아니다.

개발 outer/inner/튜닝 및 외부 nuisance의 적합 객체가 없으므로, 그 객체의 예측·사전·실제 최적화 잔차까지 포함한 전체 적합 정확성은 **증거 부족으로 판정 보류**다. 저장된 수렴 로그와 코드를 확인한 일을 전 적합의 독립 재계산으로 확대하지 않았다.

기존 집계·분할의 재합산, 저장 Y/A/p/mu에서 정책 복원, 기존 적합 객체의 예측 재생성과 기존 계수의 정상방정식 평가만 수행했다. `models/bcap/run.py`, `verify_bcap.py` 및 기존 핵심 계산 함수는 import/호출하지 않았다. NumPy/pandas로 새 코드를 썼고, pickle의 모델 클래스는 실행 메서드가 없는 안전한 Container로 대체했다. 재학습·새 외부 모델 평가·SWING 2026 평가·신규 원자료 수집·기존 파일 수정은 수행하지 않았다. unknown 한 블록 예시는 기존 적합값의 코드 동작 확인용 합성 입력 fixture이며 새 외부 성과 비교가 아니다.

## 확인한 계산

| 대상 | 독립 확인 범위 | 결과 |
| --- | --- | --- |
| 개발 2건·외부 3건, 97개 분할 기록 | seed 규칙에서 경기 fold를 새로 생성, 역할별 train/evaluation 집합·모든 outer/inner 상위 holdout 배제 | 불일치 0 |
| 개발 outer와 최종 정책 OOF 자료 | 원 정제본의 실제 해당 훈련행 키/A/Y/선수/count, inner 경기 배정, 양 행동 30회 repertoire와 known | 불일치 0 |
| 336개 정책 상태 | 저장 phi 평균을 재사용하지 않고 Y/A/p/mu에서 delta·표본·경기 수·엄격 부호 규칙을 재구성 | 최대 delta 차이 1.11e-16; 선택 행동 불일치 0 |
| 개발 outer 평가·외부 평가/고정예측 | outer마다 해당 outer 정책, 외부는 개발 최종 정책, fallback .5 및 보수 H=0/기여Y | 불일치 0 |
| 276개 저장 적합/보정 로그 | 훈련행 수·알파 후보·loss 기반 선택/동률시 큰 alpha·적용 alpha·로그상 수렴 | 불일치 0; 실제 중간 적합계수는 미보존 |
| 외부 고정 개발 예측 3건 2,067,593행 | final 계수·훈련 사전에서 raw propensity/p/mu0/mu1·known/repertoire/measurement/support | raw/mu0/mu1 최대차 0; p 최대차 2.22e-16; 표지 불일치 0 |
| 개발 final Ridge 6개 | 실제 해당 훈련행으로 사전·중심화·비벌점 절편·양 선수 효과·목적함수·정상방정식 잔차 | 상대 잔차 최대 1.50821e-09, 명세 한도 1e-7 충족 |
| final Platt 보정 2개 | 훈련에서 별도로 떼어 둔 calibration 경기의 목적함수와 gradient 재계산 | loss 저장치와 차이 0; gradient 최대 PITCH 4.57641e-11, SWING 1.94423e-11 |

정책 상태의 정확한 동률은 관측되지 않았다. 새 계산의 `<0`/`>0` 규칙과 원 코드 `run.py:149`의 엄격 비교는 정확한 0에서 action0을 선택한다. `run.py:157`의 미관측/지지 없는 Z fallback=.5와 실제 관측 메커니즘 유지 기여 Y는 서로 다른 동작이며, 저장 평가 행에서 각각 일치했다. 정책에 저장된 훈련용 `conditional_low/high`를 이 하위 검사에서 별도로 재계산하지는 않았다. 이 항목은 상태별 delta·선택 행동 복원과 구분한다.

선수 효과는 outcome의 각 행동별 실제 훈련 사전에 투수·타자 ID가 모두 있으며, 모든 category coefficient에 alpha 벌점이 포함된다. final 모델의 사전·빈도 중심화는 실제 훈련행에서 독립 복원됐다. unseen 범주 한 블록은 0을 더하고 다른 선수/상황 블록은 남는다. 예를 들어 PITCH 2023 propensity의 개발 미관측 투수 행 68,125개는 모두 절편 하나와 다른 예측이었다. 외부 `known_*`는 외부 재적합 사전이 아니라 최종 개발 roster를 기준으로 했고, repertoire는 각 OPE 훈련 fold에서 별도로 계산됐다. 선수 개인 효과는 구종별 품질·당일 컨디션·목표 위치·의도 등 미측정 교란의 제거를 뜻하지 않으며, 선수 수준의 양 행동 30회는 세부 상황별 positivity를 보장하지 않는다.

## 실제 final 목적함수 재계산

| 모델 | 성분 | 훈련행 | alpha | 독립 상대 정상방정식 잔차 | 목적함수 |
| --- | --- | ---: | ---: | ---: | ---: |
| PITCH | prop | 1,130,737 | 100 | 1.50821e-09 | 254129.072675380 |
| PITCH | m0 | 631,341 | 1000 | 7.89582e-10 | 147113.772455187 |
| PITCH | m1 | 784,225 | 1000 | 2.71233e-10 | 185749.032420451 |
| SWING | prop | 1,131,023 | 100 | 8.45816e-10 | 192674.534771352 |
| SWING | m0 | 737,453 | 1000 | 4.40477e-10 | 161800.729854177 |
| SWING | m1 | 678,590 | 1000 | 8.19754e-10 | 165290.601109693 |

잔차는 원 엔진의 sparse Gram/PCG 계산을 호출하지 않고, 훈련행 예측 잔차와 각 범주별 `bincount`로 `(X-Xbar)^T residual + alpha beta`를 구성했다. 목적함수는 실제 훈련 잔차 제곱합과 alpha×계수 제곱합이다. 기존 수렴 로그의 자기 보고와 구분되는 실제 저장 계수 검산이며, 계수를 다시 적합하지 않았다. final 목적함수 자체는 원 로그에 없으므로 본 검수값으로 새로 남겼다. 최종 Platt의 실제 gradient도 작았지만 모든 중간 calibrator의 `opt.success`를 1e-10 gradient 충족의 증거로 해석하지 않았다.

## 정확한 증거 위치와 남은 범위

- 현재와 실행 당시 코드: 5개 주 실행 `artifacts/frozen_run.py`의 SHA256은 모두 `2ca51aab6398774ff619c10f19566ef7cf287520e6c356af3f4b32858e3562c9`이며 현재 `models/bcap/run.py` 및 각 manifest의 code 해시와 일치한다. 각 configuration은 실행 당시 specification과 같다. `source_evidence.json`에 전체 경로와 시각이 있다. 이 확인은 현재 해시 일치이며, 이 하위 보고서 자체로 모든 과거 미변경을 증명하지 않는다.
- 훈련 사전/중심화와 shrinkage: `models/bcap/run.py:41`, `:63`, `:95`, `:122`. 독립 실제 final 검산은 `checks.csv`의 `final_dictionary_*`, `final_actual_normal_equation/*` 행 및 `final_actual_fit_diagnostics.csv` 2~7행.
- 튜닝/보정/상위 holdout: `models/bcap/run.py:95`, `:119`, `:164`, `:174`. 실제 분할·전 훈련 크기 결과는 `checks.csv`의 `fold/`, `ancestor_holdout/`, `fit_training_size/`, `fit_alpha/` 행.
- 정책: `models/bcap/run.py:149`, `:157`, `:174`, `:258`, `:298`, `:304`; 원 정책과 `independent_policies.csv`의 run_id/policy/state 키, `checks.csv`의 적용확률 행을 대조했다.
- 외부 고정/재적합 역할과 known: `models/bcap/run.py:295`~`:307`. `fixed_development_predictions.pkl`의 nuisance는 개발 final 모델이고, `scores.pkl`의 nuisance는 외부 교차 적합이다. 이번 실제 예측 재생성은 앞쪽만 가능했다. 서로 다른 지원 집단의 성과를 같은 대상의 직접 비교로 인증하지 않았다.
- 보존 범위: 개발 artifacts에는 `final_nuisance.pkl`만 적합 객체이며, 외부 artifacts에는 `scores.pkl`, `fixed_development_predictions.pkl`만 있다. 237개 nonfinal/tuning Ridge 및 31개 nonfinal calibrator의 실제 계수/훈련 점수는 이 산출물에서 독립 재검산할 수 없다. 튜닝 저장 loss에서 선택을 복원한 결과와 loss 자체를 다시 계산한 결과는 다르다.

## 제작 작업에 돌려보낼 요청

`F-FOLD-01`(주요 수정·증거 부족): 검증 문서에서 저장 예측의 산술 일치와 적합 객체부터의 예측 재생성을 명확히 분리하고, 중간 적합 객체 미보존으로 남은 범위를 명시한다. 향후 실행에는 튜닝/outer/inner/외부 nuisance의 계수·훈련 사전·calibrator·선택된 alpha·훈련행 해시와 실제 잔차를 보존한다. 이 검수에서 발견된 산술 불일치는 없으므로 즉시 전체 재학습할 필요는 확인되지 않았다.

전 적합 정확성의 인증을 추가로 요구한다면 먼저 개발 자료만으로 PITCH/SWING 각각 outer0의 evaluation nuisance와 inner0 nuisance를 기존 경기 seed/명세 그대로 새 검수 실행 ID에 재현하고, 계수·사전·calibration 입력·예측·잔차를 저장해 해당 기존 scores와 비교한다. 기존 성공 개발 전체 소요 약 8분(PITCH), 13분(SWING)은 비용 참고값이며 현재 환경 재측정 없이 동일 소요를 보장하지 않는다. 외부 계수를 재적합해 평가하는 단계는 별도 범위·새 실행 ID·외부 재노출 기록이 필요하며 이번에는 시작하지 않았다. 동일 설계 재현은 새 실행이고, 변수/추정대상/보정 변경이 생기면 프로젝트 규칙에 따른 새 모델 버전도 필요하다.

`F-FOLD-02`(주요 수정·알려진 한계): 개인 효과 보정과 broad repertoire를 상황별 교환가능성/positivity 또는 행동 추천의 증거로 확대하지 않는다. 이는 현재 구현 오류가 아니라 남는 식별 한계이며, 정책 권고를 가능하게 하려면 추가 자료·식별 설계가 필요하다. 설명을 더 정확하게 만드는 문서 보완과 결과에 영향을 주는 설계 변경을 구분한다.

## 재현·환경·보존

명령은 `execution.log`, `supplement_execution.log` 및 `evidence_manifest.json`의 argv/환경을 따른다. Python 실행 시 `-B`로 기존 pycache를 만들거나 바꾸지 않았다. `review_protocol.json`에 결과 전 선언한 허용오차를 그대로 사용했다: 키/표지/fold/행동수는 정확 일치, 정책 delta는 atol1e-10/rtol1e-9, 기존fit 예측은 atol1e-8/rtol1e-8. 외부 저장 p/mu/raw 예측의 비유한 값은 0이며 NaN을 0으로 대치하지 않았다. 새 보고/비교/검사 코드만 이 `folds_prediction/` 안에 저장했다.
