# 분해 입력 계약 — BCAP-DECOMP-v0.1.0

현재 상태는 **DRAFT, 구성요소 적합기 미구현**이다. `compose.py`는 이미 만든 구성요소 예측을 읽어 산술 합성과 소규모 입력 검사를 수행한다. 실제 MLB 분석 결과는 없다. 완성된 모의 예제는 [모의 입력](../../../../columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r01/artifacts/synthetic_input.json)에 있다.

JSON 최상위 필드는 `schema_version="1"`, `synthetic`(참/거짓), `fit_provenance`(적합 기록 경로·설명), `outcome_definition`, `fold_training_games`, `reference_rows`, `predictions`다. 결과 정의는 `kind="final_PA_W"`, `unit="season_weighted_final_PA_W"`, `weight_manifest_sha256`(가중치 정의 SHA256)를 요구한다. 모의 입력의 0으로 채운 해시는 실제 가중치 파일이 아닌 시험용 표식이다. 해시 형식을 검사하지만 대상 가중치 파일의 내용·동일성까지 자동 검증하지 않는다.

`reference_rows`의 각 행은 문자열 `row_id`, `game_pk`, `at_bat_number`, `pitch_number`, `outer_fold`, `count`, 정수 `season`, 목록 `regions`, 실제 라벨 `observed_description`을 가진다. 한 경기는 한 평가 fold에만 속한다. `fold_training_games`는 fold 문자열을 훈련 경기 ID 문자열 목록에 연결한다. 평가 경기와 자기 훈련 경기의 중복을 거부한다. 훈련 안에서 전처리·범주·튜닝·교정이 이루어졌는지는 별도 적합 기록으로 확인해야 한다.

각 참조행은 `action="Take"`와 `action="Swing"`의 예측을 각각 하나씩 가져야 한다. 예측의 `row_id`와 `prediction_fold`가 참조행과 맞아야 한다. `branches`에는 명세의 해당 행동 모든 가지를 넣는다. 각 가지의 `p`는 유한한 [0,1] 확률, `mean_W`는 그 가지 이후 최종 PA W의 조건부 예측, `supported`는 상위 적합기의 지원 판정이다. 양의 확률에 값이나 지원이 없으면 중단하며 임의의 0을 넣지 않는다. 확률이 0인 가지에만 빈 값을 허용한다. 확률 합을 강제로 다시 맞추지 않는다.

먼저 **행별 Σ(확률×조건부 W)**를 구하고, 같은 참조행에서 평균한다. 평균 확률과 평균 조건부 값을 따로 곱하면 다른 계산이다. `direct_mean_W`를 넣으려면 모든 행의 두 행동에 함께 넣어야 한다. 두 방식의 직접 결과 회귀 평균만 대조하며 AIPW와 비교했다고 쓰지 않는다. 이 입력에는 최종 관측 Y가 필요하지 않으며 AIPW를 계산하지 않는다.

`CENTER`는 존 안 전체, 나머지는 존 밖 상·하·몸쪽·바깥쪽이다. 모서리의 두 집합 소속을 허용하지만 전체·카운트 평균에서 행을 복제하지 않는다. 빈 위치·측정 정합성 문제·적격 표본 선택은 상위 생산자가 해결해야 한다. 코드가 위치 라벨의 물리적 정당성이나 전체 제외 분모를 새로 입증하지 않는다.

`hit_into_play`는 번트 인플레이도 포함할 수 있어 비번트라고 부르지 않는다. 체크스윙을 독립 식별하는 정보는 없으며 기존 판정 라벨만 따른다. HBP를 Take 가지로 유지하는 것은 기존 모델의 분류를 따른 것이지 자발적 테이크 의도가 확인됐다는 뜻이 아니다. 삼진·볼넷·실책·낫아웃은 최종 PA 결과 정의를 통해 W에 연결하고, 현재 description만으로 임의 종료 보상을 넣지 않는다. 파울은 파울 가지의 최종 W를 예측한다.

실제 적합 전에는 같은 기존 적격·관측 조건과 선수 축소 보정을 적용하는 **분기 확률 모형 및 분기별 결과 회귀의 선택**, 희소 가지의 부분 풀링·지원 기준, 훈련 내부 교정, 동일 OOF 행의 직접 회귀 비교, 경기 의존성과 구성요소 재학습 불확실성, 주요 비교 범위를 고정해야 한다. 이 인터페이스의 PASS는 그러한 통계 설계나 실증 검증의 PASS가 아니다.

실행 예시(출력은 새 파일이어야 한다):

```powershell
python -B models/bcap/decomposition/v0.1.0/compose.py --input component_predictions.json --output new_composed_values.json
```

출력은 집계 JSON이다. `observed_action_predictive_diagnostics`는 관측 행동의 Brier·로그손실이며 교정 곡선이나 관측하지 못한 반대 행동의 정확도가 아니다. 개인별 순위·추천·구간·Nash 균형은 만들지 않는다.
