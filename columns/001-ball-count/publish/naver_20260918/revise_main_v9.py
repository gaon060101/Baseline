from pathlib import Path
import re,csv
p=Path('columns/001-ball-count/publish/naver_20260918')
s=(p/'revisions/v8_before_structure_v9/01_ball_count.md').read_text(encoding='utf-8-sig')
def between(a,b): return s.split(a,1)[1].split(b,1)[0].strip()
def qblock(text,num):
 return re.search(r'#### '+num+r'[^\n]*\n[\s\S]*?(?=\n#### |\Z)',text).group(0).strip()
bcai=between('### 상세 설명','카운트별 결과는 확인했다.')
loc=between('## 2. 공이 들어온 위치','<a id="chapter-swing">')
swing=between('## 3. 스윙과 기다리기','<a id="chapter-three">')
three=between('## 4. 스윙 빈도','<a id="chapter-pitch">')
pitch=between('## 5. 구종','<a id="chapter-game">')
end=s.split('<a id="chapter-game"></a>',1)[1].split('## 본문에 사용한 문헌은 어떤 역할을 했을까?',1)[0].strip()
rows={r['count']:r for r in csv.DictReader((p/'main_v8/bcai_12counts.csv').open(encoding='utf-8-sig'))}
def matrix(kind):
 title='카운트별 BCAI · 타석 시작 평균 = 100' if kind=='bcai' else '투수의 위치별 결과 · 허용 공격가치가 낮은 쪽'
 out=[f'<div class="count-board {kind}-board"><div class="board-title">{title}</div>', '<table class="count-matrix"><thead><tr><th scope="col">볼</th>'+''.join(f'<th scope="col">{k}스트라이크</th>' for k in range(3))+'</tr></thead><tbody>']
 for b in range(4):
  out.append(f'<tr><th scope="row">{b}볼</th>')
  for st in range(3):
   c=f'{b}-{st}'
   if kind=='bcai':
    r=rows[c];lo=float(r['low']);hi=float(r['high']);cl='neutral' if c=='0-0' else 'batter' if lo>100 else 'pitcher'
    strength=' strong-cell' if c in ['0-2','3-0'] else ''
    num='100.00' if c=='0-0' else f'<span>{lo:.2f}</span><span class="range-end">–{hi:.2f}</span>'
    out.append(f'<td class="{cl}{strength}" data-count="{c}"><span class="cell-count">{c}</span><strong class="cell-value">{num}</strong><small>{int(r["PA"]):,}타석</small></td>')
   else:
    if c in ['0-2','1-2']: cl,label,sub='outside','존 밖','11시즌 추정 방향'
    elif c in ['0-1','2-2']: cl,label,sub='neutral','불명확','11시즌 모두'
    elif c=='1-1': cl,label,sub='inside','존 안','일부 해 불명확'
    else: cl,label,sub='inside','존 안','11시즌 모두'
    out.append(f'<td class="{cl}" data-count="{c}"><span class="cell-count">{c}</span><strong class="cell-value">{label}</strong><small>{sub}</small></td>')
  out.append('</tr>')
 out.append('</tbody></table>')
 if kind=='bcai': out.append('<div class="board-legend"><span class="pitcher-key">100 미만 · 시작보다 투수 유리</span><span class="batter-key">100 초과 · 시작보다 타자 유리</span></div>')
 out.append('</div>')
 return '\n'.join(out)
