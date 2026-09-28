# BCAP 블로그 해설의 집필 근거표

**현재 원고 — 2026-09-28 모델 해설 15차:** [개편 기록](revision_v15.md). 본문 표 3개만 초반에 재사용하고 공통 AIPW 계산과 위치·스윙·구종별 정의·입력·지원·평균 차이를 설명한다. 각 명세와 R 엔진의 실제 수식을 대조했다. 아래 결과 주장 대응은 과거 원고 근거로 유지하며 수정 전 원고는 [보관본](revisions/v14_before_models_v15/03_bcap.md)에 있다.

**최신 기준 — 2026-09-28 7차:** 2015–2025의 11시즌 반영을 완료했다. 현재 주장·근거·변경 위치는 [7차 반영표](revision_v7.md), 정확한 파생 표는 `revision_v7_tables/`, 수치·보존 검수는 [검사 기록](revision_v7_numerical.json)을 따른다. 아래는 기존 두 시즌·외부 확인 원고의 작성 당시 근거로 보존하며 현재 결과 전체로 일반화하지 않는다.


대상: [03_bcap.md](03_bcap.md) · 작성일: 2026-09-18 · 사용자 검토용. 새 모델 실행·원자료 재집계 없이 저장 결과와 정의·검수 기록을 읽어 작성했다. 이 문서는 발행 본문이 아닌 확인용 메모다.

## 수치 주장과 원 결과

CSV의 ‘행’은 헤더를 제외한 데이터 행이다. 소수는 본문에서 반올림했다. 데이터 파일 전체는 기존 위치를 유지한다.

