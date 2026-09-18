# 볼카운트 칼럼: 실제 사용할 참고문헌과 원문 기반 집필 해설

**2026-09-17 · 사용자 독후 의견 반영 · 현재 집필 기준**

[미리보기](references_in_use_20260917.html) · [수정 개요](outline_mlb.md) · [모델 발전 검토](model_research_followup_20260917.md) · [다른 작업에 전달할 프롬프트](model_followup_prompt_20260917.md)

## 먼저: 모델에서 발전시킬 부분

**현재 BCAP에는 이미 12카운트별 존 안 S·존 밖 B의 보정 가치가 있다.** 추가할 것은 같은 표의 재계산보다, ‘실제 볼 하나·스트라이크 하나로 카운트가 바뀌는 가치’와 ‘그 위치의 공에 스윙·테이크했을 때 생기는 결과’를 구분한 설명이다.

1. 기존 S/B의 Q(B)·Q(S)·차이를 함께 공개한다. 수치는 [모델 발전 검토](model_research_followup_20260917.md)에 기존 산출물에서 옮겼다.
2. 12카운트 상태가치에 실제 볼/스트라이크 이후 상태가치를 연결한다. 현재 위치별 S/B와 다른 신규 분석이다.
3. BART 논문을 참고해 BCAP-SWING을 판정·접촉·후속 결과의 가지로 설명하는 보조 모형을 검토한다. 기존 W와 비교할 수 있도록 목표를 맞춘다.
4. 0-2에서 존 밖 비중을 높이면 타자의 반응도 달라진다는 민감도 분석을 검토한다. 기존 평균표만으로 균형이나 최적 비율을 계산할 수는 없다.
5. BCAI 경로 세분화는 이번에 실행하지 않는다. 외부 연구의 제한된 결과를 소개한다. KBO 강타자·강투수 특성은 후속 과제로 남긴다.

모델·기존 실행·원본 데이터는 수정하지 않았다. 구현 범위와 검증 조건은 별도 전달 프롬프트에 적었다.

## 1. 원문 접근 확인 결과

**현재 본문에 채택한 12편은 모두 본문을 확인했다.** 논문만 12편이라는 뜻은 아니며 학술 연구와 전문 분석 글을 합한 수다. KBO 후속용 1편과 정의·자료 문서 5건도 확인했다. 조건부 본문 후보인 Mercier의 2024년 미니맥스 논문은 출판사 초록만 확인했고 전문은 아직 확보하지 못했다.

따라서 아래의 **현재 검토 대상 19건 중 18건 본문 확인, 1건 초록 확인**이다. 원문 접근은 관련 본문·표를 읽었다는 뜻이며, 부록·코드·원자료 재현 또는 재배포 권한 확보와는 다르다. 공개 arXiv 원고는 아래 버전 기준으로 확인했으며 출판 최종본과 같다고 가정하지 않는다.

