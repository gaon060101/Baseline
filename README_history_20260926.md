# Baseline

## 2026-09-18 3차 원고 — 결과 우선·두괄식·서식 분리

001의 [읽기 화면](columns/001-ball-count/publish/naver_20260918/index.html)을 두괄식으로 갱신했다. BCAI·BCAP는 결과를 앞쪽에 모으고 계산을 뒤에서 설명한다. 본문 첫머리에 모델의 역할과 결과 요약을 두었으며, 결과·해석 메모·참고문헌을 독립 서식으로 구분했다. [수정 내역과 MD 목록](columns/001-ball-count/publish/naver_20260918/revision_v3.md). 최신 두괄식 요청이 이전 질문 우선 순서에 우선한다. 2차 원고는 `revisions/v2/`에 보관했고 사용자 검토 대기·외부 미게시 상태다.

## 2026-09-18 2차 집필 수정 — 설명 확장·문헌 해설 추가

001의 [읽기 화면](columns/001-ball-count/publish/naver_20260918/index.html)을 갱신했다. 세 원고의 기존 구조를 유지하면서 질문·비교·그림 읽기를 자세히 풀고, 해석 메모를 별도 상자로 표시했다. [참고문헌 한국어 해설](columns/001-ball-count/publish/naver_20260918/04_references_ko.md)은 원문 12건의 연구 내용·칼럼 인용 부분·개념 예시를 구분한다. [수정 기록](columns/001-ball-count/publish/naver_20260918/revision_v2.md). 이전 세 원고는 `publish/naver_20260918/revisions/v1/`에 보관했다. 사용자 검토 대기이며 분석·모델 상태와 외부 미게시 상태는 유지한다.

## 2026-09-18 네이버 블로그용 세 글 집필 완료 — 사용자 검토 대기

001의 [세 글 읽기 화면](columns/001-ball-count/publish/naver_20260918/index.html)을 만들었다. [볼카운트 본문](columns/001-ball-count/publish/naver_20260918/01_ball_count.md), [BCAI 설명](columns/001-ball-count/publish/naver_20260918/02_bcai.md), [BCAP 설명](columns/001-ball-count/publish/naver_20260918/03_bcap.md)을 상호 연결했다. 상세 개요·독후 의견·최신 후속 구현·검수를 반영했고, 표 12개와 차트·도식 8종을 기존 저장 결과에서 제작했다. [배치·원고 안내](columns/001-ball-count/publish/naver_20260918/README.md) · [집필 반영표](columns/001-ball-count/publish/naver_20260918/manuscript_source_map.md).

본문 사용 논문·분석 글 12건은 이번 집필에서 원문 본문을 재열람했다. 전문 미확인 자료는 제외했다. 네이버 게시·Drive/Docs 업로드는 하지 않았다. 기존 모델·원본·실행과 OBS/Ridge/BCAP 상태는 유지한다.

## 2026-09-18 후속 변경 제한적 검수

[검수 결과](columns/001-ball-count/analysis/runs/bcap_followup_review__mlb_2024_2025__20260918__r01/report.md). Sol 두 에이전트의 비중복 산술·구현 확인과 주 작업의 설계·해석 검토를 완료했다. 확인 범위에서 중대한 오류는 발견하지 못했다. 상태 표는 설명용 관찰 차이로 사용 가능하며 분해는 실제 학습 없는 DRAFT, 상대 반응·2026 위치 분석은 보류를 유지한다. 기존 모델·수치는 변경하지 않았다.


001 발표 자료: [간단 PT용 PPT 8장](columns/001-ball-count/publish/ball_count_pt_20260917.pptx) — 2026-09-17 상세 개요 기반, 약 5~7분 발표용 사용자 검토본. 제작·렌더링·검증 기록은 `columns/001-ball-count/figures/pt_build_20260917/`에 보관한다. 분석·모델 상태는 유지한다.

## 2026-09-17 후속 구현·간단한 확인 완료

다음 작업의 시작 문서: [BCAI·BCAP 후속 구현 인수인계](columns/001-ball-count/analysis/handoff_bcap_followup_20260917.md). 완료 결과·DRAFT 구현·보류 사유·재현 명령을 구분했다.

001의 [한국어 구현 보고서](columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md)·[HTML](columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.html)를 추가했다. 기존 S/B 개발·2023 결과는 재표시했고, BCAI 원 W에서 시즌별 상태 평균 차이 24행을 새로 계산했다. 상태 차이 모듈은 EXPERIMENTAL, 행동 가치 분해는 계산 코드와 모의 확인만 갖춘 DRAFT다. 상대 반응 시나리오는 결합값·공통 지원 미확보로 수치 보류한다. 전체 학습·전체 검증은 하지 않았으며 기존 BCAP 상태와 2026 위치 측정 보류를 유지한다.

