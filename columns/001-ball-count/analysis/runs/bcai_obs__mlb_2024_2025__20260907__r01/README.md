# bcai_obs__mlb_2024_2025__20260907__r01

- 모델: BCAI-OBS-v1.0.0 (VALIDATED)
- 실행일: 2026-09-07, 등록일: 2026-09-08. 기존 공동 실행의 사후 등록이며 새 분석을 뜻하지 않는다.
- [실행 manifest](manifest.json): 정확한 버전, 표본, 설정, 코드, 환경, SHA256. manifest 안 경로는 프로젝트 루트 기준, 원 audit 입력은 칼럼 폴더 기준.
- [모델 정의](../../../../../models/bcai/observed/v1.0.0/model_card.md)
- [통합 보고서](../../count_advantage_2024_2025.md), [재실행 절차](../../../../../models/bcai/README.md)

## 물리적 산출물 기준 위치

[artifacts/advantage_count_results.csv](artifacts/advantage_count_results.csv)의 index·CI·grade·confirmed_grade와 설명/민감도 파일은 OBS 결과다. adjusted_index_alpha20/100/500은 [Ridge 실행](../bcai_ridge__mlb_2024_2025__20260907__r01/README.md)에 속한다. audit.model도 Ridge 진단이다. 기존 파일을 그대로 보존하기 위해 공유 컨테이너를 이곳에 한 번만 저장한다.

- [advantage_audit.json](artifacts/advantage_audit.json)
- [advantage_bootstrap.npz](artifacts/advantage_bootstrap.npz)
- [advantage_context_strata.csv](artifacts/advantage_context_strata.csv)
- [advantage_count_exclusions.csv](artifacts/advantage_count_exclusions.csv)
- [advantage_count_results.csv](artifacts/advantage_count_results.csv)
- [advantage_denominator_sensitivity.csv](artifacts/advantage_denominator_sensitivity.csv)
- [advantage_event_audit.csv](artifacts/advantage_event_audit.csv)
- [advantage_exclusion_sensitivity.csv](artifacts/advantage_exclusion_sensitivity.csv)
- [advantage_pa_outcomes.csv](artifacts/advantage_pa_outcomes.csv)
- [advantage_pitch_explanators.csv](artifacts/advantage_pitch_explanators.csv)
- [advantage_season_sensitivity.csv](artifacts/advantage_season_sensitivity.csv)
- [advantage_validation.json](artifacts/advantage_validation.json)
