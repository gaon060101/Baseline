"""Render editorial figures from immutable saved aggregates; never fit a model."""
from pathlib import Path
import csv, json, hashlib
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
C = HERE.parent.parent
OUT = C / 'figures/naver_20260918'
OUT.mkdir(parents=True, exist_ok=True)
REG = 'C:/Windows/Fonts/malgun.ttf'
BOLD = 'C:/Windows/Fonts/malgunbd.ttf'
INK='#17333B'; MUTED='#51656B'; TEAL='#147C80'; ORANGE='#BC562D'; GRAY='#EEF1F2'; LINE='#D6DFE0'
inputs={}; figures=[]
def read(rel):
    p=C/rel; inputs[rel]=hashlib.sha256(p.read_bytes()).hexdigest()
    return list(csv.DictReader(p.open(encoding='utf-8-sig')))
bc=read('analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_count_results.csv')
sb=read('analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/artifacts/sb_reformatted.csv')
sw=read('analysis/runs/bcap_swing__mlb_2023__20260914__r01/artifacts/values.csv')
st=read('analysis/runs/bcai_state_delta__mlb_2024_2025__20260917__r01/artifacts/state_delta_2024_2025.csv')
pi=read('analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_pitch_explanators.csv')
counts=[r['count'] for r in bc]
def font(n,b=False): return ImageFont.truetype(BOLD if b else REG,n)
def txt(d,xy,s,n=32,fill=INK,b=False,anchor=None): d.text(xy,str(s).replace('−','-'),font=font(n,b),fill=fill,anchor=anchor)
def canvas(title,sub,h=1200,w=1200):
    im=Image.new('RGB',(w,h),'white'); d=ImageDraw.Draw(im)
    d.rectangle((0,0,w,14),fill=TEAL)
    txt(d,(52,43),'BASELINE  /  볼카운트를 읽는 방법',24,TEAL,True)
    txt(d,(52,98),title,46,b=True)
    txt(d,(52,165),sub,27,MUTED)
    return im,d
def footer(d,y,lines):
    for i,s in enumerate(lines): txt(d,(52,y+i*36),s,24,MUTED)
