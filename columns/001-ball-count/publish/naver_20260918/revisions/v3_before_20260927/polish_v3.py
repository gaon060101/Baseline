from pathlib import Path
import re,json
D=Path(__file__).resolve().parent
def box(label,body):return '> **참고문헌 | '+label+'**\n>\n> '+body.replace('\n','\n> ')
p=D/'01_ball_count.md';s=p.read_text(encoding='utf-8')
for prefix,num,title in [('한 공의 중요성을 다룬 Burley',2,'Burley — 한 번의 가치와 발생 빈도'),('2스트라이크도 하나로 묶기 어렵다.',8,'Gentile — 2스트라이크의 행동 빈도')]:
 paragraphs=s.split('\n\n')
 i=next(i for i,v in enumerate(paragraphs) if v.startswith(prefix))
 link=re.search(r'\['+str(num)+r' · [^\]]+\]\([^)]+\) · \[한국어 해설 '+str(num)+r'\]\([^)]+\)',s).group(0)
 s=s.replace(' '+link,'',1)
 s=s.replace(paragraphs[i],box(title,paragraphs[i]+' '+link),1)
labels={1:'Stotz·Bickel — 카운트별 타율의 분모',4:'Ciardiello·Turkenkopf — 서로 다른 버리는 공의 정의',6:'Yee·Deshpande — 기대득점으로 판단 평가',7:'Weinberg — 3-0과 3-1의 행동 차이',9:'Kovash·Levitt — 상대가 대응하는 배합',10:'Douglas 외 — 제구와 반응을 넣은 게임',11:'MONEYBaRL — 타석 전체의 정책',12:'Baxamusa — 같은 카운트의 다른 경로'}
for num,label in labels.items():
 pattern=r'> \*\*참고문헌 \| 외부 연구와 이 글의 연결\*\*\n>\n>[^\n]*\['+str(num)+r' · [^\n]*'
 m=re.search(pattern,s);assert m,num;s=s[:m.start()]+m[0].replace('외부 연구와 이 글의 연결',label,1)+s[m.end():]
p.write_text(s,encoding='utf-8')

p=D/'03_bcap.md';s=p.read_text(encoding='utf-8')
m=re.search(r'> \*\*해석 메모 \| 이 결과는 관측 자료의 보정 비교다\*\*\n>\n>[^\n]+\n\n',s);assert m
note=m[0];s=s[:m.start()]+s[m.end():]
s=s.replace('### 위치부터 확인하기',note+'### 위치부터 확인하기',1)
p.write_text(s,encoding='utf-8')

p=D/'02_bcai.md';s=p.read_text(encoding='utf-8')
needle='## 3. 계산의 재료 — 타석 결과에 W 붙이기\n\n'
s=s.replace(needle,needle+'**W는 최종 결과의 종류마다 다른 점수를 붙인 값이다. 볼넷·단타·장타의 차이를 평균 공격가치에 반영한다.**\n\n',1)
sentence='결과마다 다른 가치를 부여한다는 배경은 [FanGraphs의 wOBA 설명](https://library.fangraphs.com/offense/woba/)에서 확인할 수 있다.'
s=s.replace(sentence,'\n\n'+box('FanGraphs — wOBA의 가중치 개념',sentence+' 가중치의 배경을 참고했으며, 이 글의 W 분모와 처리 방식은 아래 자체 정의를 따른다.'),1)
p.write_text(s,encoding='utf-8')

p=D/'04_references_ko.md';s=p.read_text(encoding='utf-8')
s=s.replace('### 먼저 읽는 결과와 결론\n\n| 원문 집계','### 먼저 읽는 결과와 결론\n\n**2스트라이크의 낮은 통상 타율과 인플레이 성적은 같은 결론을 가리키지 않았다. 분모를 나눠 읽어야 한다.**\n\n| 원문 집계',1)
s=re.sub(r'\n{3,}','\n\n',s)
p.write_text(s,encoding='utf-8')

p=D/'finalize_draft.py';s=p.read_text(encoding='utf-8').replace('3편은 04,05.','3편은 05,04.');p.write_text(s,encoding='utf-8')
p=D/'revision_v3_check.json';checks=json.loads(p.read_text(encoding='utf-8'))
for name in ['01_ball_count','02_bcai','03_bcap','04_references_ko']:
 old=(D/'revisions/v2'/f'{name}.md').read_text(encoding='utf-8');new=(D/f'{name}.md').read_text(encoding='utf-8')
 tables=re.findall(r'^\|.*(?:\n\|.*)*',old,flags=re.M);assert all(t in new for t in tables)
 checks[name].update(notes=new.count('**해석 메모 |'),reference_boxes=new.count('**참고문헌 |'))
p.write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print('최종 문맥·문헌 양식 확인 완료')
