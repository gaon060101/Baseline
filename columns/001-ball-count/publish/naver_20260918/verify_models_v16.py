from pathlib import Path
import re,json,hashlib
P=Path(__file__).resolve().parent
B=P/'revisions/v15_before_models_v16'
main=(P/'01_ball_count.md').read_text(encoding='utf-8-sig')
a=(P/'02_bcai.md').read_text(encoding='utf-8')
b=(P/'03_bcap.md').read_text(encoding='utf-8')
checks=[]
def check(name,ok):checks.append({'check':name,'pass':bool(ok)})
hashes=json.loads((B/'hashes.json').read_text(encoding='utf-8'))
for name,h in hashes.items():check('보관본 '+name,hashlib.sha256((B/name).read_bytes()).hexdigest()==h)
for name in ['01_ball_count.md','01_ball_count.html','04_references_ko.md','04_references_ko.html','05_data_validation.md','05_data_validation.html']:check('범위 밖 보존 '+name,hashlib.sha256((P/name).read_bytes()).hexdigest()==hashes[name])
def matrix(s,cls):return re.search(r'<div class="count-board '+cls+r'">[\s\S]*?</table>',s).group(0)
check('BCAI 표 보존',matrix(a,'bcai-board')==matrix(main,'bcai-board'))
check('위치 표 보존',matrix(b,'location-board')==matrix(main,'location-board'))
for header in ['| 카운트 | 존 안의 스윙·테이크 비교 | 존 밖의 스윙·테이크 비교 |','| 카운트 | 패스트볼 계열 대 나머지 | 포심 대 비포심 |']:
 pat=re.escape(header)+r'\n(?:\|[^\n]*\n)+'
 check('본문 비교표 '+header,re.search(pat,b).group(0)==re.search(pat,main).group(0))
check('위치 표가 2부 안에 있음',b.index('## 2부.')<b.index('<div class="count-board')<b.index('## 3부.'))
check('스윙 표가 3부 안에 있음',b.index('## 3부.')<b.index('| 카운트 | 존 안')<b.index('## 4부.'))
check('구종 표가 4부 안에 있음',b.index('## 4부.')<b.index('| 카운트 | 패스트볼'))
for name,s in [('BCAI',a),('BCAP',b)]:
 check(name+' 질문형 제목 없음',not re.search(r'^#{1,4}.*\?',s,re.M))
 links=re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',s)
 check(name+' 발행 5편 밖 내부 링크 없음',all(u.startswith(('#','01_ball_count','02_bcai','03_bcap','04_references_ko','05_data_validation','http')) for u in links))
 check(name+' W 독립 설명',all(t in s for t in ['0.689','2.050','공식 wOBA']))
check('Ridge 지수 가상 산술',abs(100+100*(-.060/.300-(-.006/.300))-82)<1e-10)
check('상태 차이 가상 산술',all(abs(x-y)<1e-10 for x,y in [(.34-.28,.06),(.20-.28,-.08),(.34-.20,.14)]))
check('AIPW 0행 가상 산술',abs(.20+(0-.20)/.40+.30)<1e-10)
check('가상 평균과 차이',abs((.70+.30+.20)/3-(.25-.30+.20)/3-.35)<1e-10)
check('ESS 가상 산술',(1+1+4)**2/(1+1+16)==2)
report={'pass':all(c['pass'] for c in checks),'checks':checks,'scope':'원고의 표·산술 예시·구성·링크 범위·보존 확인. 통계 재분석 아님.'}
(P/'models_v16/content_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pass':report['pass'],'checks':len(checks),'failed':[c for c in checks if not c['pass']]},ensure_ascii=False))
if not report['pass']:raise SystemExit(1)