def save(im,name,desc):
    p=OUT/name; im.save(p,optimize=True)
    figures.append({'file':name,'description':desc,'size_px':list(im.size),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
def blend(hexcolor,a):
    c=tuple(int(hexcolor[i:i+2],16) for i in (1,3,5))
    return tuple(round(255*(1-a)+x*a) for x in c)

# 1. The complete count grid; counts are pre-pitch states, not terminal counts.
im,d=canvas('같은 타석, 서로 다른 출발선','BCAI · 0-0 평균 = 100 · 높을수록 타자 쪽 공격가치가 높음',1190)
for j in range(3): txt(d,(362+j*280,249),f'{j}스트라이크',31,b=True,anchor='mm')
for i in range(4):
    txt(d,(100,365+i*165),f'{i}볼',32,b=True,anchor='mm')
    for j in range(3):
        r=next(x for x in bc if x['count']==f'{i}-{j}'); v=float(r['index'])
        x=222+j*280; y=290+i*165
        col=ORANGE if v>100 else TEAL if v<100 else INK; a=min(abs(v-100)/80,.85)*.45+.06
        d.rounded_rectangle((x,y,x+260,y+147),14,fill=blend(col,a))
        txt(d,(x+130,y+28),r['count'],24,MUTED,anchor='mm')
        txt(d,(x+130,y+75),f'{v:.2f}',45,col,True,'mm')
        txt(d,(x+130,y+120),f"{int(r['N_PA']):,}타석",22,MUTED,anchor='mm')
footer(d,997,['MLB 2024–2025 · 유효 완료 364,124타석 · 4,859경기',
              '각 칸: 도달 타석 기준 점추정. 한 타석은 여러 카운트에 포함될 수 있음.',
              '출처: BCAI-OBS v1.0.0 저장 결과 · 구간은 BCAI 설명 글 참조',
              '100은 승률 50%가 아니며, 값의 차이는 카운트를 바꾼 인과 효과가 아님.'])
save(im,'01_bcai_grid.png','12카운트 관찰 지수와 도달 타석 수')

# 2. Development location contrast and multiplicity-adjusted intervals.
dev=[r for r in sb if '개발' in r['period']]
im,d=canvas('카운트별 존 안·밖의 결과 비교','투수 위치 비교 · 차이 = 존 안 허용 W − 존 밖 허용 W',1380)
x0,x1=270,950; lo,hi=-.20,.06
sx=lambda v:x0+(v-lo)/(hi-lo)*(x1-x0)
txt(d,(400,240),'← 존 안의 허용 W가 낮음',25,TEAL,True,anchor='mm')
txt(d,(940,240),'존 밖이 낮음 →',25,ORANGE,True,anchor='mm')
for v in [-.20,-.15,-.10,-.05,0,.05]:
    d.line((sx(v),285,sx(v),1090),fill=INK if v==0 else LINE,width=3 if v==0 else 1)
    txt(d,(sx(v),1120),f'{v:+.2f}',23,MUTED,anchor='mm')
for i,r in enumerate(dev):
    y=315+i*66; v=float(r['delta_S_minus_B_W']); l=float(r['ci_low_W']); h=float(r['ci_high_W'])
    co=ORANGE if l>0 else TEAL if h<0 else MUTED
    txt(d,(62,y-22),r['count'],32,b=True)
    txt(d,(160,y-13),f"n={int(r['n']):,}",20,MUTED)
    d.line((sx(l),y,sx(h),y),fill=co,width=6)
    for z in [l,h]: d.line((sx(z),y-9,sx(z),y+9),fill=co,width=3)
    d.ellipse((sx(v)-8,y-8,sx(v)+8,y+8),fill=co)
    txt(d,(1000,y-21),f'{v:+.3f}',29,co,True)
footer(d,1190,['MLB 2024–2025 · n은 카운트별 비교 가능한 투구 수',
              '선: 기존 219개 비교 보정 명목 95% 구간 · 0-1은 0을 포함',
              '출처: BCAP-PITCH-SB v0.1.0 · 고정 점수의 경기 군집 구간',
              'W는 최종 타석의 가중 공격가치. 실제 위치 비교이며 투구 지시가 아님.'])
save(im,'02_sb_development.png','개발 12카운트 S−B와 기존 219개 비교 보정 구간')

# 3. Prior-year replication, shown separately because interval families differ.
ext=[r for r in sb if '2023' in r['period'] and r['count'] in ['0-2','1-2']]
im,d=canvas('2023년의 0-2·1-2를 비교하면','존 안 − 존 밖 · 양수이면 존 밖의 허용 공격가치가 낮음',870)
sx=lambda v:290+v/.055*700
for v in [0,.01,.02,.03,.04,.05]:
    d.line((sx(v),285,sx(v),575),fill=LINE if v else INK,width=2)
    txt(d,(sx(v),617),f'{v:.2f}',24,MUTED,anchor='mm')
for i,r in enumerate(ext):
    y=365+i*160; v=float(r['delta_S_minus_B_W']);l=float(r['ci_low_W']);h=float(r['ci_high_W'])
    txt(d,(60,y-47),r['count'],44,b=True)
    txt(d,(60,y+9),f"n={int(r['n']):,}",24,MUTED)
    d.line((sx(l),y,sx(h),y),fill=ORANGE,width=7)
    d.ellipse((sx(v)-11,y-11,sx(v)+11,y+11),fill=ORANGE)
    txt(d,(sx(v),y-47),f'{v:+.4f} W',30,ORANGE,True,'mm')
footer(d,694,['MLB 2023 · n은 비교 투구 수 · 선: 주4개 비교 보정 명목 95% 구간',
              '출처: BCAP-PITCH-SB v0.1.0 외부 연도 재현 · EXPERIMENTAL',
              '과거 연도에서 학습 절차를 재현한 비교. 새 전략을 시행한 효과가 아님.',
              '2026 위치 분석은 좌표·존 정의의 정합성 미확보로 측정 보류.'])
save(im,'03_sb_2023.png','2023 0-2·1-2 재현 결과와 주4개 비교 보정 구간')

# 4. Schematic only. Inside/outside labels refer to batter-relative horizontal direction.
im,d=canvas('공의 위치를 다섯 구역으로 읽는다','타자 기준으로 좌우를 맞춘 설명용 도식 · 축척 없는 개념도',1010)
L,T,R,B=410,380,790,680
d.rectangle((210,275,990,785),fill='#F5F7F7')
d.rectangle((L,T,R,B),fill='#D8ECEA',outline=TEAL,width=5)
txt(d,(600,490),'존 안 전체',41,TEAL,True,'mm')
txt(d,(600,547),'한가운데만 뜻하지 않음',23,MUTED,anchor='mm')
txt(d,(600,320),'높은 존 밖',34,b=True,anchor='mm')
txt(d,(600,735),'낮은 존 밖',34,b=True,anchor='mm')
txt(d,(300,510),'몸쪽',34,b=True,anchor='mm');txt(d,(300,558),'존 밖',30,anchor='mm')
txt(d,(890,510),'바깥쪽',34,b=True,anchor='mm');txt(d,(890,558),'존 밖',30,anchor='mm')
d.ellipse((296,304,326,334),fill=ORANGE)
txt(d,(90,215),'● 이 모서리 공은 높은 존 밖 + 몸쪽 존 밖에 함께 포함',26,ORANGE,True)
footer(d,843,['분류 기준: 관측 공 중심과 정규화한 존 경계 · 경계는 존 안에 포함',
              '모서리 공은 두 보고 구역에 겹침. 다섯 구역의 n을 합산하면 안 됨.',
              '도식에는 실제 투구 표본을 그리지 않음 · 출처: BCAP-SWING v0.2.0 명세'])
save(im,'04_zone_map.png','타자 기준 5구역 도식, 모서리 중복 설명')

# 5. Full supported region table with neutral and unsupported cells distinguished.
im,d=canvas('스윙과 테이크, 위치에 따라 달랐다','2023년 · 차이 = 스윙 W − 테이크 W · +는 스윙 방향',1800,1440)
regions=['CENTER','HIGH','LOW','INSIDE','OUTSIDE']; labels=['존 안 전체','높은 존 밖','낮은 존 밖','몸쪽 존 밖','바깥쪽 존 밖']
for j,l in enumerate(labels):txt(d,(316+j*235,263),l,30,b=True,anchor='mm')
stats={'swing':0,'take':0,'uncertain':0,'unsupported':0}
for i,c in enumerate(counts):
    y=302+i*104;txt(d,(82,y+48),c,35,b=True,anchor='mm')
    for j,re in enumerate(regions):
        r=next(r for r in sw if r['count']==c and r['region']==re and r['population']=='own')
        v=float(r['delta']); l=float(r['adjusted95_low']); h=float(r['adjusted95_high']); ok=r['support_gate']=='True'
        key='unsupported' if not ok else 'uncertain' if l<=0<=h else 'swing' if l>0 else 'take';stats[key]+=1
        x=203+j*235;fill={'swing':'#E3EEEC','take':'#F7E9E0','uncertain':'#F0F1F2','unsupported':'#FFFFFF'}[key]
        d.rounded_rectangle((x,y,x+223,y+96),10,fill=fill,outline=LINE,width=2)
        co={'swing':TEAL,'take':ORANGE,'uncertain':MUTED,'unsupported':MUTED}[key]
        top='자료 부족' if not ok else f'{v:+.3f}'
        txt(d,(x+111,y+27),top,31,co,True,'mm')
        bottom='판정 보류' if not ok else ('불명확 · ' if key=='uncertain' else '')+f"n={int(r['n']):,}"
        txt(d,(x+111,y+68),bottom,20,co,anchor='mm')
footer(d,1583,['청록: 스윙 방향 10셀 · 주황: 테이크 방향 44셀 · 회색: 불명확 2셀 · 흰색: 자료 부족 4셀',
              'n은 비교 투구 수. 모서리 중복으로 셀 표본 수를 더할 수 없음. 단위 W.',
              '색 판정: 기존 236개 비교 보정 명목 95% 구간 + 지원 기준 · 개별 공의 정답표가 아님.',
              '출처: BCAP-SWING v0.2.0 · 2023 외부 연도 저장 결과 · 2026 위치 분석은 측정 보류'])
assert stats=={'swing':10,'take':44,'uncertain':2,'unsupported':4},stats
save(im,'05_swing_2023.png','2023 12×5 스윙/테이크 차이·방향·지원 상태와 표본 수')

# 6. BCAI simultaneous intervals preserve scale and uncertainty.
im,d=canvas('지수는 점 하나보다 구간으로 읽는다','BCAI-OBS · 점은 관찰 지수, 선은 동시 95% 구간',1360)
sx=lambda v:240+(v-50)/140*770
for v in [60,80,100,120,140,160,180]:
    d.line((sx(v),270,sx(v),1100),fill=INK if v==100 else LINE,width=3 if v==100 else 1)
    txt(d,(sx(v),1140),str(v),25,MUTED,anchor='mm')
for i,r in enumerate(bc):
    y=305+i*67;v=float(r['index']);l=float(r['simultaneous95_low']);h=float(r['simultaneous95_high']);co=ORANGE if v>100 else TEAL if v<100 else INK
    txt(d,(65,y-23),r['count'],34,b=True)
    d.line((sx(l),y,sx(h),y),fill=co,width=6);d.ellipse((sx(v)-7,y-7,sx(v)+7,y+7),fill=co)
    txt(d,(1052,y-21),f'{v:.2f}',27,co,True)
footer(d,1200,['MLB 2024–2025 · 유효 완료 364,124타석 · 경기 단위 2,000회 재표본',
              '같은 재표본으로 12카운트를 함께 계산. 카운트별 도달 타석 수는 표 참조.',
              '출처: BCAI-OBS v1.0.0 · OBS의 구간을 Ridge 보정값에 옮기지 않음.'])
save(im,'06_bcai_intervals.png','BCAI OBS 점추정과 동시 95% 구간')

# 7. Only differences between reached-state averages, never realized transition effects.
im,d=canvas('두 스트라이크, 상태 사이 간격은?','2024년 · 다음 볼 상태의 값 − 현재 카운트의 관찰 평균 W',970)
rows=[r for r in st if r['year']=='2024' and r['count'] in ['0-2','1-2','2-2']]
for i,r in enumerate(rows):
    y=310+i*132;v=float(r['delta_ball_W']);dest='볼넷 종료값' if r['count']=='3-2' else r['next_ball_state']+' 평균'
    txt(d,(55,y),f"{r['count']} 평균 → {dest}",30,b=True)
    d.rounded_rectangle((590,y,590+v/.12*370,y+43),8,fill=TEAL)
    txt(d,(1080,y+21),f'{v:+.4f}',29,TEAL,True,'mm')
    n2=r['next_ball_state_N_PA'];end=f"{int(n2):,}타석" if n2 else 'BB 가중치 0.689'
    txt(d,(55,y+54),f"{int(r['N_reached_PA']):,}타석 / {end}",22,MUTED)
footer(d,760,['서로 다른 카운트 도달 집단의 평균 차이. 실제 볼 사건 뒤 평균이 아님.',
              '2024 유효 181,840타석 · W 단위 · 새 불확실성 구간은 미산출',
              '볼을 하나 던졌을 때의 인과 효과나 그 다음 공의 발생 확률이 아님.',
              '출처: BCAI-STATE-DELTA v0.1.0 · EXPERIMENTAL'])
save(im,'07_state_gaps.png','2024 2스트라이크 카운트의 다음 볼 상태 평균 차이')

# 8. Two separate scales explicitly distinguish value from action frequency.
im,d=canvas('3볼의 가치와 스윙 빈도 비교','3볼 카운트 · 공격가치와 스윙 빈도는 다른 질문',1030)
txt(d,(350,261),'BCAI  /  기준 100',31,ORANGE,True,anchor='mm')
txt(d,(875,261),'스윙률  /  %',31,TEAL,True,anchor='mm')
for i,c in enumerate(['3-0','3-1','3-2']):
    y=336+i*165;r=next(r for r in bc if r['count']==c);p=next(r for r in pi if r['count']==c)
    v=float(r['index']);z=float(p['Swing%']);txt(d,(60,y+14),c,38,b=True)
    d.rectangle((205,y,205+v/200*340,y+58),fill='#ECD4C8');txt(d,(565,y+28),f'{v:.2f}',30,ORANGE,True,'mm')
    d.rectangle((750,y,750+z/100*260,y+58),fill='#C9E2DF');txt(d,(1080,y+28),f'{z:.2f}%',30,TEAL,True,'mm')
    txt(d,(205,y+82),f"도달 {int(r['N_PA']):,}타석",23,MUTED)
    txt(d,(750,y+82),f"해당 {int(p['pitches']):,}투구",23,MUTED)
footer(d,864,['MLB 2024–2025 · 왼쪽은 최종 타석 가치, 오른쪽은 투구별 행동 비율',
              '서로 다른 단위·분모·축. 두 막대의 길이를 직접 비교하지 않음.',
              '출처: BCAI-OBS 저장 결과 + advantage_pitch_explanators.csv'])
save(im,'08_three_ball.png','3볼 카운트의 상태 가치와 투구별 스윙률, 분모 분리')

(OUT/'figure_manifest.json').write_text(json.dumps({'purpose':'저장 집계표의 표시용 차트. 새 모델 학습 없음.','inputs_sha256':inputs,'figures':figures,'swing_cell_checks':stats},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'figures':len(figures),'swing_cells':stats},ensure_ascii=False))
