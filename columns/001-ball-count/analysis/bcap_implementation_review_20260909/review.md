# BCAP v0.1.0 독립 구현 검수

이 문서는 주 실행기를 작성하지 않은 검수 작업의 기록이다. 기존 OBS/Ridge 정의·원본 위치·실행 manifest·수렴 진단을 확인한 뒤, BCAP 주 실행기를 불러 쓰지 않는 별도 AIPW/OPE 검산기를 구현했다. 모델의 인과 식별이나 행동 추천을 인증하는 문서는 아니다.

## 개발 결과와 확인 범위

| 모델·실행 | 평가 행 | 같은 공통 지지 행 | 독립 검산 |
| --- | ---: | ---: | --- |
| PITCH 2024·2025 r02 | 1,415,566 | 1,395,402 | 행별 AIPW·OPE·OBS Y 최대 차이 0; 13개 전체/카운트 요약 일치 |
| SWING 2024·2025 r01 | 1,416,043 | 1,354,516 | 행별 점수 최대 차이 7.11×10⁻¹⁵; OBS Y 차이 0; 13개 전체/카운트 요약 일치 |

검산 코드는 [verify_bcap.py](../../../../models/bcap/verify_bcap.py)다. 주 실행기의 `phi0/phi1` 혼합식을 그대로 사용해 정책가치를 계산하지 않고, `정책 평균 결과회귀 + 정책/관찰 행동확률 비 × 관찰 행동 잔차`라는 다른 식으로 복원한다. 같은 행에서 행동 0과 1, 실제 관찰 정책, 학습 후보, 보수적 유지 정책을 비교했다. 투수 이득은 `관찰 Y − 정책가치`, 타자 이득은 반대 부호다.

검사는 투구 키 중복, PA 내 Y·시즌·최종 결과의 일관성, OBS 최종 event→결과 분류와 연도별 원단위 가중치, 이진 행동과 확률 범위, 경기·PA의 fold 단일 소속을 확인한다. 지지 마스크는 `0.05≤p≤0.95`, 훈련 선수의 양 행동 최소 기록 조건, SWING 측정 조건의 교집합이며 두 행동과 모든 정책이 같은 분모를 사용한다. 원본 전체를 두 번째로 읽어 PA를 재구성하는 검사는 아니므로 원자료 연결·행동 라벨의 타당성은 별도 정제 감사도 확인해야 한다.

- [PITCH 첫 수치 검산](pitch_development_arithmetic.json): outer 평가 완료 시점의 27개 분할 기록. 이후 final 학습 완료 기록과 구분한다.
- [PITCH 완료 검산](pitch_development_complete_validation.json): 전체 분할 및 3개 outer 정책·최종 정책 검증. 정책별 저장 delta 재계산의 최대 차이 2.71×10⁻¹⁸.
- [SWING 첫 수치 검산](swing_development_arithmetic.json): outer 평가 완료 시점의 기록. 최종 정책 검사는 아래 후속 기록으로 추가한다.
- [SWING 완료 검산](swing_development_complete_validation.json): 3개 outer 정책과 최종 정책 각각 72개 상태를 검산했다. 정책별 delta 최대 차이는 1.11×10⁻¹⁶이며 학습 경기와 상위 평가 경기의 분리도 통과했다.

PITCH 전체/카운트 요약의 Q·delta·군집 표준오차는 1×10⁻¹⁶ 정도 이내, ESS는 1.17×10⁻¹⁰ 이내로 일치한다. CSV 반올림과 부동소수점 연산 순서에 따른 차이다. 최종 판정 등급의 임계값을 새로 선택하거나 수정한 검사가 아니다.

## 학습·평가 분리

각 분할 기록의 훈련/평가 경기 교집합을 검사하고, `outer0/inner0/cal` 같은 하위 기록을 모든 상위 평가 경기와 대조했다. 단순히 자신의 calibration 경기만 겹치지 않는지 확인하는 수준을 넘어, 하위 튜닝·calibration·정책 점수 생성이 outer 및 inner 평가 경기 밖에서 이루어졌는지 검사한다.

