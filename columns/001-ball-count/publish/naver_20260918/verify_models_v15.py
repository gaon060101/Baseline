from pathlib import Path
import re,json,hashlib,csv

P=Path(__file__).resolve().parent
B=P/'revisions/v14_before_models_v15'
main=(P/'01_ball_count.md').read_text(encoding='utf-8-sig')
a=(P/'02_bcai.md').read_text(encoding='utf-8-sig')
b=(P/'03_bcap.md').read_text(encoding='utf-8-sig')
checks=[]
def check(name,ok): checks.append({'check':name,'pass':bool(ok)})
hashes=json.loads((B/'hashes.json').read_text(encoding='utf-8'))
for name,digest in hashes.items():
    check('수정 전 보관본 '+name,hashlib.sha256((B/name).read_bytes()).hexdigest()==digest)
for name in ['01_ball_count.md','01_ball_count.html','04_references_ko.md','04_references_ko.html','05_data_validation.md','05_data_validation.html']:
    check('범위 밖 원고 보존 '+name,hashlib.sha256((P/name).read_bytes()).hexdigest()==hashes[name])
def board(s,cls):
    return re.search(r'<div class="count-board '+cls+r'">[\s\S]*?</div>\s*\n\n\*표 ',s).group(0)
check('BCAI 본문 표 일치',board(a,'bcai-board')==board(main,'bcai-board'))
check('위치 본문 표 일치',board(b,'location-board')==board(main,'location-board'))
for header in ['| 카운트 | 존 안의 스윙·테이크 비교 | 존 밖의 스윙·테이크 비교 |','| 카운트 | 패스트볼 계열 대 나머지 | 포심 대 비포심 |']:
    pat=re.escape(header)+r'\n(?:\|[^\n]*\n)+'
    check('본문 비교표 일치 '+header,re.search(pat,b).group(0)==re.search(pat,main).group(0))
for name,s in [('BCAI',a),('BCAP',b)]:
    check(name+' 질문형 제목 없음',not re.search(r'^#{1,4} .*\?',s,re.M))
    check(name+' 구버전 결과 그림 없음','history_comparison_20260928_r01/figures' not in s)
    check(name+' 불필요한 분석 결과 소제목 없음',not re.search(r'^#{2,4}.*(주 결과|보조 결과|결과의 해석|반복됐)',s,re.M))
check('BCAP 세 비교별 계산 장',all(x in b for x in ['## 2. 투구 위치 비교','## 3. 스윙 비교','## 4. 구종 비교']))
check('가상 AIPW 산술',abs(.30+(.50-.30)/.50-.70)<1e-12)
check('가상 BCAI 산술',abs(.240/.300*100-80)<1e-12)
report={'pass':all(c['pass'] for c in checks),'checks':checks,'scope':'본문 표와 수식 설명·가상 산술·보존 검사. 모델 재실행과 통계 검증은 수행하지 않음.'}
(P/'models_v15/content_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pass':report['pass'],'checks':len(checks),'failed':[c for c in checks if not c['pass']]},ensure_ascii=False))
if not report['pass']: raise SystemExit(1)
