# BCAP-PITCH-v0.2.0 기본 확인과 검증 상태

**EXPERIMENTAL — 2024·2025 개발 결과 산출, 후속 검증 미실시**. UTC 2026-09-11T17:21:55.606631+00:00.

제작 과정의 기본 확인: PASS. 적격 1,415,566행, 지지 1,395,443행, OOF 결과 MSE 0.235968449, 행동 Brier 0.225528209. 적합·보정 로그 12건 모두 수렴했다. 이 수치는 외부 예측 성능이 아니다.

[실제 확인 항목](../../../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260912__r01/artifacts/basic_checks.json) · [수렴 기록](../../../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260912__r01/artifacts/fit_diagnostics.csv) · [공통 입력 기본 확인](../../../../columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/preparation/preparation.json) · [코드·설정·입출력·환경·시각 manifest](../../../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260912__r01/manifest.json)

확인 범위는 개발 시즌, 투구 키·유효 카운트·행동·최종 결과·시즌 W 연결, 닫힌 매핑/금지 입력, 경기 fold 분리, 계산 유한값과 수렴, 양 행동 같은 분모·부호·표 합계다. 기존 예외 6건 중 개발 2행은 표시 후 유지했으며 원인 감사·임의 수정은 하지 않았다. 각 항목의 구체적인 검사와 한계는 연결한 JSON/코드가 기준이다.

219개 차이에 대한 Bonferroni 보정 명목 구간을 결과 전에 정했다. 경기별 고정 점수 변동만 반영하며 nuisance/정책 재학습·경기 간 선수 의존성과 실제 구간 포함률은 미검증이다. 이 모듈의 출력 13개를 포함한 전체 가족이다. 차이 불명확과 비교 자료 부족을 나눴으며 인과 권고 등급은 부여하지 않았다.

보존: 각 평가 fold의 nuisance.pkl(양 행동 결과 계수, 사전·중심화, 행동 계수, Platt 보정 자료/행 ID), fold_membership.csv, fold_records.json, 행별 scores.pkl, 적합 로그. S/B는 훈련 내부 튜닝 Ridge 객체도 보존한다. 최종 전체 개발 재적합 모델과 정책은 만들지 않았다. 저장 객체는 해당 engine 모듈을 import할 수 있는 환경에서 복원한다.

미실시: 2023/2026 적용·외부 평가, 반복 재학습/여러 seed/bootstrap, 별도 독립 검산기·전면 방법론 검수, 기존 원본 전체 재해시. V1의 외부/독립 검수 기록을 이 버전의 통과 증거로 쓰지 않는다.
