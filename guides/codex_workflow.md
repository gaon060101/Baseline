# Codex 작업 안내

이 프로젝트는 대화 기록 대신 담당 문서에 결정을 남긴다. 기존 폴더 구조를 사용하며 새 작업마다 전체 문서를 읽거나 데이터를 수집하지 않는다.

## 시작: 공통 문맥 다음에 작업별 문맥

먼저 [AGENTS.md](../AGENTS.md) → [README](../README.md) → 해당 칼럼 `column.md`의 현재 상태·인수인계를 읽는다. 현재 칼럼은 [001 볼카운트](../columns/001-ball-count/column.md#current-status)다. `git status --short`로 기존 변경을 확인한 다음 아래에서 필요한 자료만 추가한다.

Git 협업 작업은 [대기 인수인계](../collaboration/pending/README.md)도 확인한다. 지정된 팀원 관점에서 실제 내용을 읽은 뒤에만 자기 코멘트 파일에 확인 주체·버전을 기록한다. 삭제는 [양쪽 확인과 Git 보존 조건](collaboration.md#git-handoff)을 모두 만족한 건에 한정한다.

| 요청 종류 | 추가로 읽을 최소 자료 | 결과를 기록할 곳 |
| --- | --- | --- |
| 상태 확인·인수인계 | 요청과 관련된 출처·보고서, `column.md`의 현재 상태 | `column.md`; 목록·한 줄 상태 변경 시 README |
| 분석 설계·결과 해석 | [분석 지침](analysis.md), 해당 `sources.md` 항목, 대상 실행의 manifest·보고서 | 칼럼 결정·분석 보고서; 신규 실행은 새 run ID |
| 모델 변경·검증 | 분석 지침의 모델 관리, [레지스트리](../models/registry.md), 해당 버전 카드·명세·검증·연결된 실행 | 해당 모델 정의·레지스트리·칼럼 실행 연결 |
| 원고 검토·집필 | [집필 지침](writing.md), 지정 원고, 관련 출처·원문 확인 기록 | 승인된 원고와 칼럼 결정; 중단 상태면 검토·보류 기록만 |
| 발행 준비 | 집필 지침, 해당 `publish/` README·원고·그림 배치, 생성/검수 스크립트의 실제 쓰기 대상 | 요청된 발행 자료·칼럼 상태; 외부 게시와 구분 |
| Git 공유·데이터 준비 | [협업 인수인계](../collaboration/README.md), [공유 안내](github_sharing.md), [준비 안내](data_setup.md), [제외 목록](excluded_files.json), 필요한 출처 | push별 변경사항·팀원 코멘트·읽음, 공유 지침·제외 목록·칼럼 상태; 재수집은 명시된 범위만 |
| 공동 집필·Drive/Docs | [협업 지침](collaboration.md), 해당 칼럼 `collaboration.md`, 요청된 공동 문서의 최신 내용 | 칼럼 협업 기록; 실제 반영 성공 여부와 범위 |

현재 상태를 찾는 데 과거 대화·모든 보고서·원본 CSV 전체 로드는 필요하지 않다. 증거가 충돌하면 문서의 날짜·역할·실제 파일을 대조하고, 확인되지 않은 항목은 ‘미확인’으로 남긴다. 단순히 더 늦은 수정 시각만으로 기존 모델 상태나 공유 문서 소유권을 바꾸지 않는다.

## 기준 위치와 작업 경계

- 공통 규칙은 AGENTS와 해당 guide, 칼럼의 현재 상태는 `column.md`, 모델 정의·상태는 `models/`, 실행 증거는 `analysis/runs/<run_id>/manifest.json`이 기준이다. 과거 이력은 당시 상태를 보존하는 자료다.
- 중단·보류는 명시적인 재개 요청 전까지 유지한다. 원고를 바꾸기 전 대상 파일과 허용 범위를 확인한다. 분석 재실행·입력 다운로드·외부 게시·Git push는 문서 정리의 일부가 아니다.
- Git에 없는 원본·행별 자료·캐시가 있다고 분석 실패나 삭제로 단정하지 않는다. 제외 목록은 날짜가 있는 목록이며 현재 미추적 파일 전체를 뜻하지 않는다. 열람만 하면 재수집할 필요가 없다.
- 로컬 날짜별 초안과 공동 Docs 최신본은 구분한다. 공동 문서를 읽지 못했다면 동기화·이관·덮어쓰기가 완료됐다고 보고하지 않는다.

## 확인 명령과 부작용 — 2026-09-26 코드 확인 기준

아래는 저장소 루트 기준이다. 명령 이름만 보고 읽기 전용으로 판단하지 않는다. 로컬 Python·Node 경로와 의존성은 환경마다 다르다.

문서 정리에서 쓸 수 있는 읽기 전용 확인:

```powershell
git status --short
git diff --name-only
Get-FileHash -LiteralPath 'columns/001-ball-count/publish/naver_20260918/01_ball_count.md' -Algorithm SHA256
```

기존 분석·발행 도구는 다음처럼 구분한다. 아래 도구들은 이번 문서 정리에서 실행하지 않았다.

| 도구·명령 | 실제 동작과 주의점 |
| --- | --- |
| `python -B tools/check_model_structure.py` | 읽기·구문·해시·링크 검사. 9월 8일 고정 목록과 로컬 입력에 의존하므로 후속 변경이나 공유본의 입력 부재를 구별해야 한다. 현재 프로젝트 전체에 맞는 무조건적인 합격 판정기가 아니다. |
| `python -B tools/check_ridge_v02.py` | 외부 진단 수치를 다시 계산하고 `models/bcai/ridge/v0.2.0/structure_validation.json`을 쓴다. 기존 검증 결과를 바꿀 수 있어 정리용으로 실행하지 않는다. |
| `models/bcap/check_artifacts.py` | 입력·산출물 무결성을 확인하지만 `--output` JSON을 새로 쓰고 기존 출력이 있으면 중단한다. 단순 조회와 다르다. |
| `columns/001-ball-count/analysis/bcap_followup_20260917/check_delivery.py` | 지정 실행의 `delivery_check.json`을 쓰며 이미 있으면 중단한다. 과거 문서 해시도 검사하므로 옛 결과를 덮어써 해결하지 않는다. |
| `columns/001-ball-count/analysis/verify_count_advantage.py` | 검증 CSV·JSON을 기록한다. 검증 이름이어도 기존 결과에 쓰기가 발생한다. |
| `columns/001-ball-count/analysis/inspect_advantage.py` | 데이터 확인 과정에서 캐시를 만든다. 문서 목록 확인용이 아니다. |
| `node columns/001-ball-count/publish/naver_20260918/build_preview.mjs` | 01 본문 MD를 다시 쓰고 01–04 HTML·index·렌더 확인 JSON을 생성/갱신한다. 05는 생성 대상이 아니다. 편집 중단 중 실행하지 않는다. |
| `node columns/001-ball-count/publish/naver_20260918/check_preview.mjs` | 브라우저로 확인하면서 QA PNG·`visual_check.json`을 생성/갱신한다. 단순 읽기 전용 검사가 아니다. |

재학습·데이터 다운로드 명령은 [데이터 준비 안내](data_setup.md)와 해당 모델·실행의 재현 문서를 필요한 때만 확인한다. 먼저 출력 경로와 새 run ID를 확인하고, 기존 실행을 덮어쓰지 않는다. 이번 정리의 링크·해시 검사는 기존 결과 파일을 쓰지 않는 별도 읽기 전용 점검으로 수행했다.

## 종료: 다음 작업이 바로 이해할 만큼만 남기기

`column.md`의 현재 상태·인수인계에 실제 완료, 바꾼 파일, 검증 범위, 미완료·의도적 보류, 다음 행동과 필요한 승인을 남긴다. README에는 칼럼 목록과 한 줄 상태만 맞춘다. 숫자·규칙을 여러 안내 문서에 반복 복사하지 않고 담당 보고서·지침으로 연결한다. 사용자에게 어떤 MD에 무엇을 반영했는지, 로컬만 바꿨는지 외부에도 반영했는지 구분해 알린다.

공식 OpenAI 문서의 [AGENTS.md 안내](https://learn.chatgpt.com/docs/agent-configuration/agents-md)와 [필요한 문맥만 연결하는 지침](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)을 참고해 공통 지침은 짧게 두고 작업별 자료로 연결했다. 계정·모델·전역 설정 변경이나 대화 이관을 의미하지 않는다.