intro='''# 스트라이크는 언제나 좋은 공일까?

**0-2에서는 하나 빼라?**

**0-2에서 존 밖으로 승부할 만한 근거는 있었다.** MLB 2015–2025년의 열한 시즌 모두, 0-2에서는 실제 존 밖 공이 존 안 공보다 타자의 공격가치를 낮게 허용한 것으로 추정됐다. 다만 이것이 한 구를 무조건 멀리 버리라는 뜻은 아니다. 타자가 따라 나올 만한 공인지까지 봐야 한다.

이 조언의 출발점은 카운트다. 0-2에서는 타자가 헛스윙 한 번으로 삼진을 당할 수 있지만, 볼 하나를 골라도 아직 볼넷은 아니다. 투수에게는 타자가 따라 나오는지 시험할 여유가 생긴다. 반대로 3-0에서는 볼 하나가 곧 출루로 이어진다. 같은 존 밖 공이라도 카운트에 따라 의미가 달라지는 것이다.

그렇다면 **각 카운트는 타자와 투수 중 누구에게 얼마나 유리하고, 그 상황에서 어떤 행동이 더 좋은 결과와 연결됐을까?** 이 글은 이 두 질문을 MLB 11시즌 기록으로 살펴본다. 카운트별 유불리는 BCAI로, 같은 카운트에서의 위치·스윙·구종별 차이는 BCAP로 읽는다.

<a id="count-basics"></a>

## 먼저, 0-2와 3-0은 무슨 뜻일까?

**앞 숫자는 볼, 뒤 숫자는 스트라이크다.** 0-2는 ‘0볼 2스트라이크’, 3-0은 ‘3볼 0스트라이크’다. 한 타자가 타석에 들어서면 0-0에서 시작하며, 공 하나를 두고 벌이는 승부가 쌓여 카운트가 달라진다.

- **볼이 네 개면 볼넷:** 타자는 공을 치지 않고도 1루로 나간다.
- **스트라이크가 세 개면 삼진:** 타자는 보통 아웃된다.
- **스트라이크존:** 홈플레이트 위의 정해진 높이 범위다. 휘두르지 않은 공의 볼·스트라이크 판정 기준이 된다. 존 밖 공도 헛스윙하면 스트라이크다.

*기본 규칙: MLB [볼넷](https://www.mlb.com/glossary/standard-stats/walk) · [삼진](https://www.mlb.com/glossary/standard-stats/strikeout) · [스트라이크존](https://www.mlb.com/glossary/rules/strike-zone).*

그래서 일반적으로 볼이 쌓이면 타자는 볼넷에, 스트라이크가 쌓이면 투수는 삼진에 가까워진다. 하지만 ‘유리하다’는 말만으로는 차이의 크기를 알 수 없다. **0-2가 얼마나 불리한지, 볼과 스트라이크를 하나씩 받은 1-1은 처음과 같은지**를 실제 타석 결과로 확인할 필요가 있다.

## 이 글의 순서

1. [BCAI — 카운트별로 누가 얼마나 유리할까?](#chapter-bcai)
2. [BCAP — 같은 카운트에서 어떤 행동의 결과가 좋았을까?](#chapter-bcap)
   - [투수: 존 안과 존 밖](#chapter-location)
   - [타자: 스윙과 기다리기](#chapter-swing)
   - [투수: 구종 선택](#chapter-pitch)
3. [결과에서 이어지는 질문 — 왜 이런 차이가 생길까?](#chapter-questions)
4. [다시 0-2로 — 경기에서 무엇을 볼까?](#chapter-game)

<a id="chapter-bcai"></a>

## 1. BCAI — 카운트별로 누가 얼마나 유리할까?

**열한 시즌 내내 0-2가 투수에게 가장 유리했고, 3-0이 타자에게 가장 유리했다.** 이 차이를 점수로 나타낸 것이 BCAI다.

BCAI는 **그 카운트를 한 번이라도 거친 타석의 최종 공격가치**를 비교한다. 여기서 공격가치는 볼넷·안타·장타가 타석에 남긴 성과를 가중치로 합친 점수다. 타자는 높은 쪽, 그 성과를 막아야 하는 투수는 낮은 쪽이 유리하다.

### 카운트별 점수는 어떻게 읽을까?

**각 시즌의 타석 시작 평균을 100으로 놓는다.** 100보다 높으면 시작할 때보다 타자에게, 낮으면 투수에게 유리한 결과가 나왔다는 뜻이다. 아래 표는 행이 볼 수, 열이 스트라이크 수다. 같은 행에서 오른쪽으로 가면 스트라이크가, 같은 열에서 아래로 가면 볼이 하나씩 늘어난다.

'''
cap='''

*표 1. MLB 2015–2025, 1,896,892타석·25,193경기. 큰 숫자는 11개 연도별 BCAI의 최솟값–최댓값, 작은 숫자는 그 카운트를 거친 11시즌 타석 수다. 출처: [연도별 점수·타석 수](../../analysis/history_comparison_20260928_r01/tables/bcai_all_132.csv).*

> **해석 메모 | 11시즌의 점수 범위**
>
> 하나의 통합 점수나 신뢰구간이 아니다. 각 시즌의 점수가 어디부터 어디까지였는지 보여준다. 같은 타석이 여러 카운트를 거칠 수 있으므로 칸별 타석 수를 모두 합하면 안 된다. BCAI 120은 그해 시작 평균보다 가중 공격가치가 20% 높았다는 뜻이며, 승률이나 실제 득점이 20% 높다는 뜻은 아니다.

### 열한 시즌 내내 이어진 흐름은 무엇일까?

**같은 볼 수에서는 스트라이크가 늘수록, 같은 스트라이크 수에서는 볼이 줄수록 투수에게 유리했다.** 표를 오른쪽으로 읽으면 점수가 내려가고, 아래로 읽으면 올라간다. 이 흐름은 열한 시즌 모두 같았다.

0-2의 점수는 61.10–64.78로 언제나 가장 낮았다. 삼진이 가까워진 타자의 불리함이 실제 최종 결과에도 나타난 것이다. 반대로 3-0은 170.75–176.95로 가장 높았다. 이 점수에는 안타와 장타뿐 아니라 이후 얻은 볼넷도 포함된다.

한 가지는 더 구별해야 한다. **유리한 카운트에 있다는 것과, 다음 공을 어떻게 상대해야 하는지는 다른 질문이다.** 3-0의 높은 점수가 곧 스윙하라는 뜻은 아니며, 0-2의 낮은 점수가 투수에게 어느 공을 던져도 괜찮다는 뜻도 아니다. 다음 공의 위치와 타자의 반응을 같은 카운트 안에서 비교해야 하는 이유다.

<a id="chapter-bcap"></a>

## 2. BCAP — 같은 카운트에서 어떤 행동의 결과가 좋았을까?

**0-2·1-2에서는 실제 존 밖 공이 투수에게, 비교 가능한 존 밖 공에서는 기다리기가 타자에게 더 좋은 결과와 연결됐다.** 이런 위치와 행동별 차이를 살펴보는 분석이 BCAP다.

BCAI가 카운트별 평균을 보여준다면, BCAP는 **같은 카운트에서 존 안과 밖, 스윙과 기다리기, 서로 다른 구종을 비교한다.** 선수와 경기 상황의 차이가 결과에 섞이는 문제를 줄이기 위해 기록된 조건을 보정했다.[용어 2](#term-02)

비교 기준은 타석의 최종 공격가치다. 투수의 공을 비교할 때는 낮은 쪽이, 타자의 행동을 비교할 때는 높은 쪽이 좋은 결과다.

<a id="chapter-location"></a>

### 2-1. 투수는 존 안과 밖 중 어디에서 더 좋은 결과를 얻었을까?

**0-2·1-2에서는 존 밖 방향이 반복됐고, 0-0과 3볼 카운트 등에서는 존 안의 결과가 더 좋았다.** 다음 표는 공격가치를 더 낮게 허용한 위치를 보여준다.

'''
loc_table=matrix('location')+'''

*표 2. MLB 2015–2025, 열두 카운트의 연도별 위치 비교. ‘존 밖’은 11시즌 추정값의 방향이며 매년 차이가 확실했다는 뜻은 아니다. 출처: [BCAP 연도별 결과](../../analysis/history_comparison_20260928_r01/tables/bcap_all_2552_screened.csv).*

'''
loc_note=re.search(r'> \*\*해석 메모 \| 반복된 방향[\s\S]*?(?=\n### 상세 설명)',loc).group(0).strip().replace('표의 일곱 존 안 카운트','나머지 일곱 존 안 카운트')
locq=qblock(loc,'①')
loclast=loc[loc.index('> **해석 메모 | 위치별 결과'):].strip()
swingintro='''

실제 위치에서 투수에게 유리한 쪽을 확인했다면, 타자 쪽에서는 반대 질문이 생긴다. **존 밖 공이 투수에게 좋은 결과를 남겼다면, 타자는 그 공에 어떻게 반응했을까?**

<a id="chapter-swing"></a>

### 2-2. 타자는 어떤 공에 휘두르고 어떤 공을 지켜봤을 때 결과가 좋았을까?

**존 안에서는 대체로 스윙, 비교 가능한 존 밖 구역에서는 지켜보기의 공격가치가 더 높았다.** 같은 카운트와 위치 구역에서 스윙한 경우와 지켜본 경우를 비교한 결과다.

'''
swingresults=swing.split('> **결과 요약',1)[1].split('### 상세 설명',1)[0]
swingresults=swingresults[swingresults.index('| 공이 들어온 구역'):].strip()
swingq=qblock(swing,'①')
pitchintro='''

위치와 스윙 여부만으로 다음 공을 모두 설명할 수는 없다. 투수는 빠른 공과 휘어지는 공을 섞고, 같은 위치에도 다른 구종이 들어온다. **그렇다면 카운트에 따라 구종별 결과도 달랐을까?**

<a id="chapter-pitch"></a>

### 2-3. 투수의 구종 선택에서도 반복되는 차이가 있었을까?

**3-0에서는 패스트볼 계열 이외 구종, 3-2에서는 비포심 쪽이 좋은 결과를 보이는 방향이 반복됐다.** 다만 ‘패스트볼 계열’과 ‘포심’은 다른 분류다.

패스트볼은 빠른 공 계열을 가리키며, 이 비교에서는 포심·싱커·커터를 묶었다. 포심만 따로 비교할 때는 싱커와 커터가 반대편인 비포심에 들어간다. 두 비교를 구별해 읽어야 하는 이유다.

'''
pitchresults=pitch[pitch.index('| 카운트와 구종 분류'):].replace('### 상세 설명\n\n','').strip()
extra='''

카운트별 유불리와 그 안의 행동별 결과는 여기까지다. 이제 결과표를 보며 생길 법한 질문을 나눠 살펴보자. **카운트 점수를 읽는 질문, 두 스트라이크에서 승부하는 질문, 타자의 선택을 평가하는 질문**이다.

<a id="chapter-questions"></a>

## 3. 결과에서 이어지는 질문 — 왜 이런 차이가 생길까?

### 3-1. 카운트 점수를 더 읽어 보면

'''+bcai+'''

### 3-2. 두 스트라이크에서는 왜 승부가 달라질까?

'''+qblock(loc,'②')+'\n\n'+qblock(loc,'③').split('> **해석 메모 | 위치별 결과')[0].strip()+'\n\n'+qblock(swing,'②')+'''

<a id="chapter-three"></a>

### 3-3. 유리한 카운트라면 더 자주 휘둘러야 할까?

**그렇지는 않다. 높은 BCAI에는 기다려서 얻은 볼넷도 포함돼 있다.** 실제로 얼마나 휘두르는지와, 그 카운트를 거친 타석의 결과가 얼마나 좋은지는 나누어 봐야 한다.

'''
threebody=three[three.index('> **결과 요약'):].replace('### 상세 설명\n\n','')
# Place the source-supported result immediately above its citation.
threebody=threebody.replace('> **결과 요약 | 유리한 3-0에서도 타자들은 대부분 기다렸다**\n>\n> ','')
threebody=re.sub(r'\n\*위 수치는 Weinberg[\s\S]*?\n\n','\n\n',threebody,count=1)
new=intro+matrix('bcai')+cap+loc_table+loc_note+'\n\n'+locq+'\n\n'+loclast+swingintro+swingresults+'\n\n'+swingq+pitchintro+pitchresults+extra+threebody.strip()+'\n\n'+qblock(swing,'③')+'\n\n<a id="chapter-game"></a>\n\n'+end.replace('## 6. 경기에서 다시 보기 — 다음 0-2에서 무엇을 눈여겨볼까?','## 4. 다시 0-2로 — 경기에서 무엇을 볼까?')
# Reset local question ordinals after moving sections.
parts=new.split('### ')
for i,part in enumerate(parts):
 n=[0]
 def ren(m):
  n[0]+=1;return '#### '+str(n[0])+'）'
 parts[i]=re.sub(r'#### [①②③④⑤] ?',ren,part)