저장 정책 검사는 정책을 선택할 때 사용한 inner 점수 파일의 경기 집합이 각 outer 훈련 집합과 정확히 같은지, 각 inner fold가 그 예측의 heldout 경기와 정확히 같은지 확인한다. 동일 공통 지지 안에서 AIPW 차이를 독립 재합산한 뒤 PITCH의 최소화/SWING의 최대화 방향, 상태 사전·표본·경기 수·fallback 0.5·보수적 유지 플래그를 대조한다. 최종 개발 정책의 학습 점수는 최종 외부 평가 점수와 구분한다.

## 수치 해법과 미관측 선수

[독립 수치 fixture](independent_numerical_fixture.json)는 **합성 60행**을 이용한 구현 검사다. 실제 MLB 표본 또는 결과로 인용하면 안 된다. 훈련 범주별 설계행렬을 독립적으로 밀집 행렬로 만들고 중심화한 뒤, 정규방정식을 직접 풀어 주 실행기의 축소 회귀와 비교했다.

- 계수 최대 차이: 5.09×10⁻¹².
- 훈련 예측 최대 차이: 5.33×10⁻¹².
- known/unseen을 섞은 평가 예측 최대 차이: 2.48×10⁻¹².
- 모든 범주가 unseen인 행의 예측은 훈련 절편과 정확히 같다.
- 고의로 만든 상위 holdout 침범을 검산기가 거부했다.

이는 작은 문제에서 중심화·축소·unseen 처리 구현을 확인한 것이다. 실제 적합 전체의 수렴은 각 실행의 `fit_diagnostics.csv`로 확인해야 하며, 수렴은 유용한 예측이나 교란 제거의 증거가 아니다.

## 추가 진단

[supplement_diagnostics.py](../../../../models/bcap/supplement_diagnostics.py)는 기존 완료 실행을 읽고 새 폴더에만 결과를 쓴다. [PITCH 개발 보조 기록](pitch_development_supplement/supplement_manifest.json)은 다음을 보완한다.

- 동일 지지 행의 비정규화 IPW, 별도 분모를 명시한 Hájek, 결과회귀 표준화, AIPW.
- 투수/타자 known·unseen 각각의 주변 집단과 공동 집단: 행·PA·경기·선수 수, ESS, 경기 가중치 집중도, 예측 오차와 가치 구간.
- 실제 행동 1 비율, 후보 정책의 예상 행동 1 비율과 관찰 행동과의 예상 불일치율.
- 고정 10개 확률 구간의 calibration, ECE와 최대 구간 차이.
- 고정 개발 평균을 사용한 외부 상수 예측 기준과, 외부 결과를 알고 계산한 사후 집단 평균 기준을 구분한 MSE.

PITCH 개발 전체에서는 AIPW FB−NFB가 −0.0000140 W인 반면 비정규화 IPW는 +0.0044445 W, Hájek은 +0.0000535 W다. 세 방식은 명칭·분모를 섞지 않고 원표를 함께 봐야 한다. 후보의 예상 FB 비율은 60.63%, 같은 지지 행의 실제 비율은 55.37%, 예상 불일치는 45.32%다. 이는 정책 실행 권고가 아니다. 보수적 정책의 개선량 0은 모든 행에서 관찰 기전을 유지한다는 정의의 결과다.

[SWING 개발 보조 기록](swing_development_supplement/supplement_manifest.json)도 작성했다. 같은 지지 집단의 AIPW Swing−Take 차이는 −0.0245982 W, 학습 후보 이득은 +0.0255722 W다. 서로 다른 상태의 평균 대비와 상태별 선택을 혼동하면 안 된다. 후보 예상 Swing 비율 45.63%, 실제 49.07%, 예상 불일치 31.50%이며 모두 사후 공 특성에 조건부인 진단이다. 이 수치를 실행 가능한 실시간 행동 효과로 해석하지 않는다.

