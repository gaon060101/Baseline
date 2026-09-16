# Baseline

MLB 데이터로 가설을 세우고 KBO 데이터로 검증하는 야구 분석 칼럼 프로젝트.

## 칼럼 목록

한 스레드에서 칼럼 한 편씩 진행한다. 새 스레드에는 칼럼 번호와 주제를 알려주고, 기존 작업을 이어갈 때는 해당 `column.md`를 기준으로 시작한다. 세부 작업 규칙은 `AGENTS.md`를 따른다.

| 번호 | 제목 | 상태 | 중심 문서 |
| --- | --- | --- | --- |
| 001 | 볼카운트별 상황 분석 | BCAP V2 2024·2025 개발 결과 산출·후속 검증 미실시(EXPERIMENTAL) · 기존 OBS/Ridge·BCAP V1 기록 보존 · KBO 미착수 | [첫 번째 칼럼](columns/001-ball-count/column.md) |

## 작업 구조

```text
Baseline/
├─ AGENTS.md
├─ README.md
├─ guides/
│  ├─ analysis.md
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
│     ├─ run.py / data.py / verify_bcap.py
│     ├─ refit_stability.py / supplement_diagnostics.py
│     ├─ build_report.py / finish_documents.py / record_invocations.py
│     └─ check_artifacts.py / finalize_seal.py
├─ tools/                # check_model_structure.py, check_ridge_v02.py
├─ columns/
│  └─ 001-ball-count/
│     ├─ column.md
│     ├─ sources.md
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
│     │  ├─ bcap_document_backups_20260909_r01/  # MD 갱신 전 보존
│     │  └─ runs/             # BCAI 및 BCAP 개발·외부·재학습·실패 실행 보존
│     │     ├─ bcai_obs__mlb_2024_2025__20260907__r01/  # README, manifest, artifacts
│     │     ├─ bcai_ridge__mlb_2024_2025__20260907__r01/  # 기존 공동 결과 참조
│     │     └─ bcai_ridge__mlb_*__20260908·20260909__r*/  # 신규 개발·외부·실패 실행 각각 보존
│     ├─ figures/
│     └─ publish/
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

2026-09-12: [BCAP V2 통합 개발 보고서](columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/report.html)를 완료했다. 2024·2025 개발 결과 산출, 후속 검증 미실시이며 세 모듈 모두 EXPERIMENTAL이다. 타자 상·하·좌·우·가운데 5구역의 모서리 중복은 보고 표에만 반영했다. 외부 검증·반복 재학습·별도 독립 검수는 후속 요청 범위다. 아래 2026-09-09 기록은 V1 이력이다.

2026-09-09: [BCAP 실제 보고서](columns/001-ball-count/analysis/bcap_v010_report_20260909.md)와 [갱신 인계](columns/001-ball-count/analysis/handoff_bcap_review.md)에 모델 구현·개발·외부 진단·독립 검산·8회 전체 재학습 안정성을 연결했다. 두 모델은 EXPERIMENTAL이며 모든 행동 추천을 보류한다. 2026 SWING은 측정 정합성 부족으로 전체 평가를 보류했다. 이어서 검수할 항목은 인과 식별·실시간 지각 자료·측정 교량·완전한 학습 불확실성이다.

이어서 할 업무 요청 시 [001의 다음에 이어서 할 업무](columns/001-ball-count/column.md#다음에-이어서-할-업무)를 기준으로 안내한다. 로컬 폴더만 주제에 맞춰 변경했고 드라이브에는 미반영.



## 분석 모델 목록

[모델 레지스트리](models/registry.md)를 기준으로 설계와 칼럼 실행을 분리한다. 현재 BCAI-OBS-v1.0.0은 VALIDATED 주 모델, BCAI-RIDGE-v0.1.0은 EXPERIMENTAL 민감도 모델이다. [BCAI 안내](models/bcai/README.md)에 단일 결과 보관 위치와 새 실행 절차를 기록했다. [2026-09-08 구조 변경 기록](models/migration_20260908.md) 참조. 이번 모델 구조 변경은 로컬만 반영하며 Drive/Docs 변경·데이터 재수집·KBO 분석은 수행하지 않는다.

2026-09-09 후속 작업: [BCAI-RIDGE-v0.2.0](models/bcai/ridge/v0.2.0/model_card.md)을 EXPERIMENTAL로 추가했다.2024·2025 개발,2023 외부 재현,2026-09-07까지 외부 시간 순방향 검증을 완료했다. [보고서](columns/001-ball-count/analysis/ridge_v02_validation_report.md). 요청 범위의2023·2026 원본만 새 스냅샷에 확보했으며 기존 입력·모델·실행은 보존했다.2026 첫 확보 실패 후 누락 경기만 보충한 이력을 분리한다. Drive/Docs·KBO에는 미반영.




## BCAP 실제 구현·평가 반영 — 2026-09-09

두 BCAP 모델은 EXPERIMENTAL이다. 실제 개발과 외부 진단·독립 검산을 수행했지만 행동 추천은 없으며 SWING의 2026 검증은 측정 정의 불일치로 보류했다. [모델 안내](models/bcap/README.md) · [주 보고서](columns/001-ball-count/analysis/bcap_v010_report_20260909.md) · [수정 MD와 변경 이력](columns/001-ball-count/analysis/bcap_document_update_20260909.json). 기존 BCAI 자산·원본·실행은 보존하고 KBO·Drive·외부 게시에는 반영하지 않았다.
