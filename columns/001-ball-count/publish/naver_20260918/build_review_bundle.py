"""Create a portable reading bundle without distributing analysis inputs."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import re, json, hashlib, shutil, zipfile

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
B=P/'revisions/v3_before_20260927'
OUT=P/'review_v4_20260927'
OUT.mkdir(exist_ok=True)
(OUT/'assets').mkdir(exist_ok=True)
names=['01_ball_count','02_bcai','03_bcap','04_references_ko','05_data_validation']
figdir=P.parent.parent/'figures/naver_20260918'
figures=sorted(figdir.glob('0*.png'))
assert len(figures)==8
for f in figures:shutil.copy2(f,OUT/'assets'/f.name)

placement='''# 그림 배치 — 2026-09-27 4차

그림의 수치·기간·단위·표본·출처와 본문의 캡션을 함께 유지한다.

| 파일 | 배치 |
| --- | --- |
| 01_bcai_grid.png | 본문 그림 1 |
| 02_sb_development.png | 본문 그림 2 |
| 03_sb_2023.png | 검증 글 그림 1 |
| 04_zone_map.png | 본문 그림 3 · BCAP 그림 2 |
| 05_swing_2023.png | 본문 그림 4 · BCAP 그림 1 |
| 06_bcai_intervals.png | BCAI 그림 1 |
| 07_state_gaps.png | BCAI 그림 2 |
| 08_three_ball.png | 본문 그림 5 |
'''
with zipfile.ZipFile(P/'네이버_첨부그림_8장_v4.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in figures:z.write(f,f.name)
 z.writestr('그림_배치_안내.md',placement)
shutil.copy2(P/'네이버_첨부그림_8장_v4.zip',OUT/'네이버_첨부그림_8장_v4.zip')

removed=[]
def portable_url(url):
 if url.startswith(('https://','http://','mailto:','#','data:')):return url
 parts=urlsplit(url);f=Path(unquote(parts.path)).name
 if f in [n+'.html' for n in names]+[n+'.md' for n in names]+['index.html','README.md','네이버_첨부그림_8장_v4.zip']:
  return f+('#'+parts.fragment if parts.fragment else '')
 if f in [x.name for x in figures]:return 'assets/'+f
 return None

for name in names+['index']:
 h=(P/(name+'.html')).read_text(encoding='utf-8')
 def anchor(m):
  before,url,after,body=m.groups();u=portable_url(url)
  if u is None:
   removed.append({'from':name,'url':url})
   return body
  return '<a'+before+'href="'+u+'"'+after+'>'+body+'</a>'
 h=re.sub(r'<a([^>]*?)href="([^"]+)"([^>]*)>([\s\S]*?)</a>',anchor,h)
 def src(m):
  u=portable_url(m[1]);assert u is not None,m[1]
  return 'src="'+u+'"'
 h=re.sub(r'src="([^"]+)"',src,h)
 if name!='index':
  h=h.replace('</article>','<p class="note">프로젝트 내부 검토자료의 이름은 남기고 로컬 전용 링크는 제외했습니다. 상세 근거 경로는 원본 프로젝트 MD에 보관돼 있습니다. 이 파일은 4차 사용자 검토본이며 외부 발행본이 아닙니다.</p></article>')
 (OUT/(name+'.html')).write_text(h,encoding='utf-8')
 if name=='index':continue
 s=(P/(name+'.md')).read_text(encoding='utf-8')
 def mdlink(m):
  bang,label,url=m.groups();u=portable_url(url)
  return f'{bang}[{label}]({u})' if u else label
 s=re.sub(r'(!?)\[([^\]]+)\]\(([^)]+)\)',mdlink,s)
 s+='\n\n*공유용 사본: 이미지·글 간 경로를 묶음 안으로 조정하고 프로젝트 내부 전용 링크를 자료명으로 바꿨다. 원고 내용과 수치는 유지했다.*\n'
 (OUT/(name+'.md')).write_text(s,encoding='utf-8')

(OUT/'README.md').write_text('''# 볼카운트 연재 다섯 편 — 4차 검토본

2026-09-27. 압축파일 전체를 풀고 `index.html`을 브라우저에서 연다. HTML만 따로 옮기지 말고 assets 폴더와 다섯 글을 함께 보관한다. 인터넷 없이도 글과 그림을 읽을 수 있으며 외부 원문 링크만 인터넷이 필요하다.

- 01: 가볍게 읽는 칼럼 본문
- 02: BCAI 결과와 계산
- 03: BCAP 결과와 비교 방법
- 04: 문헌 12건 한국어 해설, 본문 직접 인용과 확장 읽기 구분
- 05: 데이터 검증·모델 한계·개발 과정

각 MD는 편집용 사본, HTML은 검토용 표시본이다. 이미지와 글 간 경로만 묶음 내부로 조정했다. 내부 보고서·모델·CSV 링크는 자료명으로 남기고, 실제 근거는 원본 프로젝트에 보존했다. 원본 CSV·개별 투구 자료·모델 객체는 포함하지 않았다.

네이버 이전 시 본문·표를 옮기고 PNG를 지정 위치에 첨부한다. 해석 메모·문헌·용어 제목을 유지한다. HTML 서식이나 각주 이동 기능이 그대로 옮겨진다고 가정하지 않는다. 다섯 글의 로컬 링크는 실제 게시 주소로 바꿔야 한다. 공개 주소가 없는 상태에서 블로그 발행 완료라고 표시하지 않는다.

기존 원격 공유 링크의 Not Found 원인은 확인하지 않았으며 이 묶음은 서버 복구가 아닌 이동 가능한 검토본이다.
'''+ '\n'+placement,encoding='utf-8')

class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.ids=set()
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.add(a['id'])
  for k in ['href','src']:
   if k in a:self.links.append(a[k])

checks=[];parsed={}
for f in OUT.glob('*.html'):
 q=Links();q.feed(f.read_text(encoding='utf-8'));parsed[f.name]=q
for name,q in parsed.items():
 for u in q.links:
  if u.startswith(('http:','https:','mailto:','data:')):continue
  v=urlsplit(u);target=(OUT/unquote(v.path)) if v.path else OUT/name
  okay=target.exists() and target.resolve().is_relative_to(OUT.resolve())
  if v.fragment and target.suffix=='.html':okay=okay and v.fragment in parsed[target.name].ids
  checks.append({'from':name,'url':u,'exists':okay})

protected=json.loads((B/'protected_hashes.json').read_text(encoding='utf-8'))
changed=[name for name,h in protected.items() if not (ROOT/name).exists() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h]
def tables(s):return re.findall(r'(?m)^\|[^\n]+\n(?:\|[^\n]+\n)+',s)
table_checks=[]
for name in ['02_bcai','03_bcap','04_references_ko']:
 old=tables((B/(name+'.md')).read_text(encoding='utf-8'))
 new=tables((P/(name+'.md')).read_text(encoding='utf-8'))
 # The reference table's question-column label was updated to match the whole series.
 old=[x.replace('| 본문에서 생기는 질문 |','| 연재에서 이어지는 질문 |') for x in old]
 table_checks.append({'file':name,'original_tables':len(old),'all_original_tables_preserved':all(x in new for x in old)})
metrics={'counting':'공백 포함 MD 문자 수, 줄바꿈 LF 통일','before':len((B/'01_ball_count.md').read_text(encoding='utf-8')),'after':len((P/'01_ball_count.md').read_text(encoding='utf-8'))}
metrics['reduction_pct']=round((1-metrics['after']/metrics['before'])*100,1)
(P/'revision_v4_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
report={'date':'2026-09-27','protected_files_compared':len(protected),'protected_files_changed':changed,'protection_scope':'선택한 MD/JSON/CSV/YAML/PY/PNG 중 20MB 이하 1296개; runtime/qa/대형파일 제외. 전체 원본 데이터 해시 검사는 아님.','original_tables':table_checks,'bundle_link_checks':checks,'internal_links_rendered_as_text':removed,'main_length':metrics,'pass':not changed and all(x['exists'] for x in checks) and all(x['all_original_tables_preserved'] for x in table_checks)}
(P/'revision_v4_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
assert report['pass'],json.dumps(report,ensure_ascii=False)
with zipfile.ZipFile(P/'볼카운트_5편_검토본_20260927.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(OUT.rglob('*')):
  if f.is_file():z.write(f,f.relative_to(OUT))
(P/'delivery_check.json').write_text(json.dumps({'date':'2026-09-27','revision':'v4','article_count':5,'bundle':'볼카운트_5편_검토본_20260927.zip','figures_zip':'네이버_첨부그림_8장_v4.zip','checks':'revision_v4_check.json','visual_checks':'visual_check.json','published':False},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pass':report['pass'],'protected':len(protected),'links':len(checks),'tables':table_checks,'metrics':metrics},ensure_ascii=True))
