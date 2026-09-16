# BCAP 모델과 재현 안내

## 포심/비포심 추가 비교 완료 — 2026-09-12

**2024·2025 개발 비교 완료, 외부 검증 미실시 — EXPERIMENTAL**. [FB/NFB·FF/non-FF 보고서](../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/report.html) · [새 FF 모듈 카드](pitch_ff/v0.1.0/model_card.md) · [실제 실행·재현 명령](../../columns/001-ball-count/analysis/bcap_pitch_classification_20260912__r01/reproduction.md). 기존 FB 결과·점수를 재사용하고 FF nuisance만3fold로 적합했다. 자체/공통 표본48개 주요 비교와 연도/fold 내부 탐색을 완료했다. 타자/SB 및 기존 모델은 수정·재학습하지 않았다. 요청된 비교에서 종료하며 외부 검증·분류 추가 탐색은 미실시다.

## 최신 개발 V2 — 2026-09-12

**2024·2025 개발 결과 산출, 후속 검증 미실시 — EXPERIMENTAL**. [통합 결과 보고서](../../columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/report.html) · [실행 명령](../../columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/reproduction.md) · [기본 확인](../../columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/basic_summary.json).

[BCAP-PITCH-v0.2.0](pitch/v0.2.0/model_card.md) · [BCAP-PITCH-SB-v0.1.0](pitch_sb/v0.1.0/model_card.md) · [BCAP-SWING-v0.2.0](swing/v0.2.0/model_card.md). 실제 사용한 fold 적합 객체와 분할·행별 점수를 새 실행에 보존했다. 2024·2025만 계산했고 외부/재학습/독립 검수는 수행하지 않았다. 타자 5구역은 상·하·좌(몸쪽)·우(바깥쪽)·가운데(존 안 전체), 모서리는 두 구역에 포함된다.

## 기존 V1 구현·검증 이력

BCAP 실제 구현·평가 반영 — 2026-09-09. 2026-09-09T08:49:31.268706+00:00.

BCAP-PITCH-v0.1.0과 BCAP-SWING-v0.1.0은 모두 **EXPERIMENTAL**이다. 실제 개발·외부 진단과 독립 검산을 완료했으나 행동 추천은 없다. BCAP-JOINT는 두 모델의 식별·외부 근거가 충분하지 않아 설계하지 않았다.

[PITCH 카드](pitch/v0.1.0/model_card.md) · [SWING 카드](swing/v0.1.0/model_card.md) · [주 보고서·16종 표·12카운트 해석](../../columns/001-ball-count/analysis/bcap_v010_report_20260909.md) · [카운트별 실제·후보 행동 비율 비교](../../columns/001-ball-count/analysis/bcap_implementation_review_20260909/behavior_comparison.md) · [별도 검수 인계](../../columns/001-ball-count/analysis/handoff_bcap_review.md)

행동 비율 비교는 이미 저장된 같은 공통 지지 집단의 실제·후보 비율·%p 차이·불일치율을 읽기 쉽게 제시한 봉인 뒤 표현 보완이다. 새 분석·주 검증 변경·행동 추천은 없으며 개발 outer 평가 정책과 외부에 적용한 최종 개발 정책의 역할을 구분한다.

문서 갱신 뒤 실행하는 최종 보존·해시·내부 링크 검사의 실제 결과는 [최종 보존·해시·링크 검사 폴더](../../columns/001-ball-count/analysis/bcap_final_validation_20260909)의 `validation.json`에서 확인한다. 이 문서 생성 시점에는 예정 출력이며 PASS를 선제적으로 단정하지 않는다.

## 역할과 추정 대상

