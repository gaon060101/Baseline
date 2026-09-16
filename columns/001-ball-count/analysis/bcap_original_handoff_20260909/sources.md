# 001. 출처와 데이터 확보 기록

## Ridge v0.2 외부 검증 확보 결과 — 2026-09-09 확인

| 시즌·역할 | 기간 | 원본 행 | 완료 경기 | 전체 관측 PA | 유효 PA | 검증 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 2023 외부 재현 | 2023-03-30~2023-10-01 | 720,684 | 2,430 | 184,478 | 183,534 | 일정 누락0·중복 투구 키0 |
| 2026 외부 시간 순방향 | 2026-03-25~2026-09-07 | 639,042 | 2,165 | 164,281 | 163,327 | 보충 후 일정 누락0·중복 투구 키0 |

- 2023 원본: `data/raw/mlb/2023/snapshot_20260908_ridge_v02/`.2026 최초 원본: `data/raw/mlb/2026/snapshot_20260908_ridge_v02/`, 보충: `data/raw/mlb/2026/supplement_20260909_ridge_v02/`.2024·2025 원본·정제본은 재수집·덮어쓰기하지 않았다.
- 2026 최초 확보는635,803행·2,154경기로, 공식 완료된9월7일11경기 누락을 발견해 평가 전에 FAILED로 중단했다.9월9일 요청의 계속 진행 과정에서 누락 경기3,239행을 별도 파일로 보충했다. 최초 원본·일정·실패 manifest는 보존했다. 종료일과 모델은 변경하지 않았고2026 첫 성능 평가는 보충 후1회만 수행했다.
- 2023 제외: 고의볼넷474, truncated272, 최종 결과 결측102, 타격방해96.2026 제외: 고의볼넷489, truncated292, 결측96, 타격방해77. 사건별 규칙은 기존 OBS와 동일하다.
- 공식 요청 URL·확보 시각·경기 키·파일별 행수/바이트/SHA256은 각 원본 폴더의 acquisition_audit.json과 완료 실행의 입력 목록에 보존했다.2026 완성 목록은 보충 폴더의 audit 및 아래 완료 실행이 기준이다. 기존 실패 audit를 완성본으로 덮어쓰지 않았다.
- 실행: [2023 manifest](analysis/runs/bcai_ridge__mlb_2023__20260908__r01/manifest.json), [2026 manifest](analysis/runs/bcai_ridge__mlb_2026_ytd_20260907__20260909__r01/manifest.json), [2026 보충 수집 코드·해시](analysis/runs/bcai_ridge__mlb_2026_ytd_20260907__20260909__r01/manifest_extension.json).
- 두 외부 자료 모두 개발 모델·α·평가 규칙 고정 뒤 확보·평가했다.2026은2025 가중치 고정이며 시즌 최종 검증은 미실시다. 신규 결과는 [v0.2 보고서](analysis/ridge_v02_validation_report.md)에 있다. 아래 이용 조건 확인 상태를 유지하며 원본 재배포·Drive/Docs 업로드·KBO 작업은 하지 않았다.

## Ridge v0.2 외부 검증 확보 계획 — 2026-09-08

