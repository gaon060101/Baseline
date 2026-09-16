# 실제 실행·재현 기록

프로젝트 루트: C:/Users/백창현/Desktop/Baseline

아래는 이번에 실제 실행한 명령이다. 완료된 실행·정제본·보고서는 보호하므로 같은ID로 재실행하면 중단한다. 새 재현은 같은 고정 명세를 사용하고 새 bundle의 analysis_plan.json에 미사용 new_run/comparison_run을 지정해야 한다. --bundle과 --run-id에 그 값을 전달한다. 기존 FB scores는 재사용하며 재학습하지 않는다.

```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B models/bcap/setup_pitch_ff.py
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B models/bcap/pitch_ff/v0.1.0/prepare.py --bundle columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B models/bcap/pitch_ff/v0.1.0/run.py --bundle columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01 --run-id bcap_pitch_ff__mlb_2024_2025__20260912__r01
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B models/bcap/pitch_ff/v0.1.0/compare.py --bundle columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B models/bcap/pitch_ff/v0.1.0/report.py --bundle columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01
```

setup_pitch_ff.py는 이번 최초 명세·bundle 생성 기록이며 기존 정의가 있으면 보호를 위해 중단한다. 새 검수에서는 이미 고정된 명세·입력을 참조한다. engine.py는 기존 V2 수치 코어의 동일 바이트 사본이며 기존 runtime_ridge_v02 SciPy를 사용한다. run/compare는 해당 기존 분석 환경을 읽기 위한 정식 실행 승인을 사용했다.

원입력: columns/001-ball-count/data/processed/bcap_dev_v2_20260912__r01.pkl
새 입력·SHA256: preparation.json
기존 점수: columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260912__r01/artifacts/scores.pkl
새 점수: columns/001-ball-count/analysis/runs/bcap_pitch_ff__mlb_2024_2025__20260912__r01/artifacts/scores.pkl
공통 membership 및 주요표: columns/001-ball-count/analysis/runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/

FF의 실제 nuisance 객체3개는 새 학습 실행의 artifacts/fits/fold0..2/nuisance.pkl에 있다. 사전·계수·중심화·Platt 자료/행ID·훈련 경기·seed를 포함한다. 복원 시 이 버전의 engine 모듈을 import할 수 있어야 한다. 기존FB 적합 객체와 점수는 원래 위치를 유지한다. 전체개발 최종 재적합·학습 정책·외부 평가 파일은 없다.
