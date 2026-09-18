# 제한적 확인 — BCAP-DECOMP-v0.1.0

## 2026-09-18 별도 모의 예제 확인 추가

[검수 보고서](../../../../columns/001-ball-count/analysis/runs/bcap_followup_review__mlb_2024_2025__20260918__r01/report.md)와 [인터페이스 기록](../../../../columns/001-ball-count/analysis/runs/bcap_followup_review__mlb_2024_2025__20260918__r01/interface_review/checks.json). 기존 fixture와 다른 모의2행에서 손으로 지정한 기대값으로 행별 확률×조건부 W·공통 행 비교·가지 기여·Brier/로그손실·입력 오류·파일 보존을 확인했다. 실제 분기 적합·경험적 지원·교정·AIPW·구간·정책을 검증한 것은 아니다. DRAFT를 유지한다. 아래는 최초 구현 시점의 기록이다.


2026-09-17, **DRAFT 유지**. 두 개의 명시적 모의 투구로 입력·산술·CLI 오류 처리를 확인한다. 실제 선수·실제 MLB 관측값·경험적 분해 결과가 아니다. [실행 manifest](../../../../columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r01/manifest.json)와 [검사 출력](../../../../columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r01/artifacts/checks.json)에 실행 시각·해시·실제 PASS 목록을 기록한다.

확인 대상은 기존 12개 description 매핑 일치, 행별 확률×W와 평균의 순서, 동일행 양 행동 대조, 모서리 중첩의 전체 분모 보존, 확률 합·양의 질량 결측·미지원·미분류·fold 겹침·불완전 가지·일부만 있는 직접 회귀 비교의 거부, CLI와 함수 출력 일치 및 완료 파일 보존이다.

실제 분기 모형 학습·전처리 누수 검수·경험적 지원·교정 곡선·조건부 W 정확도·AIPW·불확실성 전파·외부 검증·상대 반응 시나리오는 하지 않았다. 입력으로 받은 지원 표시와 훈련 경기 목록의 구조를 확인했을 뿐, 실제 생성 과정의 정당성은 검증하지 않았다. 기존 BCAP나 BCAI의 검증 이력을 이 초안에 전용하지 않는다.

재현은 프로젝트 루트에서 다음처럼 **새 실행 ID**로 한다. 표준 라이브러리만 사용한다.

```powershell
python -B models/bcap/decomposition/v0.1.0/run_smoke.py --out columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r02
```