아래는 앞선 작업 시점의 기록이다.

## 2026-09-17 실사용 참고문헌·개요 개정

001 칼럼의 [실사용 문헌 해설](columns/001-ball-count/references_in_use_20260917.md)·[미리보기](columns/001-ball-count/references_in_use_20260917.html)를 만들고 [집필 개요](columns/001-ball-count/outline_mlb.md)를 독후 의견에 맞춰 개정했다. 본문 12편의 본문을 확인했고 2024 미니맥스 연구는 전문 확보 전 조건부다. [모델 발전 검토](columns/001-ball-count/model_research_followup_20260917.md)와 [다른 작업 전달 프롬프트](columns/001-ball-count/model_followup_prompt_20260917.md)를 저장했다. 모델·실행 상태는 유지한다. KBO 선수 집단 특성은 후속 분석, 주자·아웃카운트는 다음 칼럼 후보로 기록했다.

## 2026-09-17 참고문헌 해설 심화

001 볼카운트 칼럼의 [한국어 참고문헌 해설집](columns/001-ball-count/reading_references_ko.md)과 [미리보기](columns/001-ball-count/reading_references_ko.html)를 개정했다. 45건의 실제 내용·결과·결론을 보강하고 본문/초록 확인 범위를 구별했다. 칼럼 집필 참고자료 보강 완료이며 모델·실행 상태는 기존과 같다.

MLB 데이터로 가설을 세우고 KBO 데이터로 검증하는 야구 분석 칼럼 프로젝트.

## GitHub 공유본 시작하기

이 저장소는 코드·문서·모델 정의·집계 결과 공유본입니다. 원본 데이터·대형 캐시·행별 예측·설치 라이브러리는 포함하지 않습니다. 로컬 원본은 삭제하지 않았습니다.

- [공유 범위](guides/github_sharing.md)
- [데이터 직접 확보·재생성 안내](guides/data_setup.md)
- [업로드 제외 파일별 목록](guides/excluded_files.json)

보고서 열람에는 다운로드가 필요 없습니다. 재분석할 팀원만 출처·이용 조건을 확인한 뒤 필요한 MLB 원본을 직접 확보하고 정제본/모델 객체를 새 실행으로 생성합니다. 과거 manifest가 참조하는 제외 파일은 클론에 없으므로 전체 검증은 입력 복원 전 실행할 수 없습니다.

## 칼럼 목록

한 스레드에서 칼럼 한 편씩 진행한다. 새 스레드에는 칼럼 번호와 주제를 알려주고, 기존 작업을 이어갈 때는 해당 `column.md`를 기준으로 시작한다. 세부 작업 규칙은 `AGENTS.md`를 따른다.

| 번호 | 제목 | 상태 | 중심 문서 |
| --- | --- | --- | --- |
| 001 | 볼카운트별 상황 분석 | 네이버용 본문·BCAI·BCAP 3편 초안 작성 / 사용자 검토 대기 · BCAP EXPERIMENTAL·2026 위치 보류·KBO 미착수 | [첫 번째 칼럼](columns/001-ball-count/column.md) |

## 작업 구조

001 참고문헌 읽기: [한국어 상세 해설집](columns/001-ball-count/reading_references_ko.md) · [미리보기](columns/001-ball-count/reading_references_ko.html) — 2026-09-17 자료 45건의 한국어 해설과 정식 제목·원문 링크 정리. 개요에서도 정식 제목으로 연결.

001 집필: [상세 개요](columns/001-ball-count/outline_mlb.md) · [미리보기](columns/001-ball-count/outline_mlb.html) — 2026-09-16 여섯 절의 문단·근거·자료 45건 활용 배치 정리 완료. 로컬 집필 제안이며 공동 Docs에는 미전송.

001 참고자료: [볼카운트 전반 리서치 — 2026-09-15](columns/001-ball-count/research_ball_counts_20260915.md). 해외 논문을 포함한 문헌·공식 자료 45건과 12카운트별 연구 질문 정리 완료. 기존 분석·모델 상태는 유지한다.

