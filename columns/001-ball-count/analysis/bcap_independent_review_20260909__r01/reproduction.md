# 독립 검수 재현 명령

아래는 이번 검수에서 사용한 명령 기록이다. 기존 생산 run.py develop/external은 실행하지 않는다. 완료된 검수 결과도 보존해야 하므로 재검수 때에는 같은 analysis 부모 아래 새 미사용 검수 폴더를 만들고 코드와 review_protocol.json의 새 선언본을 옮긴 뒤 아래 경로를 새 폴더로 치환한다. 초기 출력 JSON/CSV를 복사해 재사용하지 않는다. 코드의 ROOT/HERE 상대 깊이는 유지한다. `inventory.py`는 기존 before/after가 있으면 중단한다. 일부 보조 감사는 앞 단계의 새 산출물에 의존한다.

현재 환경은 Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, Windows다. scipy.stats.t만 기존 runtime_ridge_v02 라이브러리에서 읽으며 샌드박스 접근 제한 시 정식 승인이 필요할 수 있다. 외부 원본 수집·재학습은 없다. 각 구성품 증거 manifest에 실제 시각·입출력 해시가 있다.

review baseline:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\inventory.py' before
```

raw reconstruction:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\lineage\independent_lineage.py'
```

source exceptions and saved-score reaggregation:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\lineage\supplement_lineage.py'
```

lineage evidence finalization:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\lineage\finalize_lineage_review.py'
```

saved-fit recreation and partition/policy reconstruction:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\folds_prediction\review_folds_prediction.py'
```

saved-fit missing and unknown behavior:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\folds_prediction\supplement_saved_fit.py'
```

saved Y/A/nuisance training interval reconstruction:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\folds_prediction\policy_intervals_review.py'
```

existing aggregate/resampling reaggregation:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\methodology_bootstrap\bootstrap_audit.py'
```

saved Y/A/nuisance AIPW/OPE reconstruction:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\numeric_audit.py'
```

resolved hashes and timestamps:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\provenance_audit.py'
```

existing tables and behavior reaggregation:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\methodology_bootstrap\report_tables_audit.py'
```

review boundary preservation:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\inventory.py' after
```

review evidence assembly:
```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_independent_review_20260909__r01\finalize_review.py'
```

하위 source_audit.py/write_review.py 등 증거·문서 조립 보조 명령은 해당 하위 execution log/manifest를 따른다. 이번 최종 보고서는 저장 산술과 원자료 계보·기존fit 예측을 분리하며, 명령의 성공만으로 더 넓은 통계적 주장을 인증하지 않는다.
