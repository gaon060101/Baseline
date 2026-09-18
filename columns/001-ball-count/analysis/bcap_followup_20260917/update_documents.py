"""완료된 소형 실행을 공유 인덱스에 추가한다. 이전 본문은 보존한다."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01"
TAG = "2026-09-17 후속 구현·간단한 확인 완료"


def main():
    if not (RUN / "manifest.json").is_file():
        raise FileNotFoundError("보고서 생성 완료 후 실행하세요")
    marker = RUN / "document_update.json"
    if marker.exists():
        raise FileExistsError("이 문서 반영 기록은 이미 있습니다")
    specs = {
        "README.md": f"""## {TAG}

001의 [한국어 구현 보고서](columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md)·[HTML](columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.html)를 추가했다. 기존 S/B 개발·2023 결과는 재표시했고, BCAI 원 W에서 시즌별 상태 평균 차이 24행을 새로 계산했다. 상태 차이 모듈은 EXPERIMENTAL, 행동 가치 분해는 계산 코드와 모의 확인만 갖춘 DRAFT다. 상대 반응 시나리오는 결합값·공통 지원 미확보로 수치 보류한다. 전체 학습·전체 검증은 하지 않았으며 기존 BCAP 상태와 2026 위치 측정 보류를 유지한다.

아래는 앞선 작업 시점의 기록이다.""",
        "models/registry.md": f"""## {TAG}

[구현 보고서](../columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md) · [보고 실행](../columns/001-ball-count/analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/manifest.json). 기존 S/B-v0.1.0 추정값은 재사용했으며 정의·기존 상태를 바꾸지 않았다.

| 모델 | 현재 상태·범위 | 정의·기본 확인 | 이번 실행 |
| --- | --- | --- | --- |
| BCAI-STATE-DELTA-v0.1.0 | EXPERIMENTAL · 저장된 시즌 원 W의 상태 평균 차이 24행, 간단한 산술 확인 | [카드](bcai/state_delta/v0.1.0/model_card.md) · [명세](bcai/state_delta/v0.1.0/specification.yaml) · [확인](bcai/state_delta/v0.1.0/validation.md) | [2024·2025 계산](../columns/001-ball-count/analysis/runs/bcai_state_delta__mlb_2024_2025__20260917__r01/manifest.json) |
| BCAP-DECOMP-v0.1.0 | DRAFT · 행별 확률×조건부 W 합성 구현; 실제 MLB 학습·추정·지원·구간 미실행 | [카드](bcap/decomposition/v0.1.0/model_card.md) · [명세](bcap/decomposition/v0.1.0/specification.yaml) · [확인](bcap/decomposition/v0.1.0/validation.md) | [명시적 모의 자료 확인만](../columns/001-ball-count/analysis/runs/bcap_decomp__synthetic_smoke__20260917__r01/manifest.json) |

상태 평균 차이는 실제 전이 사건조건부 값·행동 효과가 아니다. 기존 OBS 검증 상태를 승계하지 않는다. 반응률 시나리오는 설계/지원 미확보로 수치 미산출이며 JOINT 모델을 등록하지 않았다. 기존 외부 재현 및 2026 S/B·SWING 측정 보류는 유지한다.""",
        "columns/001-ball-count/column.md": f"""## {TAG}

[구현 보고서](analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md)·[HTML](analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.html)에 기존 S/B의 Q(B)·Q(S), 차이·구간·표본을 12카운트로 정리했다. 2023은 별도 재현 표, 2026 위치 분석은 측정 보류다. 이번에 새 S/B 추정을 한 것은 아니다.

[새 BCAI 상태 표](analysis/runs/bcai_state_delta__mlb_2024_2025__20260917__r01/report.md)는 시즌별 도달 PA 평균 W의 차이 24행이다. 볼/스트라이크를 추가한 인과 효과 또는 실제 전이 사건 뒤의 평균으로 쓰지 않는다. 새 구간과 사건 발생률은 미산출이다. 분해 모듈은 DRAFT 구현·모의 확인까지만 완료했고 실제 MLB 결과는 없다. 상대가 존 밖 공을 덜 따라올 때의 이점과 임계 반응률은 동일 조건 결합값이 없어 계산 보류했다.

기존 패턴을 소개하는 칼럼 결론은 유지한다. 새 분해·상대 반응 효과가 확인된 것처럼 본문에 추가하지 않는다. 상세 완료/보류·재현 명령은 [최신 인계](analysis/handoff_bcap_review.md)와 보고서에 연결했다. 기존 모델·완료 실행·원본은 보존했고 전체 학습·검증·KBO·외부 업로드는 수행하지 않았다.

아래는 앞선 문헌 검토 시점의 기록이다.""",
        "columns/001-ball-count/sources.md": f"""## {TAG}

[실행·입출력 해시](analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/manifest.json). 기존 2024·2025 S/B count_values.csv와 2023 values.csv를 재표시했다. 새 상태 차이는 기존 OBS의 시즌별 advantage_season_sensitivity.csv 원 W·PA 도달 분모를 사용했다. 새로운 원본이나 정제본은 만들지 않았고 기존 자료를 재수집하지 않았다. 2026 위치 측정 보류를 유지한다.

