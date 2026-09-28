# Baseline

## 협업 공유 — 2026-09-28

백가온의 요청으로 오늘 완료 업무와 앞선 미공유 기반 문서를 GitHub 공유 대상으로 정리했다. 최신 원고는 본문 15차와 모델 해설 15차이며, 2015–2025 R 분석·역사 비교는 완료 상태다. [이번 인수인계](collaboration/pending/20260928-210719-gaon-daily-share/changes.md)와 [팀원용 프롬프트](collaboration/pending/20260928-210719-gaon-daily-share/continuation_prompt.md)를 시작점으로 삼는다. 실제 전송 상태·내용 커밋은 인수인계에서 확인한다. 아래의 과거 ‘push 미실시’는 당시 기록이며, Drive/Docs·블로그 게시와 Git 공유는 별개다.


## 최신 작업 상태 — 2026-09-28 모델 해설 15차

[BCAI](columns/001-ball-count/publish/naver_20260918/02_bcai.html)·[BCAP](columns/001-ball-count/publish/naver_20260918/03_bcap.html)를 계산 순서 중심의 설명형 원고로 수정했다. 초반에는 본문의 표를 재사용하고 계산 도중의 분석 결과 서술을 제거했다. [수정·보존·검수 기록](columns/001-ball-count/publish/naver_20260918/revision_v15.md). 본문·문헌·검증 글은 보존했으며 로컬 사용자 검토 단계다. 아래는 이전 작업 이력이다.

2026-09-28: [볼카운트 본문 15차](columns/001-ball-count/publish/naver_20260918/01_ball_count.html)의 참고문헌 연구 결과 보완을 끝으로 사용자 요청에 따른 본문 편집을 마무리했다. 추가 요청 전까지 유지한다. [수정·검수 기록](columns/001-ball-count/publish/naver_20260918/revision_v15.md). 외부 게시·업로드는 미실시다.

## 최신 작업 상태 — 2026-09-28 11시즌 원고 반영 완료

사용자 요청으로 [볼카운트 연재 7차 검토본](columns/001-ball-count/publish/naver_20260918/index.html)을 완성했다. 본문·BCAI·BCAP·검증 글의 결론과 표·그림을 2015–2025로 갱신하고 문헌 해설의 연결을 맞췄다. [수정·근거·검수 기록](columns/001-ball-count/publish/naver_20260918/revision_v7.md). 기존 승인 원고는 수정 전 보관본으로 남겼다. BCAP EXPERIMENTAL·2026 위치/스윙 보류를 유지하며 외부 게시·업로드는 미실시다. 아래는 이전 작업 이력이다.

## 최신 작업 상태 — 2026-09-28 역사 비교 보고서 완료

기존 2024–2025 주장과 추가 2015–2023 증거를 대조하고 전체 11시즌을 정리한 [비교 보고서](columns/001-ball-count/analysis/history_comparison_20260928_r01/report.html)를 완료했다. 주장 비교 14건·한국어 그림 5장·파생 표·재사용 R 코드와 근거 장부를 포함한다. [최종 검수](columns/001-ball-count/analysis/history_comparison_20260928_r01/audit/final_review.md): 저장 수치 검사 13개, 13개 HTML의 PC·모바일 화면과 링크 검사 통과. 승인 원고·기존 모델 실행을 보존했으며 BCAP EXPERIMENTAL과 2026 위치·스윙 보류를 유지한다. 아래 계산·편집 상태는 이전 이력이다.

## 최신 작업 상태 — 2026-09-28 R 전 연도 계산·검수 완료

