# 001 협업 기록

## GitHub 공유 — 2026-09-28

백가온 요청으로 오늘 완료 업무·재사용 코드·원고·검수·보관본과 앞선 미공유 기반 문서를 정리했다. [인수인계와 전송 상태](../../collaboration/pending/20260928-210719-gaon-daily-share/changes.md), [팀원용 이어가기 프롬프트](../../collaboration/pending/20260928-210719-gaon-daily-share/continuation_prompt.md). Drive/Docs 반영이나 팀원 읽음 확인은 수행하지 않았다.


## 위치

- 칼럼 폴더: https://drive.google.com/drive/folders/1fthOKlpTFBMbAAZ6win-o6uHUiKPVJor
- 공동 원고 폴더: https://drive.google.com/drive/folders/1t7biefeXPeFKFmoNs_SWpgmcz3wHekQb
- 정제 데이터: https://drive.google.com/drive/folders/1q0K4EfDErBTW1xuKxui6S4mZmA7-E_Rh
- 차트: https://drive.google.com/drive/folders/1vVtj27L7kWEXtUjUMIkU8i4tA8YxK-gw
- 출처와 분석 설명: https://drive.google.com/drive/folders/1-gBGEG2qhYVABYUO0aSclYXHSdBD86ZH
- 발행본: https://drive.google.com/drive/folders/1LEPICjrmQIMZ7JfvpVL04VNOjhj9AxXz

## 원고 상태

