# 재현 안내

기존 실행 ID·완료 결과를 덮어쓰지 않는다. 아래는 이번 실제 실행의 명령 구조이며, 다시 계산하려면 새 bundle·새 출력 경로·새 실행 ID와 새 봉인이 필요하다.

프로젝트: `C:/Users/백창현/Desktop/Baseline`

1. `plan.json`과 `plan_seal.json`의 입력·설정·코드 SHA256을 확인한다.
2. `prepare_external.py --year 2023`, `--year 2026`으로 기존 V1 정제본을 새 경로에 준비한다.
3. 각 연도에 `run_external.py --year YEAR --model MODEL`을 실행한다. MODEL은 pitch_sb, swing, pitch, pitch_ff이다. 2026 pitch_sb·swing은 적합 없이 측정 보류 manifest를 남긴다.
4. `run_external.py --year YEAR --model compare`로 구종 자체·공통 표본을 재집계한다.
5. `build_report.py`는 완료 CSV·manifest만 읽어 이 보고서를 만든다. 기존 산출물이 있으면 중단한다.

실제 Python 경로·명령·시각·환경은 각 실행 manifest의 command/environment에 있다. 보고서 비교표는 comparison.csv 240행, 주요 S/B는 primary_SB.csv 4행이다. 값·표본·구간·지원 판정은 원 CSV와 연결되며, 측정 보류 행의 외부 값은 비워 둔다.
