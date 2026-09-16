"""Korean report from frozen FF/FB comparison tables; no statistical refits."""
from pathlib import Path
import argparse,datetime,hashlib,html,json,os,sys,math
import pandas as pd
ROOT=Path(__file__).resolve().parents[4];CODE=Path(__file__).parent;AN=ROOT/'columns/001-ball-count/analysis'
COUNTS=[f'{b}-{s}' for b in range(4) for s in range(3)]
def j(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def clean(o):
 if isinstance(o,dict):return {k:clean(v) for k,v in o.items()}
 if isinstance(o,list):return [clean(v) for v in o]
 if isinstance(o,float) and not math.isfinite(o):return None
 return o
def js(p,o):p.write_text(json.dumps(clean(o),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def h(s):return html.escape(str(s))
def n(v):return f'{int(v):,}'
def pct(v):return f'{v:.1%}'
def signed(v):return f'{v:+.4f}'
def ci(r):return f'[{r.adjusted95_low:+.4f}, {r.adjusted95_high:+.4f}]'
def mdtable(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(v).replace('|','/').replace('\n','; ') for v in row)+' |' for row in rows])
def table(headers,rows):return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+h(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+h(x).replace('\n','<br>')+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table></div>'
def interpretation(r):
 if not r.support_gate:return '비교 자료 부족'
 if r.category=='SMALL_RANGE':return '±0.01W 안 작은 범위'
 if r.category=='UNSTABLE':return '분할·방법 불안정'
 if r.category=='CONSISTENT_DEVELOPMENT':return r.point_direction+' 방향 · 개발 내 일관'
 if r.adjusted95_low>0 or r.adjusted95_high<0:return r.point_direction+' 방향 · 세부 근거 제한'
 return '차이 크기·방향 미확정'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bundle',required=True);a=ap.parse_args();b=ROOT/a.bundle;plan=j(b/'analysis_plan.json');run=AN/'runs'/plan['comparison_run'];art=run/'artifacts';m=j(run/'manifest.json');assert m['status']=='COMPLETE'
 ffman=j(AN/'runs'/plan['new_run']/'manifest.json');summary=j(art/'summary.json');pr=pd.read_csv(art/'primary_values.csv');au=pd.read_csv(art/'year_fold_values.csv');comp=pd.read_csv(art/'pitch_composition.csv');exc=pd.read_csv(art/'support_exclusions.csv')
 assert not (b/'report.html').exists()
 def row(s,p,c):return pr[pr.scheme.eq(s)&pr.population.eq(p)&pr['count'].eq(c)].iloc[0]
 def link(p,label):return '['+label+']('+Path(os.path.relpath(p,b)).as_posix()+')'
 def alink(p,label):return '<a href="'+h(Path(os.path.relpath(p,b)).as_posix())+'">'+h(label)+'</a>'
 md=['# 포심만 따로 떼면 카운트별 차이가 더 잘 보일까?'];body=[]
 def section(title,paras,headers=None,rows=None,anchor=None):
  md.extend(['\n## '+title]+['\n'+p for p in paras]);s='<section'+(' id="'+anchor+'"' if anchor else '')+'><h2>'+h(title)+'</h2>'+''.join('<p>'+h(p)+'</p>' for p in paras)
  if headers:md.append('\n'+mdtable(headers,rows));s+=table(headers,rows)
  body.append(s+'</section>')
 def val(s,p,c):r=row(s,p,c);return signed(r.delta)+' '+ci(r)
 ff32=row('FF','common','3-2');fb30=row('FB','common','3-0');ff30=row('FF','common','3-0')
 headlines=[
  '2024·2025 개발 결과 · EXPERIMENTAL · 외부 검증 미실시. 기존 FB/NFB는 저장 OOF 점수를 재사용했고 포심/비포심만 3fold로 한 번 학습했다.',
  f"3-2에서 포심−비포심은 공통 표본 기준 {val('FF','common','3-2')} W다. 비포심의 허용 공격가치가 낮은 방향이 두 연도와 세 분할의 점추정에서 유지됐다. 구간 하한이0.01보다 작으므로 차이가 적어도0.01 W라고 보장하지는 않는다.",
  f"3-0의 기존 FB−NFB는 공통 표본에서도 {val('FB','common','3-0')} W로 남는다. 포심−비포심은 {val('FF','common','3-0')} W이며 분할에 따라 방향이 바뀐다. 행동 분류를 바꾸면 다른 질문이 되며 기존 결과의 오류를 뜻하지 않는다.",
  '0-0은 두 분류 모두 자체·공통 표본의 보정 구간 전체가±0.01 W 안에 들어온다. 이번 고정 점수 계산과 설정한 실질 기준 안에서 작은 차이라고 볼 근거가 있다. 다른 카운트의 불명확을 모두 같은 뜻으로 해석하지 않는다.',
  '대부분의 카운트는 우열을 충분히 구분하지 못했다. 3-2의 제한된 개발 단서를 남기고 이번 비교를 종료한다. 자동으로 구종 분류를 더 바꾸거나 복잡한 모형·외부 검증을 추가하지 않는다.'
 ]
 section('이번 비교에서 얻은 답',headlines,anchor='answer')
 section('어떻게 읽어야 하나',[
  'Δ는 앞 행동의 보정 공격가치에서 뒤 행동의 값을 뺀 것이다. FB−NFB가 음수면 FB, 양수면 NFB가 투수에게 낮은 허용 공격가치와 연결된다. FF−non-FF가 음수면 포심, 양수면 비포심 방향이다. W는 시즌 가중 최종 PA 공격가치이며 실제 득점·PA 전체 정책 개선량이 아니다.',
  '각 비교에서 결과모형 평균과 최종 AIPW 평균은 같은 실제 선수·상황 행에 양 행동을 적용한 값이다. 단순 평균은 그 표본 안의 실제 행동별 Y 평균이므로 두 행동의 실제 상황 구성은 다를 수 있다. 단순 평균과 보정 추정치의 차이를 오류로 단정하지 않는다.',
  '자체 표본은 각 분류의 지원 기준을 통과한 행이다. 공통 표본은 두 기준을 모두 통과한 동일한 행이다. 포함률의 분모는 해당 카운트 전체 적격 행이며, 공통 표본으로 잘라 포함률을100%로 만들지 않았다. 공통 표본도 두 분류의 행동 내용까지 동일하게 만들지는 않는다.',
  '주요 구간은 고정 점수 경기 변동에 대한 Bonferroni255 명목95%다. 기존219개에 새로운36개 차이를 더했다. 기존 FB 자체219 구간은 CSV에 따로 보존했고 이번 표는 양쪽 모두255를 적용한다. 연도·fold 구간은 개별 명목95% 참고용이며 추가 유의성 판정이나 독립 검증이 아니다.'
 ])
 supportrows=[]
 for label,key in [('FB/NFB 자체','FB_own'),('FF/non-FF 자체','FF_own'),('두 분류 공통','common')]:supportrows.append([label,n(summary[key]),pct(summary[key]/summary['rows_eligible'])])
 section('분류를 바꾸면서 표본도 달라졌다',[
  f"전체 적격은 {n(summary['rows_eligible'])}행·4,859경기다. FB만 지원되는 행 {n(summary['FB_only'])}, FF만 지원되는 행 {n(summary['FF_only'])}, 어느 쪽도 지원되지 않는 행 {n(summary['neither'])}다. 지지 집단은 학습한 선택 확률과 훈련 투수별 행동 수로 정해진 분석 집단이다.",
  '포심 비교에서 지원이 줄어든 주요 이유는 투수의 훈련 표본에서 FF와 non-FF가 각각30회 이상 있어야 한다는 조건이다. 싱커·커터도 FB였던 기준과 달라졌다. 이 기준은 관측 구종 사용 여부이며 선수의 실제 능력이나 의도를 평가한 값은 아니다.',
  '새 적격 코드: FF / non-FF=SI, FC, SL, CH, ST, CU, FS, KC, SV, FA, EP, KN, FO, CS, SC. FA는 기존 Other 한계를 유지한다. PO, UN, 결측과 기존 PA 제외는 non-FF로 편입하지 않았다. 포심 대 비포심이며 패스트볼 대 변화구라는 명칭을 쓰지 않는다.'
 ],['표본','행 수','전체 적격 대비'],supportrows,anchor='samples')
 er=[]
 for scheme in ['FB','FF']:
  d=exc[exc.scheme.eq(scheme)].groupby('reason').n.sum();er.append([scheme,n(d.get('training_action_support',0)),n(d.get('propensity_tail',0)),n(d.get('supported',0))])
 section('지원 제외의 구성',[
  '제외 사유는 훈련 투수 행동 수 부족을 먼저, 남은 행의 propensity .05~.95 이탈을 다음으로 센 상호 배타적 집계다. 두 사유가 동시에 해당하는 행은 첫 사유로 들어간다.'
 ],['분류','훈련 행동 수 부족','확률 범위 이탈','지원 행'],er)
 for pop,title in [('own','자체 비교 가능 표본: 12카운트'),('common','동일한 공통 표본: 12카운트')]:
  rows=[]
  for count in COUNTS:
   x=row('FB',pop,count);y=row('FF',pop,count)
   rows.append([count,signed(x.delta)+'\n'+ci(x),x.point_direction+'\n'+interpretation(x),n(x.n)+'\n'+pct(x.coverage),signed(y.delta)+'\n'+ci(y),y.point_direction+'\n'+interpretation(y),n(y.n)+'\n'+pct(y.coverage)])
  section(title,['값은 AIPW Δ W와 Bonferroni255 명목95% 구간이다. 점추정 유리 방향은 구간·근거 판정과 함께 읽는다. 분류 간 Δ 차이를 구종의 상호작용 검정이나 효과 차이의 유의성으로 해석하지 않는다.'],['카운트','FB−NFB / 구간','FB 비교 방향·근거','FB 행 / 포함률','FF−non-FF / 구간','FF 비교 방향·근거','FF 행 / 포함률'],rows,anchor=pop)
 section('3-0: 기존 차이는 남지만 포심 단독 차이로 이어지지 않는다',[
  '기존 FB/NFB 자체 표본의 NFB는738행, ESS624.65,640경기에 분산돼 있다. 최대 한 경기의 NFB 가중치 비중은0.630%로 기존 기준5% 아래다. 적은 비율이라는 사실만으로 전체 지원 기준을 실패한 것은 아니다.',
  '다만 자체 표본의 fold0은 NFB ESS193.76이고, 공통 표본의 fold0·fold2는 각각176.04·187.27로200 기준에 못 미친다. 두 연도와 세fold의 FB−NFB 점추정 부호는 모두 양수다. 이번 ‘개발 내 일관성’ 등급을 보류한 이유는 부호 반전이 아니라 일부 분할 지원 부족이다. 통합 구간의 방향은 여전히 남는다.',
  f"공통 표본에서 기존 비교는 단순 평균 {signed(row('FB','common','3-0').naive_delta)}, 결과모형 평균 {signed(row('FB','common','3-0').gcomp_delta)}, AIPW {signed(fb30.delta)} W다. 단순 평균과 보정 비교의 방향이 다르므로 보정 모형·표본 선택에 대한 의존성을 숨기지 않는다.",
  '같은3-0 공통 표본11,809행에서 기존 NFB는670행이다. 새 non-FF는 여기에 SI2,339행·FC447행을 더한3,456행이다. FF8,353행과 비교한다. 이런 행동 내용의 변경 때문에 두 비교는 다른 결과를 줄 수 있다. SI/FC가 원인이라고 분해해 입증한 것은 아니다.',
  'FF의 공통 표본3-0은 fold0 −0.02366, fold1 +0.00032, fold2 +0.02223 W다. 서로 반대인 양 끝 분할이±0.01 W를 넘어 사전 기준상 불안정으로 표시했다. 분할별 명목 구간은 모두0을 포함한다. 전체 점추정이0 근처라고 작은 차이가 입증된 것은 아니다.'
 ],anchor='count30')
 section('3-1: 결과모형과 최종 보정의 방향이 달랐다',[
  f"기존 FB/NFB 자체 표본에서 단순 평균 Δ={signed(row('FB','own','3-1').naive_delta)}, 결과모형 Δ={signed(row('FB','own','3-1').gcomp_delta)}, AIPW Δ={signed(row('FB','own','3-1').delta)} W다. 결과모형은 NFB 쪽, 최종 보정은 FB 쪽 점추정이다. NFB 결과모형의 잔차 보정이 더 크게 양의 방향으로 반영됐다.",
  '기존3-1의 개별 명목95% 구간은 아주 근소하게0을 제외하지만,219 및255 보정 구간은0을 포함한다. 작은 차이의 확인이 아니라 방법별 부호 민감성과 다중비교 후 보류가 섞인 경우다. 결과모형 점추정은0.01 W보다 작아 사전에 정한 ‘양쪽 모두 실질 크기 이상의 반전’ 등급에는 해당하지 않지만 부호 변화 자체는 표에 표시한다.',
  f"새 FF/non-FF의 공통 표본3-1은 {val('FF','common','3-1')} W다. 분류 변경 뒤에도 구간이0을 포함하므로 이 카운트의 선택을 확정하지 않는다."
 ],anchor='count31')
 section('3-2: 비포심 방향의 제한된 개발 근거',[
  f"FF/non-FF의 자체 표본은 {val('FF','own','3-2')} W, 공통 표본은 {val('FF','common','3-2')} W다. 공통 표본의 단순 평균·결과모형·AIPW Δ는 각각 {signed(ff32.naive_delta)}, {signed(ff32.gcomp_delta)}, {signed(ff32.delta)} W로 모두 비포심 방향이다.",
  '공통 표본에서2024는+0.02005,2025는+0.01403 W이고, fold0/1/2는+0.01666/+0.00800/+0.02627 W다. 모든 점추정의 부호가 같고 지원 기준도 통과한다. fold1의 개별 명목 구간은0을 포함하므로 ‘모든 분할에서 유의하다’는 뜻은 아니다.',
  '통합 보정 구간의 하한은 약0.0014 W로 실질 기준0.01보다 작다. 방향의 개발 단서는 있으나 최소0.01 W 이상의 이득, 다른 시즌 재현성 또는 행동 지시의 인과 효과는 확보하지 못했다.'
 ],anchor='count32')
 section('작은 차이와 아직 모르는 차이를 구분했다',[
  f"0-0 공통 표본: FB/NFB {val('FB','common','0-0')} W, FF/non-FF {val('FF','common','0-0')} W. 두 구간 모두±0.01 W 안이다. 이 계산 조건에서 설정한 범위 안의 작은 차이라는 해석을 허용했다.",
  '반면 점추정이0에 가까워도 구간이±0.01 밖까지 넓거나, 방법·연도·분할의 실질적인 반전이 있으면 작은 차이라고 부르지 않았다. 방향이 있어도 다중비교 후 구간이0을 포함하는 경우는 별도 이유를 표시한다.',
  '판정 우선순위는 지원 부족 → 실질 반전 → 구간 전체가±0.01 안 → 통합 구간0 배제·점추정0.01 이상·연도2/fold3 지원 및 같은 방향 → 나머지 불확실이다. 사후에 유의성을 얻도록 기준을 조정하지 않았다. 근소한 부호 차이는 별도 표시하며 실질 반전 기준과 구분한다.'
 ])
 # Overall composition is a count-only diagnostic, not an additional effect contrast.
 cr=[]
 for (scheme,pop,ar),g in comp.groupby(['scheme','population','action']):
  denom=int(g.n.sum());parts=g.groupby('component').n.sum()
  cr.append([scheme+' '+('자체' if pop=='own' else '공통'),('FB' if scheme=='FB' else 'FF') if ar else ('NFB' if scheme=='FB' else 'non-FF'),n(denom)]+[pct(parts.get(x,0)/denom) for x in ['FF','SI','FC','legacy_NFB']])
 section('각 행동 안에 들어 있는 구종 구성',[
  '비율의 분모는 해당 분류·표본의 실제 행동 행 수다. 12카운트를 합친 구종 구성 진단이며 추가 전체 효과 검정이 아니다. 카운트별 전체 코드 빈도는 pitch_composition.csv에 있다.'
 ],['분류·표본','행동','행 수','FF','SI','FC','기존 NFB'],cr)
 details=[]
 for count in COUNTS:
  mr=[];sr=[];yr=[];notes=[]
  for pop in ['own','common']:
   for scheme in ['FB','FF']:
    r=row(scheme,pop,count);label=scheme+' '+('자체' if pop=='own' else '공통')
    mr.append([label,r.action0+' / '+r.action1,f'{r.naive0:.4f} / {r.naive1:.4f}',f'{r.gcomp0:.4f} / {r.gcomp1:.4f}',f'{r.Q0:.4f} / {r.Q1:.4f}',signed(r.naive_delta),signed(r.gcomp_delta),signed(r.delta),signed(r.correction_delta)])
    sr.append([label,n(r.n_all),n(r.rows0)+' / '+n(r.rows1),f'{r.ESS0:,.1f} / {r.ESS1:,.1f}',n(r.games0)+' / '+n(r.games1),pct(r.coverage),pct(r.max_game_share0)+' / '+pct(r.max_game_share1),f'{r.max_weight0:.2f} / {r.max_weight1:.2f}'])
    sub=au[au.scheme.eq(scheme)&au.population.eq(pop)&au['count'].eq(count)];ys=[label]
    for lev,valx in [('year',2024),('year',2025),('fold',0),('fold',1),('fold',2)]:
     z=sub[sub.level.eq(lev)&sub.value.eq(valx)].iloc[0]
     ys.append(signed(z.delta)+f'\n[{z.nominal95_low:+.4f}, {z.nominal95_high:+.4f}]'+('' if z.support_gate else '\n지원 미달: '+str(z.support_reasons)))
    yr.append(ys);notes.append(label+': '+interpretation(r)+' — '+str(r.reason))
  text='<details><summary>'+count+' 카운트: 분모·방법·연도·분할</summary>'+''.join('<p>'+h(t)+'</p>' for t in notes)
  text+=table(['분류·표본','행동0 / 행동1','단순 Q0 / Q1','모형 Q0 / Q1','AIPW Q0 / Q1','단순Δ','모형Δ','AIPWΔ','잔차보정Δ'],mr)
  text+=table(['분류·표본','적격 행','행동0 / 1 수','ESS0 / 1','경기0 / 1','포함률','최대경기 비중0 / 1','최대IPW0 / 1'],sr)
  text+=table(['분류·표본','2024','2025','fold0','fold1','fold2'],yr)+'</details>';details.append(text)
  md.extend(['\n### '+count+' 카운트 상세']+['\n'+t for t in notes]+['\n'+mdtable(['분류·표본','단순Δ','결과모형Δ','AIPWΔ'],[[r[0],r[5],r[6],r[7]] for r in mr])])
 body.append('<section id="details"><h2>12카운트의 근거 상세</h2><p>모든 Δ는 행동1−행동0 W다. 아래 연도·fold 구간은 개별 명목95%이며 독립 검증이나 다중비교 판정용이 아니다. 경기는 각fold 안에서 반복 투구를 묶지만, 학습자료가 겹치는fold 결과들을 독립 반복 실험으로 취급하지 않는다.</p>'+''.join(details)+'</section>')
 section('무엇을 확인했고 어디서 멈추나',[
  '기존 FB/NFB는 단순 재현을 위해 재학습하지 않았다. 새 FF 모델은 기존14개 투구 전 특징, 투수·타자 축소 효과, alpha p100/결과1000, 같은 경기3fold와 훈련 안 Platt를 사용했다. 현재 구종·위치·스윙·구속·타구 결과는 예측 입력에 없다. 직전 구종 입력은 기존 FB/NFB를 유지했다.',
  '새 FF 적합·보정12개 로그는 모두 수렴했다. 키·행동·시즌 W·경기 분리·사전과 보정의 훈련 범위·유한값·AIPW 행별 산술·같은 분모·표본 합계·기존 저장 결과 일치를 기본 확인했다. 별도 전면 독립 검수는 아니다. 두 모델의 행동 비율이 다르므로 Brier 수치만으로 새 모델 성능이 좋아졌다고 비교하지 않는다.',
  '완료 PA·IBB·최종결과 결측·지원 제외는 선택된 분석 집단을 만든다. 선수 보정으로 의도·구종 품질·컨디션·기타 미측정 교란이 제거되지 않는다. 고정 점수 구간은 전체 nuisance 재학습 불확실성과 경기 간 선수 의존성을 포함하지 않으며 실제95% 포함률은 미검증이다. 기존 개발 카운트 예외2행은 표시한 채 유지했다.',
  '정책은 학습하지 않았고 2023/2026 외부 평가·다른 연도 확보·KBO·bootstrap·추가seed·타자/SB 재학습·광범위 탐색은 하지 않았다. 0-0의 작은 범위,3-0의 분류 차이와 지원 한계,3-1의 방법 민감성,3-2의 제한된 비포심 방향을 결과로 남기고 이번 범위에서 종료한다.'
 ],anchor='limits')
 sources=[(art/'comparison_12counts.csv','두 분류12카운트 비교 CSV'),(art/'primary_values.csv','48개 주요 결과·판정 이유'),(art/'year_fold_values.csv','연도·분할240개 내부 탐색'),(art/'pitch_composition.csv','구종 구성'),(art/'propensity_by_count_action.csv','선택 확률 분포'),(art/'calibration.csv','확률 보정 진단'),(art/'support_exclusions.csv','지원 제외'),(art/'basic_checks.json','저장 점수 기본 확인'),(run/'manifest.json','재집계 manifest'),(AN/'runs'/plan['new_run']/'manifest.json','새 FF 학습 manifest'),(b/'analysis_plan.md','추가 결과 전 기준'),(b/'plan_seal.json','기준 고정 시각·해시'),(b/'result_access_log.json','결과 열람 기록')]
 md.append('\n## 파일과 재현\n\n'+' · '.join(link(p,l) for p,l in sources))
 body.append('<section><h2>파일과 재현</h2><ul>'+''.join('<li>'+alink(p,l)+'</li>' for p,l in sources)+'</ul><p>'+alink(b/'reproduction.md','실제 재현 명령')+' · '+alink(b/'report_manifest.json','보고서 해시·입력 연결')+'</p></section>')
 reproduction=f'''# 실제 실행·재현 기록

프로젝트 루트: {ROOT.as_posix()}

아래는 이번에 실제 실행한 명령이다. 완료된 실행·정제본·보고서는 보호하므로 같은ID로 재실행하면 중단한다. 새 재현은 같은 고정 명세를 사용하고 새 bundle의 analysis_plan.json에 미사용 new_run/comparison_run을 지정해야 한다. --bundle과 --run-id에 그 값을 전달한다. 기존 FB scores는 재사용하며 재학습하지 않는다.

```powershell
& '{sys.executable}' -B models/bcap/setup_pitch_ff.py
& '{sys.executable}' -B models/bcap/pitch_ff/v0.1.0/prepare.py --bundle {a.bundle}
& '{sys.executable}' -B models/bcap/pitch_ff/v0.1.0/run.py --bundle {a.bundle} --run-id {plan['new_run']}
& '{sys.executable}' -B models/bcap/pitch_ff/v0.1.0/compare.py --bundle {a.bundle}
& '{sys.executable}' -B models/bcap/pitch_ff/v0.1.0/report.py --bundle {a.bundle}
```

setup_pitch_ff.py는 이번 최초 명세·bundle 생성 기록이며 기존 정의가 있으면 보호를 위해 중단한다. 새 검수에서는 이미 고정된 명세·입력을 참조한다. engine.py는 기존 V2 수치 코어의 동일 바이트 사본이며 기존 runtime_ridge_v02 SciPy를 사용한다. run/compare는 해당 기존 분석 환경을 읽기 위한 정식 실행 승인을 사용했다.

원입력: {plan['source']}
새 입력·SHA256: preparation.json
기존 점수: columns/001-ball-count/analysis/runs/{plan['old_run']}/artifacts/scores.pkl
새 점수: columns/001-ball-count/analysis/runs/{plan['new_run']}/artifacts/scores.pkl
공통 membership 및 주요표: columns/001-ball-count/analysis/runs/{plan['comparison_run']}/artifacts/

FF의 실제 nuisance 객체3개는 새 학습 실행의 artifacts/fits/fold0..2/nuisance.pkl에 있다. 사전·계수·중심화·Platt 자료/행ID·훈련 경기·seed를 포함한다. 복원 시 이 버전의 engine 모듈을 import할 수 있어야 한다. 기존FB 적합 객체와 점수는 원래 위치를 유지한다. 전체개발 최종 재적합·학습 정책·외부 평가 파일은 없다.
'''
 (b/'reproduction.md').write_text(reproduction,encoding='utf-8')
 style='body{font:16px/1.7 "Malgun Gothic",Arial,sans-serif;color:#203241;background:#eef3f6;margin:0}main{max-width:1450px;margin:auto;padding:30px 25px 65px}header,section{padding:26px;background:white;border-radius:10px;margin-bottom:22px}h1{font-size:31px;line-height:1.4}h2{font-size:22px;color:#15475a}p{max-width:1170px}a{color:#176b88}nav a{display:inline-block;margin:4px 18px 4px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.5;margin:18px 0}th{background:#e9f2f6;white-space:nowrap}th,td{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid #dce6eb}tbody tr:nth-child(even){background:#f9fbfc}details{border:1px solid #dce6eb;padding:16px;border-radius:8px;margin:14px 0}summary{cursor:pointer;font-weight:bold;font-size:18px}small{color:#65727c}@media print{body{background:white}main,section{padding:5px}nav{display:none}}'
 header='<header><small>BASELINE · BCAP V2 · FF EXTENSION</small><h1>포심만 따로 떼면 카운트별 차이가 더 잘 보일까?</h1><p>2024·2025 개발 결과 · EXPERIMENTAL · 외부 검증 미실시</p><nav>'+''.join('<a href="#'+id+'">'+label+'</a>' for id,label in [('answer','핵심 결과'),('own','자체 표본'),('common','공통 표본'),('count30','3-0'),('count31','3-1'),('count32','3-2'),('details','카운트별 근거'),('limits','한계·종료')])+'</nav></header>'
 out='<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BCAP V2 · FB/NFB와 포심/비포심</title><style>'+style+'</style></head><body><main>'+header+''.join(body)+'</main></body></html>'
 (b/'report.html').write_text(out,encoding='utf-8');(b/'report.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
 js(b/'headlines.json',{'headlines':headlines,'new_FF_3_2_common':ff32.to_dict(),'legacy_FB_3_0_common':fb30.to_dict(),'new_FF_3_0_common':ff30.to_dict(),'stopping':'Requested comparison complete; no automatic follow-on exploration.'})
 js(b/'report_manifest.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'COMPLETE','scope':'Korean development report from saved comparison tables','inputs':[meta(art/f) for f in ['primary_values.csv','year_fold_values.csv','pitch_composition.csv','support_exclusions.csv','summary.json']]+[meta(run/'manifest.json')],'code':meta(Path(__file__)),'outputs':[meta(b/f) for f in ['report.html','report.md','reproduction.md','headlines.json']]})
 print(json.dumps({'status':'COMPLETE','report':str(b/'report.html')},ensure_ascii=True))
if __name__=='__main__':main()
