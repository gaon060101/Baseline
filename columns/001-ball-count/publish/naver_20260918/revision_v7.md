# 7차 개정 — 11시즌 전체 결과 반영

2026-09-28 사용자 요청으로 기존 원고를 수정했다. 새 분석이나 모델 재학습 없이 완료된 2015~2025 저장 결과를 원고에 반영했다. 로컬 사용자 검토본이며 외부 게시·업로드는 하지 않았다.

## 읽기

[다섯 글 읽기](index.html) · [본문](01_ball_count.md) · [BCAI](02_bcai.md) · [BCAP](03_bcap.md) · [문헌](04_references_ko.md) · [검증](05_data_validation.md)

## 바뀐 설명과 근거

| 대상 | 변경 내용 | 근거 |
| --- | --- | --- |
| 본문·BCAI 결과 | 11시즌 모두 0-2 최저·3-0 최고, 1-1<100·3-2>100. 단일 두 시즌 값 대신 연도별 범위와 반복을 중심에 배치 | [132행 지수·W·분모](../../analysis/history_comparison_20260928_r01/tables/bcai_all_132.csv) |
| BCAI 세부 해석 | 가까운 카운트의 순위 역전, 최근 두 시즌의 역사적 위치, 지수와 원 W의 차이 추가 | [연도별 모양](../../analysis/history_comparison_20260928_r01/tables/bcai_year_shape.csv), [역사적 위치](../../analysis/history_comparison_20260928_r01/tables/baseline_historical_position.csv) |
| 본문·BCAP 위치 | 0-2·1-2 각각 11/11년 점추정 반복, 구간도 같은 방향은 10/11·8/11. 0-1·2-2 불명확을 명시 | [전체 패턴](../../analysis/history_comparison_20260928_r01/tables/bcap_pattern_counts_all_groups.csv), all_2015_2025/count/pitch_sb |
| 본문·BCAP 스윙 | 존 안 132칸 중 130양수·2음수, 존 밖 481/528 지원·481음수·477음수 구간. 반대 점추정과 확정적 반례 구분 | [기간 집계](../../analysis/history_comparison_20260928_r01/tables/window_totals.csv), all_2015_2025/region |
| 본문·BCAP 구종 | ‘대부분 불명확’에 FB/NFB 3-0 및 포심/비포심 3-2의 반복 단서 추가. 2020 자료 부족 유지 | [전체 BCAP 표](../../analysis/history_comparison_20260928_r01/tables/bcap_all_2552_screened.csv), count/3-0/pitch 및 count/3-2/pitch_ff |
| 검증 글 | 약 190만 타석과 비교별 분모, R 재현과 연도별 적합 차이, 측정·가중치·지원·구간 가족 및 민감도 설명 추가 | [기술 부록](../../analysis/history_comparison_20260928_r01/technical_appendix.md) |
| 문헌 해설 | 12건의 연구 설명·인용 내용은 유지하고 자체 11시즌 결과와의 역할 구분 및 본문 절 번호 갱신 | [기존 문헌 원고 보관본](revisions/v6_before_history_v7/04_references_ko.md) |

주 결과는 11시즌이지만 미실시 항목을 확장한 것으로 쓰지 않았다. 실제 3볼 스윙률은 기존 2024·2025 사례, Ridge와 상태 차이의 정밀 예시는 기존 기간의 보조 결과로 표시했다. 2026은 9월 7일 기준·2025 고정 가중치 보조이며 S/B·SWING 측정 보류를 유지했다. BCAP은 EXPERIMENTAL이다.

## 원문 보존과 근거의 시점

수정 전 원고·HTML·생성/검사 스크립트·기록 34개는 [보관 폴더](revisions/v6_before_history_v7/)와 [SHA-256 목록](revisions/v6_before_history_v7/snapshot_hashes.json)에 보존했다. 11시즌 비교 보고서의 ‘원 주장’과 기존 감사는 편집 전 시점의 기록이다. 해당 보고서의 원 주장 장부에 있는 원고 경로는 현재 7차로 바뀌었으므로, 당시 원문은 이 보관 폴더의 같은 이름 파일로 읽는다. 기존 감사의 해시는 보관본과 대조해 유지했다. [원천 대조표](revision_v7_source_preservation.csv).

원고의 결과 절은 새 근거로 교체했고, 기존 통계·문헌 설명과 야구 예시는 가능한 범위에서 유지했다. 제거된 기존 결과표·문장은 보관본 및 기존 개발 보고서에 남아 있다. [기존 주장→확장 판단](../../analysis/history_comparison_20260928_r01/claim_comparison.html)도 별도로 유지한다.

## 그림 배치

| 현재 위치 | 그림 |
| --- | --- |
| 본문 1 · BCAI 1 | [11시즌 카운트 지수](../../analysis/history_comparison_20260928_r01/figures/01_bcai_profile.png) |
| BCAI 2 | [지수와 원 W](../../analysis/history_comparison_20260928_r01/figures/02_index_and_W.png) |
| 본문 2 · BCAP 1 | [연도별 위치 비교](../../analysis/history_comparison_20260928_r01/figures/03_location_years.png) |
| 본문 3 · BCAP 2 | [연도별 스윙 지원·방향](../../analysis/history_comparison_20260928_r01/figures/04_swing_support.png) |
| 본문 6 · BCAP 3 | [구종 반복 단서](../../analysis/history_comparison_20260928_r01/figures/05_pitch_patterns.png) |
| 본문 4 · BCAP 4 | [기존 구역 도식](../../figures/naver_20260918/04_zone_map.png) |
| 본문 5 | [기존 두 시즌 3볼 스윙률](../../figures/naver_20260918/08_three_ball.png) |
| BCAI 3 | [기존 2024 상태 간격 예시](../../figures/naver_20260918/07_state_gaps.png) |
| 검증 글 1 | [기존 Python 2023 확인 이력](../../figures/naver_20260918/03_sb_2023.png) |

새 그림은 만들지 않고 검수된 R 그림 5장과 기존 보조 그림을 활용했다. 모바일 표는 카드로 읽고 그림은 버튼으로 확대·축소할 수 있다. 이전 4차 ZIP은 최신 원고가 아니며 그대로 보존했다.

## 재현과 검수

프로젝트 루트에서 `tools/run_r.ps1`로 `prepare_history_v7.R`를 실행하면 저장 결과로 11시즌 표 4개를 생성한다. `revise_history_v7.py`는 보관본에서 7차 원고를 만든 일회성 편집 기록으로, 후속 수동 편집 후 재실행하지 않는다. `build_preview.mjs`는 현재 MD를 읽어 HTML을 만들며 MD를 다시 쓰지 않는다.

[수치·보존 검사](revision_v7_numerical.json)는 `verify_history_v7.R`, [화면·링크·앵커 검사](revision_v7_visual.json)는 `check_history_v7.mjs`로 재현한다. 검사 범위와 실제 결과는 각 JSON을 기준으로 한다. 원자료 재수집·재적합·모델 상태 변경·자동화 재개는 수행하지 않았다.
