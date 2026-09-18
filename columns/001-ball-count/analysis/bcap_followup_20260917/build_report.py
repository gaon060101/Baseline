"""기존 소형 집계로 후속 구현 보고서를 생성한다. 학습/원자료 접근 없음."""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ANALYSIS = ROOT / "columns/001-ball-count/analysis"
RUNS = ANALYSIS / "runs"
DEV = RUNS / "bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/count_values.csv"
EXT = RUNS / "bcap_pitch_sb__mlb_2023__20260914__r01/artifacts/values.csv"
COMPARISON = ANALYSIS / "bcap_external_20260914__r01/comparison.csv"
STATE_RUN = RUNS / "bcai_state_delta__mlb_2024_2025__20260917__r01"
DECOMP_RUN = RUNS / "bcap_decomp__synthetic_smoke__20260917__r01"
COUNTS = [f"{b}-{s}" for b in range(4) for s in range(3)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def md_table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"] + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def inline(value):
    value = html.escape(value)
    value = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"`([^`]+)`", r"<code>\1</code>", value)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", value)


def render(md):
    output, table, listing = [], False, False
    for line in md.splitlines():
        if not line.startswith("| ") and table:
            output.append("</tbody></table></div>")
            table = False
        if not line.startswith("- ") and listing:
            output.append("</ul>")
            listing = False
        if line.startswith("| "):
            cells = [x.strip() for x in line.strip("|").split("|")]
            if all(set(x) <= set("- :") for x in cells):
                continue
            if not table:
                output.append('<div class="scroll"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr></thead><tbody>")
                table = True
            else:
                output.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
        elif line.startswith("#"):
            n = len(line) - len(line.lstrip("#"))
            output.append(f"<h{n}>{inline(line[n:].strip())}</h{n}>")
        elif line.startswith("- "):
            if not listing:
                output.append("<ul>")
                listing = True
            output.append("<li>" + inline(line[2:]) + "</li>")
        elif line.strip():
            output.append("<p>" + inline(line) + "</p>")
    if table:
        output.append("</tbody></table></div>")
    if listing:
        output.append("</ul>")
    return '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BCAI·BCAP 후속 구현 — 간단한 확인</title><style>body{font:16px/1.8 "Malgun Gothic",sans-serif;color:#243848;background:#f3f6f8;margin:0}main{max-width:1240px;margin:auto;padding:32px 24px 70px}h1{font-size:31px;border-bottom:4px solid #216575;padding-bottom:22px}h2{margin-top:42px;color:#17586a}h3{color:#17586a}p{max-width:1080px}a{color:#006f84}table{border-collapse:collapse;font-size:13px;background:white;min-width:100%}th,td{padding:10px 12px;text-align:left;border-bottom:1px solid #d9e3e9;white-space:nowrap}th{background:#e7eff3}tr:nth-child(even){background:#f7fafb}.scroll{overflow:auto}code{background:#e7edf0;padding:2px 4px;overflow-wrap:anywhere}li{margin:5px 0}footer{margin-top:40px;color:#607584}@media(max-width:700px){main{padding:18px 14px}h1{font-size:25px}}</style><main>''' + "\n".join(output) + "<footer>Baseline · 001 볼카운트 · 기존 결과 보존 · 새 학습 및 전체 검증 미실시</footer></main></html>"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"bcap_followup__mlb_2024_2025__\d{8}__r\d{2,}", args.run_id):
        raise ValueError("새 실행 ID 형식을 확인하세요")
    out = RUNS / args.run_id
    if out.exists():
        raise FileExistsError("기존 실행을 덮어쓰지 않습니다. 새 실행 ID를 사용하세요")
    state_manifest = STATE_RUN / "manifest.json"
    decomp_manifest = DECOMP_RUN / "manifest.json"
    state_csv = STATE_RUN / "artifacts/state_delta_2024_2025.csv"
    for p in (state_manifest, decomp_manifest):
        if not p.is_file():
            raise FileNotFoundError(p)
    out.mkdir()
    artifacts = out / "artifacts"
    artifacts.mkdir()
    link = lambda p: os.path.relpath(p, artifacts).replace(os.sep, "/")
    stamp = datetime.now(timezone.utc).isoformat()
    inputs = [DEV, EXT, COMPARISON, state_manifest, state_csv, decomp_manifest,
              RUNS / "bcap_pitch_sb__mlb_2026_ytd_20260907__20260914__r01/manifest.json"]
    input_hashes = {str(p.relative_to(ROOT)): digest(p) for p in inputs}
    dev = read_csv(DEV)
    ext = [r for r in read_csv(EXT) if r["region"] == "ALL" and r["population"] == "own"]
    comp = {r["count"]: r for r in read_csv(COMPARISON) if r["year"] == "2023" and r["model"] == "pitch_sb" and r["region"] == "ALL" and r["population"] == "own"}
    results, checks = [], []
    for label, rows in (("2024–2025 개발", dev), ("2023 기존 재현", ext)):
        assert len(rows) == 12 and sorted(r["count"] for r in rows) == sorted(COUNTS)
        for r in sorted(rows, key=lambda x: COUNTS.index(x["count"])):
            q0, q1, delta = (float(r[k]) for k in ("Q0", "Q1", "delta"))
            assert all(math.isfinite(v) for v in (q0, q1, delta))
            assert abs(q1 - q0 - delta) < 1e-12
            assert int(r["rows0"]) + int(r["rows1"]) == int(r["n"])
            assert abs(int(r["n"]) / int(r["n_all"]) - float(r["coverage"])) < 1e-12
            assert r["action0"] == "B" and r["action1"] == "S"
            is_dev = label.startswith("2024")
            lo, hi = (r[k] for k in (("family95_low", "family95_high") if is_dev else ("adjusted95_low", "adjusted95_high")))
            assert float(lo) <= delta <= float(hi)
            if not is_dev:
                c = comp[r["count"]]
                assert all(abs(float(r[k]) - float(c[k])) < 1e-12 for k in ("Q0", "Q1", "delta", "adjusted95_low", "adjusted95_high"))
            row = dict(period=label, count=r["count"], Q_B_W=r["Q0"], Q_S_W=r["Q1"], delta_S_minus_B_W=r["delta"],
                       ci_low_W=lo, ci_high_W=hi, family="219" if is_dev else r["family"],
                       n_all=r["n_all"], n=r["n"], coverage=r["coverage"], rows_B=r["rows0"], rows_S=r["rows1"],
                       ESS_B=r["ESS0"], ESS_S=r["ESS1"], games=r["games"], PA=r["PA"], support_gate=r["support_gate"],
                       classification=r["evidence"] if is_dev else comp[r["count"]]["judgment_ko"],
                       unit="W per selected current decision; not runs/probability or PA sum",
                       source=str((DEV if is_dev else EXT).relative_to(ROOT)))
            results.append(row)
        checks.append({"period": label, "rows": len(rows), "checks": ["12개 카운트 완전성", "Q_S-Q_B=delta", "n_B+n_S=n", "n/n_all=coverage", "action B/S", "stored CI contains point", "external comparison matches source" if not label.startswith("2024") else "original evidence retained"], "status": "PASS"})
    with (artifacts / "sb_reformatted.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    scenarios = {
        "status": "WITHHELD_DESIGN_AND_JOINT_SUPPORT",
        "empirical_calculation_executed": False,
        "counts_of_interest": ["0-2", "1-2"],
        "proposal": "고정된 공통 기준 행 i에 대해 q_i(r)=r*q_i(0), 0<=r<=1; Q_B(r)=mean_i[q_i(r)*M_B,Swing(i)+(1-q_i(r))*M_B,Take(i)].",
        "fixed": ["시즌별 최종 PA W", "기준 선수·투구 전 상황 분포", "존 밖 공 특성의 조건부 분포", "각 공·상황에서 행동별 조건부 최종 W", "존 안 공 및 존 안 반응 분포", "현재 한 구 이후의 관측된 후속 행동 체계"],
        "required": ["동일 훈련/평가 게임 분리 아래 q_i와 두 M의 결합 교차 적합 예측", "0-2·1-2의 양 행동 지원·ESS·보정 점검", "동일 투구 전 기준 분포로 표준화한 S 기준값 및 B 값", "불확실성 전달과 시나리오 해석 범위의 실행 전 고정"],
        "forbidden_substitution": "기존 S/B Q와 기존 Swing/Take Q의 네 집단 평균을 연결할 수 없음",
        "limits": "반응률만 바꿔도 접촉 품질·의도·상대 적응이 고정된다는 가정이며 실제 개입 효과나 Nash 균형이 아니다. 입력·지원이 없으므로 임계 반응률과 경험적 수치는 미산출."
    }
    dump(artifacts / "scenario_contract.json", scenarios)
    dump(artifacts / "quick_checks.json", {"created_at_utc": stamp, "status": "PASS", "scope": "소형 기존 집계 24행의 표기·산술 확인; 저장 점수/원자료/신뢰구간 재추정 없음", "checks": checks})
    headers = ["카운트", "Q(B) W", "Q(S) W", "Δ=S−B W", "기존 보정 구간 W", "n / 적격 투구", "포함률", "B / S 관측 수", "판정"]
    def values(row):
        return [row["count"], f'{float(row["Q_B_W"]):.4f}', f'{float(row["Q_S_W"]):.4f}', f'{float(row["delta_S_minus_B_W"]):+.4f}', f'[{float(row["ci_low_W"]):+.4f}, {float(row["ci_high_W"]):+.4f}]', f'{int(row["n"]):,} / {int(row["n_all"]):,}', f'{float(row["coverage"]):.1%}', f'{int(row["rows_B"]):,} / {int(row["rows_S"]):,}', row["classification"]]
    state_rows = read_csv(state_csv)
    assert len(state_rows) == 24
    state_tables = []
    for year in ("2024", "2025"):
        rows = [r for r in state_rows if r["year"] == year]
        state_tables.append("### " + year + " 상태 평균 차이 — 단위 W\n\n" + md_table(
            ["카운트", "도달 PA", "PA 도달률", "현재 V", "다음 볼 V", "다음 스트라이크 V", "볼−현재", "스트라이크−현재", "볼−스트라이크"],
            [[r["count"], f'{int(r["N_reached_PA"]):,}', f'{float(r["PA_reach_fraction"]):.1%}'] +
             [f'{float(r[k]):.4f}' for k in ("current_V_W", "next_ball_W", "next_strike_W", "delta_ball_W", "delta_strike_W", "ball_minus_strike_W")] for r in rows]))
    sections = [
        "# BCAI·BCAP 후속 구현 — 간단한 확인까지",
        "2026-09-17 · 기존 결과 재사용과 소형 파생 계산을 완료했다. 새 행동 가치 학습·전체 검증은 수행하지 않았다. 아래 네 종류를 구분한다.",
        md_table(["종류", "이번 반영", "현재 상태"], [
            ["기존 결과 재사용", "S/B 개발 12카운트의 양 행동 W·차이·기존 구간·표본 정리; 2023 별도 표시", "기존 BCAP EXPERIMENTAL 유지"],
            ["새 관찰 계산", "시즌별 BCAI 원 W에서 볼·스트라이크 다음 상태 평균 차이 24행", "BCAI-STATE-DELTA-v0.1.0 EXPERIMENTAL; 제한적 산술 확인"],
            ["새 탐색 구현", "확률×조건부 최종 W 합성 코드·입력 계약·모의 자료 확인", "BCAP-DECOMP-v0.1.0 DRAFT; 실제 자료 학습·추정 미실행"],
            ["가정 시나리오", "존 밖 스윙률 변화의 고정 조건·필수 입력 명세", "결합 추정과 공통 지원 미확보로 수치 보류"]]),
        "## 1. 기존 투수 S/B 결과를 읽기 쉽게",
        "S는 관측된 공 중심이 존 안, B는 존 밖이다. 심판 판정이나 투수 의도가 아니다. Q는 같은 비교 가능 기준 행에 표준화한 기존 보정 최종 PA 공격가치다. 낮은 W가 투수에게 유리하므로 양의 Δ=S−B는 B 쪽이 낮다는 뜻이다. W는 득점·확률이 아니며 타석의 각 공 Δ를 합산하지 않는다.",
        "### 2024–2025 개발 — 기존 추정 재표시",
        md_table(headers, [values(r) for r in results[:12]]),
        "기존 Bonferroni 219개 비교 보정 구간과 판정을 그대로 옮겼다. 12개 모두 기존 지원 기준을 통과했다. 포함률은 n/해당 카운트 적격 투구이며 B/S 관측 수는 이 비교 표본의 행동 수다. 같은 타석이 반복 투구로 나타날 수 있어 n은 고유 PA 수가 아니다. CSV에 경기·고유 PA·ESS도 보존했다.",
        f'[개발 원 CSV]({link(DEV)}) · [읽기용 24행 CSV](sb_reformatted.csv)',
        "### 2023 — 기존 과거 연도 재현을 별도로",
        md_table(headers, [values(r) for r in results[12:]]),
        "2023의 0-2·1-2 구간은 주4개, 나머지 10카운트는 보조236개 비교 보정이다. 개발219와 보정 범위가 다르므로 구간 폭을 직접 성능 순위로 해석하지 않는다. 2023은 이미 노출된 과거 자료에서 고정 학습 절차를 재현한 결과이며 이번에 새로 학습하지 않았다. 2026 S/B·SWING은 좌표 기준면·존 정의의 정합성 미확보로 계속 측정 보류한다.",
        f'[2023 원 CSV]({link(EXT)}) · [기존 외부 최종 보고서]({link(ANALYSIS / "bcap_external_20260914__r01/final_report.html")})',
        "## 2. 새 계산 — 볼·스트라이크 상태 평균의 차이",
        "V_y(c)는 해당 시즌에 카운트 c를 한 번 이상 밟은 유효 완료 PA의 최종 W 평균이다. 같은 PA가 같은 카운트를 반복해도 한 번만 센다. 2024 유효 PA 181,840개, 2025 182,284개이며 카운트마다 도달 PA 분모가 달라진다. 기존 저장 원 W를 사용했고 0-0=100인 지수 I(c)를 W로 오인하지 않았다.",
        "새 표는 V(다음 볼)−V(현재), V(다음 스트라이크)−V(현재), V(다음 볼)−V(다음 스트라이크)를 시즌별로 계산한다. 각 값의 집단은 서로 다르다. 볼을 의도적으로 하나 추가한 인과 효과나 실제 해당 전이 사건 뒤의 평균 W가 아니다.",
        f'[시즌별 24행·예외·분모 설명]({link(STATE_RUN / "report.md")}) · [원 CSV]({link(state_csv)}) · [실행·입출력 해시]({link(state_manifest)})',
        "3볼 다음 볼은 해당 시즌 BB 가중치, 2스트라이크 다음 종료 삼진은 기존 OBS 정의의 W=0이다. 보통 2스트라이크 파울의 상태 변화는0이다. HBP는 별도 종료 가치이며 번트 파울·파울팁·낫아웃·실책은 사건/최종 결과 정의를 확인해야 하므로 일반 볼·스트라이크 전이로 강제하지 않는다. 종료 삼진/실책의 W=0은 실제 주자 진루·득점이0이라는 뜻이 아니다. 상세 예외는 새 명세에 기록했다.",
        "도달 PA 비율은 상태 등장 빈도이며 실제 투구 사건 빈도와 다르다. 사건별 발생률·사건조건부 W 표와 새 불확실성 구간은 미산출했다. 차이에 필요한 공동 변동 정보를 기존 개별 지수 구간에서 만들지 않았고, 전이 차이를 최종 W에 더하지 않았다.",
        "\n\n".join(state_tables),
        "## 3. 별도 분해 구현 — 실제 MLB 결과는 아직 없음",
        "현재 행 i와 행동 a에서 m_dec(i,a)=Σ_k p(k|i,a)×E[최종 PA W|i,a,k]로 합성한 뒤 같은 기준 행에서 평균한다. 집단별 평균 확률과 평균 조건부 W를 먼저 곱하면 일반적으로 다른 값이 되므로 행별 합성을 구현했다. 카운트·5구역 평균과 가지별 기여를 보고하며 모서리는 두 보고 집합에 포함된다. 전체 평균이나 학습 행을 중복시키지 않는다.",
        "테이크는 볼(블로킹 볼 포함)·루킹 스트라이크·HBP로, 스윙은 헛스윙·보통 파울·파울팁·번트 파울·번트 헛스윙·번트 파울팁·인플레이로 나눈다. 인플레이의 번트 여부는 description만으로 강제 분리하지 않는다. 체크스윙은 판정된 기존 행동 라벨의 한계를 유지하며 자동 판정·피치아웃·미분류를 테이크로 채우지 않는다. 가지의 description은 정답 구성에만 쓰고 예측 입력으로 쓰지 않는다.",
        "같은 행의 직접 결과회귀 예측값과 합성 예측값을 비교하는 입력 경로를 만들었다. 이것은 기존 AIPW Q와의 새 실증 비교 완료가 아니다. 실제 가지 확률·조건부 W 보정 모형의 적합, 훈련 내부 범주/보정, 가지별 지원 기준, 경기 군집 구간 및 학습 불확실성은 후속 실행 전에 구체화해야 한다. 이번에는 모의 자료로 계산과 잘못된 입력의 거절만 확인했다.",
        f'[분해 카드]({link(ROOT / "models/bcap/decomposition/v0.1.0/model_card.md")}) · [분해 확인 실행]({link(decomp_manifest)})',
        "분해 구조와 추정기를 별도로 선택했다. 참고 논문은 이닝 잔여 득점을 분해하며 §5.1에서 다른 목표·추정기·세분 가지를 허용한다. 우리는 최종 PA W와 기존 라벨을 유지한다. BART 도입이나 인과 식별 개선을 주장하지 않는다. [Yee·Deshpande, §2.2·3·5.1](https://arxiv.org/html/2305.05752v2).",
        "## 4. 상대가 덜 스윙하는 경우 — 계산 보류",
        "검토할 수식은 Q_B(r)=평균_i{r q_i M_B,스윙(i)+(1−r q_i)M_B,테이크(i)}이며 0≤r≤1이다. 기준 상황·선수·존 밖 공 특성 분포, 행동별 조건부 W, 존 안 반응과 이후 타석 행동 체계는 고정한다고 가정한다. 타자의 반응 변화로 접촉 품질이나 투수의 대응이 바뀌는 경우까지 설명하지 않는다.",
        "현재 저장 표에는 이 계산에 필요한 같은 기준 행의 결합 q·두 조건부 W와 맞춰진 S 기준값이 없다. 기존 S/B와 Swing/Take의 평균을 연결하면 보정 상태와 기준 집단이 달라진다. 따라서 0-2·1-2 이점이 사라지는 반응률, 2×2 보수, 최적 혼합비율을 산출하지 않았다. [고정 조건·필수 입력 명세](scenario_contract.json).",
        "최적 투구 논문의 3-0 목표 행동, 구종별 Gaussian 제구 오차, 카운트에 공통인 오차는 모형 가정이다. 해당 게임의 최적해 계산은 실제 적용 정책의 검증과 구별한다. [Douglas 외, §4.2](https://arxiv.org/html/2110.04321v1). MONEYBaRL의 전략 평가에는 현재 구종을 정확히 아는 가정이 있고, 이후 시뮬레이션에서 인식 오차를 다룬다. 사후 기록된 위치·구종을 타자의 실제 의사결정 정보와 동일시하지 않는다. [Sidhu·Caffo, §4.1–4.2](https://arxiv.org/html/1407.8392v1).",
        "## 간단한 확인과 남은 실행",
        "이번 직접 확인은 S/B 24행의 행동 부호·Q 차이·표본 합·포함률·원 구간 복사, 새 상태 표의 소형 산술, 분해 코드 구문·작은 모의 자료 확인이다. 기존 신뢰구간·교차 적합의 전체 검증을 새로 수행한 것이 아니다. [S/B 확인 기록](quick_checks.json).",
        "실제 분해 모델은 학습하지 않았고 지원·calibration·직접/분해 추정값 일치·불확실성에 대한 MLB 수치도 없다. 이 확인을 통과해도 실제 결과를 칼럼에 추가할 수 없다. 상태 표는 설명용 관찰 차이로만 사용할 수 있으며 강한 통계적 주장에는 PA 연결·전이 사건 분모와 공동 불확실성의 별도 검토가 필요하다.",
        "기존 BCAP 구간은 저장 점수의 경기 군집 변동 범위로, 전체 재학습과 경기 간 선수 의존성을 모두 반영하지 않는다. 선수 보정 뒤 미측정 차이도 남는다. 이 한계를 이유로 기존 관찰 패턴을 지우거나 새 추천을 만들지는 않았다.",
        "새 원본·정제본·행별 MLB 캐시·모델 객체를 만들지 않아 새 업로드 제외 파일은 없다. 기존 제외 목록을 유지한다. 전체 학습·추가 seed·부트스트랩·KBO·2026 위치 재개·경로 전체 확장·외부 업로드는 수행하지 않았다.",
        "## 칼럼에 쓸 수 있는 결론",
        "2024–2025 개발자료에서 0-2와 1-2는 실제 공 중심이 존 밖에 온 경우의 보정 최종 공격가치가 각각 약0.028 W, 0.021 W 낮았다. 기존 2023 재현에서도 같은 방향이었지만, 이는 투수가 의도적으로 볼을 빼면 그만큼 이득이라는 뜻은 아니다. 새 상태 표는 볼·스트라이크 다음 카운트를 밟은 타석들의 평균 가치가 어떻게 다른지 보여준다. 상대가 존 밖 공에 덜 스윙할 때 이 이점이 유지되는지는 아직 계산하지 않았다.",
        "## 재현과 파일",
        "보고서 재생성은 프로젝트 루트에서 `python -B columns/001-ball-count/analysis/bcap_followup_20260917/build_report.py --run-id bcap_followup__mlb_2024_2025__20260917__r02`를 사용한다. 목적지가 있으면 새로운 ID가 필요하다. 이 명령은 학습하지 않고 완료된 두 소형 실행을 읽는다.",
        f'[보고 실행 manifest](../manifest.json) · [상태 계산 재현 안내]({link(STATE_RUN / "report.md")}) · [분해 구현/입력 안내]({link(ROOT / "models/bcap/decomposition/v0.1.0/model_card.md")})',
        "공유 문서 변경: README·모델 레지스트리·column·sources·인계와 기존 모델 발전 검토에 이번 구현/보류 범위를 연결했다. 기존 모델 정의와 완료 실행은 보존했으며 어느 모델도 VALIDATED로 승격하지 않았다.",
    ]
    md = "\n\n".join(sections) + "\n"
    (artifacts / "report.md").write_text(md, encoding="utf-8")
    (artifacts / "report.html").write_text(render(md), encoding="utf-8")
    assert all(digest(ROOT / p) == h for p, h in input_hashes.items())
    manifest = {
        "run_id": args.run_id, "run_type": "presentation_and_small_derived_results_bundle",
        "model_id": "BCAP-PITCH-SB-v0.1.0", "version": "0.1.0", "model_status": "EXPERIMENTAL",
        "related_models": ["BCAI-STATE-DELTA-v0.1.0", "BCAP-DECOMP-v0.1.0"],
        "status": "COMPLETE_WITH_EXPLICIT_DEFERRALS", "created_at_utc": stamp,
        "executed": ["기존 집계 S/B 24행 재표시·산술", "가정 시나리오 입력 계약 저장", "완료된 새 소형 실행 연결"],
        "not_executed": ["모델 학습", "원자료 전체 검토", "새 신뢰구간", "경험적 분해·상대반응 추정", "2026 위치 평가"],
        "inputs_sha256": input_hashes, "code_sha256": {str(Path(__file__).relative_to(ROOT)): digest(Path(__file__))},
        "command": f"python -B {Path(__file__).relative_to(ROOT).as_posix()} --run-id {args.run_id}",
        "outputs_sha256": {p.relative_to(out).as_posix(): digest(p) for p in sorted(artifacts.iterdir()) if p.is_file()},
        "input_preservation": "PASS", "sharing": "새 대형/행별 데이터·캐시·모델 객체 없음; excluded_files 추가 대상 없음"
    }
    dump(out / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "report": str(artifacts / "report.html"), "sb_rows": len(results)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
