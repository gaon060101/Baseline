# BCAI-RIDGE-v0.1.0 검증

## 근거와 범위

2026-09-07 [기존 보고서](../../../../columns/001-ball-count/analysis/count_advantage_2024_2025.md)와 [인계](../../../../columns/001-ball-count/analysis/handoff_count_advantage.md)의 사실을 등록했다. 이번 등록일은 2026-09-08이며 재분석일이 아니다. [실행 기록](../../../../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2024_2025__20260907__r01/manifest.json)에 입력·환경·실제 설정·산출물 해시가 있다.

상태 EXPERIMENTAL. [원 audit.model](../../../../columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_audit.json)에 α별 5개 fold 진단을 그대로 보존했다.

| α | OOF MSE | 상수 기준 MSE |
| --- | --- | --- |
| 20.0 | 2.7119595872972533 | 2.712496201602141 |
| 100.0 | 2.7048340310431147 | 2.712496201602141 |
| 500.0 | 2.702816939988148 | 2.712496201602141 |

모든 15개 적합이 150회 반복 한도에 도달했다. 엄격한 1e-7 기준 미충족이며 전체 max_last_change 최대 1.0800681081502006e-05. α100 개선 약 0.28%, OBS 대비 최대 이동 약 1.77포인트. 이것은 미래 예측 검증이나 높은 설명력의 증거가 아니다. 재적합 CI·외부 기간 평가·KBO 검증 미실시. OBS의 독립 지수 재집계 통과를 Ridge의 완전 검증으로 전용하지 않는다.

## 구조 변경 검증

[구조 변경 기록](../../../../models/migration_20260908.md)과 [재검사 도구](../../../../tools/check_model_structure.py)를 참조한다. 기존 검증을 다시 수행했다는 뜻이 아니라, 원 데이터·산출물 보존 및 현재 경로/명세를 별도 점검한다.
