# BCAI 모델군

최신 Ridge 후속은 [v0.2.0](ridge/v0.2.0/model_card.md)이며 개발·2023 외부 재현·2026 부분 시즌 시간 검증을 완료했다. [검증과 실행](ridge/v0.2.0/validation.md), [전체 보고서](../../columns/001-ball-count/analysis/ridge_v02_validation_report.md), [명세](ridge/v0.2.0/specification.yaml)를 따른다. 아래의 기존 공동 실행 절차는 v0.1/OBS 원 실행용이며 v0.2를 재현하지 않는다.

[레지스트리](../registry.md) · [OBS 카드](observed/v1.0.0/model_card.md) · [Ridge 카드](ridge/v0.1.0/model_card.md)

## 정의와 실행의 분리

모델 카드/명세는 설계, validation은 검증 범위와 실행 근거다. 시즌 가중치·표본·실제 q·환경·해시는 칼럼별 manifest에 보관한다. specification.yaml은 사람이 읽고 표준 JSON으로도 검사할 수 있는 YAML 1.2 형식이다. 현재 기존 코드가 이 명세를 직접 읽지는 않으므로 설계 변경 시 코드와 명세를 함께 수정·검증해야 한다.

최초 결과는 공동 코드가 하나의 CSV에 OBS와 Ridge를 함께 저장했다. 수치를 다시 만들거나 파일을 복제하지 않고 [OBS 실행](../../columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/README.md)의 artifacts/에 단일 보관한다. [Ridge 실행](../../columns/001-ball-count/analysis/runs/bcai_ridge__mlb_2024_2025__20260907__r01/README.md)은 adjusted 열과 audit.model을 참조한다. 물리 파일 공유는 추정 대상·검증 상태 공유를 의미하지 않는다.

## 기존 파일과 재현 경로

코드·중간 캐시는 기존 analysis/에 유지한다. 원본과 7개 통합 정제 CSV도 이동하지 않는다. 통합 해석 보고서와 인계는 칼럼 문서로 남는다. 경로 선택은 [bcai_paths.py](../../columns/001-ball-count/analysis/bcai_paths.py)가 담당한다.

과거 r01은 보호하며, 재실행에는 새 OBS 실행 ID의 artifacts 절대 경로를 BCAI_OUTPUT_DIR에 명시한다. 이 코드의 지원 범위는 MLB 2024·2025 공동 계산으로 한정된다. 다른 리그·기간은 폴더명만 바꿔 지원되지 않는다. 날짜는 실제 재실행일, 번호는 해당 날짜/모델/리그/기간에서 사용하지 않은 번호로 선택한다.

PowerShell 예시(실제로 재분석할 때만 실행; 아래 날짜·번호는 실행 당일의 미사용 값으로 교체):

```powershell
$env:BCAI_OUTPUT_DIR = 'C:/Users/백창현/Desktop/Baseline/columns/001-ball-count/analysis/runs/bcai_obs__mlb_2024_2025__20260908__r01/artifacts'
python columns/001-ball-count/analysis/analyze_count_advantage.py
python columns/001-ball-count/analysis/verify_count_advantage.py
python columns/001-ball-count/analysis/write_advantage_report.py
Remove-Item Env:BCAI_OUTPUT_DIR
```

Python은 numpy/pandas가 있는 실행기를 사용한다. 기존 환경: Python 3.12.14, pandas 3.0.1, numpy 2.3.5. 로컬 실행기 경로는 칼럼 인계 문서 참조. 캐시는 이미 있으므로 inspect_advantage.py를 반복 실행하지 않는다. 캐시가 없을 때만 기존 원본으로 재생성한다. 통합 정제본이 없으면 자동 재수집하지 말고 중단한다.

순서: 캐시 확인 → 공동 계산 → 검증 → 보고서 생성 → 출력 검사 → 새 OBS/Ridge manifest와 레지스트리 등록. 같은 새 출력 폴더를 세 단계에서 사용한다. 보고서는 새 artifacts/에 생성하므로 기존 칼럼 보고서를 덮어쓰지 않는다. 완료 후 manifest를 등록하면 해당 run은 쓰기 보호된다. 미등록 중간 실행의 단계 재시도는 출력 덮어쓰기가 가능하므로 실패한 실행을 보존하려면 새 번호를 사용한다. 이 레거시 코드는 manifest를 자동 생성하지 않으므로 실행 후 정확한 버전·설정·입력/출력 해시·코드 해시를 반드시 기록한다.

Ridge만 독립 실행하면 RNG 상태와 fold가 달라질 수 있다. 원 실행과 같은 교차 적합을 재현하려면 OBS의 bootstrap부터 순서를 유지한다. 단독 실행기 분리는 별도 설계 작업이다.

## 구조만 검사

```powershell
python tools/check_model_structure.py
```

검사는 파일·해시·참조·출력 열·명세·경로 보호를 점검하며 다운로드, 모델 적합, bootstrap을 수행하지 않는다. 최초 전체 재실행은 이번 구조 변경 범위에서 수행하지 않았다.