| 사용처 | 문헌 정식 제목·저자 | 이번 확인 범위 |
| --- | --- | --- |
| 본문 | [Batting Average by Count and Pitch Type](https://sabr.org/journal/article/batting-average-by-count-and-pitch-type/) — Dean Stotz·J. Eric Bickel (2002) | 공개 웹 본문 확인 |
| 본문 | [The Importance Of Strike One (and Two, and Three…), Part 2](https://tht.fangraphs.com/the-importance-of-strike-one-part-two/) — Craig Burley (2004) | 공개 웹 본문 확인 |
| 본문 | [Evaluating plate discipline in Major League Baseball with Bayesian Additive Regression Trees](https://arxiv.org/html/2305.05752v2) — Ryan Yee·Sameer K. Deshpande (2023 원고; 2024 학술지) | arXiv v2 공개 전문 |
| 본문 | [Computing an Optimal Pitching Strategy in a Baseball At-Bat](https://arxiv.org/html/2110.04321v1) — Connor Douglas·Everett Witt·Mia Bendy·Yevgeniy Vorobeychik (2021) | arXiv v1 공개 전문 |
| 본문 | [How Should Pitchers Approach 0-2 Counts?](https://blogs.fangraphs.com/how-should-pitchers-approach-0-2-counts/) — Carmen Ciardiello (2021) | 공개 웹 본문 확인 |
| 본문 | [A pitch is a terrible thing to waste. Or is it? (Part 1)](https://tht.fangraphs.com/a-pitch-is-a-terrible-thing-to-waste-or-is-it-part-1/) — Dan Turkenkopf (2009) | 공개 웹 본문 확인 |
| 본문 | [Taking the close pitch with two strikes](https://tht.fangraphs.com/Taking-the-close-pitch-with-two-strikes/) — James Gentile (2013) | 공개 웹 본문 확인 |
| 본문 | [Should One Strike Make This Much Difference?](https://tht.fangraphs.com/should-one-strike-make-this-much-difference/) — Neil Weinberg (2015) | 공개 웹 본문 확인 |
| 본문 | [Thanks for the memories](https://tht.fangraphs.com/thanks-for-the-memories/) — Sal Baxamusa (2007) | 공개 웹 본문 확인 |
| 본문 | [Professionals Do Not Play Minimax: Evidence from Major League Baseball and the National Football League](https://www.nber.org/papers/w15347) — Kenneth Kovash·Steven D. Levitt (2009) | NBER 공개 PDF 전문, 결론·표 확인 |
| 본문 | [MONEYBaRL: Exploiting pitcher decision-making using Reinforcement Learning](https://arxiv.org/abs/1407.8392) — Gagan Sidhu·Brian Caffo (2014) | arXiv v1 공개 전문 |
| 본문 | [The Impact of the One-Off 1887 Four-Strike Strikeout](https://sabr.org/journal/article/the-impact-of-the-one-off-1887-four-strike-strikeout/) — Woody Eckard (2022) | 공개 웹 본문 확인 |
| 본문 조건부 | [Professionals do play Minimax: Revisiting the Nash equilibrium in Major League Baseball](https://www.sciencedirect.com/science/article/pii/S2773161824000168) — Jean-François Mercier (2024) | 초록 확인 / 전문 미확보 |
| KBO 후속 | [Commanding the Zone](https://blogs.fangraphs.com/commanding-the-zone/) — Josh Weinstock (2011) | 공개 웹 본문 확인 |
| 정의·자료 | [wOBA](https://library.fangraphs.com/offense/woba/) — FanGraphs | 공개 웹 본문 확인 |
| 정의·자료 | [Plate Discipline](https://library.fangraphs.com/offense/plate-discipline/) — FanGraphs | 공개 웹 본문 확인 |
| 정의·자료 | [Statcast CSV Documentation](https://baseballsavant.mlb.com/csv-docs) — Baseball Savant | 공개 웹 본문 확인 |
| 정의·자료 | [Event Files](https://www.retrosheet.org/eventfile.htm) — Retrosheet | 공개 웹 본문 확인 |
| 정의·자료 | [Player Splits Tool](https://library.fangraphs.com/features/player-splits-tool/) — FanGraphs | 공개 웹 본문 확인 |

### 아직 전문 확인이 안 된 1편

[Professionals do play Minimax: Revisiting the Nash equilibrium in Major League Baseball](https://www.sciencedirect.com/science/article/pii/S2773161824000168)은 출판사 페이지와 저자가 공개한 [공유 링크](https://authors.elsevier.com/a/1jgIm9sYqDR9Ye)를 모두 확인했지만, 현재 접근 환경에서는 전문 요청이 차단됐다. 유료라고 확정하거나 공유 링크가 만료됐다고 단정하지 않는다. **결론의 방향을 초록 수준으로 소개할 수는 있으나, 상세 방법·검정·효과 크기는 전문 확보 후 확정한다.**

반면 [Professionals Do Not Play Minimax: Evidence from Major League Baseball and the National Football League](https://www.nber.org/papers/w15347)은 일반 웹 열람 도구에서 막혔지만 [NBER 공식 PDF](https://www.nber.org/system/files/working_papers/w15347/w15347.pdf)는 실제 열렸고 본문을 확인했다. 두 문헌을 모두 ‘원문 접근 불가’로 처리하면 안 된다.

## 2. 삼진 위험이 있는데, 왜 무조건 일찍 승부하라고 할 수 없을까?

### Batting Average by Count and Pitch Type

**Dean Stotz·J. Eric Bickel (2002) · [원문](https://sabr.org/journal/article/batting-average-by-count-and-pitch-type/) · 배치: 2절의 통계 해석**

**실제 비교.** 1998~2001년 스탠퍼드 자료 약 7만 6천 투구·2만 500타석에서, 2스트라이크 이전 타율은 .353, 이후는 .183이었다. 그러나 인플레이 타구 기준 안타율은 .353과 .326이었다. 저자는 종료 카운트 타율의 큰 차이에 삼진이 포함되는 분모 구조가 영향을 준다고 설명한다. 이는 삼진 비용을 없애거나 2스트라이크가 무해하다고 주장하는 연구가 아니다.

**사용자 질문에 대한 답.** 삼진을 피하려는 이유는 분명 있다. 다만 ‘지금 스윙하면 삼진을 피한다’가 곧 ‘지금 스윙하면 전체 타석 가치가 높다’는 뜻은 아니다. 빨리 친 약한 땅볼도 아웃이다. 일찍 휘둘렀다가 헛스윙하거나 파울을 치면 타석이 끝나지 않고 스트라이크만 늘 수도 있다. 기다리면 삼진 위험과 함께 볼넷·더 좋은 공의 가능성도 달라진다. 무엇이 큰지는 같은 상황에서 두 선택을 비교해야 한다.

**특히 통계에 빠지는 부분.** 초구 타율 표에는 초구를 쳐서 타석이 끝난 결과가 들어간다. 초구 스윙 후 헛스윙·파울로 이어진 타석은 ‘초구 종료 타율’에서 빠진다. 기존에 타자가 칠 만하다고 골라 친 공의 성적을, 앞으로 더 넓게 휘두를 모든 공의 예상 성적으로 쓰기도 어렵다. 이 문단은 논문의 분모 문제를 우리 질문에 연결한 해설이다.

**칼럼용 문단.**

> 삼진의 위협은 일찍 좋은 공을 놓치지 말아야 할 이유가 된다. 하지만 나쁜 공까지 일찍 치라는 근거는 되지 않는다. 비교할 것은 초구에 끝난 타석과 2스트라이크에 끝난 타석의 타율이 아니라, 지금 이 공에 휘둘렀을 때와 지켜봤을 때 타석이 어떻게 이어지는가다.

**결론의 범위.** ‘일찍 승부하는 편향을 가지면 안 된다’보다 **‘종료 카운트 타율만으로 일찍 승부할수록 이득이라고 결론 낼 수 없다’**가 정확하다. 일찍 오는 좋은 공에는 스윙이 유리할 수 있다. 그 조건을 찾는 것이 BCAP의 질문이다.

## 3. 같은 스트라이크라도 가치가 다른가?

### The Importance Of Strike One (and Two, and Three…), Part 2

**Craig Burley (2004) · [원문](https://tht.fangraphs.com/the-importance-of-strike-one-part-two/) · 배치: 2절 끝, 상태가치와 투구가치 연결**

2003년 투수 타석을 제외한 자료에서 카운트 전이의 가치를 비교한 분석이다. 공 하나가 스트라이크로 판정될 때와 볼로 판정될 때의 격차는 1-1에서 약 .092, 초구에서 .069였다. 반면 해당 기회의 수는 1-1이 68,748, 초구가 175,638이었다. **한 번의 차이가 큰 카운트와 시즌 전체에서 기회가 많은 카운트는 다르다.** 저자는 2스트라이크 관련 추정의 과대평가 가능성도 논의한다.

**BCAP와 연결.** 현재 S/B는 공이 실제로 존 안/밖에 도착한 위치 분류다. 존 안 공에도 안타·파울·헛스윙이 있고, 존 밖 공에도 스윙이 있다. 이 연구처럼 실제 스트라이크/볼 이후 상태의 차이를 계산한 것과 같지 않다. 새 표에서는 ‘존 안 공의 평균 W’와 ‘스트라이크 이후 상태 W’를 따로 적어야 한다.

**칼럼용 문단.**

> 초구 스트라이크가 중요하다는 말은 두 가지로 나뉜다. 한 번 성공했을 때의 차이가 큰가, 아니면 모든 타석에서 반복되는 기회인가. 두 질문의 답은 같을 필요가 없다. 카운트 표에 다음 볼과 다음 스트라이크가 이어질 자리를 표시하면 그 차이가 보인다.

**추가 분석 상태.** 새로운 상태 전이표는 아직 계산하지 않았다. 기존 S/B 결과를 재명명해 전이 분석을 했다고 쓰지 않는다. terminal 삼진·볼넷, 2스트라이크 파울의 자기 회귀, 반복 도달의 분모 처리는 전달 프롬프트에서 정했다.

## 4. BART 논문은 BCAP와 정확히 무엇이 같은가?

### Evaluating plate discipline in Major League Baseball with Bayesian Additive Regression Trees

**Ryan Yee·Sameer K. Deshpande (2023 원고; 2024 학술지) · [확인한 공개 원고 v2](https://arxiv.org/html/2305.05752v2) · 배치: 4절 핵심 방법 설명**

### 연구가 계산하는 것

한 투구에 대해 지켜봤을 때의 기대득점과 휘둘렀을 때의 기대득점을 각각 만든다. 관측한 실제 결과로 판단을 채점하기 전에, 가능한 결과를 가지로 나눈다. §2.2의 테이크 쪽은 볼/콜드 스트라이크, 스윙 쪽은 접촉/헛스윙을 중심으로 확률과 후속 가치를 결합한다. BART는 여러 작은 회귀나무를 더해 비선형 관계를 추정하는 베이지안 방법이다.

### 실제 자료와 추정 구성

2019년의 테이크 380,654개와 스윙 341,725개를 각각 판정·접촉 확률 추정에 사용하고, 득점 가치 쪽에는 2015~2018년 2,853,912개 투구를 사용한다. §3.2에서는 판정·접촉 확률 모형에 투타 정보와 위치를 활용하지만, 사건 이후 기대득점 모형에는 선수와 위치를 같은 방식으로 모두 넣지 않는다. 따라서 모든 선수·위치 조합의 장기 결과까지 정교하게 개인화했다고 설명하면 과장이다.

각 확률과 가치를 사후표본별로 결합해 스윙−테이크 차이와 불확실성을 얻는다. ‘BART를 쓰니 개인별 판단의 정답을 안다’가 아니라, 정한 조건·모형에서 두 선택의 예상 차이를 추정한다.

### 실제 결과와 결론

논문은 이 차이를 이용한 판단 평가를 제시한다. 제안한 평가와 실제 행동의 일치율은 69.4%, 비교 휴리스틱은 68.4%였다. 이 수치는 행동을 바꿨을 때 득점이 그만큼 늘었다는 실험 결과가 아니다. 위치를 반영한 GAM과 비교한 예측 개선도 압도적이지 않다. 우리에게 중요한 성과는 특정 알고리즘의 이름보다 **결과를 나눠 행동 가치를 설명한 구성**이다. §5.1은 다른 목표·추정기를 사용할 여지도 설명한다.

### BCAP와 대조해서 읽기

| 항목 | 논문 | 현재 BCAP-SWING | 활용 판단 |
| --- | --- | --- | --- |
| 질문 | 스윙과 테이크의 예상 차이 | 같은 조건의 스윙/테이크 보정 W 차이 | 문제의식이 매우 가깝다 |
| 최종 목표 | 기대득점 R | 최종 타석 W | 단위·목표를 맞춰야 수치 비교 가능 |
| 계산 구조 | 사건 확률×사건 이후 가치의 합 | 행동 확률·결과 회귀를 이용한 AIPW | BART가 현 모형의 단순 상위 버전은 아니다 |
| 추정기 | BART 중심 | Ridge 기반 nuisance 모형 | 추정기 교체와 사건 분해는 별개의 결정 |
| 불확실성 | 사후표본으로 결합 | 현재 고정 점수의 경기 군집 구간·다중 비교 보정 | 구간이 포함하는 불확실성이 다르다 |
| 전달할 내용 | 개인별 점수까지 포함 | 이번 칼럼은 일반적 카운트·위치 관계 | 개인 순위·개별 행동 채점은 사용하지 않는다 |
| 얻을 수 없는 것 | 현장 정책 변경의 보장 | 현장 정책 변경의 보장 | 양쪽 모두 반사실·모형 가정이 필요하다 |

### 칼럼에는 어디까지 쓸까?

> 지켜보는 선택에는 볼과 스트라이크가, 휘두르는 선택에는 접촉과 헛스윙이 있다. 앞선 연구는 이 갈림길을 각각 계산해 두 선택을 비교했다. BCAP도 한 번의 결과보다 선택의 평균 가치를 묻지만, 여기서는 득점 대신 최종 타석의 W를 비교했다.

본문은 이 정도로 설명하고, 표와 구현 차이는 방법 해설에 연결한다. **연구의 선수별 채점 목적 전체를 가져올 필요는 없다.** 일반적 패턴을 설명하는 데 사건 분해 방법만 가져오는 것이 사용자 방향에 맞는다.

## 5. 최적 투구 연구와 BCAP의 한계는 같은가?

### Computing an Optimal Pitching Strategy in a Baseball At-Bat

**Connor Douglas·Everett Witt·Mia Bendy·Yevgeniy Vorobeychik (2021) · [원문 v1](https://arxiv.org/html/2110.04321v1) · 배치: 5절 모형과 전략 사이**

**실제 연구.** 카운트 상태에서 투수의 구종·목표 위치와 타자의 반응을 연결하고, 출루 억제를 목표로 게임을 푼다. 의도한 위치와 실제 도착 위치가 다를 수 있다는 실행 오차도 넣는다. 의도한 위치는 직접 관측되지 않으므로 3-0 투구를 이용한 가정과 구종별 가우시안 오차를 사용한다. 이는 실제 목표 지점을 확보한 연구라는 뜻이 아니다.

**실제 검증.** 약 270만 투구·73만 타석을 활용한다. 학습/평가의 선수 중복을 피한 검증을 포함하고, 3,600개 대결에서 모형의 출루율 평균 .242와 실제 .329를 비교한다. 이 큰 차이를 현장 투구 지시로 재현한 실험은 아니다. 논문은 상대 반응을 게임 안에 넣었으므로 ‘상대를 고정해서 실패했다’고 요약해서도 안 된다.

**정확한 판단.** ‘BCAP와 똑같이 실패했다’는 표현은 피한다. 논문은 자신이 정의한 모형의 전략을 계산했다. 우리의 현재 BCAP는 주로 관측 행동의 보정 평균을 비교하며, 최적 순차 정책을 계산한 모형이 아니다. 서로 다른 단계의 한계를 구분해야 한다.

**우리 검토에서 드러나는 공통 난점.**

- 의도한 행동과 관측된 도착 위치의 차이: S/B 평균으로 목표 위치의 효과를 대신할 수 없다.
- 보지 못한 선택의 결과: 같은 공·상황에서 다른 행동의 결과는 동시에 관측되지 않는다.
- 자료가 드문 선택: 최적화가 실제 장점 대신 예측 오차가 큰 영역을 고를 수 있다.
- 정책 변경 후 상대 반응: 과거 행동 분포의 결과가 배합을 바꾼 뒤에도 유지될지 별도 문제다.
- 목표의 차이: 출루율 최소화, W 최소화, 득점 최소화가 항상 같은 전략을 고르지는 않는다.
- 검증의 차이: 예측 적합도와 새로운 정책의 경기 효과는 다른 검증 대상이다.

위 목록은 논문과 BCAP를 대조한 **이번 검토의 해석**이며, 저자가 여섯 항목 모두를 실패 원인으로 실증했다는 뜻은 아니다.

**칼럼용 문단.**

> 최적이라는 말에는 어떤 경기 규칙과 어떤 상대를 가정했는지가 따라붙는다. 목표로 삼은 위치에 얼마나 정확히 던질 수 있는지, 기록에 드물게 나타난 선택의 결과를 얼마나 믿을 수 있는지도 답을 바꾼다. 평균 비교에서 발견한 유리한 방향을 실제 배합표로 바꾸려면 이 단계를 더 건너야 한다.

## 6. 0-2의 존 밖 공: 버리는 공인가, 유인구인가?

### How Should Pitchers Approach 0-2 Counts?

**Carmen Ciardiello (2021) · [원문](https://blogs.fangraphs.com/how-should-pitchers-approach-0-2-counts/) · 배치: 3절 외부 비교**

2019~2020년 0-2에서 존 밖 공 전체와 존 안 공을 비교한다. 존 밖 공은 볼이 되는 비율 56.8%, 인플레이 7.7%, 헛스윙 12.7%였고, 존 안 공은 각각 2.7%, 27.1%, 9.5%였다. 타자 기준 100구당 run value는 존 밖 −.39, 존 안 +.70이었다. 단순히 볼 확률 하나만 보는 것과 여러 종료·진행 결과를 함께 보는 것이 다름을 보여준다.

존 밖 전체의 관측 비교다. BCAP와 기간·단위·보정이 다르므로 같은 수치의 재현이라고 쓰지 않는다. ‘공을 무조건 멀리 빼라’라는 권고를 검증한 것도 아니다.

### A pitch is a terrible thing to waste. Or is it? (Part 1)

**Dan Turkenkopf (2009) · [원문](https://tht.fangraphs.com/a-pitch-is-a-terrible-thing-to-waste-or-is-it-part-1/) · 배치: 바로 이어지는 범주 설명**

2008년 0-2 투구 38,606개 중 매우 멀리 빠진 공을 별도로 정의해 4,297개, 약 11%로 집계한다. 매우 먼 공을 많이 던진 집단과 적게 던진 집단의 FIP는 4.29와 4.28로 비슷했다. 이 집단 비교만으로 그런 투구를 늘리거나 줄일 때의 효과가 같다고 결론 낼 수 없다. 특히 이 글은 Part 1의 범위로 읽는다.

**두 글을 합친 칼럼용 문단.**

> 존 밖이라는 말은 넓다. 경계에서 타자의 스윙을 끌어낼 만한 공과 아주 멀리 빠진 공을 같은 선택으로 부르면 비교가 흐려진다. 기존 분석들도 ‘버리는 공’을 서로 다르게 정의했다. 우리의 S/B 역시 실제 도착 위치의 구분이므로, 그 차이만으로 투수의 의도까지 읽을 수는 없다.

## 7. 3볼과 2스트라이크를 묶어 읽는 법

### Taking the close pitch with two strikes

**James Gentile (2013) · [원문](https://tht.fangraphs.com/Taking-the-close-pitch-with-two-strikes/) · 배치: 4절의 2스트라이크 네 카운트**

경계 공 스윙률은 0-2 74.5%, 1-2 78.6%, 2-2 81.6%, 3-2 84.8%였다. 2스트라이크여도 볼 수에 따라 실제 대응이 달랐다는 관측이다. 이를 모두 과잉 스윙이라고 판정하는 자료는 아니다. 경계 위치의 정의와 존 전체 비교는 구별해야 한다.

이 글의 개인별 비교·선수 순위는 빼고 카운트별 전체 패턴만 쓴다. 같은 삼진 위험을 공유해도 볼넷까지 남은 거리와 만나는 공의 구성이 다르다는 질문으로 연결한다.

### Should One Strike Make This Much Difference?

**Neil Weinberg (2015) · [원문](https://tht.fangraphs.com/should-one-strike-make-this-much-difference/) · 배치: 자체 3-0/3-1 표 다음**

3-0 스윙률 7.6%와 3-1 55.2%라는 큰 격차를 출발점으로 삼는다. 2014년 고의사구 제외 자료의 단순 계산에서 전부 지켜보는 경우와 실제 선택 혼합의 가치가 3-0에서는 .21/.19, 3-1에서는 .15/.13이었다. 이 계산은 상대 투수가 행동을 바꾸지 않는 가정에 기대며 새로운 정책의 실험이 아니다.

결론을 ‘그러니 3-0에서 더 휘둘러라’로 뒤집어 읽으면 안 된다. 저자는 오히려 3-1에서도 덜 휘두르는 쪽을 생각하게 한다. 현재 BCAP의 3-0 등 불명확한 비교와 결합해 어느 한 방향의 지시를 확정하지 않는다.

**칼럼용 문단.**

> 유리한 카운트는 휘두를 이유만 늘리지 않는다. 기다렸을 때 얻을 볼넷의 가능성도 바꾼다. 그래서 카운트의 공격가치가 높다는 사실과 스윙의 가치가 높다는 사실은 구분해야 한다.

## 8. 같은 1-1이라도 도달 경로가 다르면 성적이 다를까?

### Thanks for the memories

**Sal Baxamusa (2007) · [원문](https://tht.fangraphs.com/thanks-for-the-memories/) · 배치: 5절, BCAI가 압축한 정보**

2006년 Retrosheet 자료에서 첫 두 공이 볼→스트라이크(BS)인지 스트라이크→볼(SB)인지 비교한다. 1-1 이후 동일하게 진행된 일부 경로를 맞춰 보며, 초반 순서 차이가 가까운 후속 결과에서 나타나는지 살핀다.

### 원문에서 확인한 작은 결과 표

**표 A: 1-2에서 인플레이로 끝난 경우. X는 인플레이 타구를 뜻한다.**

| 앞선 순서 | 타구 기준 AVG | ISO |
| --- | ---: | ---: |
| BSSX: 볼→스트라이크→스트라이크→인플레이 | .292 | .142 |
| SBSX: 스트라이크→볼→스트라이크→인플레이 | .322 | .151 |

**표 B: 1-1 뒤 세 공 이상 더 이어진 타석. 표 A와 분모가 다르다.**

| 첫 두 공 | AVG | OBP | ISO |
| --- | ---: | ---: | ---: |
| BS | .214 | .348 | .130 |
| SB | .212 | .342 | .132 |

초기 SB 경로의 우세는 가까운 일부 비교에서 나타나지만, 2-2 비교는 1표준편차 안의 차이였고 더 오래 이어진 타석에서는 뚜렷한 우세가 남지 않았다. **같은 카운트의 경로에 정보가 더 있을 수 있지만, 그 차이가 모든 상황에서 크고 지속적인 것은 아니다**라는 정도로 결론을 잡는다.

**칼럼용 문단.**

> 카운트가 같으면 지나온 길도 잊어도 될까. 2006년 자료를 비교한 분석에서는 첫 두 공의 순서에 따라 가까운 후속 성적이 달랐다. 다만 공이 더 오간 뒤에는 차이가 뚜렷하게 남지 않았다. 카운트는 유용한 요약이지만, 이전 투구의 모든 정보를 보존하는 표는 아니다.

이것은 2006년의 외부 분석 결과다. 우리 2024~2025 BCAI의 경로별 W를 새로 추정한 것이 아니다. 타구 기준 안타율의 차이를 타석 전체 가치 차이 또는 경로의 인과효과로 부르지 않는다. 직접 분석을 대신해 질문에 제한된 답을 주는 용도로 사용한다.

## 9. 좋은 공만 반복하면, 상대도 그대로일까?

### Professionals Do Not Play Minimax: Evidence from Major League Baseball and the National Football League

**Kenneth Kovash·Steven D. Levitt (2009) · [NBER 공식 전문 PDF](https://www.nber.org/system/files/working_papers/w15347/w15347.pdf) · 배치: 5절 핵심 논의**

2002~2006년 MLB 약 311만 투구를 사용한다. 직구·체인지업·슬라이더·커브 등의 선택을 비교하고, 특정 구종의 상대적 성과와 순서의 독립성이 미니맥스 조건과 맞는지 검토한다. 성과 계산에 쓰인 종료 투구와 이어진 투구의 구분은 중요하다. 종료 타석 결과에 가중치를 준 OPS 계열 척도이며 우리 W가 아니다.

원문 표 3에서 직구와 체인지업 성과 차이는 카운트 등을 통제한 뒤에도 남는다. 저자는 구종의 보수가 평준화되지 않은 점과 직전 구종 뒤 전환이 지나치게 나타나는 패턴을 근거로 모형이 요구한 혼합과 실제 선택의 불일치를 보고한다. ‘프로가 무작위 선택을 못 한다’라는 일반적 심리 진단으로 옮기지 않는다.

직구 비중을 10%p 줄이는 계산에서 시즌 약 15실점 감소를 제시하지만, **타자가 대응하면 이득이 줄어드므로 저자 자신이 상한으로 설명한다.** 이 점이 우리 0-2 해석에 특히 직접 연결된다.

### Professionals do play Minimax: Revisiting the Nash equilibrium in Major League Baseball — 전문 확인 전 조건부

**Jean-François Mercier (2024) · [출판사 초록](https://www.sciencedirect.com/science/article/pii/S2773161824000168)**

초록은 2010~2022년 자료, 스윙/테이크와 존 안/밖의 2×2 행동 정의, 관측되지 않은 선택 결과를 추정하는 접근을 설명한다. 대부분의 비교에서 보수 평준화와 순서 독립성에 부합하는 결과를 보고하지만, 이것을 모든 실제 선택이 이론적 최적 비율과 정확히 같았다는 뜻으로 읽으면 안 된다. 상세 모형·검정과 결론의 범위는 전문 확보 후 확인해야 한다.

| 함께 읽을 점 | 2009 연구 | 2024 연구 |
| --- | --- | --- |
| 기간 | 2002~2006 | 초록상 2010~2022 |
| 주된 행동 구분 | 구종 선택 | 초록상 위치×스윙/테이크 |
| 보수·모형 | 종료 결과의 OPS 계열 비교 등 | 전문 확인 후 상세 확정 |
| 보고 결론 | 검토한 미니맥스 조건과 불일치 | 초록상 대체로 조건에 부합 |
| 칼럼 의미 | 관측 빈도와 이론의 차이 | 무엇을 행동으로 정의하느냐도 중요 |

**두 논문으로 ‘15년 동안 야구가 시스템화되어 균형에 도달했다’고 말할 수는 없다.** 기간뿐 아니라 행동·추정·검정이 달라졌다. 시간 변화 가설을 검증하려면 같은 방법을 양 시기에 적용해야 한다. 2024년 논문은 더 최근의 실증연구이지 미니맥스라는 이론 자체가 새로 생긴 것은 아니다.

**칼럼용 문단.**

> 0-2에서 존 밖 공의 평균 결과가 좋았다고 해서 모든 공을 밖으로 던져도 같은 이익이 남지는 않을 것이다. 타자가 그 규칙을 알면 스윙을 줄일 수 있다. 가위가 잘 통했던 기록만 보고 다음에도 가위만 내는 것과 비슷하다. 전략을 섞는다는 것은 평균적으로 좋은 선택을 포기하는 일이 아니라, 상대의 대응까지 포함해 그 가치를 지키는 문제다.

이는 게임이론을 적용한 해설이다. **현재 BCAP가 최적 혼합비율을 추정했다는 뜻이 아니다.** 2024 연구의 상세 인용은 전문 확보 전까지 출판용 본문에서 보류한다.

## 10. 강화학습은 무엇을 더하나?

### MONEYBaRL: Exploiting pitcher decision-making using Reinforcement Learning

**Gagan Sidhu·Brian Caffo (2014) · [공개 전문 v1](https://arxiv.org/html/1407.8392v1) · 배치: 5절 짧은 방법 사례**

2008~2010년 25명 투수의 자료로 타석을 상태·행동·전이·보상으로 표현한다. 단일 투구의 결과만이 아니라 이후 카운트까지 이어질 가치를 계산해 스윙/테이크 정책을 비교한다. BCAP와 ‘다른 행동을 했으면 어땠을까’라는 질문은 가깝지만, 타석 전체의 정책을 갱신·평가하는 강화학습과 관측 행동 평균을 보정하는 현 BCAP는 같지 않다.

**실제 결과를 정확히 읽기.** 150개 연도 간 비교 중 87개에서 제안 전략이 비교 전략보다 **더 좋거나 같았다**. ‘87번 승리’로 바꾸면 안 된다. 복잡한 모형의 특정 CRLIB 비교에서는 p=.03을 보고하지만 다른 검정까지 모두 유의했다고 쓰지 않는다.

**가장 중요한 가정.** 해당 정책 평가에는 현재 구종을 정확히 안다는 정보 가정이 들어간다. 이후 궤적 인식 시뮬레이션도 별도로 다룬다. 따라서 87/150을 ‘타자가 실제 경기에서 이 방법을 쓰면 이길 확률’로 옮길 수 없다.

**칼럼용 문단.**

> 타석을 여러 번의 선택으로 풀어 정책을 계산한 연구도 있다. 다만 어떤 공인지 알고 고르는 모형과 날아오는 공을 보고 결정하는 실제 타격은 조건이 다르다. 선택의 이론적 가치를 계산하는 일과 그 정보를 경기 중에 사용할 수 있는지는 구분해야 한다.

개별 선수 정책·랭킹은 빼고, **한 공 비교에서 타석 전체의 정책으로 확장할 때 필요한 정보와 가정**을 설명하는 데 사용한다.

## 11. 중간에 쉬어갈 이야기: 삼진이 네 스트라이크였다면?

### The Impact of the One-Off 1887 Four-Strike Strikeout

**Woody Eckard (2022) · [원문](https://sabr.org/journal/article/the-impact-of-the-one-off-1887-four-strike-strikeout/) · 배치: 2절 끝의 짧은 역사 박스**

1887년에는 삼진에 네 스트라이크가 필요했다. 연구는 동시기 규칙 변화를 고려해 주로 1888년과 비교하고, 당시 볼넷을 안타로 세던 기록 방식도 일반적인 타율 기준으로 조정한다.

비교에서 4스트라이크 시즌의 경기당 삼진은 약 1개 적고, 안타는 두 리그에서 1.22개·1.47개, 득점은 1.54점·1.46점 더 많았다. 저자는 스트라이크 한 번의 여유가 공격 양상에 영향을 줬다고 해석한다. 당시 리그의 변화와 역사적 비교이므로 현대 MLB에 네 스트라이크를 적용하면 정확히 같은 수치가 된다는 예측은 아니다.

**칼럼용 박스.**

> 지금의 카운트 표는 자연법칙이 아니라 규칙이 만든 구조다. 1887년 야구에서는 스트라이크를 네 번 받아야 삼진이었다. 그 한 번의 여유가 있었던 시즌은 삼진이 적고 안타와 득점이 많았다. 오늘날 2스트라이크의 압박도 세 번째 스트라이크가 타석을 끝낸다는 규칙에서 출발한다.

박스는 짧게 두고 0-2 위치 분석으로 돌아간다. 저자의 장타 접근 해석을 타자의 실제 의도 측정으로 서술하지 않는다.

## 12. 후속 KBO 분석에서 쓸 자료

### Commanding the Zone

**Josh Weinstock (2011) · [원문](https://blogs.fangraphs.com/commanding-the-zone/) · 이번에는 마무리의 전망, 실행은 후속**

2011년 최소 100타자 상대 투수를 대상으로 인플레이를 제외한 투구의 선형가치를 100구당으로 비교한다. FIP와 상관 .65, K−BB/PA와 −.94를 보고한다. 이 지표는 카운트를 유리하게 진행시키는 투구 과정과 결과 지표가 연결됨을 보여준다. 의도한 목표 위치와의 오차를 직접 잰 제구 지표는 아니다.

**KBO에 가져올 질문.** 강투수는 어떤 카운트로 자주 앞서 나가는가? 강타자는 어떤 카운트에서 불리한 진행을 줄이는가? 똑같이 불리한 카운트에 도달했을 때의 회복은 어떻게 다른가? 이번 BCAI·BCAP의 일반 패턴을 집단 특성으로 확장할 수 있다.

‘강한 선수’의 정의를 같은 카운트 지표로 만든 뒤 그 지표가 높다고 결론 내리면 순환 논리가 된다. 별도 기간·외부 성과로 집단을 먼저 정하고 기회·리그·측정 차이를 보정하는 설계가 필요하다. 이번에 KBO 데이터를 수집하거나 선수 순위를 만들지는 않았다.

RE24는 주자·아웃카운트에 관한 **다음 칼럼 후보 자료**로 넘긴다. 새 칼럼 번호·가설·분석 결과를 여기서 확정하지 않는다.

## 13. 제외 결정과 전체 45건의 최종 분류

개별 타자의 순간 판단·스윙 동작·인지·개인 맞춤 채점은 이번 본문에서 줄인다. BART·최적 투구·MONEYBaRL은 사용자가 선택한 방법론이므로 일반적 비교 구조와 한계를 가져온다. 그 논문들의 개인별 응용은 가져오지 않는다.

특히 *Using PITCHf/x to model the dependence of strikeout rate on the predictability of pitch sequences*는 투구 연속성의 예측 가능성과 삼진율에 관한 연구지만, 이번 카운트의 평균 가치 설명에 직접 연결하기가 약하다. 쓸모없는 연구라는 판정 없이 본문에서 제외한다. 경로 질문은 더 직접적인 *Thanks for the memories*로 처리한다.

아래 분류가 기존 45건 해설집의 ‘핵심/보충’ 분류보다 우선한다. 기존 해설집은 자료 보존용이다.

### 이번 본문 — 12건

- [Batting Average by Count and Pitch Type](https://sabr.org/journal/article/batting-average-by-count-and-pitch-type/) — Dean Stotz·J. Eric Bickel (2002)
- [The Importance Of Strike One (and Two, and Three…), Part 2](https://tht.fangraphs.com/the-importance-of-strike-one-part-two/) — Craig Burley (2004)
- [Evaluating plate discipline in Major League Baseball with Bayesian Additive Regression Trees](https://arxiv.org/html/2305.05752v2) — Ryan Yee·Sameer K. Deshpande (2023 원고; 2024 학술지)
- [Computing an Optimal Pitching Strategy in a Baseball At-Bat](https://arxiv.org/html/2110.04321v1) — Connor Douglas·Everett Witt·Mia Bendy·Yevgeniy Vorobeychik (2021)
- [How Should Pitchers Approach 0-2 Counts?](https://blogs.fangraphs.com/how-should-pitchers-approach-0-2-counts/) — Carmen Ciardiello (2021)
- [A pitch is a terrible thing to waste. Or is it? (Part 1)](https://tht.fangraphs.com/a-pitch-is-a-terrible-thing-to-waste-or-is-it-part-1/) — Dan Turkenkopf (2009)
- [Taking the close pitch with two strikes](https://tht.fangraphs.com/Taking-the-close-pitch-with-two-strikes/) — James Gentile (2013)
- [Should One Strike Make This Much Difference?](https://tht.fangraphs.com/should-one-strike-make-this-much-difference/) — Neil Weinberg (2015)
- [Thanks for the memories](https://tht.fangraphs.com/thanks-for-the-memories/) — Sal Baxamusa (2007)
- [Professionals Do Not Play Minimax: Evidence from Major League Baseball and the National Football League](https://www.nber.org/papers/w15347) — Kenneth Kovash·Steven D. Levitt (2009)
- [MONEYBaRL: Exploiting pitcher decision-making using Reinforcement Learning](https://arxiv.org/abs/1407.8392) — Gagan Sidhu·Brian Caffo (2014)
- [The Impact of the One-Off 1887 Four-Strike Strikeout](https://sabr.org/journal/article/the-impact-of-the-one-off-1887-four-strike-strikeout/) — Woody Eckard (2022)

### 본문 조건부: 전문 추가 확보 — 1건

- [Professionals do play Minimax: Revisiting the Nash equilibrium in Major League Baseball](https://www.sciencedirect.com/science/article/pii/S2773161824000168) — Jean-François Mercier (2024)

### KBO 후속 분석 — 1건

- [Commanding the Zone](https://blogs.fangraphs.com/commanding-the-zone/) — Josh Weinstock (2011)

### 이번 정의·데이터 각주 — 5건

- [wOBA](https://library.fangraphs.com/offense/woba/) — FanGraphs
- [Plate Discipline](https://library.fangraphs.com/offense/plate-discipline/) — FanGraphs
- [Statcast CSV Documentation](https://baseballsavant.mlb.com/csv-docs) — Baseball Savant
- [Event Files](https://www.retrosheet.org/eventfile.htm) — Retrosheet
- [Player Splits Tool](https://library.fangraphs.com/features/player-splits-tool/) — FanGraphs

### KBO 제도 배경 보존 — 4건

- [Analyzing the Impact of the Automatic Ball Strike System in Professional Baseball through a Case Study on KBO League Data](https://arxiv.org/abs/2407.15779) — Kichang Lee·Kyungsik Han·JeongGil Ko (2024; 2025 개정)
- [Auditing Contextual Bias in Human Ball-Strike Calls Using KBO’s Automated Umpiring Transition](https://arxiv.org/abs/2609.03786) — Kichang Lee·JeongGil Ko (2026-09-03)
- [2025 리그 규정·주요 변경 사항](https://www.koreabaseball.com/Kbo/League/GameManage2025.aspx) — KBO (2025)
- [ABS Challenge Dashboard](https://baseballsavant.mlb.com/abs) — Baseball Savant

### 다음 칼럼 후보 — 1건

- [RE24](https://library.fangraphs.com/misc/re24/) — FanGraphs

### 이번 사용 제외·자료집 보존 — 21건

- [Study of ‘The Count’ Yields Fascinating Data](https://sabr.org/journal/article/study-of-the-count-yields-fascinating-data/) — Stanley M. Katz (1986)
- [Run Value (기존 swing-take 주소)](https://baseballsavant.mlb.com/leaderboard/swing-take) — Baseball Savant
- [On the Decision to Take a Pitch](https://pubsonline.informs.org/doi/10.1287/deca.1090.0145) — J. Eric Bickel (2009)
- [Quantifying Swing Decisions: An Individualized Approach](https://drivelinebaseball.com/blogs/blog/quantifying-swing-decisions-an-individualized-approach) — Driveline Baseball (2019)
- [Changing Up With the Count 3-0](https://blogs.fangraphs.com/changing-up-with-the-count-3-0/) — Drew Fairservice (2014)
- [Swinging, Fast and Slow: Interpreting variation in baseball swing tracking metrics](https://arxiv.org/html/2507.01238v1) — Scott Powers·Ronald Yurko (2025)
- [Do hitters have a 2-strike approach? Data says Yes!](https://www.mlb.com/news/mlb-hitters-have-a-two-strike-approach-at-the-plate) — Mike Petriello (2024)
- [Strategic Pitch Location: The Role of Two-Pitch Sequences in Pitching Success](https://sabr.org/journal/article/strategic-pitch-location-the-role-of-two-pitch-sequences-in-pitching-success/) — John Z. Clay (2023)
- [Using PITCHf/x to model the dependence of strikeout rate on the predictability of pitch sequences](https://journals.sagepub.com/doi/10.3233/JSA-170103) — Glenn Healey·Shiyuan Zhao (2017)
- [Hit Probability as a Function of Foul-Ball Accumulation](https://sabr.org/journal/article/hit-probability-as-a-function-of-foul-ball-accumulation/) — Jeffrey N. Howard (2018)
- [Investigating the Importance of Pitch Selection with Clustering](https://tht.fangraphs.com/investigating-the-importance-of-pitch-selection-with-clustering/) — Peter L’Oiseau (2019)
- [Counterfactual Optimization of Baseball Pitch Sequences and Estimation of Its Impact on Season-Level Statistics](https://arxiv.org/abs/2606.17345) — Ryota Takamido·Hiroki Nakamoto (2026-06-15)
- [Baseball, An Extensive-Form Game-Theoretic Duel](https://arxiv.org/abs/2607.29041) — Sebastian E. Ferrando·Eli Kohn (2026-07-31)
- [Integrating visual trajectory and probabilistic information in baseball batting](https://www.sciencedirect.com/science/article/pii/S1469029217306775) — Rob Gray·Rouwen Cañal-Bruland (2018)
- [‘Markov at the Bat’: A Model of Cognitive Processing in Baseball Batters](https://journals.sagepub.com/doi/10.1111/1467-9280.00495) — Rob Gray (2002)
- [Contextual influences on baseball ball-strike decisions in umpires, players, and controls](https://vuir.vu.edu.au/3800/) — Clare MacMahon·Janet L. Starkes (2008)
- [What Does it Take to Call a Strike? Three Biases in Umpire Decision Making](https://www.sloansportsconference.com/research-papers/what-does-it-take-to-call-a-strike-three-biases-in-umpire-decision-making) — Etan Green·David Daniels (2014)
- [Decision Making Under the Gambler’s Fallacy: Evidence from Asylum Judges, Loan Officers, and Baseball Umpires](https://academic.oup.com/qje/article/131/3/1181/2590011) — Daniel L. Chen·Tobias J. Moskowitz·Kelly Shue (2016)
- [A Hierarchical Bayesian Model of Pitch Framing](https://arxiv.org/abs/1704.00823) — Sameer K. Deshpande·Abraham J. Wyner (2017)
- [순차패턴마이닝 기법을 활용한 상황별 볼넷 구종패턴 분석](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002951027) — 김주학·강지연·조선미·노갑택 (2023)
- [머신러닝(XGBoost)기반 미국프로야구(MLB)의 투구별 안타 및 홈런 예측 모델 개발](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002951025) — 조선미·김주학·강지연·김상균 (2023)

## 14. 발행 전 남은 확인

- Mercier 2024 전문을 확보하면 2009 연구와 같은 항목으로 방법·검정·한계를 비교한다. 확보 전에는 초록 범위를 넘는 내용을 넣지 않는다.
- 새 상태 전이·사건 분해·상대 반응 분석은 다른 작업의 결과가 생긴 뒤 개요에 추가한다. 지금은 제안이다.
- 역사·경로·외부 투구 비교 수치에는 원래 기간·분모·단위를 붙인다. 현재 BCAI/BCAP 값과 합산하지 않는다.
- 로컬 문서만 수정했다. 공동 문서 업로드·외부 발행은 수행하지 않았다.