new='### '.join(parts)
# Remove explanation-of-use language; mark supported propositions themselves.
replacements={
'Gentile은 스트라이크존 경계 부근의 공을 따로 살폈고, 두 스트라이크 안에서도 카운트에 따라 실제 스윙 빈도가 달라지는 모습을 보고했다. 이 글에서는 ‘두 스트라이크 타격’을 하나로 묶지 않고 정확한 볼카운트를 함께 읽어야 한다는 설명에 사용했다.':'<u class="source-claim">Gentile의 경계 부근 투구 분석에서도 두 스트라이크 안에서 카운트에 따라 실제 스윙 빈도가 달랐다.</u> 따라서 같은 두 스트라이크라도 정확한 볼카운트를 함께 읽어야 한다.',
'Yee·Deshpande의 연구는 이런 가능성과 가치를 결합해 두 선택을 비교한다. 이 글에서 결과 하나와 선택의 평가를 구별하는 이유다.':'<u class="source-claim">Yee·Deshpande의 연구는 접촉·헛스윙·볼·스트라이크의 가능성과 가치를 결합해 스윙과 지켜보기를 비교한다.</u> 안타 하나가 나왔는지보다 선택 당시 기대할 수 있었던 결과를 보는 접근이다.',
'Ciardiello의 0-2 분석에서는 존 밖 공이 존 안 공보다 볼로 이어지는 비중이 큰 동시에, 헛스윙 비중은 높고 타구로 이어지는 비중은 낮았다.':'<u class="source-claim">Ciardiello의 0-2 분석에서는 존 밖 공이 존 안 공보다 볼로 이어지는 비중이 큰 동시에, 헛스윙 비중은 높고 타구로 이어지는 비중은 낮았다.</u>',
'Turkenkopf는 존에서 멀리 벗어난 공을 따로 정의해 분석했다.':'<u class="source-claim">Turkenkopf는 존에서 멀리 벗어난 공을 따로 정의해 분석했다.</u>',
'Weinberg의 분석에서도 실제로 스윙한 공의 성적을 나머지 공에 그대로 적용하기 어렵다는 점이 핵심이다.':'<u class="source-claim">Weinberg 역시 스윙한 공이 선택된 표본이라는 점 때문에, 그 성적을 지켜본 공에 그대로 적용하기 어렵다고 짚었다.</u>',
'Weinberg가 분석한 2007–2014년 MLB 자료에서 스윙 비율은 3-0에서 7.6%, 3-1에서 55.2%였다.':'<u class="source-claim">Weinberg가 분석한 2007–2014년 MLB 자료에서 스윙 비율은 3-0에서 7.6%, 3-1에서 55.2%였다.</u>',
'두 스트라이크에서 끝난 타율에는 삼진도 들어간다. 그보다 앞서 끝난 타율에는 일반적인 삼진이 들어갈 수 없다.':'<u class="source-claim">두 스트라이크에서 끝난 타율에는 삼진도 들어간다. 그보다 앞서 끝난 타율에는 일반적인 삼진이 들어갈 수 없다.</u>',
}
for a,b in replacements.items():
 assert a in new,a
 new=new.replace(a,b)