- Google Docs 공동 원고: [볼카운트 상황 분석 초안 - 가온](https://docs.google.com/document/d/154euYH3WOqZH0ck3T0FtT5uPo8aQXf_WOZr32BrgXY8/edit?usp=drivesdk)의 `개요` 탭은 유지하고, `상세` 탭에 2024·2025 MLB 통합 분석을 반영함.
- 공동 편집 원고의 최신본은 위 Google Docs의 `초안 작성` 탭이다. 현재는 완성 원고가 아닌 간략한 본문 개요를 반영했다. 로컬 `outline_mlb.md`는 이번 전송 원본이며 이후 Docs의 공동 편집 내용을 먼저 확인한 뒤 동기화한다. `column.md`는 결정·분석 결과·연결을 관리한다.
- 칼럼 주제: 볼카운트별 상황 분석. 2024·2025 MLB 통합 결과를 중심 데이터로 사용함.

## 반영 이력

- 2026-09-14: 사용자의 요청으로 기존 Google Docs 세 탭을 수정했다. `카운트 비교 분석 (BCAI)`의 기존 등급표·12카운트 표와 작성자 표기는 유지하고, 초기 Ridge 설명을 v0.2.0의 α300·207개 적합 수렴·최대1.61포인트 이동·MSE0.428% 개선으로 교체했다. 점추정 순위 주의, 지수·W·분모·계산 기준·검증 범위·해석 한계를 추가했다. 비어 있던 `카운트 행동 분석 (BCAP)`에는 로컬 `bcap_explained.md`를 바탕으로 정의·보정·결과·외부 재현·2026 위치 보류·한계를 설명하는 본문을 넣었다. `초안 작성`에는 `outline_mlb.md`의 간략 개요를 반영했다. 해설 링크는 동일 Docs의 해당 탭으로 연결했고, 공개되지 않은 로컬 경로를 웹 링크로 넣지 않았다. 재조회로 세 탭의 삽입 내용·교체·BCAI 표2개·제목 및 링크 서식을 확인했다. 문서6개 탭의 이름·순서는 유지했고 다른 탭·공유 권한은 변경하지 않았다. 화면 렌더링 검사는 수행하지 않았다. [검증 기록](analysis/docs_sync_20260914/verification.json), 수정 전 대상 탭 사본은 `analysis/docs_sync_20260914/read_targets/`에 보존했다.

- 2026-09-07: Google Docs의 별도 `카운트별 비교 분석` 탭에 관찰 공격가치 판정식, 12개 카운트 지수·판정, 핵심 이유, ridge 보정의 역할·수렴·설명력 한계를 기록함. 위치를 잘못 잡아 `개요` 탭에 잠시 들어간 동일 블록은 제거했으며 재조회로 `개요` 미포함과 비교 분석 탭 반영을 확인함.
- 2026-09-07: 전체 분석 보고서 `analysis/count_advantage_2024_2025.md`를 `04-출처와분석설명` 폴더에 `count_advantage_2024_2025_2026-09-07_v01.md`로 업로드했다. [보고서 열기](https://drive.google.com/file/d/13ynadLlMGQCEQwsLsU0NFk5r2njhFwQv/view?usp=drivesdk). 업로드 응답의 부모 폴더와 재조회 목록의 파일명·text/markdown·32,133바이트를 확인했다. 보고서 MD 한 파일만 반영했으며 기존 공동 원고와 공유 권한은 변경하지 않았다.
- 2026-09-07: 제미나이 편집으로 변경된 Google Docs `상세` 탭을 사용자 최초 양식에 맞춰 재생성함. 네이티브 표 35개를 제거하고 12개 카운트마다 1~6번 항목을 일반 텍스트로 복구했으며, 분석표 10개와 하단 약어 정의를 다시 추가함. `개요` 탭은 유지함.
- 2026-09-07: Google Docs `상세` 탭 하단에 `약어 정의`와 `구종 약어` 섹션을 추가함. 본문·분석표의 결과, 타격 행동, 경기 상황, 구종 약어를 영문 원어와 한글 뜻으로 정리하고 문서 재조회로 반영을 확인함.
- 2026-09-07: Google Docs [볼카운트 상황 분석 초안 - 가온](https://docs.google.com/document/d/154euYH3WOqZH0ck3T0FtT5uPo8aQXf_WOZr32BrgXY8/edit)에 2024·2025 통합 데이터 반영. `개요` 탭은 유지하고 `상세` 탭의 12개 카운트에 1~5번 분석과 6번 코멘트를 완성함. B·S·BIP·CS·SwStr·F·H·K·BB·OUT·HBP·FB·NFB·RV/100 등 영문 약어를 사용하고, 기존 출처 파일 대응표는 삭제함. 하단에는 지금까지 요청한 순위·분석표 10개(카운트 점유율, S%, B%, BIP%, S/B/BIP 전체표, 구종 Top 3, FB/NFB, FB% 순위, NFB% 순위, MLB 전체 구종 사용량)를 원문 표 형식으로 추가함. 재조회 결과 카운트 12개, 각 1~6번 12개, 분석표 제목 10개, 빈칸 0개, 기존 출처 대응표 0개를 확인함.
- 2026-09-07: 정제 데이터 폴더의 기존 `count_analysis_2025_2026-09-06_v01.md`를 삭제하고, 2024·2025 통합 정제 CSV 7개를 업로드. 폴더 목록에서 기존 MD가 없고 CSV 7개만 존재하는 것을 확인함.
- 2026-09-06: `analysis/count_analysis_2025.md`를 정제 데이터 폴더에 `count_analysis_2025_2026-09-06_v01.md`로 업로드. 업로드 후 폴더 목록에서 이름·형식·위치를 확인함.
- 2026-09-06: 현재 로컬 `column.md`를 공동 원고 폴더에 `볼카운트별_상황분석_column_2026-09-06_v01.md`로 업로드. 기존 팀원 Google Docs는 수정하지 않음. 업로드 후 폴더 목록에서 이름·형식·위치를 확인함.
- 2026-09-06: 로컬 폴더를 001-ball-count로 변경하고 기획·다음 업무를 저장. 드라이브 폴더와 공유 사본은 변경하지 않음.

- 2026-09-05: 드라이브에 칼럼 폴더와 하위 5개 폴더 생성. 데이터·차트·본문은 아직 업로드하지 않음.
- 2026-09-05: 최상위 드라이브 폴더에 프로젝트 공통 안내 업로드 완료. `guides/collaboration.md` → [협업안내.md](https://drive.google.com/file/d/1XoIaTEqy2PPCdGqNAf4U1ZICFSxJZJgg/view?usp=drivesdk), `README.md` → [프로젝트구조.md](https://drive.google.com/file/d/1VLAuu_1xRZF4oqGuFguQYTvDpuFBSCfD/view?usp=drivesdk). 초기 버전 v01, 업로드 응답과 폴더 목록으로 이름·부모 폴더 확인. 업로드된 README의 상대경로는 로컬 프로젝트용이며 드라이브 문서 간 링크로는 작동하지 않는다.

## 산출물 업로드 기록

### GitHub 공유 준비 — 2026-09-16

대상: https://github.com/gaon060101/Baseline . 사용자 요청에 따라 원본·행별 자료·캐시·적합 객체·설치 라이브러리를 제외하고 코드·문서·집계 결과를 공유한다. [제외 목록](../../guides/excluded_files.json)과 [팀원 데이터 준비 안내](../../guides/data_setup.md)를 추가했다. 로컬 데이터는 유지하고 신규 수집·재분석·Drive/Docs 변경은 하지 않는다. 전송 완료 여부는 원격 main 커밋과 현재 로컬 커밋을 비교하여 확인한다. 아래 표는 기존 Drive 이력이다.


| 일자 | 로컬 파일 | 버전 | 드라이브 파일 링크 | 검증 결과 |
| --- | --- | --- | --- | --- |
| 2026-09-07 | `analysis/count_advantage_2024_2025.md` | v01 | [전체 분석 보고서](https://drive.google.com/file/d/13ynadLlMGQCEQwsLsU0NFk5r2njhFwQv/view?usp=drivesdk) | 출처와분석설명 폴더·파일명·text/markdown·32,133바이트 확인 |
| 2026-09-07 | `data/processed/count_summary_2024_2025.csv` | 통합 | [카운트 기본 요약](https://drive.google.com/file/d/1V2DHS7aWhsnuSCCgj3OCSnsN28Pj-BQ_/view?usp=drivesdk) | text/csv·정제 데이터 폴더 확인 |
| 2026-09-07 | `data/processed/count_pitch_mix_2024_2025.csv` | 통합 | [구종 선택](https://drive.google.com/file/d/1tSv3QqnQyiQpJ_xqwd_2jKBnvcP3kAjM/view?usp=drivesdk) | text/csv·정제 데이터 폴더 확인 |
| 2026-09-07 | `data/processed/count_next_pitch_outcomes_2024_2025.csv` | 통합 | [다음 공 판정](https://drive.google.com/file/d/19LjmldiJ7E9szIxT_ZcLoc9x3u627F4k/view?usp=drivesdk) | text/csv·정제 데이터 폴더 확인 |
| 2026-09-07 | `data/processed/count_immediate_results_2024_2025.csv` | 통합 | [다음 공 즉시 결과](https://drive.google.com/file/d/1ldYiP28_Q9K2gou4S7o1t9r46sqAlJmc/view?usp=drivesdk) | text/csv·정제 데이터 폴더 확인 |
| 2026-09-07 | `data/processed/count_plate_appearance_results_2024_2025.csv` | 통합 | [타석 최종 결과](https://drive.google.com/file/d/1jaPCD9m0HrhApXxFRjDHxNKzbymHcB6X/view?usp=drivesdk) | text/csv·정제 데이터 폴더 확인 |
| 2026-09-07 | `data/processed/count_game_context_2024_2025.csv` | 통합 | [경기 상황](https://drive.google.com/file/d/1NwE9OBdG92aC_XiAJcWLR9kqoXRC9LwB/view?usp=drivesdk) | text/csv·정제 데이터 폴더 확인 |
| 2026-09-07 | `data/processed/count_context_pitch_choices_2024_2025.csv` | 통합 | [상황별 구종 선택](https://drive.google.com/file/d/1i-HpWjI6bXbs1BstnPCcnrx63ymTju0l/view?usp=drivesdk) | text/csv·정제 데이터 폴더 확인 |
| 2026-09-06 | `analysis/count_analysis_2025.md` | v01 | 삭제됨 | 2026-09-07 사용자 요청으로 드라이브에서 삭제 |
| 2026-09-06 | `column.md` | v01 | [볼카운트별 상황분석 column](https://drive.google.com/file/d/1w5BM3SGVlIeLKsCBbSAXs_8t_pVnXvvd/view?usp=drivesdk) | 공동 원고 폴더에서 파일명·text/markdown 형식·파일 ID 확인 |

