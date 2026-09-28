from pathlib import Path
import json,hashlib,shutil,csv
p=Path('columns/001-ball-count/publish/naver_20260918');b=p/'revisions/v12_before_results_v13';b.mkdir()
for n in ['01_ball_count.md','01_ball_count.html','build_preview.mjs']:shutil.copy2(p/n,b/n)
keep=[f'{n}.{e}' for n in ['02_bcai','03_bcap','04_references_ko','05_data_validation'] for e in ['md','html']]+['index.html']
(b/'untouched_files.json').write_text(json.dumps({n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in keep}),encoding='utf-8')
(p/'main_v13').mkdir()
s=(p/'01_ball_count.md').read_text(encoding='utf-8')
s=s.replace('   - [투수: 구종 선택]', '   - [타자: 스윙과 기다리기](#chapter-swing)\n   - [투수: 구종 선택]')
s=s.replace('<a id="chapter-bcap"></a>\n<a id="chapter-swing"></a>','<a id="chapter-bcap"></a>')
s=s.replace('**0-2와 1-2에서는 열한 시즌 모두 존 밖 공의 결과가 투수에게 더 좋은 쪽으로 추정됐다.** 아래 표는 같은 카운트 안에서 타자의 공격가치를 더 낮게 허용한 위치를 보여준다.','같은 카운트에서 실제 존 안 공과 존 밖 공의 보정된 최종 타석 결과를 비교했다. 표에는 타자의 공격가치를 더 낮게 허용한 쪽을 표시했다.')
r=list(csv.DictReader(Path('columns/001-ball-count/analysis/history_comparison_20260928_r01/tables/bcap_all_2552_screened.csv').open(encoding='utf-8-sig')))
counts=[f'{a}-{b}' for a in range(4) for b in range(3)]
audit=[]
def result(model,c,region=None):
 a=[x for x in r if x['model']==model and x['count']==c and ((x['level']=='region' and (x['region']=='CENTER' if region=='CENTER' else x['region']!='CENTER')) if region else x['level']=='count')]
 supported=[x for x in a if x['support_gate']=='TRUE'];positive=sum(float(x['family95_low'])>0 for x in supported);negative=sum(float(x['family95_high'])<0 for x in supported);unclear=len(supported)-positive-negative
 audit.append(dict(model=model,count=c,region=region or 'ALL',total=len(a),supported=len(supported),positive=positive,negative=negative,unclear=unclear))
 return len(a),len(supported),positive,negative,unclear
swing=['| 카운트 | 존 안의 스윙·테이크 비교 | 존 밖의 스윙·테이크 비교 |','| --- | --- | --- |']
for c in counts:
 n,sup,pos,neg,u=result('swing',c,'CENTER')
 inside='불명확' if u==sup else '스윙' if u==0 else '스윙 · 일부 해 불명확'
 n,sup,pos,neg,u=result('swing',c,'OUT')
 outside='자료 부족' if sup==0 else '테이크' + (' · 일부 불명확' if u else '') + (' / 일부 자료 부족' if sup<n else '')
 swing.append(f'| {c} | **{inside}** | **{outside}** |')
