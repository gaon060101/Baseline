# V2 개발 재현

아래는 실제 실행 명령 기록이다. 완료 실행을 보존하기 위해 다시 계산할 때에는 실제 날짜·미사용 run_id를 정하고 새 입력/보고 폴더를 사용한다. 기존 스크립트의 날짜별 준비·보고 폴더 r01은 경로를 명시적으로 새 폴더로 바꾼 후 사용한다. 원본 재수집·외부 평가·bootstrap 명령은 없다.

```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:/Users/백창현/Desktop/Baseline/models/bcap/development_v2/v0.2.0/run.py' --model pitch_sb --run-id bcap_pitch_sb__mlb_2024_2025__20260912__r01
```

```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:/Users/백창현/Desktop/Baseline/models/bcap/development_v2/v0.2.0/run.py' --model pitch --run-id bcap_pitch__mlb_2024_2025__20260912__r01
```

```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:/Users/백창현/Desktop/Baseline/models/bcap/development_v2/v0.2.0/run.py' --model swing --run-id bcap_swing__mlb_2024_2025__20260912__r01
```

공통 준비는 prepare.py, 결과 보고는 report.py, 문서 연결은 register_results.py다. SciPy는 기존 runtime_ridge_v02에서 읽으며 샌드박스 제한 시 정식 실행 승인을 사용했다. -B로 기존 bytecode를 변경하지 않는다.

3개 fold nuisance.pkl(계수·훈련 사전·calibration 점수/행ID·훈련 경기·seed)과 S/B 튜닝 Ridge 객체가 실제 사용한 모델이다. 복원 시 이 버전의 engine 모듈을 import할 수 있어야 한다. 정책은 학습하지 않아 policy 파일은 없다.
