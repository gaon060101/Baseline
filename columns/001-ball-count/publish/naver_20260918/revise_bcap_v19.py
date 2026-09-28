from pathlib import Path
import shutil,json,hashlib
P=Path(__file__).resolve().parent
B=P/'revisions/v18_before_bcap_v19'
if B.exists():raise SystemExit('보관본 존재')
B.mkdir(parents=True)
before={}
for name in ['03_bcap.md','03_bcap.html','02_bcai.md','02_bcai.html','01_ball_count.md','01_ball_count.html']:
 shutil.copy2(P/name,B/name);before[name]=hashlib.sha256((P/name).read_bytes()).hexdigest()
(B/'hashes.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
s=(P/'03_bcap.md').read_text(encoding='utf-8')
old=s
s=s.replace('### 9단계 · 집단별 비교 가능 기준을 적용한다\n\n','''### 9단계 · 집단별 비교 가능 기준을 적용한다

여기서는 **계산된 숫자를 결과로 내놓을 만큼 비교 근거가 충분한지** 확인한다. 투구가 많아도 한쪽 행동이 드물거나 몇 기록에 큰 가중치가 붙으면, 그 몇 사례가 평균을 좌우할 수 있다. 그래서 단순한 투구 수와 함께 양쪽 행동의 정보량, 경기 수와 가중치 집중을 살핀다.

''')
s=s.replace('*모델에 정한 표시 기준이다.', '*500개·200개 등의 경계는 이번 모델에서 정한 점검 기준이며, 그 수를 넘으면 언제나 충분하다는 통계 법칙은 아니다.')
s=s.replace('가중치가 1·1·4인 가상 세 기록의 ESS는 36÷18=2다.','''가중치가 1·1·4인 가상 세 기록의 ESS는 36÷18=2다.

이 예에서 세 번째 기록은 앞의 각 기록보다 네 배 크게 반영된다. 기록은 세 개지만 세 개가 고르게 평균을 뒷받침하지는 않는다. ESS=2는 이런 가중치 쏠림을 ‘동일한 가중치의 기록 몇 개에 해당하는지’로 요약한 값이다. 기록 하나를 삭제했다는 뜻도, 경기 안의 모든 의존성까지 해결했다는 뜻도 아니다.''')
s=s.replace('### 10단계 · 경기 단위 변동으로 구간을 만들고 표시를 정한다\n\n','''### 10단계 · 경기 단위 변동으로 구간을 만들고 표시를 정한다

자료가 충분하다고 두 행동의 차이까지 확실한 것은 아니다. 이제는 **다른 경기들을 관찰했어도 차이가 비슷한 방향으로 나올지** 살핀다. 그 평균 차이가 표본에 따라 흔들리는 크기를 나타내는 값이 표준오차(SE)다. 개별 투구 점수의 흩어짐과 평균 차이의 불확실성은 구별한다.

''')
s=s.replace('경기 군집 방식이다.\n\n투구별', '경기 군집 방식이다. 같은 경기에서 나온 100개의 공을 서로 다른 100경기에서 나온 공처럼 취급하면 공통 환경을 공유한다는 점을 놓치기 때문이다.\n\n투구별')
s=s.replace('개별 구간은 평균 차이 ± t 임계값×SE로 만든다.', '개별 구간은 평균 차이 ± t 임계값×SE로 만든다. 여기서 t 임계값은 원하는 신뢰수준과 경기 수에 맞춰 정하는 배수이고, 자유도는 그 배수를 정할 때 쓰는 정보량의 기준이다.')
s=s.replace('여러 카운트·구역을 한꺼번에 비교하므로', '비교를 많이 하면 실제 차이가 없어도 우연히 뚜렷해 보이는 결과를 하나쯤 만날 가능성이 커진다. 여러 카운트·구역을 한꺼번에 비교하므로')
s=s.replace('마지막 표시는 **자료 기준', '''구간을 읽는 가상 예시로, 평균 차이가 +0.02 W이고 오차 폭이 ±0.03 W라면 구간은 −0.01부터 +0.05 W다. 양수와 음수가 모두 가능해 보여 방향을 분명히 가르지 못한다. 같은 +0.02 W라도 폭이 ±0.01 W라면 구간 전체가 양수다. 계산값의 크기만 보는 것이 아니라 그 값의 흔들림도 함께 보는 이유다.

마지막 표시는 **자료 기준''')
s=s.replace('BCAP 해설 18차','BCAP 해설 19차')
(P/'03_bcap.md').write_text(s,encoding='utf-8')
(P/'models_v19').mkdir(exist_ok=True)
for src,dst in [('build_bcap_v18.mjs','build_bcap_v19.mjs'),('check_bcap_v18.mjs','check_bcap_v19.mjs')]:
 t=(P/src).read_text(encoding='utf-8-sig').replace('models_v18','models_v19').replace('BCAP 해설 18차','BCAP 해설 19차')
 (P/dst).write_text(t,encoding='utf-8')
checks={'after_step10_preserved':s[s.index('공통 계산은 여기까지'):]==old[old.index('공통 계산은 여기까지'):],'before_step9_preserved':s[:s.index('### 9단계')].replace('19차','18차')==old[:old.index('### 9단계')],'other_articles_preserved':all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in before.items() if not n.startswith('03_bcap'))}
assert all(checks.values())
(P/'models_v19/content_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(checks)