| 본문의 주장 | 정확한 파일·행 또는 선택 조건 | 근거 열·값 |
| --- | --- | --- |
| 개발 0-2의 Q(B)·Q(S)·차이·구간·표본 | [개발 S/B](../../analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/count_values.csv), 데이터 3행, `count=0-2` | Q0=0.1937251102348688, Q1=0.22155203147852384, delta=0.02782692124365505, family95=[0.015208161528231484,0.04044568095907861], n=95,563, n_all=96,411, games=4,859 |
| 개발 1-2의 같은 열 | 같은 파일 데이터 6행, `count=1-2` | Q0=0.2184982651520924, Q1=0.23987183478519455, delta=0.021373569633102118, family95=[0.010980303835694968,0.03176683543050927], n=138,265, n_all=139,503, games=4,859 |
| 2023 0-2의 같은 열 | [2023 S/B](../../analysis/runs/bcap_pitch_sb__mlb_2023__20260914__r01/artifacts/values.csv), `count=0-2`, `model=pitch_sb` | Q0=0.19650878347966227, Q1=0.23077480325493746, delta=0.034266019775275186, adjusted95=[0.022303546967570195,0.046228492582980174], family=4, n=47,912, n_all=48,733, games=2,430 |
| 2023 1-2의 같은 열 | 같은 파일 `count=1-2`, `model=pitch_sb` | Q0=0.21871917735078725, Q1=0.24283642790467067, delta=0.02411725055388348, adjusted95=[0.014006186212988603,0.03422831489477836], family=4, n=68,412, n_all=69,569, games=2,430 |
| 위 4행의 읽기 쉬운 재표시 | [재표시 CSV](../../analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/sb_reformatted.csv), 데이터 3·6·15·18행 | `period`와 `count`로 선택. `Q_B_W/Q_S_W/delta_S_minus_B_W/ci_low_W/ci_high_W/family/n/n_all/games` |
| 개발 S/B: B 방향 2, 0-1 불명확, 나머지 9개 S 방향 | 개발 S/B 파일 12행 전체 | `point_direction` B인 count=0-2,1-2; `evidence=차이 불명확`은 0-1; 나머지 9개 `point_direction=S`이면서 `family95_high<0` |
| 개발 존 안 12개 모두 스윙 점추정, 3-0 불명확 | [개발 5구역](../../analysis/bcap_v2_development_20260912__r01/batter_five_regions.csv), `region=CENTER`, `pitch_group=ALL` 12행 | `delta>0` 모두, 3-0 `evidence=차이 불명확`; 나머지 11개 `family95_low>0` |
| 개발 3-0 밖 4구역 자료 부족 | 같은 파일 `count=3-0`, `region=HIGH/LOW/INSIDE/OUTSIDE`, `pitch_group=ALL` | `support_gate=False`, `evidence=비교 자료 부족` |
| 2023 존 안 12개 스윙 점추정, 그중 10개 구간도 같은 방향, 3-0·3-1 불명확 | [2023 타자](../../analysis/runs/bcap_swing__mlb_2023__20260914__r01/artifacts/values.csv), `region=CENTER`, `population=own`, 12행 | `delta>0` 모두; `adjusted95_low<=0<=adjusted95_high`인 count=3-0,3-1; 나머지 10개 `adjusted95_low>0` |
| 2023 밖 48개 중 지원 44개 모두 테이크, 3-0 밖 4개 자료 부족 | 같은 파일 `region=HIGH/LOW/INSIDE/OUTSIDE`, 48행 | 지원 44행 `support_gate=True`, `delta<0`, `adjusted95_high<0`; count=3-0 4행 `support_gate=False` |
| 외부 구종 총96개 중92개 불명확 | [2023 구종](../../analysis/runs/bcap_pitch_compare__mlb_2023__20260914__r01/artifacts/values.csv), [2026 구종](../../analysis/runs/bcap_pitch_compare__mlb_2026_ytd_20260907__20260914__r01/artifacts/values.csv), 각48행 | 각 파일 `model=pitch/pitch_ff`, `population=own/common`, 12카운트. 총96=2연도×2모델×2표본×12카운트. 보정 구간이0 포함92행. [기존 최종 결론](../../analysis/bcap_external_20260914__r01/final_column_conclusion.md)에서도 확인 |
| 외부 3-2 비포심 방향이지만 불명확 | 같은 외부 구종 파일, `model=pitch_ff,count=3-2,population=common` | 두 연도 `delta>0`, 보정 구간0 포함. 본문은 외부점수 자체의 소수 수치를 추가하지 않음 |
| 비교 범위 219·주4·명목95%·참고선0.01W | [S/B 명세](../../../../models/bcap/pitch_sb/v0.1.0/specification.yaml)의 `comparison_family/uncertainty/practical_delta_W`; [외부 계획](../../analysis/bcap_external_20260914__r01/plan.md), [외부 보고서](../../analysis/bcap_external_20260914__r01/report.md)의 ‘표를 읽는 방법’ | 개발 S/B·타자219, 구종 추가255; 외부 주4/보조236. 본문 표2는 개발219와 외부 주4만 표시. 2026 위치 보류 뒤에도 주가족4 유지 |
| 존 폭17인치·경계 포함·반경 미확대 | S/B 명세 `s_b_definition` | abs(plate_x)≤17/24 feet; sz_bot≤plate_z≤sz_top. 폭=2×17/24×12=17inch. 통계 결과가 아니라 정의 |
| 5구역·모서리 중복·100% 초과 가능 | S/B 명세 `region`, [SWING 카드](../../../../models/bcap/swing/v0.2.0/model_card.md) 보고 구역 설명 | CENTER 전체 존, HIGH/LOW/INSIDE/OUTSIDE는 중첩 보고 집합. 전체 학습 행은 중복 없음 |
| 선택 확률5~95%, 경기3집단 | S/B 명세 `trim=.05/outer_folds=3/support/split` 및 SWING/PITCH/FF 현재 명세 | 양 행동 기준 .05≤p≤.95. 경기 단위3fold OOF. 추가 기준 상세는 원 명세 링크로 남김 |
| 2026년9월7일까지 | [외부 자료 준비·범위](../../analysis/bcap_external_20260914__r01/plan.md), [출처](../../sources.md) ‘BCAP 외부 자료 재사용’ | 기존 2026-03-25~09-07 스냅샷. 이후 자료가 포함됐다고 쓰지 않음 |

## 정의·시행착오·현재 상태의 근거