```text
Baseline/
├─ AGENTS.md
├─ README.md
├─ guides/
│  ├─ analysis.md
│  ├─ github_sharing.md
│  ├─ data_setup.md
│  ├─ excluded_files.json
│  ├─ writing.md
│  └─ collaboration.md
├─ models/
│  ├─ registry.md
│  ├─ migration_20260908.md / migration_20260908.json
│  ├─ bcai/
│  │  ├─ README.md
│  │  ├─ observed/v1.0.0/  # model_card.md, specification.yaml, validation.md
│  │  └─ ridge/
│  │     ├─ v0.1.0/      # 기존 모델 정의 보존
│  │     └─ v0.2.0/      # 정의·사전 계획·고정 코드·검증 문서
│  └─ bcap/
│     ├─ README.md / design_decisions.md / measurement_review.md
│     ├─ pitch/v0.1.0/ / swing/v0.1.0/  # 기존 카드·불변 명세·검증
│     ├─ pitch/v0.2.0/ / swing/v0.2.0/ / pitch_sb/v0.1.0/  # V2 개발
│     ├─ development_v2/v0.2.0/  # V2 준비·실행·보고·문서 연결
│     ├─ pitch_ff/v0.1.0/  # 포심/비포심 정의·코드·기본 확인
│     ├─ run.py / data.py / verify_bcap.py
│     ├─ refit_stability.py / supplement_diagnostics.py
│     ├─ build_report.py / finish_documents.py / record_invocations.py
│     └─ check_artifacts.py / finalize_seal.py
├─ tools/                # check_model_structure.py, check_ridge_v02.py
├─ columns/
│  └─ 001-ball-count/
│     ├─ column.md
│     ├─ sources.md
│     ├─ research_ball_counts_20260915.md  # 12카운트 전반·해외 논문 자료집
│     ├─ reading_references_ko.md / .html  # 45건 한국어 해설·읽기 순서
│     ├─ collaboration.md
│     ├─ data/
│     │  ├─ raw/mlb/
│     │  ├─ raw/kbo/
│     │  └─ processed/
│     ├─ analysis/        # 기존 코드·캐시·통합 보고서·인계 유지
│     │  ├─ bcai_paths.py
│     │  ├─ bcap_original_handoff_20260909/  # 원 인계·문서 스냅샷 보존
│     │  ├─ bcap_implementation_review_20260909/  # 독립 검산·보조 표
│     │  ├─ bcap_report_20260909_r01/  # 16종 CSV·보고 manifest
│     │  ├─ bcap_v2_development_20260912__r01/  # V2 통합 보고·CSV·변경 기록
│     │  ├─ bcap_pitch_classification_20260912__r01/  # FB/NFB·FF/non-FF 비교 보고
│     │  ├─ bcap_document_backups_20260909_r01/  # MD 갱신 전 보존
│     │  └─ runs/             # BCAI 및 BCAP 개발·외부·재학습·실패 실행 보존
│     │     ├─ bcai_obs__mlb_2024_2025__20260907__r01/  # README, manifest, artifacts
│     │     ├─ bcai_ridge__mlb_2024_2025__20260907__r01/  # 기존 공동 결과 참조
│     │     └─ bcai_ridge__mlb_*__20260908·20260909__r*/  # 신규 개발·외부·실패 실행 각각 보존
│     ├─ figures/
│     │  └─ naver_20260918/  # PNG 차트·도식 8종, 입력 기록, 표시 검토 이미지
│     └─ publish/
│        └─ naver_20260918/  # 세 원고·문헌 해설 MD/HTML, 근거표, 그림 묶음, revisions/v1·v2 이전본
└─ shared/
```

이 트리는 프로젝트 구조의 기준 문서다. 폴더 역할을 변경하거나 공통 구조를 확장할 때 함께 갱신한다. 빈 폴더는 Git에 자동 보존되지 않으므로 새 환경에서는 이 구조를 참고해 필요한 폴더를 생성한다.

- `AGENTS.md`: 프로젝트 작업 규칙과 MD 반영·보고 규칙
- `guides/analysis.md`: 가설 설계, 데이터 검증, 해석 기준
- `guides/writing.md`: 원고·출처·발행 자료 작성 기준
- `guides/collaboration.md`: 드라이브 업로드와 공동 집필 운영 기준
- `columns/`: 칼럼별 원고, 출처, 데이터, 분석, 차트, 발행본
- `shared/`: 여러 칼럼에서 실제로 재사용하게 된 코드

각 칼럼은 `column.md`에서 질문·가설·분석 설계·본문·남은 확인 사항을 관리한다. 출처와 데이터 확보 이력은 같은 폴더의 `sources.md`에 기록한다.

진행 순서: 기획 → 자료 확보 → 분석 → 집필 → 검토 → 발행.
MLB 탐색 뒤 KBO 검증 전에 가설과 판단 기준을 기록한다. 분석 결과에 따라 이전 단계로 돌아갈 수 있다.

새 칼럼에는 필요한 폴더만 만든다. 001에는 향후 작업을 위한 기본 폴더를 준비해 두었다. 주제가 정해지면 폴더 이름과 이 목록을 함께 갱신한다.

