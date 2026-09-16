# BCAI-OBS-v1.0.0 검증

## 근거와 범위

2026-09-07 [기존 보고서](../../../../columns/001-ball-count/analysis/count_advantage_2024_2025.md)와 [인계](../../../../columns/001-ball-count/analysis/handoff_count_advantage.md)의 사실을 등록했다. 이번 등록일은 2026-09-08이며 재분석일이 아니다. [실행 기록](../../../../columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/manifest.json)에 입력·환경·실제 설정·산출물 해시가 있다.

상태 VALIDATED는 해당 관찰 계산의 검증 통과를 뜻한다. [원 검증 JSON](../../../../columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_validation.json)의 6개 검증: 독립 PA 집계 지수 1e-9 이내 일치, 이벤트 비율 합계 100, 기존 정제 투구 수 일치, 0-0=100, CI 포함, 입력 SHA256 일치.
원본 1424427행, 전체 366231 PA, 유효 364124 PA, 4859경기, 타자 788명, 투수 1113명. 제외 IBB 1065·truncated 635·결측 221·타격방해 186. 반복 PA×count 제거 98606.
동시 임계값 2.7778553014574583. 시즌 지수 최대 차이 2.07포인트, 제외 시나리오 최대 이동 2.502363066386124. 자연 등급 경계·인과성·리그외 일반화는 검증하지 않았다.

## 구조 변경 검증

[구조 변경 기록](../../../../models/migration_20260908.md)과 [재검사 도구](../../../../tools/check_model_structure.py)를 참조한다. 기존 검증을 다시 수행했다는 뜻이 아니라, 원 데이터·산출물 보존 및 현재 경로/명세를 별도 점검한다.