PITCH는 현재 한 구 FB/NFB의 최종 PA 공격가치 비교이며 현재·직전 좌표를 입력하지 않는다. SWING은 번트 포함 기록상 공격 시도/판정상 Take의 사후 공 특성 조건부 진단이다. 명시적 scored HBP는 Take로 포함하지만 불명 라벨을 Take로 대치하지 않는다. 타자의 실시간 지각·구종 품질·컨디션·의도·미측정 교란은 식별되지 않았다. 같은 실제 선수·상황 행에 양 행동을 적용했으며 가상 평균 선수 예측으로 대체하지 않았다. 완료 PA·IBB·최종 결과 결측 제외는 사후 선택을 포함한다. 행별 차이를 합쳐 PA 전체 정책의 개선량으로 보고하지 않는다.

주 구간은 고정 OOF 점수의 경기 군집 조건부 구간과 Bonferroni 1,536 가족 범위다. 각 모델의 8회 전체 재학습은 매 반복의 전처리·튜닝·calibration·nuisance·정책 선택을 다시 수행한 안정성 진단이며 최종 개발 정책의 완전한 95% 신뢰구간이 아니다. 경기 간 선수·시리즈 의존성과 동률 근처 선택도 남는다. known/unseen·IPW·Hájek·g-computation·추가 calibration·민감도와 보조 구간은 별도 진단이다. NO_SUPPORT는 실행된 비교의 표본·공통 지지 부족, UNCERTAIN은 지원된 비교에도 식별·학습 불확실성 근거 부족을 뜻한다. 미실행·측정 보류에는 표본 판정 등급을 부여하지 않는다. 모든 추천 행동은 비어 있고 보수 정책은 전 영역에서 실제 행동을 유지한다.

## 파일 역할

- pitch/v0.1.0, swing/v0.1.0: 모델 카드·불변 기계 명세·검증 범위. 명세의 최초 DRAFT 상태는 역사적 값이다.
- data.py: 기존 로컬 원본에서 새 정제본과 행동·PA·측정 감사를 생성. run.py: 중첩 개발·최종 정책·봉인·외부 평가.
- verify_bcap.py: 주 실행기와 분리한 AIPW/OPE 검산. refit_stability.py: 전체 재학습 경기 bootstrap 안정성 진단.
- supplement_diagnostics.py: IPW/Hájek/회귀 표준화·known/unseen·정책 비율·calibration 보조 표.
- finalize_seal.py: 보조 분석 및 보고 코드·기존 외부 입력 해시까지 포함한 최종 봉인. check_artifacts.py: 보존·해시·링크 점검.
- build_report.py: 완료 집계의 보고서·16종 CSV·후처리 manifest. finish_documents.py: 완료 후 문서·새 증거 인덱스만 갱신.
- record_invocations.py: 실제 작업에서 호출한 명령을 출처와 함께 사후 기록. 독립 shell history 회수와 구분한다.

| 모델 | 범위 | 실행 상태 | 적격 행 | 공통 지지 행 | 전체 판정 | 실행 |
| --- | --- | --- | --- | --- | --- | --- |
| PITCH | 2024·2025 개발 | COMPLETE | 1,415,566 | 1,395,402 | UNCERTAIN | [bcap_pitch__mlb_2024_2025__20260909__r02](../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260909__r02/manifest.json) |
| SWING | 2024·2025 개발 | COMPLETE | 1,416,043 | 1,354,516 | UNCERTAIN | [bcap_swing__mlb_2024_2025__20260909__r01](../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260909__r01/manifest.json) |
| PITCH | 개발 전체 재학습 8회 | COMPLETE | 해당 없음 | 해당 없음 | 등급 없음 | [bcap_pitch__mlb_2024_2025__20260909__r03](../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260909__r03/manifest.json) |
| SWING | 개발 전체 재학습 8회 | COMPLETE | 해당 없음 | 해당 없음 | 등급 없음 | [bcap_swing__mlb_2024_2025__20260909__r02](../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2024_2025__20260909__r02/manifest.json) |
| PITCH | 2023 재현 | COMPLETE | 716,113 | 697,633 | UNCERTAIN | [bcap_pitch__mlb_2023__20260909__r01](../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2023__20260909__r01/manifest.json) |
| SWING | 2023 재현 | COMPLETE | 716,385 | 682,953 | UNCERTAIN | [bcap_swing__mlb_2023__20260909__r01](../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2023__20260909__r01/manifest.json) |
| PITCH | 2026-09-07까지 | COMPLETE | 635,095 | 615,820 | UNCERTAIN | [bcap_pitch__mlb_2026_ytd_20260907__20260909__r01](../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260909__r01/manifest.json) |
| SWING | 2026-09-07까지 | WITHHELD | 해당 없음 | 해당 없음 | 등급 없음 | [bcap_swing__mlb_2026_ytd_20260907__20260909__r01](../../columns/001-ball-count/analysis/runs/bcap_swing__mlb_2026_ytd_20260907__20260909__r01/manifest.json) |
| PITCH | 개발 최초 호출 실패 보존 | FAILED | 해당 없음 | 해당 없음 | 등급 없음 | [bcap_pitch__mlb_2024_2025__20260909__r01](../../columns/001-ball-count/analysis/runs/bcap_pitch__mlb_2024_2025__20260909__r01/manifest.json) |