block='''<a id="chapter-swing"></a>

### 2-2. 타자는 어떤 공에 휘두르고 어떤 공을 지켜봤을 때 결과가 좋았을까?

같은 카운트·위치 구역에서 스윙과 테이크(휘두르지 않고 지켜보기)를 비교했다. 표에는 불확실성까지 고려해 어느 행동의 최종 공격가치가 더 높았는지를 표시했다. 존 밖은 높은 쪽·낮은 쪽·몸쪽·바깥쪽을 따로 비교했다.

'''+ '\n'.join(swing)+'''

*표 3. MLB 2015–2025의 연도별 스윙 분석 결과. ‘스윙’·‘테이크’만 적힌 칸은 비교한 모든 연도·구역에서 해당 행동 쪽으로 차이가 분명했다. ‘불명확’은 어느 쪽이 높은지 분명히 가리지 못한 경우, ‘자료 부족’은 비교 기준을 통과하지 못한 경우다. 둘은 같은 뜻이 아니다. [원천 결과](../../analysis/history_comparison_20260928_r01/tables/bcap_all_2552_screened.csv) · [세부 수치와 비교 방법](03_bcap.md#main-numeric-examples).*

<p class="question-group">스윙 결과 해석 · 카운트별 정답을 정할 수 있는가</p>

#### 이 표에서 ‘휘둘러야 할 카운트’와 ‘기다려야 할 카운트’를 나눌 수 있을까?

**카운트만으로 나눌 수는 없다.** 같은 카운트라도 공의 위치를 나누면 결과가 달라졌다. 예를 들어 0-2에서 스윙한 타석의 결과가 좋았다는 말에는 ‘존 안 공’이라는 조건이 붙는다. 이를 ‘0-2니까 휘두르는 편이 좋다’로 줄이면 분석에서 비교한 조건을 잃는다.

구종 비교에서도 마찬가지다. 특정 구종 묶음에서 차이가 나왔다고 해서 모든 투수에게 같은 구종을 권할 수는 없다. **스윙 분석도 카운트에 행동을 하나씩 배정하는 정답표를 만들지는 못했다.** 타자에게는 어떤 공을 칠 수 있는지 알아보고 골라내는 선구안과, 그 공을 실제로 쳐낼 능력을 함께 봐야 한다.

이것은 ‘스윙과 테이크의 결과 차이가 전혀 없었다’는 뜻은 아니다. 위 표의 관측된 차이는 그대로다. 다만 그 차이를 근거로 타자와 공의 조건을 지운 채 카운트별 행동을 정할 수 없다는 뜻이다.

> **해석 메모 | 두 가지 ‘구분’을 나누어 읽기**
>
> 분석에서 두 집단의 평균 차이를 구별하는 것과, 개별 타자에게 유리한 행동을 결정하는 것은 다르다. ‘카운트만으로 정답을 구분할 수 없다’는 결론을 ‘모든 평균 차이가 불명확하다’는 통계 결과로 바꾸지 않는다. 선수 능력과 카운트의 상대적 중요도를 직접 비교한 분석도 아니다.

'''
a=s.index('위치 비교에서 얻은 단서를 구종에도');b=s.index('<a id="chapter-pitch">',a)
s=s[:a]+block+s[b:]
s=s.replace('### 2-2. 카운트만으로 유리한 구종을 정할 수 있을까?','### 2-3. 카운트만으로 유리한 구종을 정할 수 있을까?')
a=s.index('**카운트만 보고 모든 투수에게 적용할 정답 구종을 정할 수는 없었다.**');b=s.index('패스트볼은 빠른 공 계열',a)
s=s[:a]+'같은 카운트에서 패스트볼 계열과 나머지 구종, 포심과 비포심을 각각 비교했다. 아래 표는 연도별로 어느 쪽의 허용 공격가치가 더 낮았는지를 보여준다.\n\n'+s[b:]
table=['| 카운트 | 패스트볼 계열 대 나머지 | 포심 대 비포심 |','| --- | --- | --- |']
for c in counts:
 cells=[]
 for m,label in [('pitch','나머지'),('pitch_ff','비포심')]:
  n,sup,pos,neg,u=result(m,c)
  assert neg==0
  cells.append(' · '.join(([f'{label} {pos}년'] if pos else [])+([f'불명확 {u}년'] if u else [])+([f'자료 부족 {n-sup}년'] if sup<n else [])))
 table.append(f'| {c} | {cells[0]} | {cells[1]} |')
a=s.index('| 카운트와 구종 분류 |');b=s.index('> **해석 메모 | 구종 비교의 범위**',a)
s=s[:a]+'\n'.join(table)+'''

*표 4. MLB 2015–2025의 두 구종 모형 결과. 각 칸은 11개 시즌 중 해당 결과가 나온 연도 수다. ‘나머지’·‘비포심’은 불확실성 구간까지 허용 공격가치가 낮았던 경우이며, 차이가 분명하지 않은 해는 따로 표시했다. ‘불명확’은 두 구종의 효과가 같다는 증명이 아니다. [원천 결과](../../analysis/history_comparison_20260928_r01/tables/bcap_all_2552_screened.csv).*

#### 결과표로 구종을 고를 수 있을까?

**카운트만 보고 모든 투수에게 적용할 정답 구종을 고를 수는 없다.** 표에는 차이가 불명확한 해가 많았고, 3-0 패스트볼 계열 비교처럼 반복된 차이도 있었다. 그러나 구종 묶음의 평균이 개별 투수의 구종 능력까지 대신하지는 않는다.

'''+s[b:]
old='가령 타자가 자신 있는 공만 골라 휘둘렀다고 해 보자. 그때의 타격 성적이 좋더라도, 더 어려운 공까지 스윙 범위를 넓히면 같은 성적을 유지한다는 보장은 없다. <u class="source-claim">Weinberg 역시 스윙한 공이 선택된 표본이라는 점 때문에, 그 성적을 지켜본 공에 그대로 적용하기 어렵다고 짚었다.</u>'
new='''앞서 스윙 빈도를 비교한 Weinberg는 여기서 한 걸음 더 들어갔다. 2014년 3-0 자료로 ‘모든 공을 지켜보는 경우’와 실제 행동을 비교했지만, 그 평균만으로 언제나 기다리라는 결론을 내리지는 않았다.

그 이유는 **스윙할 기회가 모든 타자와 상황에 똑같이 주어지지 않았기 때문**이다. <u class="source-claim">3-0 스윙 기록에는 감독이 스윙을 허용하고, 타자도 그 공에 휘두르기로 한 경우만 남는다. 연구자는 누가 언제 허락을 받았는지 알 수 없어, 모든 타자가 자유롭게 결정했다면 어떤 결과가 났을지 확인할 수 없다고 설명했다.</u>

예를 들어 타자가 자신 있는 공만 골라 휘둘렀다면 그 성적에는 공을 고른 결과가 이미 들어 있다. 이 성적을 원래 지켜본 어려운 공에도 붙여 ‘더 많이 쳐도 잘할 것’이라고 계산할 수는 없다. 반대로 전체 평균에서 기다리기가 좋았다는 이유로, 그 타자가 잘 칠 수 있는 공까지 전부 보내라고 할 수도 없다. **카운트별 스윙 비율만으로 적정 행동을 정하기 어려운 이유가 여기에 있다.**'''
assert old in s;s=s.replace(old,new)
(p/'01_ball_count.md').write_text(s,encoding='utf-8')
(p/'main_v13/result_table_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
