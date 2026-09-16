from pathlib import Path
import csv, html, json, hashlib

HERE=Path(__file__).resolve().parent
A=HERE.parent
inputs=[]
def read(p):
    p=A/p; inputs.append(p)
    return list(csv.DictReader(p.open(encoding='utf-8-sig')))
sb=read(Path('runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/count_values.csv'))
sw=read(Path('runs/bcap_swing__mlb_2024_2025__20260912__r01/artifacts/count_values.csv'))
zones=read(Path('bcap_v2_development_20260912__r01/batter_five_regions.csv'))
mix=read(Path('runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/primary_values.csv'))
e=html.escape
def f(r,k): return float(r[k])
def num(r,k): return f'{f(r,k):+.3f}'
def interval(r,p='family95'): return f'[{num(r,p+"_low")}, {num(r,p+"_high")}]'
def table(head,rows): return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+e(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
parts=[]
def section(title,body): parts.append('<section><h2>'+title+'</h2>'+body+'</section>')
section('まず結論'.replace('まず結論','먼저, 이번에 알게 된 것'),'<div class="cards"><article><b>투수 · 실제 존 안/밖</b><h3>0-2 · 1-2는 존 밖</h3><p>허용 공격가치가 약 0.02~0.03 W 낮았다. 0-1은 불명확, 나머지 9카운트는 존 안 방향이 뚜렷했다.</p></article><article><b>투수 · 구종 계열</b><h3>대부분 우열 보류</h3><p>FB/NFB와 포심/비포심 모두 확인했다. 3-2 비포심 우세의 단서는 보존하되 추가 분류 탐색은 종료한다.</p></article><article><b>타자 · 위치와 판단</b><h3>존 안 스윙 · 존 밖 테이크</h3><p>전반적인 점추정 패턴이다. 3-0 존 안은 불명확하고, 존 밖 네 구역은 비교 자료가 부족하다.</p></article></div><p class="note">MLB 2024·2025 개발 결과 · EXPERIMENTAL. 새로운 분석·재학습·외부 검증 없이 저장된 결과를 정리했다. 행동 지시의 인과 효과나 모든 선수에게 통하는 법칙은 아니다.</p>')
section('W를 읽는 방법','<p>W는 시즌별 가중치를 적용한 <strong>타석 최종 공격가치</strong>다. 타자는 클수록, 투수는 허용하는 값이 작을수록 유리하다. 공식 wOBA·득점·확률과 동일한 단위가 아니다.</p><p><strong>1-2에서는 S 약 0.240, B 약 0.218</strong>로 차이가 약 0.021 W다. 지표 수준으로는 S 대비 약 9% 낮지만, 실점이나 안타 확률이 9% 줄었다는 뜻은 아니다. 0.01 W는 기존 설계의 참고 기준이며 보편적 야구 가치 기준은 아니다.</p><p>현재 한 구와 연결된 최종 타석 가치를 비교한다. 같은 타석의 여러 투구 차이를 더해 총이득으로 계산할 수 없으며, 이후 타석 전체의 행동 정책을 바꾼 결과도 아니다.</p>')
section('투수 ① · 스트라이크존 안과 밖', '<p>S=실제 공 중심이 존 안, B=존 밖이다. 심판 판정이나 투수 의도가 아니다. 존 안 홈런도 S, 존 밖 헛스윙도 B다. Δ=S−B: <strong>음수는 S, 양수는 B 방향</strong>.</p>'+table(['카운트','B의 W','S의 W','Δ W','보정 구간','관찰상 판정','비교 투구 / 포함률'],[[r['count'],f'{f(r,"Q0"):.3f}',f'{f(r,"Q1"):.3f}',num(r,'delta'),interval(r),r['point_direction']+' · '+r['evidence'],f'{int(r["n"]):,} / {f(r,"coverage"):.1%}'] for r in sb])+'<p class="note">0-2의 B 이점은 0.028 W [0.015, 0.040], 1-2는 0.021 W [0.011, 0.032]. 두 구간 모두 0.01 W를 넘는다. 이는 관측된 존 밖 공들의 평균 비교이며, 무조건 멀리 빼는 공을 권하는 결과가 아니다.</p>')
section('투수 ② · 구종 계열을 바꿔 묶어도 답이 나왔나?','<p>FB=포심·싱커·커터, NFB=나머지 허용 구종. FF/non-FF는 포심/비포심이며 싱커·커터는 비포심에 속한다. 미상 구종은 임의로 비포심에 넣지 않았다.</p><p>아래는 <strong>두 분류 모두 비교 가능한 공통 1,268,736구</strong>에서의 결과다. 같은 표본이어도 비교하는 행동 내용은 다르다. 각 Δ는 앞 계열−뒤 계열이므로 양수면 뒤 계열이 투수에게 유리하다.</p>'+table(['카운트','FB−NFB / 구간','근거','포심−비포심 / 구간','근거'],[[c, num(next(r for r in mix if r['count']==c and r['scheme']=='FB' and r['population']=='common'),'delta')+' '+interval(next(r for r in mix if r['count']==c and r['scheme']=='FB' and r['population']=='common'),'adjusted95'),e(next(r for r in mix if r['count']==c and r['scheme']=='FB' and r['population']=='common')['judgment']),num(next(r for r in mix if r['count']==c and r['scheme']=='FF' and r['population']=='common'),'delta')+' '+interval(next(r for r in mix if r['count']==c and r['scheme']=='FF' and r['population']=='common'),'adjusted95'),e(next(r for r in mix if r['count']==c and r['scheme']=='FF' and r['population']=='common')['judgment'])] for c in [r['count'] for r in sb]])+'<p>0-0は'.replace('0-0は','<p>0-0은')+'두 분류 모두 ±0.01 W 안의 작은 범위다. 3-2 비포심 우세는 두 연도·세 분할에서 방향이 유지됐지만 최소 0.01 W 이득까지 확보하지 못했다.</p><p>기존 FB의 3-0 차이는 남아 있다. 일부 분할의 유효 표본 부족과 보정 의존성 때문에 보류한 것이며 부호 반전은 아니다. FF의 3-0은 실제 분할 반전이 있다. FB의 3-1은 결과모형과 최종 보정값의 부호가 다르다.</p>')
section('타자 ① · 카운트만 보면', '<p>아래는 해당 카운트에서 관측된 공들의 위치·특성 구성을 평균낸 결과다. <strong>모든 위치에서 같은 행동을 하라는 뜻은 아니다.</strong> Δ=스윙−테이크: 양수면 스윙, 음수면 테이크 방향이다. 스윙에는 기록상 번트 등 공격 시도가 포함된다.</p>'+table(['카운트','테이크 W','스윙 W','Δ W','보정 구간','근거','비교 투구'],[[r['count'],f'{f(r,"Q0"):.3f}',f'{f(r,"Q1"):.3f}',num(r,'delta'),interval(r),r['point_direction']+' · '+r['evidence'],f'{int(r["n"]):,}'] for r in sw]))
rows=[]
for c in [r['count'] for r in sb]:
    cells=[c]
    for z in ['HIGH','LOW','INSIDE','OUTSIDE','CENTER']:
        r=next(r for r in zones if r['count']==c and r['region']==z)
        ok=r['support_gate']=='True'; d=f(r,'delta')
        cls='unknown' if not ok or r['evidence']!='관찰상 방향 뚜렷' else ('swing' if d>0 else 'take')
        label='자료 부족' if not ok else ('스윙' if d>0 else '테이크')+(' · 불명확' if r['evidence']!='관찰상 방향 뚜렷' else '')
        cells.append(f'<div class="{cls}"><b>{label}</b><br>'+ (num(r,'delta')+' W<br><small>'+interval(r)+'</small>' if ok else '—')+f'<br><small>투구 {f(r,"fraction_of_count_all"):.1%} · 스윙 {f(r,"action1_rate_all"):.1%}</small></div>')
    rows.append(cells)
section('타자 ② · 어디의 공을 치고, 어디의 공을 참을까?', '<p>가운데는 <strong>존 안 전체</strong>다. 위·아래·몸쪽·바깥쪽은 존 밖 구역이며 모서리는 두 구역에 겹친다. 따라서 구역 비율의 합이 100%를 넘을 수 있지만 학습 자료의 공은 중복하지 않았다.</p><p>각 칸은 스윙−테이크의 W 차이와 보정 구간이다. 투구 비율은 해당 카운트 전체 적격 공 대비, 실제 스윙률은 해당 구역 적격 공 대비다. 가치 비교는 그중 비교 가능 표본에 한정한다.</p>'+table(['카운트','높음','낮음','몸쪽','바깥쪽','존 안 전체'],rows)+'<p class="note">존 밖에서 음수의 절댓값이 클수록 그 구역에서 스윙한 쪽의 가치가 테이크보다 낮았다. 존 안에서 양수가 클수록 테이크한 쪽의 가치가 낮았다. 서로 다른 구역은 공·선수 구성이 달라, 가장 큰 값을 곧바로 보편적인 ‘최약점 위치’로 단정할 수 없다.</p><p>특히 3-0 존 안은 스윙 우세 점추정이나 구간이 0을 포함한다. 존 밖 네 구역은 자료 부족이다. 공의 실제 위치·움직임은 사후에 측정한 정보로, 타자가 순간적으로 정확히 알 수 있었다는 뜻은 아니다.</p>')
review=[
('1 · 정의와 원자료 연결','우선 · 재학습 없이','S/B 기하 경계·공 반경 미반영, 타자 좌우 변환·5구역 중첩, 구종 코드·번트·HBP·체크스윙 처리와 투구 전 카운트를 원자료 표본에서 독립 확인한다. 시즌 W와 타석 종료 결과 연결, 기존 카운트 예외 2행 및 완료 타석·고의볼넷 제외의 영향을 확인한다.','틀린 행동 분류나 잘못 연결한 최종 결과로 생긴 차이가 아닌가?'),
('2 · 자료 분리와 독립 수치 검산','우선 · 저장 결과 활용','원 제작 함수와 별도 계산으로 저장 행별 점수의 Q·차이·경기 군집 표준오차·구간·표본·ESS를 재현한다. 같은 경기의 투구가 훈련/평가에 섞이지 않는지, 사전·규제 선택·선택확률 보정이 훈련 안에서만 수행됐는지 확인한다. V2는 정책 학습을 하지 않았으므로 정책 평가 검증을 했다고 부르지 않는다.','표의 수치와 분리 원칙이 실제 구현과 일치하는가?'),
('3 · 보정과 비교 가능성','우선 · 기존 예측 재사용','카운트·구역별 양 행동 겹침, 선수별 양 행동 수, 극단 가중치, 제외 표본을 확인한다. 단순 평균·결과모형·AIPW의 차이와 선택확률 보정 상태를 비교한다. 0-2/1-2 S/B, 타자 3-0, 구종 3-0/3-1/3-2를 집중 점검한다.','특정 소수 사례나 모형 가정이 결론을 좌우하는가?'),
('4 · 판정과 결과 열람 이력','우선 · 문서/구간 확인','S/B·타자의 기존219 비교와 구종 추가255 비교의 범위를 대조한다. 통합 보고서의 새 공동 판정을 만들지 않는다. 0.01 W 기준·결과 전 기록·결과 후 변경을 확인하고, 불명확/작은 차이/표본 부족을 구분한다.','결과를 본 뒤 유리한 판정 기준을 고른 것은 아닌가?'),
('5 · 학습과 반복 투구의 불확실성','후속 · 범위 합의 후','현재 구간은 고정된 점수의 경기 의존성을 반영한다. 재학습 변동과 경기 간 동일 선수·시리즈 의존성은 포함하지 않는다. 앞 검수에서 필요한 이유가 생기면 제한된 반복 적합이나 적절한 군집 설계를 정한다. 횟수를 늘리는 것만으로 유효한95% 구간이 보장되지는 않는다.','모형을 다시 만들거나 의존성을 넓혀도 핵심 패턴이 유지되는가?'),
('6 · 다른 자료에서의 재현','후속 · 별도 승인 범위','검수 후 가설·제외·좌표·판정 기준을 고정하고 외부 자료에 적용한다. 2023/2026은 과거 작업 노출 이력을 기록하며, 특히2026 타자 위치 측정 체계 정합성을 먼저 해결한다. V1 외부 결과를 V2 검증으로 전용하지 않는다. KBO는 별도 가설 검증이다.','2024·2025 개발자료 밖에서도 같은 패턴인가?')]
section('BCAP는 어떤 검수를 거쳐야 하나?', '<p><strong>현재 완료:</strong> 제작 과정의 키·행동·결과 연결, 게임 분리·금지 입력·수렴·유한값·기본 산술 확인. 구종 추가 비교는 기존 FB 재집계 일치와 연도/분할 탐색도 완료했다. 이들은 V2 전체의 독립 검수나 외부 검증을 대신하지 않는다.</p>'+table(['단계','진행 순서','확인할 내용','검수의 질문'],review)+'<p><strong>권장 시작점:</strong> 1~4를 독립 검수하고 오류·영향·수정 필요 여부를 기록한다. 5~6은 지금 자동 실행하지 않는다. 검수 통과는 계산과 제한된 해석을 지지하며 실제로 투구 지시를 바꾸면 같은 효과가 난다는 인증은 아니다.</p><p>선수 효과 보정은 관측 선수 구성의 차이를 줄이지만 당일 구위·컨디션·의도·타자의 예상 등 미측정 차이를 없애지 못한다. 타자 모델은 사후 공 특성을 조건으로 한 진단이며 실시간 선택 정책과 다르다. S/B와 스윙/테이크는 비교 조건이 달라 두 차이를 더하거나 직접 크기로 대결시킬 수 없다.</p>')
section('근거와 재현 경로','<p>아래 링크는 기존 원 결과다. 이 보고서는 모델 버전·수치·판정을 변경하지 않았다. S/B와 타자 구간은 기존219 비교, 구종 구간은255 비교 보정이다. 모두 고정 점수 기준의 명목95%이며 실제 포함률은 미검증이다.</p><ul>'+''.join(f'<li><a href="../{p.relative_to(A).as_posix()}">{e(p.relative_to(A).as_posix())}</a></li>' for p in inputs)+'<li><a href="../handoff_bcap_review.md">최신 검수 인계와 V1/V2 이력</a></li><li><a href="../bcap_v2_development_20260912__r01/report.html">기존 상세 보고서 · 구역별 표본 및 FB/NFB별 타자 결과</a></li><li><a href="../bcap_pitch_classification_20260912__r01/report.html">구종 분류 추가 비교 상세</a></li></ul>')
css='''body{margin:0;background:#f3f5f7;color:#192b3c;font:16px/1.7 "Malgun Gothic",sans-serif}header{background:#102b3d;color:white;padding:50px max(24px,calc((100vw - 1240px)/2))}header p{color:#bfd5de}h1{font-size:38px;line-height:1.3}main{max-width:1240px;margin:auto;padding:22px}section{background:white;padding:28px;margin:22px 0;border:1px solid #dde5ea;border-radius:14px}h2{font-size:25px;margin-top:0}h3{font-size:22px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}article{background:#edf4f6;border-radius:10px;padding:20px}.note{border-left:4px solid #b9862e;background:#fff8e9;padding:15px}.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:12px;border-bottom:1px solid #dde5ea;text-align:left;vertical-align:top}th{background:#edf2f5;white-space:nowrap}td:first-child{font-weight:700;white-space:nowrap}small{font-size:12px;color:#526678}.swing{color:#116657}.take{color:#245c91}.unknown{color:#866827}a{color:#21678b;overflow-wrap:anywhere}@media(max-width:750px){.cards{grid-template-columns:1fr}main{padding:8px}section{padding:18px}h1{font-size:29px}}@media print{header{padding:20px}section{break-inside:avoid;margin:10px 0;padding:12px}.scroll{overflow:visible}body{font-size:11px}table{font-size:10px}}'''
doc='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BCAP · 투수와 타자의 선택</title><style>'+css+'</style><header><p>BASELINE / 001 BALL COUNT / 2026.09.14</p><h1>투수와 타자의 선택,<br>어디까지 알게 됐을까?</h1><p>BCAP V2 + 포심 추가 비교 · 결과를 이해하는 보고서와 검수 안내</p></header><main>'+''.join(parts)+'</main></html>'
(HERE/'report.html').write_text(doc,encoding='utf-8')
manifest={'purpose':'Existing result presentation only; no model fitting or validation','inputs':{str(p.relative_to(A)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'output_sha256':hashlib.sha256((HERE/'report.html').read_bytes()).hexdigest(),'row_checks':{'sb':len(sb),'swing_count':len(sw),'five_regions':len(zones),'classification':len(mix)}}
assert (len(sb),len(sw),len(zones),len(mix))==(12,12,60,48)
(HERE/'report_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(manifest['row_checks']))
