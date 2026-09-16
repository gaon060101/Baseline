# 팀원용 데이터 준비 안내

먼저 [공유 범위](github_sharing.md)와 [제외 파일 목록](excluded_files.json)을 확인한다. 보고서·집계표를 읽기만 한다면 데이터 다운로드는 필요 없다. 아래는 복원 경로 안내이며 이번 공유 작업에서 다운로드·재분석을 실행하지 않았다.

## 1. MLB에서 직접 확보하는 원본

[Baseball Savant Statcast Search](https://baseballsavant.mlb.com/statcast_search)의 투구별 CSV가 원자료다. 필드는 [공식 CSV 설명](https://baseballsavant.mlb.com/csv-docs)을 따른다(2026-09-16 문서 확인; 검색 화면 전체의 현재 동작은 재검증하지 못함). 최신 제공 범위·이용 조건을 먼저 확인하고, 접근 제한을 우회하지 않는다. 기존 [출처 기록](../columns/001-ball-count/sources.md)상 원본 재배포 권한은 미확인이다.

| 용도 | 대상 | 로컬 입력 위치 |
| --- | --- | --- |
| BCAI OBS·Ridge / BCAP 개발 | 2024·2025 정규시즌 전체, 모든 투구 | columns/001-ball-count/data/raw/mlb/2024/ 및 2025/ |
| 외부 과거 재현 | 2023 정규시즌 | data/raw/mlb/2023/snapshot_20260908_ridge_v02/ (칼럼 기준) |
| 개발 이후 외부 표본 | 2026 정규시즌 개막~2026-09-07 | data/raw/mlb/2026/snapshot_20260908_ridge_v02/ 및 supplement_20260909_ridge_v02/ |
| 기능 확인 표본 | 2026-09-01 | 본 분석 복원에는 불필요 |

1. 선수·카운트로 표본을 미리 좁히지 말고 필요한 연도·정규시즌·기간을 지정한다. 2026은 전체 시즌이나 오늘까지로 확장하지 않는다.
2. 상세 투구 CSV를 확보한다. 응답 행 수 제한에 잘렸는지 확인하고 필요한 경우 허용된 방식으로 날짜 구간을 나눈다. 파일 이름/구간은 제외 목록과 기존 수집 로그를 참고하되, 새 스냅샷으로 기록한다.
3. 최소 키/상황: game_pk, at_bat_number, pitch_number, game_date, game_year, game_type, balls, strikes, events, batter, pitcher, stand, p_throws, on_1b/2b/3b, outs_when_up, inning, inning_topbot, bat_score, fld_score, bat_score_diff, home_team.
4. 구종/행동·위치 모델은 pitch_type, pitch_name, description, type, plate_x, plate_z, sz_top, sz_bot, des 등 모델별 요구 필드도 필요하다. 이는 완전한 공통 스키마가 아니므로 각 모델의 input_fields와 prepare 코드가 요구하는 열을 대조한다. 파생 필드가 없다고 0으로 대체하지 않는다.
5. 공식 경기 일정과 venue 연결도 필요하다. 기존 코드는 MLB Stats API의 schedule 응답을 사용했다. 예: https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2024-01-01&endDate=2024-12-31&gameTypes=R . 연도·종료일을 대상에 맞추며 실제 완료 경기와 취소 경기를 구분한다. 일정 JSON도 Git에는 없고 별도 확보 대상이다.
6. 경기 목록 대비 누락/추가, 정규시즌 여부, 날짜, 투구 키 중복, 마지막 PA event, 필수 열을 검증한 뒤 출처·확보일·행 수·SHA256을 새로 기록한다.

기존 수집 구현은 [2024](../columns/001-ball-count/analysis/download_2024.py), [2025](../columns/001-ball-count/analysis/download_2025.py), [외부 확보/평가](../models/bcai/ridge/v0.2.0/external_validation.py), [2026 보충](../models/bcai/ridge/v0.2.0/complete_2026_snapshot.py)에 있다. **읽어볼 구현이지 무조건 실행하라는 명령이 아니다.** 일부는 수집과 분석을 함께 실행하고 기존 날짜별 출력 경로를 사용한다. 이용 조건 확인·새 출력 설정 없이 일괄 실행하지 않는다.

## 2. MLB에서 받을 수 없는 프로젝트 생성물

| 제외 자료 | 준비 경로 |
| --- | --- |
| advantage_input_cache.pkl | 2024·2025 원본 → analysis/inspect_advantage.py. 캐시가 없을 때만 생성 |
| 통합 count 집계 CSV | analysis/analyze_counts_2024_2025_combined.py. 현재 소형 집계표는 Git 포함; 재생성 시 기존 결과 보호 |
| BCAI 관찰/보정 결과·bootstrap | [BCAI 재현 안내](../models/bcai/README.md). 원본/캐시/통합표 → 새 BCAI_OUTPUT_DIR → 계산/검증 |
| Ridge v0.2 PA·행별 예측 | [모델 카드](../models/bcai/ridge/v0.2.0/model_card.md)와 ridge_v02.py / external_validation.py의 명령·입력·봉인 확인 |
| BCAP V1 정제 pickle | models/bcap/data.py의 --years, --output, --audit-dir; 원본에서 생성 |
| BCAP V2/FF 정제 pickle | V1 정제본 → development_v2/v0.2.0/prepare.py → pitch_ff/v0.1.0/prepare.py. 날짜별 고정 경로를 새 작업에 맞춰 확인 |
| scores / nuisance / folds / 행별 CSV | 해당 모델 재실행·별도 검수로 생성. MLB에서 다운로드 불가 |
| 실패 실행·당시 적합 객체 | 동일 바이트 복원 미보장. 필요하면 담당자와 환경·실행 이력 확인; 성공 결과를 실패 실행 파일로 위장하지 않음 |

BCAP는 [모델 안내](../models/bcap/README.md), [V2 개발 재현](../columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/reproduction.md), [외부 재현](../columns/001-ball-count/analysis/bcap_external_20260914__r01/reproduction.md)를 순서대로 확인한다. V2가 V1 pickle에 의존하므로 V2부터 바로 실행하지 않는다. 기존 출력/봉인은 보존하고 새 run ID 및 입력 스냅샷을 사용한다.

## 3. 실행 환경과 한계

기존 기록은 Python 3.12 계열과 [버전 고정 requirements](../models/bcai/ridge/v0.2.0/requirements.txt)의 numpy/pandas/scipy를 사용한다. 별도 가상환경에 설치한다. 설치된 runtime_ridge_v02 폴더를 Git에서 받는 방식이 아니다. 추가 라이브러리 요구는 실행할 코드별로 확인한다.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r models/bcai/ridge/v0.2.0/requirements.txt
```

공유본의 사용자별 절대 Python 경로는 본인 환경으로 바꾼다. 현재 일부 스크립트는 과거 날짜·경로를 고정하므로 완전한 원클릭 복원은 지원하지 않는다.

MLB 기록은 사후 정정될 수 있어 같은 기간을 다시 받아도 과거 파일 SHA256과 수치가 동일하다고 보장하지 않는다. 불일치는 기록하고 새 실행으로 구분한다. 2026 위치/존 측정 차이로 보류된 SWING·S/B를 단순 재다운로드로 검증 완료 처리하지 않는다. 모든 역사적 manifest를 그대로 충족해야만 하는 검사는 필요한 원본/객체를 복원하기 전 실행하지 않는다.

## 4. 추가로 확보할 수 있는 자료

새 칼럼에 필요한 다른 시즌·구속·회전·타구 속도/각도 등의 필드는 공식 CSV 설명과 실제 응답에서 가용 기간·결측을 확인한 뒤 선택한다. 데이터가 제공된다는 사실과 대량 수집/재배포 허용은 별개다. 현재 모델의 누락 파일을 채운다는 이유로 다른 시즌이나 KBO를 자동 수집하지 않는다.