보조 집단 구간은 고정 점수에 대한 경기 군집 정규근사 개별 95% 구간이다. nuisance·정책 재학습, 동률 부근의 선택 불확실성, 경기 간 같은 선수 의존성을 모두 반영하지 않으며 주 분석의 1,536개 다중비교 가족에도 포함하지 않는다. 이 추가 표로 추천 등급을 올리지 않는다.

## 방법론 검수 의견

현재 구현은 한 구의 제한된 비교, 선수와 상황을 같은 실제 행에 표준화하는 비교, nuisance 입력 X와 정책 상태 Z, 고정 개발 nuisance의 외부 예측과 외부 교차 적합 nuisance의 정책가치를 구분한다. PITCH는 현재 구종·구속·도착 위치·현재 스윙/결과를 보정 변수로 사용하지 않는다. 이전 위치도 사용하지 않으므로 그 경로로 2026 위치 정의 변화가 유입되지 않는다.

완료 PA·최종 결과에 따른 선택, 행동 묶음 내부의 서로 다른 구종과 번트/스윙 버전, 선수별 구종 품질·의도·지각의 미측정 차이, 사후 측정 공 특성은 해결되지 않았다. 따라서 `identification_gate=false` 및 확정 행동 추천 보류를 유지하는 것이 타당하다. 조건부 회귀 성능이나 AIPW 수치 재현으로 그 제한을 해제할 수 없다.

추가 유의점은 다음과 같다.

1. 정제 코드의 카운트 전이 검사는 증가/유지의 일반적 가능성을 확인한다. 모든 description과 정확히 대응하는 완전한 전이 검증은 아니다.
2. `first_count_visit` 민감도는 해당 모델의 첫 적격 방문을 선택한 뒤 지지를 적용한다. 첫 지지 방문이나 OBS의 도달 PA 분모와 같다고 설명하면 안 된다.
3. 주 1,536개 가족은 5개 평가 가능 모델·기간의 주요 행동 차이와 정책 이득에 대한 상한이다. 고정 개발 nuisance의 보조 AIPW, known/unseen, 민감도, 정책 학습용 구간까지 모두 보장하지 않는다.
4. 전체 재학습 bootstrap은 동일 원 경기의 복제들을 같은 fold에 둔다. 적은 반복의 범위·표준편차·부호 안정성을 최종 95% 구간으로 바꾸면 안 된다.

## 외부 열람 이력

이 검수의 위 개발 단계에서는 기존 BCAI/Ridge의 2023·2026 결과와 입력 위치를 확인했으며, BCAP의 외부 행동별 결과를 읽거나 계산하지 않았다. 외부 BCAP 검수는 사전 봉인과 해당 실행의 평가가 완료됐다는 통지를 받은 뒤 별도 기록으로 추가한다. 기존 자료 전체가 처음 보는 독립 데이터라는 주장은 하지 않는다.

후속 외부 검수는 2026-09-09의 [최종 봉인](../../../../models/bcap/external_seal_20260909_r01.json), UTC 06:13:44.654 이후 수행했다. 봉인 SHA256은 `0fa8f05f2c2d75bc08d40433317890281c2007467520d365b5482c560d5e1105`이다. 주 실행의 최초 BCAP 행 열람은 각 실행 `artifacts/external_access_log.json`, 이 검수의 결과 열람·계산 완료 시점은 아래 검증 JSON에 있다. 완료 manifest를 확인한 다음에만 외부 결과를 검산했다.