## 재현

프로젝트 루트에서 실행한다. 기존 run ID·정제본·보고 파일은 재사용하지 않는다. 정확한 환경·입력 경로·해시와 실제 작업 호출을 실행 후 기록한 [명령 기록](../../columns/001-ball-count/analysis/bcap_execution_commands_20260909.json)과 [실행 증거 인덱스](../../columns/001-ball-count/analysis/bcap_execution_evidence_20260909.json)에 있다. 작업의 도구 호출에서 사후 기록한 명령이며 독립적으로 복구한 shell history라고 주장하지 않는다. 완료된 수치의 독립 검산·보고서 후처리는 원본 재수집이나 모델 재적합을 필요로 하지 않는다. 새 모델 재적합 후 같은 2023·2026에 적용하면 이미 노출된 외부 자료의 반복 평가로 기록해야 한다.

후처리 재현 예시(모델 적합·데이터 수집 없이 기존 완료 집계에서 새 보고 사본 생성; 아래 목적지가 이미 있으면 새 이름 사용):

```powershell
& 'C:\Users\백창현\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\백창현\Desktop\Baseline\models\bcap\build_report.py' '--pitch-dev' 'bcap_pitch__mlb_2024_2025__20260909__r02' '--swing-dev' 'bcap_swing__mlb_2024_2025__20260909__r01' '--pitch-2023' 'bcap_pitch__mlb_2023__20260909__r01' '--swing-2023' 'bcap_swing__mlb_2023__20260909__r01' '--pitch-2026' 'bcap_pitch__mlb_2026_ytd_20260907__20260909__r01' '--swing-2026' 'bcap_swing__mlb_2026_ytd_20260907__20260909__r01' '--pitch-bootstrap' 'bcap_pitch__mlb_2024_2025__20260909__r03' '--swing-bootstrap' 'bcap_swing__mlb_2024_2025__20260909__r02' '--output-dir' 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_report_recheck_20260909T084931Z' '--report' 'C:\Users\백창현\Desktop\Baseline\columns\001-ball-count\analysis\bcap_report_recheck_20260909T084931Z.md'
```

행별 독립 검산을 다시 수행할 때는 verify_bcap.py의 --rows/--model/--summary/--folds/--config에 해당 실행 artifacts를 지정하고 --output에 새 JSON 경로를 쓴다. 기존 명령의 run ID로 다시 적합하면 보존 규칙에 따라 중단되므로 새 분석 실행은 반드시 새 ID를 사용한다.

정제·적합·외부 평가 명령의 --help는 각 실행기의 역할과 필요한 인수를 확인하는 데 쓴다. 해시 봉인은 공개 사전등록이나 모든 과거 미노출을 증명하지 않는다.