notes={
'타율을 비교하기 전에 분모를 확인한다':'문헌 1 · Stotz·Bickel | 카운트별 타율과 삼진 포함 여부\n>\n> Stanford 대학야구 자료. [원문](https://sabr.org/journal/article/batting-average-by-count-and-pitch-type/) · [한국어 해설](04_references_ko.md#ref-01)',
'존 밖 공 이후의 결과를 나누어 본다':'문헌 4 · Ciardiello | 0-2 투구 이후의 결과\n>\n> MLB 2019–2020. [원문](https://blogs.fangraphs.com/how-should-pitchers-approach-0-2-counts/) · [한국어 해설](04_references_ko.md#ref-04)\n>\n> 각 경로가 이번 11시즌 BCAP 차이에 얼마나 기여했는지는 별도로 계산하지 않았다.',
'존 밖과 완전히 버리는 공을 구별한다':'문헌 5 · Turkenkopf | 멀리 벗어난 공의 구분\n>\n> 존 밖 전체보다 좁은 대상의 분석. [원문](https://tht.fangraphs.com/a-pitch-is-a-terrible-thing-to-waste-or-is-it-part-1/) · [한국어 해설](04_references_ko.md#ref-05)',
'같은 두 스트라이크라도 카운트를 구별한다':'문헌 8 · Gentile | 두 스트라이크의 경계 공 대응\n>\n> MLB 2010–2013. 실제 행동의 차이이며 권장 스윙 비율은 아니다. [원문](https://tht.fangraphs.com/Taking-the-close-pitch-with-two-strikes/) · [한국어 해설](04_references_ko.md#ref-08)',
'골라 친 공의 성적을 모든 공에 적용하지 않는다':'문헌 7 · Weinberg | 스윙한 공과 지켜본 공의 차이\n>\n> [원문](https://tht.fangraphs.com/should-one-strike-make-this-much-difference/) · [한국어 해설](04_references_ko.md#ref-07)',
'선택은 가능한 결과들을 함께 놓고 평가한다':'문헌 6 · Yee·Deshpande | 스윙·지켜보기의 기대 가치\n>\n> 해당 연구의 기대 득점 모형은 BCAP와 계산법·단위가 다르다. [원문](https://arxiv.org/html/2305.05752v2) · [한국어 해설](04_references_ko.md#ref-06)',
}
for label,body in notes.items():
 pat=r'> \*\*참고문헌 \| '+re.escape(label)+r'\*\*\n[\s\S]*?(?=\n\n(?!>)|\Z)'
 title,rest=body.split('\n',1)
 new,n=re.subn(pat,'> **참고문헌 | '+title+'**\n'+rest,new,count=1)
 assert n==1,label
needle='유리한 카운트의 높은 공격가치와 높은 스윙 빈도는 같은 말이 아니었다.'
new=new.replace(needle,needle+'\n\n> **참고문헌 | 문헌 7 · Weinberg의 실제 스윙 비율**\n>\n> MLB 2007–2014의 별도 연구다. 본문의 11시즌 자체 분석 수치는 아니다. [원문](https://tht.fangraphs.com/should-one-strike-make-this-much-difference/) · [한국어 해설](04_references_ko.md#ref-07)')
new=new.replace('‘그 카운트를 거친 타석’을 구별해야 한다.','‘그 카운트를 거친 타석’을 구별해야 한다.')
new=new.replace('따라서 ‘3-0에서는 직구가 나쁘다’로 줄이면 비교한 대상부터 흐려진다.','따라서 ‘3-0에서는 직구가 나쁘다’로 줄이면 비교한 대상부터 흐려진다.')
(p/'01_ball_count.md').write_text(new.strip()+'\n',encoding='utf-8')
print('새 본문 저장:',len(new),'자')