| 외부 평가 | 행 / 공통 지지 행 | 외부 교차 적합 AIPW 차이 | 고정 후보 정책 이득 | 독립 검산·보조 표 |
| --- | ---: | ---: | ---: | --- |
| PITCH 2023 | 716,113 / 697,633 | +0.00129297 | +0.00141215 | [검산](pitch_2023_external_validation.json), [출처·정책·선수 검증](pitch_2023_external_lineage.json), [보조 표](pitch_2023_external_supplement/supplement_manifest.json) |
| PITCH 2026-09-07까지 | 635,095 / 615,820 | +0.00116475 | +0.00192012 | [검산](pitch_2026_external_validation.json), [출처·정책·선수 검증](pitch_2026_external_lineage.json), [보조 표](pitch_2026_external_supplement/supplement_manifest.json) |
| SWING 2023 | 716,385 / 682,953 | −0.02759621 | +0.02641076 | [검산](swing_2023_external_validation.json), [출처·정책·선수 검증](swing_2023_external_lineage.json), [보조 표](swing_2023_external_supplement/supplement_manifest.json) |
| SWING 2026 | 미평가 | 미산출 | 미산출 | [WITHHELD 실행](../runs/bcap_swing__mlb_2026_ytd_20260907__20260909__r01/manifest.json): 측정 정합성 보류 |

단위는 해당 평가의 공통 지지 의사결정 행당 원 가중 공격가치 W다. 차이는 행동 1−행동 0이고, 정책 이득은 각 모델의 유리한 방향으로 부호를 정했다. 전체 평균 행동 차이와 상태에 따라 선택하는 정책 이득은 같은 양이 아니다. 이 표의 양수 정책 점추정으로 추천을 만들지 않는다. 2026에는 2025 결과 가중치를 사용했고, SWING 위치 기반 평가를 다른 모델로 대체하지 않았다.

세 외부 실행 모두 독립 산술·분모·fold 검사에 통과했다. SWING 2023의 행별 점수 최대 오차는 1.42×10⁻¹⁴이고, 두 PITCH 외부 실행은 0이다. [외부 계보 검사](verify_external_lineage.py)는 봉인 후 추가한 **동일성 검사 전용** 코드다. 결과나 임계값을 변경하지 않고 봉인 24개 파일의 해시, 고정 정책의 모든 행별 확률, 개발 정제본에서 직접 만든 선수 명단과 known/unseen 플래그를 확인한다. 세 실행의 외부 평가용 점수와 고정 개발 예측용 점수에서 모두 일치했다.

고정 개발 nuisance 적용과 외부 재적합 nuisance는 서로 다른 지지 행을 남길 수 있다. 보조 표의 두 단계 값 차이를 같은 모집단에서의 변화로 해석하면 안 된다. 특히 고정 개발 결과의 AIPW 값은 전이 진단이며 주 외부 교차 적합 OPE를 대신하지 않는다. 예측 MSE 비교 역시 실제 Y를 본 뒤 계산한 사후 평균 기준과 개발 때 고정한 상수 기준을 구분한다.

## 봉인 후 기술적 재현 비교 요약

원문이 요청한 방향 일치·상관을 [별도 비교 표](postseal_descriptive_comparison/comparison_manifest.json)에 추가했다. [코드](compare_existing_estimates.py)의 정확한 집계 방법은 외부 결과를 본 뒤 정했으므로 **봉인 후 기술통계**로 표시한다. 추정값·정책·등급은 바꾸지 않았고 p값이나 새 검정은 계산하지 않았다. 원자료 대신 이미 저장된 12개 카운트 결과 및 SWING의 유효 72개 구역×구종군 셀을 비교한다.

| 비교 대상 | 개발·외부 delta 방향 일치 | Pearson / Spearman | 고정 개발 정책과 외부 추정 방향 일치 |
| --- | ---: | ---: | ---: |
| PITCH 2023, 12카운트 | 9/12 | 0.980 / 0.769 | 10/12 |
| PITCH 2026, 12카운트 | 10/12 | 0.939 / 0.573 | 9/12 |
| SWING 2023, 12카운트 | 12/12 | 0.908 / 0.916 | 적용 불가: 정책은 같은 카운트 안에서도 셀별로 다름 |
| SWING 2023, 72셀 | 69/72 | 0.983 / 0.978 | 69/72 |
| SWING 2023, 양 기간 경험적 지지 기준을 충족한 66셀 | 63/66 | 0.992 / 0.986 | 63/66 |