- 2024·2025 기존 자료만으로 개발 후 모델을 고정했다. 개발 실행은 `analysis/runs/bcai_ridge__mlb_2024_2025__20260908__r02/manifest.json`. 2023·2026 자료는 개발에 사용하지 않았으며 로컬 원본 폴더가 없음을 확인했다.
- 확보 대상: 2023 정규시즌 전체와 2026-09-07 공식 경기일까지의 완료 정규시즌. MLB Baseball Savant 공식 Statcast CSV와 MLB Stats API 일정으로 범위·완료 상태·구장 ID를 확인한다. 원본은 연도별 새 snapshot 하위 폴더에 보존하고 행수 상한·중복·누락을 점검한다.
- 2026-09-08 [CSV 공식 설명](https://baseballsavant.mlb.com/csv-docs)에서 count와 상황 필드를 재확인했다. 2026 plate_x/plate_z 정의 변경이 있어 이번 모델에서 위치 변수를 제외한다.
- [MLB 이용약관](https://www.mlb.com/official-information/terms-of-use): 자동 수집 제한 조항 확인. 별도 허가·원본 재배포 권한은 미확인. 이번 요청의 로컬 분석 자료로만 다룬다.
- [FanGraphs 시즌 상수](https://www.fangraphs.com/tools/guts?type=cn), 열람일 2026-09-08. 2023 wBB .696, wHBP .726, w1B .883, w2B 1.244, w3B 1.569, wHR 2.004를 사전 고정했다. 2026 검증은 요청대로 2025 가중치를 고정 사용하며 2026 잠정 상수로 튜닝하지 않는다.
- 실제 확보 성공·경기수·행수·마지막 경기일·해시는 완료 후 해당 외부 실행 manifest와 acquisition_audit를 기준으로 추가 기록한다. 이 계획은 확보 성공을 뜻하지 않는다. KBO 수집·Drive/Docs 반영은 하지 않는다.

2024·2025 MLB 정규시즌 전체 자료를 확보하고 하나의 표본으로 통합했다. 아래에 출처, 확보 범위와 통합 결과 산출물을 기록한다.

## 분석 가능성 사전 확인 — 2026-09-06

- 출처: MLB Baseball Savant [Statcast Search](https://baseballsavant.mlb.com/statcast_search), [CSV 공식 설명](https://baseballsavant.mlb.com/csv-docs). 저자·기관: MLB / Baseball Savant. 문서 게시일 미표시, 열람일 2026-09-06.
- 확인 목적: 사용자 초안의 12개 카운트별 구종·스윙·투구 결과·최종 타석 결과·경기 상황 및 카운트 경로 분석 가능성 검토. 아직 본문 수치의 근거는 아님.
- 제공 필드: 투구 전 balls/strikes, pitch_type/pitch_name, description/type, 타석 결과 events, game_pk/at_bat_number/pitch_number, pitcher/batter, stand/p_throws, 주자 on_1b/on_2b/on_3b, outs_when_up/inning, 투구 전 bat_score/fld_score, plate_x/plate_z/sz_top/sz_bot.
- 정의 주의: type은 B/S/X(볼/스트라이크/인플레이)로, 존 안팎이나 투수 의도를 뜻하지 않는다. 스윙은 description의 실제 값 목록을 확인해 분류한다. 최종 타석 결과는 타석 식별자로 연결하며 미종료·누락 기록을 별도 점검한다.
- 측정 차이: 공식 설명상 2026년부터 plate_x/plate_z의 기준 위치 및 sz_top/sz_bot의 존 정의가 변경됨. 시즌을 섞는 위치 분석은 정의 차이를 반영해야 한다.
- 확보 방식 검토: 공식 검색 화면의 CSV 내려받기 기능 확인. 2026-09-01 정규시즌 하루를 기능 확인용 검색 범위로 사용하며, 본 분석 기간으로 확정한 것은 아님.
- 이용 조건: [MLB 이용약관](https://www.mlb.com/official-information/terms-of-use) 열람. 자동 수집 제한 조항이 있어 대량 자동 수집 및 원본 재배포 허용은 확인되지 않은 상태로 둔다. CSV 제공 자체를 모든 이용·재배포의 허가로 해석하지 않는다.
- KBO: 이번 확인 대상은 MLB이며 KBO의 투구별 제공 범위·구종·이용 조건은 미확인.

## 데이터 목록

| 리그 | 파일·저장 위치 | 원출처·URL | 대상 기간 | 확보일·방식 | 이용 조건 확인 | 결측·주의사항 |
| --- | --- | --- | --- | --- | --- | --- |
| MLB | `data/raw/mlb/statcast_2026-09-01_feasibility.csv` | [Statcast Search](https://baseballsavant.mlb.com/statcast_search?hfGT=R%7C&hfSea=2026%7C&player_type=pitcher&game_date_gt=2026-09-01&game_date_lt=2026-09-01&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&sort_order=desc#results) | 2026-09-01 정규시즌 | 2026-09-06, 공식 화면의 Download Data as Comma Separated Values File 클릭 후 내려받은 원본 복사 | 위 사전 확인 참조. 원본 외부 공유는 미실시 | 기능 확인용 하루 표본. 4,681행, 자동 볼·스트라이크 포함. 시즌 추정에 사용하지 않음 |

### 표본 점검 결과 — 2026-09-06

- CSV game_date는 모두 2026-09-01. 15개 game_pk, 1,196개 (game_pk, at_bat_number) 조합 확인.
- 12개 투구 전 카운트 모두 존재. (game_pk, at_bat_number, pitch_number) 중복 없음.
- description에서 볼, 블로킹된 볼, 루킹 스트라이크, 헛스윙, 파울, 파울 번트, 파울 팁, 인플레이, 몸에 맞는 공 및 자동 판정 기록을 확인.
- automatic_ball 9행, automatic_strike 2행. pitch_type 결측은 11행이며 실제 투구 분석과 자동 판정을 구분해야 함. pitcher 식별자 결측 없음.
- events가 모두 비어 있는 타석 식별자 1개 존재. 미완료 타석 또는 기록 누락인지 추가 확인 전 최종 결과를 임의 부여하지 않음.
- 경기·타석 식별자와 투구 번호로 경로 재구성 가능한 구조임을 확인. 경로 전체의 연속성, 타석 결과 대조, 구종별 결측 및 분석 지표 검증은 아직 미실시.
- 위 수치는 내려받은 CSV의 구조 점검 결과이며 카운트별 야구 성과에 대한 본 분석 결과가 아님.

## 참고 문헌

문헌을 실제로 확인한 뒤 제목, 저자·기관, 발표일, URL, 열람일, 뒷받침하는 주장과 관련 원고 위치를 기록한다.

### 카운트 유불리 판정 분석 — 2026-09-07

- FanGraphs, [Guts! Seasonal Constants](https://www.fangraphs.com/tools/guts?type=cn). 게시일 미표시, 열람일 2026-09-07. 2024/2025의 wBB·wHBP·w1B·w2B·w3B·wHR 및 wOBA scale·리그 R/PA를 직접 확인했다. 확인 값은 [분석 보고서 2절](analysis/count_advantage_2024_2025.md)과 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_audit.json`에 저장했다. 시즌 가중치 및 득점 환경 보조 환산의 근거다. 별도의 플레이 데이터는 내려받지 않았다.
- FanGraphs Sabermetrics Library, [wOBA](https://library.fangraphs.com/offense/woba/). 열람일 2026-09-07. 결과별 선형가중치와 공식 분모의 개념 확인. 이번 분석은 희생번트를 포함한 유효 완료 PA가 분모이므로 공식 wOBA가 아닌 카운트 공격가치 지수로 명명했다.
- MLB Baseball Savant, [Statcast Search CSV Documentation](https://baseballsavant.mlb.com/csv-docs). 열람일 2026-09-07. 투구 전 카운트·투구 결과·선수·상황 필드 정의 재확인. FB(포심+싱커+커터) 및 스윙/헛스윙 묶음은 프로젝트의 명시적 분석 정의이며 공식 단일 지표라고 주장하지 않는다.
- 실제 계산은 기존 2024·2025 원본 CSV와 통합 정제표를 읽었다. 구장은 보존된 `schedule_2024.json`, `schedule_2025.json`의 venue ID로 연결했다. 기존 MLB 자료 이용 조건·원본 재배포 미확인 상태는 유지한다. 신규 원본 확보나 외부 업로드는 수행하지 않았다.
- 표본: 364,124 유효 PA, 4,859경기. 결측 221·truncated 635·고의볼넷 1,065·타격방해 186 제외. 이벤트별 기록은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_event_audit.csv`, 입력 경로·SHA256·가중치·실행 설정은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_audit.json`, 재집계·해시 검증은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_validation.json`에 저장한다.
- 결과 산출물은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_*`(캐시는 기존 `analysis/advantage_input_cache.pkl`) 및 `analysis/count_advantage_2024_2025.md`에 두고, 원본·기존 통합 정제본을 덮어쓰지 않았다. KBO 제공 범위·시즌 상수·이용 조건은 여전히 미확인이다.

## 데이터 정의·변경 이력

### BCAP 검수 인계 출처 확인 — 2026-09-09

- MLB Baseball Savant, [Statcast CSV Documentation](https://baseballsavant.mlb.com/csv-docs), 게시일 미표시, 열람 2026-09-09. balls/strikes의 투구 전 기준, 구종의 Statcast 유도 분류, plate_x/z의 2026 기준면 변화와 sz_top/bot의 ABS 존 정의를 확인했다. 좌표 변환·시즌 정합성 검증은 미실시이며 위치 기반 외부 검증의 해결 과제로 남긴다.
- Dudík, Langford, Li (2011), [Doubly Robust Policy Evaluation and Learning](https://arxiv.org/abs/1103.4601), 열람 2026-09-09. 공개 초록의 DR 정책 평가·학습 범위를 확인했다. 본 프로젝트의 MLB 교란 제거를 보장하는 근거는 아니다.
- Athey, Wager, [Policy Learning with Observational Data](https://arxiv.org/abs/1702.02896) (2017 사전논문, 2021 Econometrica 출판), 열람 2026-09-09. 관찰 자료의 정책 학습과 정책 클래스에 관한 공개 초록을 확인했다.
- Nie, Brunskill, Wager (2019 사전논문), [Learning When-to-Treat Policies](https://arxiv.org/abs/1905.09751), 열람 2026-09-09. 순차적 정책에는 별도 식별·평가 설계가 필요함을 검토하는 참고 자료다. 공개 초록 확인이며 상세 정리·증명을 독립 검증한 것은 아니다.
- 적용 위치: [BCAP 검수 인계](analysis/handoff_bcap_review.md). 방법론 수정은 프로젝트 설계 판단이며 논문이 해당 야구 모델을 검증했다고 표현하지 않는다. 신규 원본 수집·재배포·Drive 업로드는 없고 기존 이용 조건 미확인 범위도 유지한다.

구종 분류, 구속 단위, 카운트 전후 기준, 측정 방식 등 해당 칼럼에 필요한 출처별 차이와 정정 사항을 기록한다.

## 2025 정규시즌 전체 확보 작업

- 사용자 요청: 2025 정규시즌 전체 투구, 모든 카운트·선수 포함. 포스트시즌 제외.
- 전체 검색 CSV가 25,000행(9월 23~28일)으로 잘려 반환되는 것을 확인하여 전체본으로 채택하지 않음.
- 완료: 날짜 분할 CSV 38개를 `data/raw/mlb/2025/`에 보존. 일정 JSON을 포함한 총 39개 파일, 491,041,383바이트(약 468.3 MiB).
- 검증 결과: 712,528행, 2,430경기, 183,362타석. 공식 완료 경기 목록 대비 누락 0·추가 0, `(game_pk, at_bat_number, pitch_number)` 중복 0, 12개 카운트 모두 존재.
- 다운로드·파일별 해시·카운트별 행 수·검증 기록: `analysis/download_2025_status.json` (`status: complete`).
- 공개 CSV 주소 구성 참고: https://github.com/jldbc/pybaseball/blob/master/pybaseball/statcast.py. 위 MLB 이용 조건 확인과 재배포 미확인 상태는 유지한다.

## 2024 정규시즌 전체 확보 — 2026-09-07

- 출처와 확보 방식: 2025년과 동일한 MLB Baseball Savant Statcast Search CSV와 MLB Stats API 정규시즌 일정을 사용하고 날짜별로 분할 확보했다.
- 원본: 날짜 분할 CSV 39개와 `schedule_2024.json`을 `data/raw/mlb/2024/`에 보존. 총 485,572,494바이트(약 463.1 MiB).
- 검증: 711,899행, 실제 완료 2,429경기, 182,869타석. 일정 대비 누락 0·추가 0, 중복 투구 키 0, 12개 카운트 모두 존재.
- 일정 예외: gamePk 746577은 일정 응답의 상위 상태가 Final이지만 상세 상태가 `Cancelled`, 사유가 `Rain`인 2024-09-29 휴스턴–클리블랜드전이라 완료 경기에서 제외했다.
- 분석 대상: 실제 구종이 확인되는 709,226투구. 자동 판정 2,387건과 구종 결측은 구종 선택 분석에서 제외했다. 최종 결과 미확인 타석은 104개다.
- 재현·검증: `analysis/download_2024.py`, `download_2024_status.json`.
- 이용 조건과 해석 제한은 2025 자료와 동일하다. 원본 외부 공유 허용은 확인하지 않았으며, 비교 결과는 통제 전 관찰 통계다.

## 2024·2025 통합 분석 — 2026-09-07

- 사용자 결정: 시즌별 주요 결과의 차이가 작아 두 시즌을 하나의 표본으로 합쳐 이후 분석의 중심 데이터로 사용한다.
- 통합 범위: 4,859경기, 원본 1,424,427행, 실제 구종 확인 1,419,135투구, 366,231타석.
- 원본 관리: 연도별 원본 폴더를 합치거나 덮어쓰지 않는다. 통합 분석 코드가 두 폴더를 읽어 정제본을 재생성한다.
- 상세 결과: `analysis/count_analysis_2024_2025.md`.
- 통합 정제본: `data/processed/count_summary_2024_2025.csv`, `count_pitch_mix_2024_2025.csv`, `count_next_pitch_outcomes_2024_2025.csv`, `count_immediate_results_2024_2025.csv`, `count_plate_appearance_results_2024_2025.csv`, `count_game_context_2024_2025.csv`, `count_context_pitch_choices_2024_2025.csv`.
- 재현·검증: `analysis/analyze_counts_2024_2025_combined.py`, `count_analysis_2024_2025_combined_summary.json`.
- 2026-09-07 정리: 시즌별 정제본과 비교표·비교 보고서·비교 코드는 사용자 결정에 따라 제거했다. 통합 정제 데이터 7개만 유지한다.


## 모델 등록 및 구조 변경 — 2026-09-08

- 주 모델: [BCAI-OBS-v1.0.0](../../models/bcai/observed/v1.0.0/model_card.md), VALIDATED.
- 탐색 모델: [BCAI-RIDGE-v0.1.0](../../models/bcai/ridge/v0.1.0/model_card.md), EXPERIMENTAL. 인과·미래 예측 모델 아님.
- [OBS 실행](analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/README.md)과 [Ridge 실행](analysis/runs/bcai_ridge__mlb_2024_2025__20260907__r01/README.md)은 2026-09-07 공동 계산의 사후 등록이다. 결과는 OBS artifacts에 한 번만 저장하고 Ridge 열과 audit.model을 구분한다.
- 원본·정제본·캐시·기존 코드·통합 보고서의 위치는 유지했다. 결과 경로만 변경했으며 수치 재계산·KBO 분석·Drive/Docs 수정은 하지 않았다. 로컬 문서와 이미 업로드된 사본은 자동 동기화되지 않는다.
- [모델 레지스트리](../../models/registry.md), [새 실행 및 재현 절차](../../models/bcai/README.md)를 따른다.

