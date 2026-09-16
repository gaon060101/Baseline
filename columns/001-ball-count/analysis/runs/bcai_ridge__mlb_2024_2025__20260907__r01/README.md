# bcai_ridge__mlb_2024_2025__20260907__r01

- 모델: BCAI-RIDGE-v0.1.0 (EXPERIMENTAL)
- 실행일: 2026-09-07, 등록일: 2026-09-08. 기존 공동 실행의 사후 등록이며 새 분석을 뜻하지 않는다.
- [실행 manifest](manifest.json): 정확한 버전, 표본, 설정, 코드, 환경, SHA256. manifest 안 경로는 프로젝트 루트 기준, 원 audit 입력은 칼럼 폴더 기준.
- [모델 정의](../../../../../models/bcai/ridge/v0.1.0/model_card.md)
- [통합 보고서](../../count_advantage_2024_2025.md), [재실행 절차](../../../../../models/bcai/README.md)

## 논리적 결과 위치

Ridge 실행의 기준 기록은 이 폴더의 manifest이며, 물리적 공동 산출물은 [OBS artifacts](../bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_count_results.csv)에만 있다. 별도 CSV 사본을 만들지 않는다.

- CSV의 count·adjusted_index_alpha20·adjusted_index_alpha100·adjusted_index_alpha500만 사용.
- [audit JSON](../bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_audit.json)의 model 항목: α별 MSE·수렴.
- OBS index/grade/confirmed_grade/CI와 bootstrap은 Ridge 결과가 아니다.
- 재적합 CI 없음, 엄격한 수렴 기준 미달. OBS의 후속 대체 모델이 아니다.