상관은 상태별 동일 가중치로 구했고, 원표에는 각 기간의 N·PA·경기·ESS·포함률을 함께 보존했다. 비교하는 두 시즌의 선수·상황·지지 분포가 같지 않다. 추정 방향과 일치했다는 뜻이지 참 최적 행동에 맞았다는 뜻이 아니며, 높은 상관도 작은 정책 이득이나 식별 문제를 해결하지 않는다. SWING 2026 비교는 만들지 않았다.

## 재현

프로젝트 루트에서 Python은 기존 NumPy/Pandas 분석 환경을 사용한다. 실제 검산의 정확한 명령·입력/코드 해시는 각 검증 JSON의 `command`, `rows_file`, `additional_inputs`, `verifier`에 있다. 수치 fixture의 SciPy 읽기는 샌드박스가 거부하여 같은 명령을 승인된 범위에서 재실행했다. 모델이나 입력 데이터를 변경한 우회는 하지 않았다.

```powershell
& 'C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' models/bcap/verify_bcap.py --rows columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260909__r02/artifacts/scores.pkl --model pitch --summary columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260909__r02/artifacts/action_values.csv --folds columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260909__r02/artifacts/fold_records.json --config models/bcap/pitch/v0.1.0/specification.yaml --policy-directory columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260909__r02/artifacts --output columns/001-ball-count/analysis/bcap_implementation_review_20260909/pitch_recheck_NEW.json
```

재검사 출력 이름은 미사용 이름으로 정한다. 검산기와 보조 진단기는 기존 검증 기록과 완료 실행을 덮어쓰지 않는다.

[기존 자산 보존 검수](legacy_asset_preservation.json): 기존 정제 CSV 7/7, BCAI 실행 파일 277/288, BCAI 모델 파일 11/19, 연결 분석 코드·캐시·보고서 7/9를 합쳐 302개 파일이 실제 사전 기록 SHA256과 일치했다. 비교 가능한 기준의 불일치·누락은 0이다. 사전 해시가 없는 20개 파일과 이전 구조 변경 전 해시만 남아 현재 해시가 다른 `write_advantage_report.py` 1개는 과거 보존 미검증으로 남겼다. 더 오래된 참조와의 차이 10건도 별도 기록했으며 이를 이번 BCAP 변경으로 단정하지 않는다. 원본 CSV 150개와 의존성 런타임은 이 검수 범위에서 제외했다.

[실제 행동과 학습 후보의 행동 비율 비교](behavior_comparison.md)는 원문의 카운트별 “실제 행동과의 차이”를 바로 읽을 수 있도록 기존 보조 CSV의 저장값을 정리한 봉인 후 표시 자료다. 개발 PITCH/SWING과 외부 PITCH 2023·2026/SWING 2023 각각 12카운트에서 같은 공통 지지 행의 실제 비율·후보 예상 비율·차이(%p)·예상 불일치율·분모를 제시한다. 개발은 outer별 학습 절차의 후보, 외부는 고정된 최종 개발 후보를 비교하며 추천은 없다. 2026 SWING은 표시하지 않았다. [입력·출력 해시와 표시 범위](behavior_comparison_manifest.json)에 새 분석·정책 변경·주 16표 변경이 없음을 기록했다.

## 전체 재학습 8회씩의 최종 독립 검산