- 네 비교와 각 부호: [S/B 카드](../../../../models/bcap/pitch_sb/v0.1.0/model_card.md), [FB/NFB 카드](../../../../models/bcap/pitch/v0.2.0/model_card.md), [포심 카드](../../../../models/bcap/pitch_ff/v0.1.0/model_card.md), [타자 카드](../../../../models/bcap/swing/v0.2.0/model_card.md). 카드의 가장 위 최신 상태를 사용했다. 아래 ‘당시 외부 미실시’ 문장은 과거 이력이다.
- W·최종 PA 연결·지원 행 표준화·AIPW·Ridge·훈련 분리: 각 현재 카드와 명세, [기존 BCAP 해설](../../bcap_explained.md), [독자 보고서](../../analysis/bcap_reader_20260914/report.html). 자체 분석 절차 설명으로 쓰며, 미측정 교란을 제거한다는 보증을 붙이지 않았다.
- 스윙/테이크 라벨: S/B 명세에 상속된 `actions`, SWING 명세·카드. 스윙은 번트 포함 공격 시도, 테이크는 명시적 `ball/blocked_ball/called_strike/hit_by_pitch`. 미분류를 테이크로 채우지 않는다는 한계 유지.
- 구종 변경: [개발 V2 보고](../../analysis/bcap_v2_development_20260912__r01/report.html), [구종 추가 보고](../../analysis/bcap_pitch_classification_20260912__r01/report.md). FB3-0의 통합 차이가 사라지거나 부호가 뒤집혔다고 쓰지 않았다. FF3-0의 분할 반전, FB3-1의 결과모형/AIPW 방향 차이를 구별했다. 보고 당시 이후 진행된 외부 결과는 최신 외부 보고서로 보완했다.
- 2026 측정 보류: [측정 검토](../../analysis/bcap_external_20260914__r01/measurement_review.md)에서 당시 공식 필드 설명을 확인한 범위. 이 집필 중 새 좌표 변환·데이터 조사 없음. ‘측정 정합성 미확보’와 ‘실증 재현 실패/자료부족’을 분리했다.
- 외부 데이터 과거 노출·외부 연도 내부3fold·고정 개발 절차: [외부 보고서](../../analysis/bcap_external_20260914__r01/report.md), 현재 모델 카드 최상단, [9/17 인계](../../analysis/handoff_bcap_followup_20260917.md). 단일 고정 예측모형의 시험이라고 표현하지 않음.
- 상태 평균 차이: [상태 차이 보고서](../../analysis/runs/bcai_state_delta__mlb_2024_2025__20260917__r01/report.md), [9/18 설계 검수](../../analysis/runs/bcap_followup_review__mlb_2024_2025__20260918__r01/methodology_review.md). 사건조건부 W나 실제 전이 빈도 미산출. 이 글에서는 숫자를 전재하지 않고 BCAI 글로 연결.
- 분해의 DRAFT·실제 MLB 미실행: [분해 카드](../../../../models/bcap/decomposition/v0.1.0/model_card.md), [후속 구현 인계](../../analysis/handoff_bcap_followup_20260917.md) §5. 모의 숫자는 이 원고에 사용하지 않음.
- 상대 반응 보류: 같은 인계 §6과 [시나리오 계약](../../analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/scenario_contract.json). 주변 평균 네 개의 조합으로 공동 보수/최적 비율을 계산하지 않음.
- 제한적 검수의 의미: [9/18 보고서](../../analysis/runs/bcap_followup_review__mlb_2024_2025__20260918__r01/report.md), [제한적 개발 검수](../../analysis/bcap_column_light_review.md), [모델 레지스트리](../../../../models/registry.md). 검수 통과를 새 모델 검증 승격·인과성 확인으로 표현하지 않음.

## 집필 선택과 확인 범위

- 요청한 ‘시행착오’는 실제 기록으로 확인되는 구종 정의 수정, 지원 부족, 측정 보류, 분해 구현과 실증의 간격, 상대 반응 결합값 부족을 중심으로 서술했다. 새로운 실패담이나 사용자 발언을 만들지 않았다.
- 사용자 개요의 ‘상태 가치→행동 비교→위치→타자→구종→상대 반응’ 흐름에 맞추되, 본문 중복을 줄이도록 이 글은 정의와 읽기 방법을 중심에 두었다.
- 외부 논문은 이 하위 작업에서 원문을 새로 읽지 않았으므로 한 편도 인용하지 않았다. 기존 문헌 해설의 요약을 논문을 읽은 것처럼 재사용하지 않았다. 외부 논문 내용이 필요하면 주 작업의 실제 원문 확인 후 별도 반영한다.
- 새 원본 수집·모델 재실행·원자료 재감사·KBO 분석·게시·업로드 없음. 저장 CSV에 대한 행 선택·열 대조는 집필용 확인이며 새 추정이 아니다.
- 설명표4개와 주 작업이 제작하는 공통 그림2개를 연결했다. `04_zone_map.png`는 정의 도식, `05_swing_2023.png`는 위 2023 타자 원 CSV의60셀에 근거한다. 그림의 실제 생성·렌더링 확인은 주 작업에서 완료한 뒤 전달한다.
- 집필 중 저장 CSV의 열을 직접 읽어 2023 존 안12/12 양수·보정 하한양수10/12·불명확3-0/3-1, 존 밖지원44/48·지원44개의 보정상한 모두음수, 외부구종 각연도46/48 불명확을 확인했다. 모델을 재학습하거나 새 추정량을 계산한 작업은 아니다.

## 16차 계산 설명 근거

필수 설명은 원고 안에 완결하고 아래는 비발행 편집 근거로 보존한다.

- [지원 기준 명세](../../../../models/bcap/swing/v0.2.0/specification.yaml)
- [BCAP 연도별 결과](../../analysis/history_comparison_20260928_r01/tables/bcap_all_2552_screened.csv)
- [원천 결과](../../analysis/history_comparison_20260928_r01/tables/bcap_all_2552_screened.csv)
- [위치·보고 구역 명세](../../../../models/bcap/pitch_sb/v0.1.0/specification.yaml)

- [BCAP R 엔진](../../../../models/bcap/r/engine.R): Ridge·Platt·AIPW·ESS·경기 군집 구간의 수식 대조.