2024·2025 BCAI와 BCAP 네 모듈의 R 재현·대조 및 2023→2015 적용을 모두 마쳤다. 2015~2025 전 11시즌의 결과와 재사용 코드·한국어 블로그 PNG를 준비하고 수치·PC·모바일 화면을 확인했다. 2026은 9월 7일까지·2025 고정 가중치의 별도 보조 결과(BCAI·구종 2종)이며 위치·스윙은 측정 보류다. [BCAI 결과](columns/001-ball-count/analysis/r_history_20260928/report.html) · [BCAP 결과](columns/001-ball-count/analysis/r_bcap_history_20260928/report.html) · [2026 보조](columns/001-ball-count/analysis/r_supplement_20260928/report.html) · [완료·검수 기록](columns/001-ball-count/analysis/r_history_20260928/completion.md) · [R 재사용 안내](guides/r_setup.md) · [칼럼 상태](columns/001-ball-count/column.md#current-status). BCAP은 EXPERIMENTAL을 유지한다. 아래는 이전 이력이다.

## 최신 작업 상태 — 2026-09-28 일시 중단

사용자의 “잠깐 멈춰봐” 지시로 R 추가 분석과 자료 수집을 중단했다. BCAI 2022~2025와 BCAP PITCH 2024·2025 R 계산까지 완료됐으며 후속 계산·통합 검수는 미완료다. [칼럼 상태](columns/001-ball-count/column.md#current-status)를 기준으로 명시적인 재개 요청을 기다린다. 아래는 중단 전 이력이다.

## R 분석 진행 — 2026-09-28

사용자가 재개를 지시해 **BCAI 2024·2025 R 재계산과 연도 차이 분석을 완료**했다. [실행 기록](columns/001-ball-count/analysis/runs/bcai_r_check__mlb_2024_2025__20260928__r02/manifest.json) · [R 연결 안내](guides/r_setup.md). 기존 점추정·표본을 재현했고, 2023부터 2015까지 순차 적용과 BCAP R 구현을 진행 중이다. 실제 연도별 완료 여부는 [진행표](columns/001-ball-count/analysis/r_history_20260928/progress.json)와 칼럼 상태를 따른다. 기존 원고 검토 상태는 아래와 같다.

## 현재 편집 상태 — 2026-09-27

**최신: 본문 6차.** 질문 → 짧은 답과 결과 → 상세 풀이의 흐름을 복원했다. 5차의 목차·새 표는 유지한다. [본문 MD](columns/001-ball-count/publish/naver_20260918/01_ball_count.md) · [6차 기록](columns/001-ball-count/publish/naver_20260918/revision_v6.md). 아래 5차 설명은 이전 이력이다.

**추가 피드백 반영:** 01 본문을 5차 구조 개편본으로 갱신했다. 각 분석 장을 간단 설명 → 결과 한눈에 보기 → 상세 설명으로 통일하고 표 6개를 새로 구성했다. [본문 MD](columns/001-ball-count/publish/naver_20260918/01_ball_count.md) · [5차 기록](columns/001-ball-count/publish/naver_20260918/revision_v5.md). 02–05 원고와 기존 공유 ZIP은 4차 상태다. 아래 4차 설명은 이전 편집 이력이다.

001의 원고 수정 계획이 승인되어 편집을 재개했다. [다섯 편의 읽기 화면](columns/001-ball-count/publish/naver_20260918/index.html)과 [4차 수정 기록](columns/001-ball-count/publish/naver_20260918/revision_v4.md)을 기준으로 사용자 검토를 받는다. 본문은 결과·야구 이야기 중심으로 줄이고 검증·개발 과정은 ⑤로 분리했다. 원본·분석·모델 상태는 유지한다. 아래 9월 26일의 편집 중단은 당시 기록이며 현재는 재개 후 검토 단계다. 외부 게시·공동 Docs 반영·업로드는 미실시다.


MLB 데이터로 가설을 만들고 KBO 데이터로 검증하는 야구 분석 칼럼 프로젝트다. 칼럼 한 편을 하나의 폴더·작업으로 관리한다.

## 현재 작업 — 2026-09-28 11시즌 반영 7차 원고 검토

| 칼럼 | 상태 | 시작 문서 |
| --- | --- | --- |
| 001. 볼카운트별 상황 분석 | 11시즌 반영 7차 원고·수치·화면 검수 완료 · 이전 원고 보관 · KBO 미착수 | [현재 상태](columns/001-ball-count/column.md#current-status) · [인수인계](columns/001-ball-count/column.md#handoff) |

상태의 상세 기준은 `column.md` 상단이다. 사용자가 9월 27일 수정 계획을 승인해 편집을 재개했다. 다섯 편 모두 [읽기 화면](columns/001-ball-count/publish/naver_20260918/index.html)에서 확인한다. [데이터·검증 글](columns/001-ball-count/publish/naver_20260918/05_data_validation.html)의 HTML과 글 사이 연결을 추가했다. 과거 원고는 보존했고 분석·모델·공동 Docs는 변경하지 않았다.

## 새 작업에서 읽을 순서

1. [공통 지침](AGENTS.md)을 확인한다.
2. 해당 [칼럼의 현재 상태·인수인계](columns/001-ball-count/column.md#current-status)를 읽고 요청 범위를 정한다.
3. [Codex 작업 안내](guides/codex_workflow.md)에 따라 필요한 지침·출처·대상 파일만 읽는다. 과거 대화나 모든 원본 CSV를 읽을 필요는 없다.

GitHub로 함께 작업할 때는 [협업 폴더](collaboration/README.md)에서 대기 인수인계도 먼저 읽는다. 백가온·박민수의 코멘트와 읽음 확인을 분리하며, 양쪽 확인과 Git 보존 조건이 충족된 건만 대기 폴더에서 지운다.

## 구조와 기준 위치

아래는 주요 역할별 구조다. 데이터·코드·실행·원고·그림의 기존 경로는 유지한다.

```text
Baseline/
├─ AGENTS.md                      # 공통 작업 규칙
├─ README.md                      # 시작점·칼럼 목록
├─ README_history_20260926.md      # 정리 전 README 원문 보관
├─ collaboration/                 # Git push별 임시 인수인계
│  ├─ templates/                  # 변경사항·팀원 코멘트 양식
│  └─ pending/                    # 양쪽 확인 전 기록만 유지; 안내는 상시 유지
├─ guides/                        # 공통 분석·집필·협업·데이터 준비 원칙
│  ├─ codex_workflow.md           # 작업별 최소 문맥·종료 절차
│  └─ organization_20260926.md     # 이번 문서 정리·검증 기록
├─ models/
│  ├─ registry.md                 # 모델 ID·버전·상태·실행 연결의 기준
│  ├─ bcai/                       # observed, ridge, state_delta
│  └─ bcap/                       # 구종·위치·스윙·분해 등 모델 정의와 코드
├─ columns/001-ball-count/
│  ├─ column.md                   # 현재 상태·결정·인수인계·날짜별 이력
│  ├─ sources.md                  # 출처·확보 조건·원문 확인 범위
│  ├─ collaboration.md            # 공동 문서 연결·업로드 기록
│  ├─ data/{raw,processed}/       # 원본·정제 데이터; 일부는 로컬 전용
│  ├─ analysis/                   # 분석 코드·보고서·과거 인계
│  │  └─ runs/<run_id>/manifest.json
│  ├─ figures/                    # 결과 그림·제작/검수 자료
│  └─ publish/naver_20260918/      # 날짜별 원고 MD·기존 HTML·수정 이력
├─ shared/                        # 공유용 자료
└─ tools/                         # 구조·검증 도구; 실행 전 쓰기 동작 확인
```

분석 정의·상태는 [모델 레지스트리](models/registry.md), 해석 원칙은 [분석 지침](guides/analysis.md), 집필 원칙은 [집필 지침](guides/writing.md)을 따른다. 현재 원고의 상태와 모델 검증 상태를 혼동하지 않는다.

## 로컬·GitHub·공동 문서의 구분

- Git 공유 범위와 제외 자료 복원은 [공유 안내](guides/github_sharing.md) · [데이터 준비](guides/data_setup.md) · [제외 목록](guides/excluded_files.json)이 기준이다. 보고서 열람에 데이터 재수집은 필요하지 않다. 제외 목록은 작성일이 있는 기록이며 모든 미추적 파일의 목록이 아니다.
- push 인수인계의 읽음·정리 조건은 [협업 운영 규칙](guides/collaboration.md#git-handoff)이 기준이다. 폴더 생성만으로 push·상대의 읽음·삭제가 완료된 것은 아니다.
- 날짜별 로컬 원고는 공동 Google Docs를 자동 대체하지 않는다. 공동 편집의 최신본·업로드 절차는 [협업 지침](guides/collaboration.md)과 [001 협업 기록](columns/001-ball-count/collaboration.md)을 따른다.
- 로컬 저장, Git 커밋·push, Drive/Docs 반영, 블로그 게시는 별도 작업이다. 이번 정리는 로컬 문서에만 반영했으며 원격 최신 상태는 확인하지 않았다.

## 이력

[정리 전 README 원문](README_history_20260926.md)은 날짜별 과거 기록이다. 그 안의 ‘현재’, ‘최신’, ‘다음 작업’은 당시 시점을 뜻하며 편집 재개 지시가 아니다. [2026-09-26 정리 보고서](guides/organization_20260926.md)에 변경 범위·상태 차이·보존 검증을 기록했다.