기존 [모델 발전 검토](model_research_followup_20260917.md)를 구현 기준으로 재사용했다. 지정 공개 원고의 BART §2.2·3·5.1, Douglas의 3-0 목표·구종별 Gaussian/카운트 공통 오차 가정, MONEYBaRL §4.1의 완전 구종 인식과 §4.2의 오류 시뮬레이션 구분을 확인했다. [BART v2](https://arxiv.org/html/2305.05752v2) · [Douglas v1](https://arxiv.org/html/2110.04321v1) · [MONEYBaRL v1](https://arxiv.org/html/1407.8392v1). 논문 재현·정책 효과 검증을 수행한 것은 아니다. 새 분해 실행은 명시적 모의 자료이며 실제 MLB 분석 결과와 구분한다.

새 산출물은 코드·모델 정의·문서·소형 집계 및 명시적 모의 예제다. 새 공유 제외 대상은 없으므로 guides/excluded_files.json은 변경하지 않았다.

아래는 앞선 자료 확인 시점의 기록이다.""",
        "columns/001-ball-count/analysis/handoff_bcap_review.md": f"""## 최신 인계 — {TAG}

이번 요청은 **구현 후 간단한 확인까지만**이다. [구현 보고서](runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md) · [HTML](runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.html) · [실행·해시](runs/bcap_followup__mlb_2024_2025__20260917__r01/manifest.json) · [문서 변경 기록](runs/bcap_followup__mlb_2024_2025__20260917__r01/document_update.json).

- 기존 결과 재사용: S/B 2024·2025 12카운트와 2023 12카운트의 Q(B), Q(S), Δ=S−B, 기존 보정 구간·분모·판정을 별도 표로 저장했다. [24행 CSV](runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/sb_reformatted.csv)·[표 산술 확인](runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/quick_checks.json). 새 학습/구간 계산은 없다.
- 새 관찰 산술: [BCAI-STATE-DELTA-v0.1.0](../../../models/bcai/state_delta/v0.1.0/model_card.md), EXPERIMENTAL. 시즌별 원 W 상태 평균 차이24행·빠른 확인84항목 PASS. [실행](runs/bcai_state_delta__mlb_2024_2025__20260917__r01/manifest.json)·[표와 재현](runs/bcai_state_delta__mlb_2024_2025__20260917__r01/report.md). PA×count 중복 제거 정의·저장 분모를 확인했으며 실제 투구 사건 빈도/사건조건부 W·새 구간은 미산출이다.
- 탐색 분해: [BCAP-DECOMP-v0.1.0](../../../models/bcap/decomposition/v0.1.0/model_card.md), DRAFT. 동일 참조행의 확률×조건부 최종 W 합성·입력 검사·모의 확인만 구현했다. [실행](runs/bcap_decomp__synthetic_smoke__20260917__r01/manifest.json). 실제 MLB 가지 모형의 적합·보정·지원 검토·새 AIPW/구간은 미실행이다.
- 상대 반응: [필수 입력과 고정 가정](runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/scenario_contract.json). 기존 S/B와 타자 주변 평균의 결합은 금지한다. 같은 기준 행의 결합값·지원이 없어 0-2/1-2 시나리오 수치와 임계 반응률은 보류했다.

모든 기존 모델·실행·원본·이전 인계 증거는 유지했다. OBS/V1 검증을 새 모듈에 전용하지 않았고 VALIDATED 승격도 없다. 2026 S/B·SWING 측정 보류, 이미 노출된 2023·2026 이력도 유지한다. 다음 검수자는 먼저 새 상태 표의 분모와 일반 전이/특수 사건 구분, 분해의 모의 실행 표시와 미실행 목록을 확인하면 된다. 실제 분해·시나리오 학습을 자동으로 이어가지 않는다.

아래는 이전 완료 작업의 인계이며 당시 범위를 보존한다.""",
        "columns/001-ball-count/model_research_followup_20260917.md": f"""## {TAG}

아래 설계 검토를 바탕으로 [구현 보고서](analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.md)와 [HTML](analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/report.html)을 추가했다. 기존 S/B의 양 행동 값을 재표시했고, 시즌 원 W 상태 평균 차이24행을 소형 계산했다. 확률×조건부 W 분해는 DRAFT 합성 코드·모의 확인까지만 구현했으며 실제 MLB 적합은 하지 않았다. 상대 반응 수치는 공동 조건·지원 미확보로 보류한다. 아래의 후속 제안은 전체 실행 완료를 뜻하지 않는다. 이번 작업은 간단한 확인에서 종료한다."""
    }
    updates = []
    for name, insert in specs.items():
        p = ROOT / name
        old_bytes = p.read_bytes()
        text = old_bytes.decode("utf-8-sig")
        if TAG in text:
            raise ValueError(f"중복 삽입 금지: {name}")
        title, body = text.split("\n", 1)
        new = title + "\n\n" + insert + "\n" + body
        p.write_text(new, encoding="utf-8", newline="")
        updates.append({"path": name, "before_sha256": hashlib.sha256(old_bytes).hexdigest(),
                        "after_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                        "change": "첫 제목 뒤 새 완료 범위 삽입; 이전 본문 보존"})
    marker.write_text(json.dumps({"timestamp_utc": datetime.now(timezone.utc).isoformat(),
                                 "status": "COMPLETE", "updates": updates}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"documents_updated": len(updates)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
