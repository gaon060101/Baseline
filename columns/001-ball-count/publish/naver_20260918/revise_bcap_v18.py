from pathlib import Path
import hashlib,json,shutil,re
P=Path(__file__).resolve().parent
B=P/'revisions/v17_before_bcap_v18'
if B.exists():raise SystemExit('보관본 존재: 재실행 금지')
B.mkdir(parents=True)
hashes={}
for n in ['01_ball_count.md','01_ball_count.html','02_bcai.md','02_bcai.html','03_bcap.md','03_bcap.html','04_references_ko.md','05_data_validation.md']:
 shutil.copy2(P/n,B/n);hashes[n]=hashlib.sha256((P/n).read_bytes()).hexdigest()
(B/'hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
s=(P/'03_bcap.md').read_text(encoding='utf-8')
insertions={
'## 2부. 투구 위치':'''### 1부 정리 · 평균 차이와 비교 근거를 함께 계산한다

공통 계산에서 얻는 것은 두 행동의 보정 평균과 그 차이다. 여기에 자료가 비교를 충분히 뒷받침하는지, 차이의 방향을 얼마나 분명히 가릴 수 있는지를 함께 표시한다. 아래의 ‘자료 부족’과 ‘불명확’은 각각 이 두 점검에서 나온 서로 다른 판단이다.

''',
'## 3부. 스윙 여부':'''### 위치 비교의 결론

**카운트에 따라 존 안과 존 밖의 결과 차이를 구분할 수 있었다.** 0-2·1-2에서는 11시즌 모두 존 밖의 허용 공격가치가 낮은 방향이었고, 불확실성 구간까지 같은 방향인 해는 각각 10시즌과 8시즌이었다. 반면 3볼 카운트에서는 존 안 방향이 분명했고, 0-1·2-2에서는 매년 차이를 분명하게 가르지 못했다.

이는 실제 도착 위치별 결과의 비교다. 모든 투수에게 같은 위치를 지시하면 같은 효과가 난다는 뜻은 아니다.

''',
'## 4부. 구종':'''### 스윙 비교의 결론

**스윙 여부는 카운트만으로 정답을 나누기 어려웠다.** 같은 카운트라도 위치를 구분하면 존 안에서는 대체로 스윙, 비교 가능한 존 밖에서는 테이크 쪽 평균 공격가치가 높았다. 다만 존 안 3-0·3-1은 차이가 불명확했고, 존 밖 3-0은 비교 자료가 부족했다.

따라서 이 표는 카운트마다 ‘무조건 휘두르기·기다리기’를 배정하는 지침이 아니다. 타자가 어떤 공을 골라 실제로 쳐낼 수 있는지를 함께 봐야 한다. 선수 능력이 카운트보다 얼마나 중요한지 직접 측정한 결과로 확대하지는 않는다.

''',
'## 적용 범위와 연도별 집계':'''### 구종 비교의 결론

**카운트마다 통용되는 구종의 우열을 정하기는 어려웠지만, 일부 비교에는 반복되는 차이가 있었다.** 3-0의 패스트볼 계열 비교는 자료가 충분한 10시즌 모두 나머지 구종의 허용 공격가치가 낮았다. 3-2의 포심 비교는 11시즌 모두 비포심 방향으로 추정됐지만, 구간까지 같은 방향인 것은 5시즌이었다.

이 단서를 모든 투수의 구종 지침으로 바꾸기는 어렵다. 넓게 묶인 구종 안의 구위 차이와 실제로 해당 구종을 쓸 수 있는 선수·상황을 함께 고려해야 한다.

'''
}
for anchor,txt in insertions.items():
 assert s.count(anchor)==1
 s=s.replace(anchor,txt+anchor)
anchor='이 글은 모델의 입력·예측·보정·평균·구간까지 설명했다.'
s=s.replace(anchor,'''## 최종 결론

**BCAP는 카운트별 위치·스윙·구종에 따른 결과 차이와, 그 차이를 판단할 수 있는 범위를 보여준다.** 위치에서는 카운트별 차이를 구분할 근거가 있었고, 스윙·구종에서는 공과 선수의 조건을 지운 보편적인 행동 지침까지 정할 수는 없었다. 관측된 차이는 활용하되, 이를 개별 선수의 정답 행동으로 바꾸는 데는 추가 근거가 필요하다.

'''+anchor)
s=s.replace('2026년 9월 28일 · 모델 해설 16차','2026년 9월 29일 · BCAP 해설 18차').replace('출처: Baseline 자체 분석..','출처: Baseline 자체 분석.')
(P/'03_bcap.md').write_text(s,encoding='utf-8')
(P/'models_v18').mkdir(exist_ok=True)
r=(P/'build_models_v16.mjs').read_text(encoding='utf-8').replace('onlyBcap?[1,2]:','onlyBcap?[2]:').replace('onlyBcap?[names[1],names[2]]:','onlyBcap?[names[2]]:').replace('models_v16','models_v18').replace('모델 해설 16차','BCAP 해설 18차').replace('2026.09.28','2026.09.29')
(P/'build_bcap_v18.mjs').write_text(r,encoding='utf-8')
q=(P/'check_models_v16.mjs').read_text(encoding='utf-8-sig').replace('models_v16','models_v18').replace("['02_bcai','03_bcap']","['03_bcap']")
(P/'check_bcap_v18.mjs').write_text(q,encoding='utf-8')
old=(B/'03_bcap.md').read_text(encoding='utf-8')
checks={'tables_preserved':re.findall(r'^\|.*$',old,re.M)==re.findall(r'^\|.*$',s,re.M),'sections_9_10_preserved':old[old.index('### 9단계'):old.index('공통 계산은 여기까지')]==s[s.index('### 9단계'):s.index('공통 계산은 여기까지')],'other_articles_preserved':all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in hashes.items() if not n.startswith('03_bcap')),'conclusions_added':all(t in s for t in ['위치 비교의 결론','스윙 비교의 결론','구종 비교의 결론','## 최종 결론'])}
assert all(checks.values())
(P/'models_v18/content_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(checks)