## Google Drive 협업

- [Baseline 공유 대상 폴더](https://drive.google.com/drive/folders/1kIsnL50yB1T7tkCkAqDhAcct9k_sZbVs)
- [첫 칼럼 드라이브 폴더](https://drive.google.com/drive/folders/1fthOKlpTFBMbAAZ6win-o6uHUiKPVJor)
- 업로드 정책: [협업 지침](guides/collaboration.md)
- 칼럼별 파일 링크와 업로드 이력: [001 협업 기록](columns/001-ball-count/collaboration.md)

로컬 Baseline과 드라이브는 자동 동기화 설정된 관계가 아니다. 현재는 플러그인을 통한 명시적 업로드 방식으로 운영한다. 드라이브 폴더 생성·업로드는 팀원 초대나 외부 발행과 구분한다.

## 다음 작업

2026-09-12 추가 비교: [FB/NFB와 포심/비포심 보고서](columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/report.html). 기존 FB는 재학습 없이 재사용하고 FF만 새로 학습했다. 자체·공통 표본을 비교했고, 0-0의 작은 범위와3-2 비포심 방향의 제한된 개발 단서를 남겼다. 요청 범위에서 완료·종료했으며 외부 검증/추가 개선은 진행하지 않는다.

2026-09-12: [BCAP V2 통합 개발 보고서](columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/report.html)를 완료했다. 2024·2025 개발 결과 산출, 후속 검증 미실시이며 세 모듈 모두 EXPERIMENTAL이다. 타자 상·하·좌·우·가운데 5구역의 모서리 중복은 보고 표에만 반영했다. 외부 검증·반복 재학습·별도 독립 검수는 후속 요청 범위다. 아래 2026-09-09 기록은 V1 이력이다.

2026-09-09: [BCAP 실제 보고서](columns/001-ball-count/analysis/bcap_v010_report_20260909.md)와 [갱신 인계](columns/001-ball-count/analysis/handoff_bcap_review.md)에 모델 구현·개발·외부 진단·독립 검산·8회 전체 재학습 안정성을 연결했다. 두 모델은 EXPERIMENTAL이며 모든 행동 추천을 보류한다. 2026 SWING은 측정 정합성 부족으로 전체 평가를 보류했다. 이어서 검수할 항목은 인과 식별·실시간 지각 자료·측정 교량·완전한 학습 불확실성이다.

이어서 할 업무 요청 시 [001의 다음에 이어서 할 업무](columns/001-ball-count/column.md#다음에-이어서-할-업무)를 기준으로 안내한다. 로컬 폴더만 주제에 맞춰 변경했고 드라이브에는 미반영.



## 분석 모델 목록

[모델 레지스트리](models/registry.md)를 기준으로 설계와 칼럼 실행을 분리한다. 현재 BCAI-OBS-v1.0.0은 VALIDATED 주 모델, BCAI-RIDGE-v0.1.0은 EXPERIMENTAL 민감도 모델이다. [BCAI 안내](models/bcai/README.md)에 단일 결과 보관 위치와 새 실행 절차를 기록했다. [2026-09-08 구조 변경 기록](models/migration_20260908.md) 참조. 이번 모델 구조 변경은 로컬만 반영하며 Drive/Docs 변경·데이터 재수집·KBO 분석은 수행하지 않는다.

2026-09-09 후속 작업: [BCAI-RIDGE-v0.2.0](models/bcai/ridge/v0.2.0/model_card.md)을 EXPERIMENTAL로 추가했다.2024·2025 개발,2023 외부 재현,2026-09-07까지 외부 시간 순방향 검증을 완료했다. [보고서](columns/001-ball-count/analysis/ridge_v02_validation_report.md). 요청 범위의2023·2026 원본만 새 스냅샷에 확보했으며 기존 입력·모델·실행은 보존했다.2026 첫 확보 실패 후 누락 경기만 보충한 이력을 분리한다. Drive/Docs·KBO에는 미반영.




## BCAP 실제 구현·평가 반영 — 2026-09-09

두 BCAP 모델은 EXPERIMENTAL이다. 실제 개발과 외부 진단·독립 검산을 수행했지만 행동 추천은 없으며 SWING의 2026 검증은 측정 정의 불일치로 보류했다. [모델 안내](models/bcap/README.md) · [주 보고서](columns/001-ball-count/analysis/bcap_v010_report_20260909.md) · [수정 MD와 변경 이력](columns/001-ball-count/analysis/bcap_document_update_20260909.json). 기존 BCAI 자산·원본·실행은 보존하고 KBO·Drive·외부 게시에는 반영하지 않았다.
