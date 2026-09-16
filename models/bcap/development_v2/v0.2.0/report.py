"""One readable V2 development report from the three completed local runs."""
from pathlib import Path
import json,hashlib,datetime,sys,html,shutil,os
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[4];AN=ROOT/'columns/001-ball-count/analysis'
DAY=datetime.datetime.now().strftime('%Y%m%d');B=AN/f'bcap_v2_development_{DAY}__r01'
MODELS=['pitch_sb','pitch','swing'];COUNTS=[f'{b}-{s}' for b in range(4) for s in range(3)]
RIDS={m:f'bcap_{m}__mlb_2024_2025__{DAY}__r01' for m in MODELS}
NAM={'pitch_sb':'투수 · 실제 존 안/밖 S/B','pitch':'투수 · FB/NFB','swing':'타자 · Swing/Take'}
LABEL={'S':'S(존 안)','B':'B(존 밖)','FB':'FB','NFB':'NFB','Swing_including_bunts':'Swing','Take':'Take','TIE':'동률'}
REGIONS=['HIGH','LOW','INSIDE','OUTSIDE','CENTER']
def j(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return dict(path=Path(p).relative_to(ROOT).as_posix(),sha256=sha(p),bytes=Path(p).stat().st_size)
def js(p,o):Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8')
def h(x):return html.escape(str(x))
def num(x,n=3):return '—' if pd.isna(x) else f'{x:.{n}f}'
def pct(x):return '—' if pd.isna(x) else f'{100*x:.1f}%'
def interval(r):return f"[{r.family95_low:+.4f}, {r.family95_high:+.4f}]" if r.support_gate else '비교 자료 부족'
def direction(r):return LABEL.get(r.point_direction,'보류') if r.support_gate else '보류'
def link(p,label):return f'<a href="{h(Path(os.path.relpath(p,B)).as_posix())}">{h(label)}</a>'
def table(headers,rows):return '<div class="scroll"><table><thead><tr>'+''.join(f'<th>{h(x)}</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def strength(r):return '<span class="'+('clear' if r.evidence=='관찰상 방향 뚜렷' else 'muted')+'">'+h(r.evidence)+'</span>'
man={};data={};basic={}
for m,rid in RIDS.items():
 run=AN/'runs'/rid;man[m]=j(run/'manifest.json');assert man[m]['status']=='COMPLETE'
 data[m]=pd.read_csv(run/'artifacts/action_values.csv');basic[m]=j(run/'artifacts/basic_checks.json');assert basic[m]['status']=='PASS'
assert sum(len(d) for d in data.values())==219
mainrows=[]
for m,d in data.items():
 for r in d[d.level.eq('count')].itertuples():mainrows.append(dict(model=m,count=r.count,n_all=r.n_all,n=r.n,action1_rate_all=r.action1_rate_all,Q0=r.Q0,Q1=r.Q1,delta=r.delta,family95_low=r.family95_low,family95_high=r.family95_high,point_direction=r.point_direction,evidence=r.evidence))
pd.DataFrame(mainrows).to_csv(B/'count_comparison_summary.csv',index=False)
regions=data['swing'][data['swing'].level.eq('region')].copy();cells=data['swing'][data['swing'].level.eq('region_pitch')].copy()
regions.to_csv(B/'batter_five_regions.csv',index=False);cells.to_csv(B/'batter_region_pitch_groups.csv',index=False)
stories=[]
for m in MODELS:
 d=data[m];ct=d[d.level.eq('count')];ok=ct[ct.support_gate];clear=ok[ok.evidence.eq('관찰상 방향 뚜렷')]
 directions=ok.point_direction.value_counts();a0=man[m]['configuration']['action0'];a1=man[m]['configuration']['action1']
 text=f"{NAM[m]}: 점추정은 {LABEL[a1]} 쪽 {int(directions.get(a1,0))}개, {LABEL[a0]} 쪽 {int(directions.get(a0,0))}개 카운트로 나뉜다. "
 text+=('동시 보정 명목 구간이 0을 제외한 카운트는 '+', '.join(clear['count'])+'이다.' if len(clear) else '동시 보정 명목 구간에서는 모든 카운트의 차이가 불명확하다.')
 stories.append(text)
center=regions[regions.region.eq('CENTER')]
outer=regions[~regions.region.eq('CENTER')]
regionaltext=f"위치를 나누면 가운데(존 안)는 12카운트 모두 Swing 쪽 점추정이며, {int(center.evidence.eq('관찰상 방향 뚜렷').sum())}개에서 보정 명목 구간이 0을 제외한다. 존 밖 상·하·좌·우는 비교 기준을 통과한 모든 셀에서 Take 쪽 점추정이다. 3-0의 존 밖 네 구역은 비교 자료 부족이다. 전체 카운트 평균과 구역별 결과는 서로 다른 집단 평균이다."
paired=cells[cells.pitch_group.eq('FB')].merge(cells[cells.pitch_group.eq('NFB')],on=['count','region'],suffixes=('_FB','_NFB'))
paired=paired[paired.support_gate_FB&paired.support_gate_NFB]
flips=paired[paired.delta_FB*paired.delta_NFB<0]
pitchtext=f"FB/NFB 양쪽이 비교 기준을 통과한 {len(paired)}/60개 카운트×구역에서는 Swing/Take의 점추정 방향이 뒤집힌 셀이 {len(flips)}개다. 차이의 크기와 구간은 각 표에 표시한다. 한쪽이라도 자료가 부족한 셀은 방향 일치 판단에서 제외했다. 구종군 사이 동등성이나 상호작용 부재를 입증한 결과는 아니다."
stories.append(regionaltext)
stories.append(pitchtext)
sb=data['pitch_sb'].query("level=='count'")
sb_reversal=sb[sb.support_gate & sb.delta.gt(0)]
sb_clear_reversal=sb_reversal[sb_reversal.evidence.eq('관찰상 방향 뚜렷')]
sbtext=('점추정에서 존 밖 B의 허용 공격가치가 더 낮은 카운트는 '+', '.join(sb_reversal['count'])+'이다.' if len(sb_reversal) else '이번 12카운트 점추정에서는 모두 존 안 S의 허용 공격가치가 더 낮았다.')
sbtext+=' 그중 보정 명목 구간에서도 방향이 분명한 경우는 '+(', '.join(sb_clear_reversal['count']) if len(sb_clear_reversal) else '없다')+'. 실제 목표 위치를 B로 바꾸면 개선된다는 뜻은 아니다.'
arrivals=regions.loc[regions.groupby('count',sort=False).n_all.idxmax()]
freq=arrivals.region_name.value_counts();freqtext='가장 자주 포함된 구역은 '+', '.join(f'{name}({n}개 카운트)' for name,n in freq.items())+'이다. 모서리는 두 구역에 들어가므로 서로 배타적인 점유율이 아니다.'
sections=[]
for m in MODELS:
 c=man[m]['configuration'];a0=LABEL[c['action0']];a1=LABEL[c['action1']];rows=[]
 for r in data[m][data[m].level.eq('count')].itertuples():
  rows.append([h(r.count),f'{pct(r.action1_rate_all)} / {pct(r.action0_rate_all)}',num(r.Q1) if r.support_gate else '—',num(r.Q0) if r.support_gate else '—',f'{r.delta:+.4f}' if r.support_gate else '—',interval(r),direction(r),strength(r),f'{int(r.n_all):,} → {int(r.n):,}<br><small>{pct(r.coverage)}</small>'])
 explanation='Δ가 음수면 '+a1+'가 투수에게 더 낮은 공격가치와 연결된다. 양수면 '+a0+'가 더 낮다.' if m!='swing' else 'Δ가 양수면 Swing, 음수면 Take의 기대 공격가치가 높다. Swing은 번트 포함 공격 시도이며 Take는 판정상 행동이다.'
 sections.append(f'<section id="{m}"><h2>{NAM[m]}</h2><p>{h(explanation)}</p>'+table(['카운트',f'실제 {a1} / {a0}',f'Q({a1})',f'Q({a0})',f'Δ {a1}−{a0}','보정 명목 95% 구간','점추정 유리 방향','근거 표시','적격 → 공통지지 행 / 포함률'],rows)+('<p class="note">'+h(sbtext)+'</p>' if m=='pitch_sb' else '')+'</section>')
regioncards=[]
for count in COUNTS:
 z=regions[regions['count'].eq(count)].set_index('region').loc[REGIONS].reset_index();rows=[];pitchrows=[]
 candidates=z[z.support_gate]
 largest=candidates.loc[candidates.delta.abs().idxmax()] if len(candidates) else None
 most=z.loc[z.n_all.idxmax()]
 for r in z.itertuples():
  risk='비교 자료 부족' if not r.support_gate else '스윙 쪽 가치 낮음' if r.delta<0 else '테이크 쪽 가치 낮음' if r.delta>0 else '동률'
  rows.append([h(r.region_name),pct(r.fraction_of_count_all),pct(r.action1_rate_all),num(r.Q0) if r.support_gate else '—',num(r.Q1) if r.support_gate else '—',f'{r.delta:+.4f}' if r.support_gate else '—',interval(r),h(risk)+'<br>'+strength(r),f'{int(r.n_all):,} → {int(r.n):,}<br><small>{pct(r.coverage)}</small>'])
  for group in ['FB','NFB']:
   rr=cells[cells['count'].eq(count)&cells.region.eq(r.region)&cells.pitch_group.eq(group)].iloc[0]
   pitchrows.append([h(r.region_name),group,pct(rr.action1_rate_all),f'{rr.delta:+.4f}' if rr.support_gate else '—',interval(rr),direction(rr),h(rr.evidence),f'{int(rr.n_all):,} → {int(rr.n):,}'])
 pattern=f"가장 자주 오는 구역: {most.region_name} {pct(most.fraction_of_count_all)}. "
 if largest is not None:pattern+=f"지원 기준을 통과한 구역 중 |차이|가 가장 큰 곳: {largest.region_name}, Δ={largest.delta:+.4f} W ({largest.evidence})."
 else:pattern+='모든 구역이 비교 자료 부족이다.'
 regioncards.append(f'<details'+(' open' if count=='0-0' else '')+f'><summary>{count} 카운트</summary><p>{h(pattern)}</p>'+table(['구역','투구 비율','실제 스윙률','Q(Take)','Q(Swing)','Δ Swing−Take','보정 명목 95% 구간','점추정 위험·근거','적격 → 공통지지 행 / 포함률'],rows)+'<h3>같은 구역의 FB/NFB별 Swing−Take 비교</h3><p class="small">각 구종군은 그 구종군의 실제 행에 표준화한다. 두 열 사이 차이는 공통 대상의 구종 효과나 통계적 상호작용 검정이 아니다.</p>'+table(['구역','구종군','실제 스윙률','Δ Swing−Take','보정 명목 95% 구간','점추정 유리','근거','적격 → 지지 행'],pitchrows)+'</details>')
overlap=pd.read_csv(AN/'runs'/RIDS['swing']/'artifacts/region_overlap_counts.csv');total=overlap.sum(numeric_only=True)
fit_info=[]
for m in MODELS:
 mm=man[m]['metrics'];fits=pd.read_csv(AN/'runs'/RIDS[m]/'artifacts/fit_diagnostics.csv')
 fit_info.append([NAM[m],f"{mm['n']:,}",f"{mm['support']:,}",pct(mm['coverage']),num(mm['MSE'],5),num(mm['Brier'],5),str(mm['fit_logs']),str(len(basic[m]['checks']))+' PASS'])
style='''body{font:16px/1.7 "Malgun Gothic",Arial,sans-serif;margin:0;color:#182737;background:#eef2f5}main{max-width:1440px;margin:auto;padding:38px 28px 70px}header,section{background:white;padding:28px;margin-bottom:24px;border-radius:12px}h1{font-size:32px;line-height:1.35;margin:8px 0}h2{font-size:23px;margin:0 0 14px;color:#123e50}h3{font-size:18px}p{max-width:1050px}a{color:#126b87}nav a{display:inline-block;margin:5px 18px 5px 0}.tag{color:#436474;font-size:14px;letter-spacing:.04em}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.55;margin:15px 0}th{background:#eaf2f5;text-align:left;white-space:nowrap}td,th{padding:10px 9px;border-bottom:1px solid #dce4e8}td{vertical-align:top}tbody tr:nth-child(even){background:#fafcfd}.clear{color:#17604d;font-weight:bold}.muted,small,.small{color:#65727b}.note{padding:16px;background:#fff7e6;border-left:4px solid #d6a448}.grid{display:grid;grid-template-columns:repeat(3,minmax(100px,180px));gap:5px;margin:20px 0}.grid div{padding:14px;text-align:center;background:#eaf2f5}.grid .center{background:#154b60;color:white}.grid .corner{background:#f8f2e5;font-size:13px}details{border:1px solid #dce4e8;border-radius:8px;padding:16px;margin:15px 0}summary{cursor:pointer;font-weight:bold;font-size:19px}code{font-size:13px}li{margin:7px 0}@media print{body{background:white}main{padding:0}section{padding:12px}details{break-inside:avoid}details>*{display:block}nav{display:none}}'''
assets='<ul>'+''.join('<li>'+link(AN/'runs'/RIDS[m]/'artifacts/count_values.csv',NAM[m]+' · 카운트 CSV')+' · '+link(AN/'runs'/RIDS[m]/'manifest.json','실행 manifest')+'</li>' for m in MODELS)+f'<li>{link(B/"batter_five_regions.csv","타자 5구역 CSV")} · {link(B/"batter_region_pitch_groups.csv","타자 구역×FB/NFB CSV")} · {link(B/"basic_summary.json","기본 확인 요약")}</li></ul>'
out='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BCAP V2 · 2024·2025 개발 보고</title><style>'+style+'</style><main><header><div class="tag">BASELINE · 001 BALL COUNT · V2</div><h1>카운트에 따라 존 안팎과 스윙의 유불리가 달라질까?</h1><p><b>2024·2025 개발 결과 산출 · 후속 검증 미실시</b><br>두 시즌 통합 MLB 정규시즌, 4,859경기. 관찰 자료를 보정한 평균 비교이며 실행 지시나 전체 PA 정책의 인과 효과가 아니다.</p><nav><a href="#pitch_sb">투수 S/B</a><a href="#pitch">투수 FB/NFB</a><a href="#swing">타자 전체</a><a href="#regions">타자 상하좌우</a><a href="#method">계산과 한계</a></nav><ul>'+''.join('<li>'+h(x)+'</li>' for x in stories)+'</ul></header>'
out+='<section><h2>표를 읽는 방법</h2><p>공격가치 W는 최종 타석 결과에 기존 시즌 가중치를 준 값이다. 투수는 낮은 쪽, 타자는 높은 쪽이 점추정상 유리하다. Q는 같은 실제 선수·상황의 공통 지지 행에서 양쪽을 비교한 보정 평균이다. <b>단위는 W/선택된 현재 의사결정 행</b>이며 공식 득점·회수 가능한 점수·PA 전체 누적 개선이 아니다.</p><p>실제 행동 비율은 적격 전체, Q·Δ·구간은 공통 지지 행이 분모다. 두 분모와 포함률을 표에 함께 표시한다. <b>점추정 방향</b>과 <b>차이 불명확/비교 자료 부족</b>은 별개다. ‘관찰상 방향 뚜렷’은 219개 차이에 대한 Bonferroni 보정 명목 구간이 0을 제외한다는 뜻이며 인과 권고 등급이 아니다. 실제 포함률·전체 학습 불확실성은 미검증이다.</p></section>'
out+=''.join(sections)
out+='<section id="regions"><h2>타자: 상·하·좌·우·가운데 5구역</h2><p>가운데는 존 안 전체다. 상·하는 존 위·아래, 좌·우는 타자 기준 몸쪽·바깥쪽이다. 좌타자는 좌우를 뒤집어 우타자와 같은 몸쪽/바깥쪽 기준으로 묶었다. <b>모서리는 두 구역 모두에 포함한다.</b> 학습·전체·카운트 집계에서는 같은 공을 한 번만 쓴다.</p><div class="grid"><div class="corner">상 + 좌<br>두 구역에 포함</div><div>상 · 높음</div><div class="corner">상 + 우<br>두 구역에 포함</div><div>좌 · 몸쪽</div><div class="center">가운데<br>존 안 전체</div><div>우 · 바깥쪽</div><div class="corner">하 + 좌<br>두 구역에 포함</div><div>하 · 낮음</div><div class="corner">하 + 우<br>두 구역에 포함</div></div><p>'+h(freqtext)+f'</p><p class="note">타자 적격 {int(total.unique_rows):,}행 중 두 구역 중복 포함 {int(total.overlap_rows):,}행, 위치 미분류 {int(total.unassigned):,}행. 5구역 membership 합계는 {int(total.membership_total):,}이며, 구역 비율을 더하면 100%를 넘을 수 있다.</p><p>스윙 쪽 가치가 낮으면 ‘스윙이 위험한 구역’, 테이크 쪽 가치가 낮으면 ‘테이크가 위험한 구역’이라는 점추정 의미다. 자주 오는 곳과 가치 차이가 큰 곳을 구분하며, 특정 선수의 약점이나 교정으로 확실히 회수할 점수로 해석하지 않는다. 카운트를 열면 FB/NFB별 차이도 볼 수 있다.</p>'+''.join(regioncards)+'</section>'
out+='<section id="method"><h2>무엇을 바꾸고 어디까지 확인했나?</h2><ul><li>FB=FF·SI·FC. NFB는 기존 닫힌 허용 목록이며 FA=Other가 포함된다. 미분류를 NFB로 채우지 않았다. 현재·직전 세부 구종 입력은 FB/NFB로 정리했다.</li><li>S는 공 중심이 |plate_x|≤17/24피트와 sz_bot≤plate_z≤sz_top을 동시에 만족한 공이다. 경계 등호는 S이고 공 반경은 더하지 않았다. 홈런이 된 존 안 공도 S, 존 밖 헛스윙 공도 B다. 판정상 strike/ball이나 투수 의도가 아니다.</li><li>새 S/B 모듈은 기존 투구 전 변수와 현재 FB/NFB만 추가 사용한다. 현재 좌표·존·스윙·구속·움직임은 보정 입력에 없다. FB/NFB 모델에는 현재 위치·S/B·스윙을 추가하지 않았다.</li><li>타자의 구속·움직임·좌표 세부 수치 구간은 기존과 같다. 기존 INNER/BOUNDARY/OUT × count × FB/NFB의 보정 범주도 유지한다. 사용자가 선택한 5개 중첩 구역은 보고 집단이며 행을 복제하거나 새 세부 위치 예측 입력을 만들지 않았다.</li><li>축소 Ridge 결과 T-learner와 Ridge+훈련 경기 Platt propensity를 재사용했다. 경기 3분할·seed20260909 한 번이며 같은 경기의 모든 PA/투구는 같은 fold다. 전처리·사전·보정은 해당 훈련 경기 안에서만 학습했다.</li><li>PITCH/SWING의 α는 기존 개발값 p100, 결과1000을 고정했다. 새 S/B는 각 훈련 안에서 기존100/1000 두 후보만 비교했다. 정책은 학습하지 않았으며 표의 방향은 평가집단 점추정이다.</li><li>공통 지지는 propensity .05~.95와 해당 훈련 선수의 양 행동30회, 타자는 유효 물리 측정도 요구한다. 표본500·행동별ESS200·100경기·포함률.5·최대경기비중.05가 그룹 기준이다. 세부상황의 교환가능성·positivity 보장이 아니다.</li><li>같은 경기의 반복 PA/투구를 묶은 고정 점수 구간을 썼다. 경기 간 선수/시리즈 의존성, 함수족 오지정, 학습 불확실성과 실제95% 포함률은 확인하지 않았다. |Δ| .01 W는 크기를 보는 기존 참고선이며 추천 기준이 아니다.</li><li>완료 PA·IBB·결과 결측·측정·지지 제외는 선택집단을 만든다. HBP·체크스윙·번트 포함 공격 시도와 판정상 Take의 한계를 유지한다. 타자의 공 특성은 사후 대리값으로 실시간 지각 관측이 아니다.</li><li>기존 카운트 예외6건 중 개발2행은 표시만 하고 그대로 유지했다. 대규모 원인 조사·임의 수정·제외를 하지 않았다.</li></ul>'+table(['모듈','적격 행','공통 지지 행','포함률','OOF 결과 MSE','OOF 행동 Brier','적합/보정 로그 수','기본 확인'],fit_info)+'<p>키·유효 count·행동·시즌 W·종료 결과 연결, 매핑·금지 입력, 경기 fold·상위 평가 배제, 수렴·유한값, 양 행동 동일 분모·차이 부호·표 합계와 중첩 구역 합계를 확인했다. 이 확인은 제작 과정의 기본 오류 확인이며 별도 독립 검수가 아니다.</p><p><b>미실시:</b> 2023·2026 데이터 적용/외부 평가, bootstrap·여러 seed 반복, 별도 독립 검산기, 원본 전체 반복 해시 감사, 알고리즘 광범위 탐색, JOINT·순차 PA·Nash, KBO·신규 원본 수집·Drive·외부 게시. 기존 안내 문서의 과거 결과는 V2 검증으로 전용하지 않는다.</p><p>V2는 개발 세대 이름이다. PITCH/SWING은 입력 변경으로 v0.2.0, 새 S/B는 BCAP-PITCH-SB-v0.1.0이다. 모두 EXPERIMENTAL이며 최종 전체 개발 재적합 모델·배포 정책은 만들지 않았다. 대신 실제 평가에 사용한 모든 fold 적합 객체·사전·calibrator·학습 분할 연결과 S/B 튜닝 객체를 보존했다.</p><p>좌표 기준 출처: <a href="https://baseballsavant.mlb.com/csv-docs">Savant CSV 공식 필드 설명</a>(필드 정의만 확인, 새 투구 자료 수집 없음). 원 W·행동·정제 자료는 기존 프로젝트 자산에서 재사용했다.</p></section>'
out+='<section><h2>결과 파일과 재현</h2>'+assets+f'<p>{link(B/"reproduction.md","실제 명령·재현 안내")} · {link(B/"design_revisions/final_choice_before_fitting.json","사용자 구역 변경과 결과 전 기준 기록")} · {link(B/"report_manifest.json","보고서 입력·출력 해시")}</p><p class="small">작성 {datetime.datetime.now().isoformat(timespec="seconds")} · 로컬 개발 보고서 · 후속 검증 미실시</p></section></main></html>'
report=B/'report.html'
if report.exists():
 assert '--refresh' in sys.argv,'Use --refresh only for this report wording/layout; no refitting.'
 previous=B/'report_before_wording_refinement.html'
 assert not previous.exists(),'Report revision snapshot already exists.'
 shutil.copy2(report,previous)
 shutil.copy2(B/'report_manifest.json',B/'report_manifest_before_wording_refinement.json')
report.write_text(out,encoding='utf-8')
summary=dict(status='PASS',scope='2024/2025 production basic checks only, not independent review',models={m:dict(run_id=RIDS[m],status=basic[m]['status'],checks=len(basic[m]['checks']),metrics=man[m]['metrics']) for m in MODELS},preparation=j(B/'preparation/preparation.json')['status'],family_planned=219,displayed_delta_groups=219,region_membership=dict(unique_rows=int(total.unique_rows),overlap_rows=int(total.overlap_rows),unassigned=int(total.unassigned),membership_total=int(total.membership_total)),not_run=['external evaluation','bootstrap','independent verifier','wide audit'])
js(B/'basic_summary.json',summary)
commands='\n\n'.join(f"```powershell\n& '{sys.executable}' -B '{Path(__file__).parent.as_posix()}/run.py' --model {m} --run-id {RIDS[m]}\n```" for m in MODELS)
(B/'reproduction.md').write_text(f'# V2 개발 재현\n\n아래는 실제 실행 명령 기록이다. 완료 실행을 보존하기 위해 다시 계산할 때에는 실제 날짜·미사용 run_id를 정하고 새 입력/보고 폴더를 사용한다. 기존 스크립트의 날짜별 준비·보고 폴더 r01은 경로를 명시적으로 새 폴더로 바꾼 후 사용한다. 원본 재수집·외부 평가·bootstrap 명령은 없다.\n\n{commands}\n\n공통 준비는 prepare.py, 결과 보고는 report.py, 문서 연결은 register_results.py다. SciPy는 기존 runtime_ridge_v02에서 읽으며 샌드박스 제한 시 정식 실행 승인을 사용했다. -B로 기존 bytecode를 변경하지 않는다.\n\n3개 fold nuisance.pkl(계수·훈련 사전·calibration 점수/행ID·훈련 경기·seed)과 S/B 튜닝 Ridge 객체가 실제 사용한 모델이다. 복원 시 이 버전의 engine 모듈을 import할 수 있어야 한다. 정책은 학습하지 않아 policy 파일은 없다.\n',encoding='utf-8')
inputs=[meta(AN/'runs'/RIDS[m]/'manifest.json') for m in MODELS]+[meta(AN/'runs'/RIDS[m]/'artifacts/action_values.csv') for m in MODELS]
js(B/'report_manifest.json',dict(created_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='V2 development report only',inputs=inputs,code=meta(Path(__file__)),outputs=[meta(p) for p in [report,B/'count_comparison_summary.csv',B/'batter_five_regions.csv',B/'batter_region_pitch_groups.csv',B/'basic_summary.json',B/'reproduction.md']],region_final_choice='Five overlapping sets; corners contribute to2region tables and1model row',external_evaluations=0,independent_review='NOT_RUN'))
js(B/'headline_results.json',dict(stories=stories,SB_answer=sbtext,regions=freqtext,region_action_pattern=regionaltext,pitch_group_pattern=pitchtext))
print(json.dumps(dict(report=str(report),headlines=stories,SB=sbtext),ensure_ascii=False))
