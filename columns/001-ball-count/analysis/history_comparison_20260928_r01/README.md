# 2015–2025 확장 비교 보고서

**후속 편집 안내 — 2026-09-28:** 이 보고서 완료 뒤 사용자가 원고 반영을 요청해 [7차 원고](../../publish/naver_20260918/index.html)를 만들었다. 이 보고서의 ‘원 주장’과 보존 검사는 편집 전 시점이다. 원 주장 장부에 적힌 원고 파일 5개의 당시 내용은 [보관본](../../publish/naver_20260918/revisions/v6_before_history_v7/)에서 같은 파일명으로 확인한다. [후속 보존 대조표](../../publish/naver_20260918/revision_v7_source_preservation.csv)가 당시 해시와 보관본의 일치를 확인한다. 기존 감사 결과는 소급 변경하지 않았다.

[보고서 읽기](report.html) · [본문 MD](report.md) · [기존 주장과 문구 제안](claim_comparison.md) · [기술 부록](technical_appendix.md)

2024–2025의 기존 결론과 추가 2015–2023 증거를 대조한 별도 해석 보고서다. 2015–2025는 11시즌이며 겹치는 두 기간의 독립 비교가 아니다. 기존 원고는 수정하지 않았다. BCAP은 EXPERIMENTAL이다.

## 파일 구성

최종 검토·전달 준비 완료. [최종 검수 기록](audit/final_review.md)에서 수치 검사와 화면 검사를 구분해 확인할 수 있다. 작은 화면에서는 각 그림의 ‘그림 확대해서 읽기’를 누른 뒤 좌우로 밀어 세부 글씨를 읽는다.

- `report.md` / `report.html`: 상세 한국어 보고서. 질문 → 짧은 답과 숫자 → 근거 → 해석과 한계.
- `claim_comparison.md` / HTML: 원문 주장·확장 증거·판정·블로그 문구 제안·한계·근거 위치.
- `technical_appendix.md` / HTML: 정의·분모·적합·구간·가중치·지원 보류·재현.
- `figures/`: 한국어 PNG 5장. 900px 너비, 본문에서 눌러 원본 열기.
- `tables/`: 전체 선별 2,552행, BCAI 132행, 기간별 패턴·민감도·가중치·사건별 비중·지원 부족·구종 세부 결과·원 주장 장부.
- `audit/`: 입력 경로·SHA-256, R 환경, 전체 선별 기록, 산술·보존·화면 확인.
- `analyze.R` / `present.R`: 저장 결과 검증·새 요약·표·그림. `inspect.R`: 세부 예외를 읽는 탐색 보조 코드. `verify.R`: 수치·해시 검산.
- `report.template.md` / `build_report.mjs`: 표를 삽입해 MD와 로컬 HTML 생성. `check_report.mjs`: PC·모바일·로컬 링크 확인.

CSV는 UTF-8 BOM이며 카운트는 `0-2` 같은 텍스트다. 스프레드시트로 열 때 자동 날짜 변환을 피하려면 카운트 열을 텍스트로 가져온다. `unsupported_source_audit_not_for_interpretation.csv`의 숫자는 지원 미달 원 감사값으로, 해석·그림에는 사용하지 않는다. 독자용 전체 표는 미지원 수치를 NA로 표시했다.

## 재현

프로젝트 루트에서 실행한다. 새 분석 요약·그림은 모두 R로 계산한다.

```powershell
& ./tools/run_r.ps1 -Script ./columns/001-ball-count/analysis/history_comparison_20260928_r01/present.R
& ./tools/run_r.ps1 -Script ./columns/001-ball-count/analysis/history_comparison_20260928_r01/verify.R
```

HTML은 `build_report.mjs`, 브라우저 검사는 `check_report.mjs`를 로컬 Node로 실행한다. 현재 환경의 Node·marked·playwright 위치는 두 스크립트 상단에 있다. R의 별도 출력 폴더 인자는 기술 부록을 참고한다. R 분석은 완료 실행만 읽으며 학습·수집·자동화 재개를 수행하지 않는다.

2026은 보조 절과 별도 CSV로만 제공한다. 9월 7일 기준·2025 고정 가중치이고, 위치·스윙은 측정 보류다. 외부 게시·Drive 업로드·Git push는 수행하지 않았다.
