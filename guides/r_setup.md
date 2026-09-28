# R 연결 안내

## 현재 상태 — 2026-09-28

R 4.6.1 설치 및 이 Codex 작업에서의 로컬 실행 확인 완료. 별도 API 키·유료 계정·RStudio·MCP 서버는 필요하지 않다. Codex가 로컬 Rscript를 호출해 계산하는 방식이다. 다른 컴퓨터나 클라우드 작업에는 이 설치가 자동 전달되지 않는다.

처음에는 연결 확인만 수행했으나 이후 사용자가 **2024·2025 BCAI 재계산, 과거 연도 순차 적용, BCAP R 구현**을 명시적으로 재개했다. 2015~2025 BCAI와 BCAP 네 모듈의 R 계산을 완료했다. 2026은 9월 7일 기준·2025 고정 가중치의 BCAI 및 BCAP PITCH/FF 보조 결과이며 S/B·SWING은 측정 보류다. 검수와 실행별 범위는 [칼럼 현재 상태](../columns/001-ball-count/column.md#current-status)를 따른다. 기존 발행 원고는 자동 수정하지 않는다.

## 설치와 확인

- R 위치: `C:/Users/백창현/AppData/Local/Programs/R/R-4.6.1/`
- 공식 배포: <https://cran.r-project.org/bin/windows/base/>. Windows 패키지 관리자의 `RProject.R`로 사용자 범위 설치, 설치 관리자 해시 확인 성공.
- 패키지: data.table 1.18.6.1, ggplot2 4.0.3, jsonlite 2.0.0, digest 0.6.39 및 의존 패키지. CRAN Windows 바이너리 설치.
- 패키지 라이브러리는 실행 환경의 `R_LIBS_USER`를 사용한다. 실제 경로·버전은 확인 기록의 `sessionInfo.txt`를 참조한다.
- 산술, 한글 CSV 왕복, ggplot2 PNG 저장 확인 통과. 1·2·3 모의 값만 사용했고 실제 야구 데이터는 읽지 않았다. 1200×800 PNG를 직접 열어 한글·숫자·축 표시를 확인했다.
- 로컬 확인 기록: `.codex/r-connection-20260928/check.json`, `sessionInfo.txt`, `synthetic_example.csv`, `synthetic_example.png`. Git 제외된 모의 확인 자료이며 칼럼 결과가 아니다.

## 실행 방법

저장소 루트에서 다음 실행기를 사용한다. 사용자가 매번 직접 실행할 필요는 없다.

```powershell
& ./tools/run_r.ps1 -Script ./tools/check_r.R
```

패키지를 새 환경에 준비할 때:

```powershell
& ./tools/run_r.ps1 -Script ./tools/setup_r_packages.R
```

모의 CSV·PNG까지 다시 확인할 때는 기존에 없는 출력 폴더를 지정한다. 기존 폴더가 있으면 중단한다.

```powershell
& ./tools/run_r.ps1 -Script ./tools/check_r.R ./.codex/r-connection-new-check
```

실행기는 `BASELINE_RSCRIPT`, PATH, R 설치 레지스트리, 일반 설치 폴더 순으로 Rscript를 찾는다. R 자체를 직접 실행할 수도 있으나, 이 환경은 Windows R이 인식하지 못하는 `C.UTF-8` 언어 설정을 전달해 기본 패키지 로딩 오류를 일으켰다. 실행기는 R 호출 중에만 `LANG`·`LC_ALL`·`LC_CTYPE`를 해제하고 호출 후 원래 값으로 복구한다. 전역 Windows 설정은 변경하지 않았다.

## 완료한 분석과 다음 연도 재사용

2024·2025의 BCAI 재현과 BCAP 네 모듈(PITCH/SB/SWING/FF) R 재현, 2023→2015 적용이 완료됐다. [BCAI 코드·재사용 안내](../models/bcai/observed/v1.0.0/r/README.md) · [BCAP 코드·재사용 안내](../models/bcap/r/README.md) · [과거 연도 실행 안내](../columns/001-ball-count/analysis/r_bcap_history_20260928/README.md). [BCAI 결과 화면](../columns/001-ball-count/analysis/r_history_20260928/report.html)과 [BCAP 결과 화면](../columns/001-ball-count/analysis/r_bcap_history_20260928/report.html)은 전 11시즌을 담았다. 사용자에게 매번 수동 실행을 요구하지 않으며, 코드와 설정을 남겨 다른 연도에 반복 적용한다.

다음 연도 적용 시에는 기간·기준일, 원자료와 가중치, 측정 호환성을 확인하고 새 설정과 미사용 run ID를 만든다. 위 안내대로 R 계산 후 입력 감사·지원 표본·산출물 검증을 거쳐 보고서와 PNG를 생성한다. 기존 자료의 부재를 자동 재수집 허가로 해석하지 않는다.

[첫 단계 계획](../columns/001-ball-count/analysis/runs/bcai_r_check__mlb_2024_2025__20260928__r02/plan.md)과 [과거 연도 계획](../columns/001-ball-count/analysis/r_history_20260928/plan.md)을 사용한다. r01 감사 분모 오류는 FAILED로 보존했고 r02에서 수정·재계산을 완료했다. 다음 새 계산에도 새 run ID를 사용한다.