[최종 검산 기록](bootstrap_final_validation.json)은 PITCH 개발 bootstrap `r03`와 SWING 개발 bootstrap `r02`가 각각 8/8 `COMPLETE`인 상태에서 수행한 **총 16회 PASS** 기록이다. [독립 코드](verify_bootstrap.py)는 봉인된 학습 코드를 호출하거나 수정하지 않고 보존된 개발 정제본과 seed에서 시즌별 경기 재추출, 복제 횟수, 원 경기의 outer 소속을 재구성했다. 원 경기의 복제본들을 서로 다른 fold로 나누지 않았음을 확인하고, outer·inner·튜닝·calibration의 훈련/평가 경기 집합 해시 432쌍 및 학습 표본 수 1,440건을 대조했다. 저장된 튜닝 손실에 따른 선택 432건과 적합 수렴 기록도 확인했다.

반복마다 전체 및 12카운트의 표본 합계, 행동 비율, 공통 지지 포함률, 가치 차이·이득의 부호, 보수적 유지 가치, 카운트에서 전체로의 가중 집계를 검산했다. 저장 산술·가중 집계의 최대 절대 차이는 2.22×10⁻¹⁶이다. [독립 안정성 요약](bootstrap_final_validation_independent_stability.csv)은 모델별 13집단×8지표, 총 208행의 평균·표본 SD·최솟값·최댓값·양수 비율을 다시 계산한 것이다. 완료 실행의 요약과 모두 일치했고, N 지표를 포함한 요약 전체의 최대 절대 차이는 5.68×10⁻¹⁴이다. 이전 [부분 검산](bootstrap_partial_validation_20260909_r01.json)은 당시 완료된 PITCH 7회·SWING 4회의 기록으로 보존한다.

| 모델 | 전체 집단 후보 이득 최솟값 | 최댓값 | 8회 표본 SD | 양수 횟수 |
| --- | ---: | ---: | ---: | ---: |
| PITCH | −0.00137650 | +0.00153482 | 0.00083090 | 6/8 |
| SWING | +0.02469531 | +0.02603555 | 0.00045696 | 8/8 |

단위는 각 재추출 표본에서 지지되는 의사결정 행당 원 가중 공격가치 W이며, PITCH는 공격가치 감소, SWING은 증가를 양의 후보 이득으로 표시한다. 이 8회 범위는 신뢰구간이 아니다. 매 반복의 공통 지지 집단과 학습 후보가 달라질 수 있다. nuisance 튜닝·calibration 및 정책 학습을 포함한 중첩 평가 절차 전체를 재학습한 안정성 진단이며, 봉인된 최종 전체 개발 정책 자체의 신뢰구간을 추정한 결과가 아니다. 양수 8/8도 식별 또는 추천 근거를 충족했다는 판정으로 바꾸지 않는다.

각 bootstrap 반복의 행별 nuisance 예측·AIPW 점수와 적합 객체는 저장되지 않았다. 따라서 이 검수는 반복별 원 행에서 AIPW를 다시 계산했다는 주장을 하지 않는다. 독립 재추출·분할·학습 N 재구성과 저장 가치의 산술·집계 검산까지 확인한 범위다. 주요 개발·외부 5개 실행의 저장 행 점수에 대한 별도 독립 AIPW 검산과 구분해야 한다. 같은 선수나 시리즈의 경기 간 의존성, 동률 부근 정책 선택의 충분한 반복 추론도 여전히 해결되지 않았다. `full_learning_interval_validated=false`와 `recommendation_gate_upgrade=false`를 유지한다.

최종 검산의 정확한 명령·입력/코드/출력 해시는 최종 JSON에 저장했다. 재검산은 아래 출력 이름을 새로운 미사용 이름으로 바꿔 실행한다.

```powershell
& 'C:/Users/백창현/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' columns/001-ball-count/analysis/bcap_implementation_review_20260909/verify_bootstrap.py --require-complete --output columns/001-ball-count/analysis/bcap_implementation_review_20260909/bootstrap_recheck_NEW.json
```
