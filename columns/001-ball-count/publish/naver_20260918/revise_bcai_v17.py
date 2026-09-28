from pathlib import Path
import csv,re,json,hashlib,shutil
P=Path(__file__).resolve().parent
B=P/'revisions/v16_before_bcai_v17'
if B.exists():raise SystemExit('보관본 존재: 재실행 금지')
B.mkdir(parents=True)
hashes={}
for n in ['01_ball_count.md','01_ball_count.html','02_bcai.md','02_bcai.html','03_bcap.md','03_bcap.html','04_references_ko.md','05_data_validation.md']:
 shutil.copy2(P/n,B/n);hashes[n]=hashlib.sha256((P/n).read_bytes()).hexdigest()
(B/'hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
s=(P/'02_bcai.md').read_text(encoding='utf-8')
start=s.index('### 2,000번의 지수로')
end=s.index('### 여러 카운트를',start)
s=s[:start]+'''### 2,000번의 지수로 개별 구간을 만든다

원래 자료에서 계산한 지수 하나만으로는 경기 구성이 달라졌을 때 얼마나 흔들리는지 알기 어렵다. 그래서 앞 절처럼 경기를 다시 뽑고, **매번 W 평균부터 지수까지 다시 계산**한다. 지수 주변에 임의의 오차를 붙이는 것이 아니라, 표본 구성이 바뀌면서 계산값이 움직이는 모습을 직접 보는 방법이다.

한 번의 재표집에서 지수 하나가 만들어지는 과정을 가상 숫자로 따라가 보자. 0-2를 예로 들면 다음 순서다.

| 계산 단계 | 가상 재표본의 값 | 계산 |
| --- | --- | --- |
| 뽑힌 경기에서 0-2 도달 타석을 모음 | 100타석, 최종 W 합계 20 | 20 ÷ 100 = 0.200 W |
| 같은 경기 목록에서 유효 시작 타석을 모음 | 400타석, 최종 W 합계 125 | 125 ÷ 400 = 0.3125 W |
| 두 평균을 나누어 100 기준으로 환산 | 0-2 평균 ÷ 시작 평균 | 0.200 ÷ 0.3125 × 100 = 64 |

*실제 시즌의 재표집 결과가 아닌 계산 예시다. 같은 경기를 두 번 뽑았다면 그 경기의 W 합계와 타석 수도 두 번 반영한다.*

이렇게 나온 **64가 첫 재표집의 0-2 지수 한 개**다. 다른 경기 목록을 뽑았을 때 평균 W가 각각 0.195와 0.310이면 두 번째 지수는 약 62.90이다. 시작 평균도 함께 바뀌므로 원래 시즌의 분모를 고정해 두지 않는다. 이 과정을 2,000회 반복하면 같은 카운트의 지수 2,000개가 생긴다.

여러 번 반복하는 이유는 한두 번 우연히 뽑힌 경기 목록에 흔들림의 판단을 맡기지 않고, 값들이 어느 범위에 모이는지 살피기 위해서다. 2,000회는 이번 계산에서 정한 반복 횟수이며 특별한 정답 횟수는 아니다. 무한히 반복한 분포의 근사이므로 반복 자체의 오차도 남는다.

다음으로 지수 2,000개를 작은 순서대로 정렬한다. 아래쪽 2.5%와 위쪽 97.5% 지점을 찾아 **개별 95% 구간**의 양 끝으로 쓴다. 양끝의 드문 값 2.5%씩을 바깥에 두고 가운데 95%를 남기는 방식이다. 정렬한 목록에서 대략 50번째와 1,950번째 부근이며, 정확한 백분위값은 인접한 값 사이를 보간할 수 있다.

최솟값부터 최댓값까지를 그대로 쓰면 드물게 나온 극단적인 재표본 하나가 구간을 크게 벌릴 수 있다. 가운데의 일정 비율을 쓰는 것은 그런 양끝과 중심적인 흔들림을 구분하기 위해서다. 95%는 이번에 택한 신뢰수준이며 자연적으로 정해진 기준은 아니다. 90%를 택하면 더 좁고 99%를 택하면 더 넓은 구간이 된다.

구간이 좁으면 이 재표집 방식 안에서 지수가 덜 흔들렸고, 넓으면 더 흔들렸다는 뜻이다. 원래 표의 대표 지수를 이 2,000개의 평균으로 바꾸지는 않는다. 특정 타석의 결과가 그 구간 안에 들어갈 확률이나, 이미 정해진 참값이 95% 확률로 그 안에 있다는 뜻도 아니다.

'''+s[end:]
start=s.index('### 두 카운트의 차이는')
end=s.index('> **해석 메모 | 계산한 구간',start)
s=s[:start]+'''### 두 카운트의 차이는 매번 직접 뺀다

앞의 두 절은 각 카운트의 지수가 얼마나 불확실한지 설명했다. 그런데 본문처럼 **카운트와 카운트 사이의 간격**을 읽으려면 한 단계가 더 필요하다. 두 지수에 각각 오차가 있다는 사실만으로는 두 값의 차이가 얼마나 확실한지 알 수 없기 때문이다.

특히 두 카운트는 같은 경기와 일부 같은 타석을 공유한다. 타격 결과가 좋았던 경기를 많이 뽑으면 두 지수가 함께 올라갈 수도 있다. 두 값이 함께 움직이는 부분은 뺄셈에서 상쇄될 수 있으므로, 각각의 구간이 겹치는지만 보고 차이를 판정하지 않는다.

그래서 **같은 재표본에서 계산한 두 지수를 바로 뺀다.** 가상으로 첫 재표본의 0-1과 2-2 지수가 85.0과 85.4라면 차이는 +0.4다. 두 번째 재표본에서 86.0과 86.2라면 차이는 +0.2다. 두 지수가 모두 올라갔어도 서로의 간격은 오히려 작아질 수 있다.

이처럼 얻은 차이 2,000개를 정렬해 2.5·97.5백분위수로 그 쌍의 개별 구간을 만든다. 구간이 0을 포함하면 그 비교에서 어느 쪽이 높다고 분명하게 가르기 어렵고, 전부 양수 또는 음수이면 그 방향의 차이를 뒷받침한다. 차이를 분명히 찾지 못했다는 것이 두 카운트가 같다는 증명은 아니다.

이 설명은 카운트 간 비교에서 필요한 불확실성 계산법이다. 본문의 정수 차이표 전체에 이 검정을 새로 적용했다는 뜻은 아니며, 특정 쌍의 구간을 만들었다고 가능한 모든 쌍을 동시에 검증한 것도 아니다.

'''+s[end:]
f=P/'../../analysis/runs/bcai_ridge__mlb_2024_2025__20260908__r02/artifacts/count_indices.csv'
rows=list(csv.DictReader(f.open(encoding='utf-8-sig')))
table='| 카운트 | OBS | Ridge | 보정 후−전 |\n| --- | ---: | ---: | ---: |\n'
tables=[]
for year in ['2024','2025']:
 subset=[r for r in rows if r['period']==year]
 assert len(subset)==12
 tables.append('**'+year+'년**\n\n'+table+'\n'.join('| '+r['count']+' | '+f"{float(r['I']):.2f}"+' | '+f"{float(r['J']):.2f}"+' | '+('0.00' if r['count']=='0-0' else f"{float(r['shift']):+.2f}")+' |' for r in subset))
maxshift=max(abs(float(r['shift'])) for r in rows if r['period']=='combined')
result='''### 2024·2025 결과 — 보정 전후의 카운트별 지수

이 보조 계산의 용도는 선수·시작 상황을 고려한 뒤에도 OBS의 모습이 유지되는지 확인하는 데 있다. 아래는 2024·2025 개발 자료에서 **자기 경기를 학습하지 않은 예측값**으로 계산한 Ridge 지수와 같은 자료의 OBS를 비교한 결과다. 앞의 11시즌 평균표와 기간이 다르다. 작은 이동 폭을 읽을 수 있도록 이 표는 소수 둘째 자리까지 표시했다.

'''+ '\n\n'.join(tables)+'''

*출처: Baseline BCAI-RIDGE v0.2.0의 저장된 시즌별 지수. 유효 타석은 2024년 181,840개, 2025년 182,284개이며 각 행의 분모는 해당 카운트 도달 타석이다. 변화량은 반올림 전 값으로 구한 뒤 표시했다. Ridge 자체의 신뢰구간은 없다.*

**두 시즌 모두 0-2가 가장 낮고 3-0이 가장 높은 모습과, 100을 기준으로 한 각 카운트의 유불리 방향은 유지됐다.** 두 시즌을 고정 비중으로 합친 결과에서 가장 큰 이동은 3-0의 175.40→173.79, 약 −1.61포인트였다. 따라서 이 보정에서 카운트별 큰 모습이 크게 달라지지 않았다는 민감도 확인에는 의미가 있었다.

다만 이것을 ‘보정 효과가 통계적으로 유의했다’거나 ‘선수 차이를 완전히 제거했다’는 결론으로 읽지는 않는다. 개별 타석 결과의 예측도 상수 예측 대비 오차 감소가 개발 자료에서 약 0.43%로 작았다. 이 결과의 역할은 정교한 개인별 예측을 제공하는 것보다, **관찰 지수의 해석이 이 정도의 시작 선수·상황 보정에 얼마나 민감한지 점검하는 것**이다.

'''
anchor='### 타석 시작의 정보로 예상 W를 만든다'
s=s.replace(anchor,result+anchor)
anchor='### 현재 상태와 비교할 다음 상태를 정한다'
s=s.replace(anchor,'''### 본문의 카운트 간격 설명과 연결되는 계산

본문에서 **‘볼이나 스트라이크 하나 차이로 점수가 가장 크게 달라지는 곳’**을 설명하고, 마지막 **‘투수에게 0-2는 무엇을 할 수 있는 상황인가’**에서 63→71→85→119를 읽을 때 사용한 것은 카운트별 상태 평균을 서로 비교하는 방식이다. 이 절의 STATE-DELTA도 그 간격을 계산하는 원리를 다룬다.

다만 현재 본문은 **11시즌 BCAI 평균 지수의 차이**, 저장된 STATE-DELTA는 **2024·2025 시즌별 원 W 평균의 차이**다. 따라서 본문에 STATE-DELTA의 출력값을 그대로 옮겼다고 말하지는 않는다. 같은 상태 평균 비교를 서로 다른 기간과 단위로 설명한 관계다. 두 경우 모두 서로 다른 도달 타석 집단을 비교하므로, 볼 하나의 인과적 효과라는 뜻은 아니다.

[본문의 카운트별 점수와 간격](01_ball_count.md#chapter-bcai) · [본문의 0-2 경기 해석](01_ball_count.md#chapter-game)

'''+anchor)
s=s.replace('2026년 9월 28일 · 모델 해설 16차','2026년 9월 29일 · BCAI 해설 17차')
(P/'02_bcai.md').write_text(s,encoding='utf-8')
(P/'models_v17').mkdir(exist_ok=True)
render=(P/'build_models_v16.mjs').read_text(encoding='utf-8').replace('onlyBcap?[1,2]:','onlyBcap?[1]:').replace('onlyBcap?[names[1],names[2]]:','onlyBcap?[names[1]]:').replace('models_v16','models_v17').replace('모델 해설 16차','BCAI 해설 17차').replace('2026.09.28','2026.09.29')
(P/'build_bcai_v17.mjs').write_text(render,encoding='utf-8')
qa=(P/'check_models_v16.mjs').read_text(encoding='utf-8-sig').replace('models_v16','models_v17').replace("['02_bcai','03_bcap']","['02_bcai']")
(P/'check_bcai_v17.mjs').write_text(qa,encoding='utf-8')
checks={'ridge_rows':sum(r['period'] in ['2024','2025'] for r in rows),'combined_max_shift':maxshift,'illustration_1':20/100/(125/400)*100,'illustration_2':.195/.310*100,'outside_scope_preserved':all(hashlib.sha256((P/n).read_bytes()).hexdigest()==h for n,h in hashes.items() if not n.startswith('02_bcai'))}
assert checks['ridge_rows']==24 and checks['outside_scope_preserved'] and abs(checks['illustration_1']-64)<1e-10
(P/'models_v17/content_check.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks))
