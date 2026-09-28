# 네이버 원고 3편 — 원문 재열람 및 인용 검수

작성일: 2026-09-18. 대상: 볼카운트 분석 칼럼, BCAI 설명, BCAP 설명. 이 문서는 집필 검수 기록이며 블로그 본문은 아니다.

## 확인 기준

기존 문헌 해설의 ‘읽음’ 표시를 재사용하지 않고, 이번 작업에서 원문을 다시 열어 저자의 본문·방법·결론·한계를 확인했다. 기존 본문 후보 12건의 원문 본문을 확인했다. HTML 논문은 저자가 제공한 해당 버전의 본문을 읽었고, Kovash·Levitt는 보관 중인 공식 NBER 원본 PDF 36쪽을 읽었다. 원자료 재분석이나 논문의 결과 재현을 수행했다는 뜻은 아니다.

텍스트로 제공된 표는 함께 읽었다. 이미지로만 된 모든 그림을 별도로 판독했다는 뜻은 아니며, 그런 그림의 미확인 세부 수치를 인용하지 않는다. MONEYBaRL의 별도 보충자료는 읽지 않았다. BART는 공개 v2와 그 안의 부록을 읽었으며, 학술지 최종판과 동일하다고 단정하지 않는다. 웹에서 실패한 주소는 접근 실패로 기록하고, 그 이유가 유료벽·삭제·만료라고 추정하지 않는다.

사용자 최신 요청에 따라 **원문 전문을 확인하지 못한 논문은 초록만으로도 원고에 사용하지 않는다.** 기존 MD의 Mercier 2024 조건부 사용 지침보다 이 요청이 우선한다.

## 기존 기록에서 바로잡을 사항

1. **Burley의 ‘strike’에는 인플레이 타구가 포함된다.** 따라서 이 글의 비교를 BCAP 후속 분석의 ‘실제 볼 대 실제 스트라이크 상태 전이’와 같은 계산으로 소개하지 않는다. 2스트라이크 파울도 제외되어 있다.
2. **MONEYBaRL의 성과 횟수에는 동률이 포함된다.** 본문과 표의 합계에도 차이가 있어 원고에서는 횟수를 생략한다.
3. **Turkenkopf Part 1의 본문과 갱신 표의 표본 수가 다르다.** 수치는 생략하고 투구의 정의 차이만 쓴다. 미열람 Part 2는 인용하지 않는다.
4. **최적 투구 논문을 ‘BCAP와 똑같이 실패한 연구’로 묘사하지 않는다.** 상대 대응을 모형에 포함한 연구다. 모형의 최적값과 실전에서 검증된 전략을 구별한다.
5. **Mercier 2024는 원고와 사용 문헌 목록에서 제외한다.** 2009년 연구와 대비해 야구의 발전·시스템화를 입증하는 서사는 사용하지 않는다.

## 원문 12건의 사용 범위

### 1. Stotz·Bickel (2002)

[Batting Average by Count and Pitch Type](https://sabr.org/journal/article/batting-average-by-count-and-pitch-type/)

- 읽은 범위: SABR 원문 전체 본문과 주석. 표본·분모 설명 및 마지막 해석까지 확인.
- 사용: 종료 카운트별 타율은 삼진이 들어가는 분모가 달라, 낮은 2스트라이크 타율만으로 조기 스윙의 이점을 결론 내릴 수 없다.
- 제한: 1998~2001년 스탠퍼드와 상대 팀의 대학야구 자료다. 현대 MLB의 결과나 ‘2스트라이크는 불리하지 않다’는 결론으로 바꾸지 않는다. 스윙 정책의 인과 효과를 추정한 연구가 아니다.
- 배치: 1편 도입의 분모 설명.

### 2. Burley (2004)

[The Importance Of Strike One (and Two, and Three…), Part 2](https://tht.fangraphs.com/the-importance-of-strike-one-part-two/)

- 읽은 범위: 본문과 모든 수치 표, 계산 정의·2스트라이크 파울 예외·마지막 논의.
- 사용: 한 번의 가치와 발생 빈도를 구분하는 사례.
- 제한: 위 분류 주의사항을 따른다. 자체 상태 차이와 계산이 다르며 코칭 권고의 인과 증거가 아니다.
- 배치: 1편 카운트 가치.

### 3. Yee·Deshpande (2023 공개 v2)

[Evaluating plate discipline in Major League Baseball with Bayesian Additive Regression Trees](https://arxiv.org/html/2305.05752v2)

- 읽은 범위: §§1~5.1, 참고문헌, 부록 §§6.1~6.3. 공개 v2 기준.
- 사용: 사건 확률과 남은 반이닝 기대득점의 결합, 불확실성 전파.
- 제한: BCAP W와 목표값이 다르다. 득점 단계는 선수·위치 효과를 단순화한다. 실제 정책 변경 실험이 아니며, 타자의 지각 정보와 사후 위치도 구별한다. 개인 순위는 제외한다.
- 배치: 1편과 BCAP 설명의 짧은 방법 비교. 같은 연구 해설을 두 글에 길게 반복하지 않는다.

### 4. Douglas 외 (2021)

[Computing an Optimal Pitching Strategy in a Baseball At-Bat](https://arxiv.org/html/2110.04321v1)

- 읽은 범위: §§1~6, 모형·자료·실험 및 참고문헌.
- 사용: 카운트, 구종, 목표 위치, 타자의 대응을 함께 둔 확률적 게임에서 최적 정책을 계산한다.
- 제한: 목표는 출루율 최소화다. 안타 종류별 W를 비교하는 BCAP와 다르다. 목표 위치는 관측하지 못해 3-0 자료와 제구 오차 가정을 이용한다. 예측 출루율 개선은 실제 정책 변경 실험이 아니다. ‘상대 대응을 무시했다’거나 ‘실패했다’고 쓰지 않는다.
- 배치: 1편 배합 설명 및 BCAP에서 최적 정책과의 차이.

### 5. Ciardiello (2021)

[How Should Pitchers Approach 0-2 Counts?](https://blogs.fangraphs.com/how-should-pitchers-approach-0-2-counts/)

- 읽은 범위: 본문 전체, 2019~2020년 결과 표, 선택 편향 및 타자 적응 논의.
- 사용: 0-2에서 존 밖·안 투구의 볼, 타구, 헛스윙과 관측 가치가 다르게 구성된다. 저자 역시 무조건 존 밖에 던지라는 결론을 피한다.
- 제한: 여기의 waste는 Gameday 존 밖 전체다. ‘아주 멀리 버린 공’으로 바꾸지 않는다. 관측 run value를 BCAP W나 BCAI 포인트와 합산하지 않는다. 상대가 대응해도 이득이 유지된다는 증거가 아니다.
- 배치: 1편 0-2 위치 사례.

### 6. Turkenkopf (2009), Part 1

[A pitch is a terrible thing to waste. Or is it? (Part 1)](https://tht.fangraphs.com/a-pitch-is-a-terrible-thing-to-waste-or-is-it-part-1/)

- 읽은 범위: 본문 전체·구역 정의·텍스트 표·업데이트. 이미지 위치도의 세부 값은 미사용.
- 사용·제한: 멀리 벗어난 투구의 정의만 소개한다. 집단 차이를 전략 변경 효과로 해석하지 않는다. 수치 불일치와 Part 2 제외는 상단 기록 참조.

### 7. Gentile (2013)

[Taking the close pitch with two strikes](https://tht.fangraphs.com/Taking-the-close-pitch-with-two-strikes/)

- 읽은 범위: 저자 본문 전체와 표. 독자 댓글은 검증 근거로 사용하지 않음.
- 사용: 2010~2013년 존 경계 투구에서 2스트라이크의 볼 수에 따라 스윙률이 달라진다는 행동 자료다.
- 제한: 경계 공의 스윙/테이크 가치나 최적 스윙률을 직접 추정한 연구가 아니다. 테이크된 공의 루킹 스트라이크율에는 선택 과정이 들어 있다. 선수·팀 순위와 성공 원인의 단정은 제외한다.
- 배치: 1편 2스트라이크 타자 대응.

### 8. Weinberg (2015)

[Should One Strike Make This Much Difference?](https://tht.fangraphs.com/should-one-strike-make-this-much-difference/)

- 읽은 범위: 본문 전체, 3-0/3-1 비교 표, 고의4구·선수 선택·감독 지시와 상대 적응 논의.
- 사용: 2007~2014년 3-0과 3-1에서 큰 스윙률 차이를 관찰하고 그 이유를 질문한다.
- 제한: 실제 3-0 스윙은 타자와 공이 선택된 표본이다. 감독의 그린라이트도 관측되지 않는다. 저자도 탐색적 논의라고 선을 긋는다. ‘3-0에서 더 휘둘러야 한다’는 검증된 처방으로 쓰지 않는다.
- 배치: 1편 3볼 사례의 질문 제기.

### 9. Baxamusa (2007)

[Thanks for the memories](https://tht.fangraphs.com/thanks-for-the-memories/)

- 본문 전체·텍스트 수치 재열람. 도식 이미지 접근 실패. 수치·분모·일반화 한계는 1편 해당 단락 참조.

### 10. Kovash·Levitt (2009)

[Professionals Do Not Play Minimax: Evidence from Major League Baseball and the National Football League — 원본 PDF](https://www.nber.org/system/files/working_papers/w15347/w15347.pdf)

- 읽은 범위: `tmp/pdfs/kovash_levitt_2009.pdf` 36쪽 전체의 원문 텍스트. MLB 본문 PDF 6~15쪽과 표 26~30쪽을 중점 확인했으며, 10·28쪽은 렌더링 이미지로 재확인. 새 웹 접속은 실패했으나 기존 보관본의 공식 표지와 내용으로 원문을 읽음.
- 사용: 2002~2006년 MLB 투구 선택의 미니맥스 예측 이탈을 다룬 NBER 워킹페이퍼다.
- 제한: 현재의 구종 분류·W와 다르다. 타석 종료 투구의 비교와 상대 적응 가정이 있다. 저자도 고정된 가치 차이를 가정한 개선량을 상한으로 설명한다. 현재 MLB의 최적 비율이나 역사적 발전을 입증하지 않는다. NBER 최종 학술지 논문으로 표기하지 않는다.
- 배치: 1편 배합에서 역사적 연구 한 사례.

### 11. Sidhu·Caffo (2014)

[MONEYBaRL: Exploiting pitcher decision-making using Reinforcement Learning](https://arxiv.org/html/1407.8392v1)

- 읽은 범위: 공개 v1 §§1~6, 표, 본문에 포함된 야구 용어 부록. 별도 보충자료는 미열람.
- 사용: 한 공 비교와 타석 전체 정책의 차이를 설명하는 사례.
- 제한: 평가 시 구종을 안다는 가정, 희소 상태·결측·시뮬레이션 처리 한계가 있다. 성과 횟수는 상단 기록대로 제외한다. 선수 순위·실전 승리 확률로 옮기지 않는다.
- 배치: 1편 또는 BCAP 설명에서 방법론 한 문단.

### 12. Eckard (2022)

[The Impact of the One-Off 1887 Four-Strike Strikeout](https://sabr.org/journal/article/the-impact-of-the-one-off-1887-four-strike-strikeout/)

- 읽은 범위: 본문 전체와 주석. 본문에 명시된 수치만 확인 자료로 사용하며 이미지 표의 추가 값을 옮기지 않음.
- 사용: 1887년 네 스트라이크 삼진 규칙을 1888년과 비교한 역사적 연구. 카운트 가치가 규칙에 의존한다는 짧은 예시다.
- 제한: 1887년에는 다른 규칙도 바뀌어 1886년과의 단순 비교를 피한다. 볼넷을 안타로 세던 당시 기록도 조정한다. 규칙 변경의 대칭성·적응 잔류 등 가정과 당시 파울 규칙 차이가 있다. 현대 MLB에 같은 수치가 재현된다는 예측으로 쓰지 않는다.
- 배치: 1편 카운트 가치 뒤 짧은 역사 박스.

## 용어·데이터 문서와 후속 자료

다음은 원문 논문 12건과 별도다. 데이터 사전은 해당 변수 정의를 확인하는 문서이며 전체 949행 등을 모두 읽은 것으로 기록하지 않는다.

| 자료 | 이번 읽은 범위 | 허용되는 사용 |
|---|---|---|
| [FanGraphs wOBA](https://library.fangraphs.com/offense/woba/) | 정의·공식·사용법·주의사항의 본문 | 연도별 가중치와 출루율 척도를 가진 지표. 원 단위 득점과 구별. 자체 W의 분모는 프로젝트 명세로 별도 설명 |
| [FanGraphs Plate Discipline](https://library.fangraphs.com/offense/plate-discipline/) | 정의 표부터 주의사항·읽을거리까지 본문 | SwStr%의 분모는 전체 투구, whiff rate는 스윙. 존 정의와 자료 출처 차이에 유의 |
| [FanGraphs Player Splits Tool](https://library.fangraphs.com/features/player-splits-tool/) | 저자 본문 전체 | 스플릿은 플레이 단위이며 필터와 그룹 구분이 다름. 이번 결과의 직접 재검산 근거는 아님 |
| [Statcast CSV Documentation](https://baseballsavant.mlb.com/csv-docs) | balls, strikes, type, zone, plate_x, plate_z, sz_top, sz_bot, woba_value, woba_denom 정의 | 카운트는 투구 전 상태. 2025년까지 앞면, 2026년부터 가운데 면의 좌표로 바뀌며 존 상하단 정의도 달라짐. 2026 위치 분석에 별도 비교가 필요한 이유 |
| [Retrosheet Event Files](https://www.retrosheet.org/eventfile.htm) | 문서 도입, play 레코드, pitch sequence 및 관련 예시 | 카운트·투구순서 필드와 결측 의미 확인. 단순 B/S 경로는 별도 요약 표기이며 원본 코드 전체와 같지 않음 |
| [Weinstock (2011), Commanding the Zone](https://blogs.fangraphs.com/commanding-the-zone/) | 저자 본문·표·참고자료 전체 | 인플레이 제외 카운트 선형가치와 성과의 연관 사례. 실제 목표 위치 오차를 잰 제구 측정이 아니며 KBO 결과도 아님 |

후속 KBO의 강투수·강타자 집단은 별도 기간이나 외부 성과로 먼저 정의해야 한다. 같은 카운트 지표로 집단을 선정한 뒤 그 지표가 높다고 결론 내리는 구조는 피한다. KBO 자료 수집·분석·선수 순위 작성을 이번 원고가 완료한 것처럼 쓰지 않는다.

## 원문 미확인으로 제외

**Jean-François Mercier (2024), Professionals do play Minimax: Revisiting the Nash equilibrium in Major League Baseball.** [출판사 주소](https://www.sciencedirect.com/science/article/pii/S2773161824000168) 및 [기존 공유 주소](https://authors.elsevier.com/a/1jgIm9sYqDR9Ye)를 이번에 열었으나 원문을 읽을 수 없었다. 두 호출 모두 접근 도구 오류였으므로 원인을 단정하지 않는다. 제목·초록·기존 해설에 기대어 결과를 사용하지 않는다. 이 검수 기록의 제외 목록에만 남긴다.

기존 자료집에서 제외·보존·차기 후보로 분류한 나머지 논문은 이번에 새로 전문을 읽은 것이 아니다. 별도의 원문 확인 없이 이번 원고의 추가 근거로 가져오지 않는다. 특히 투구 순서 예측가능성·심판 편향·인지·스윙 동작·개인 맞춤 평가를 이번 범위에 다시 넣지 않는다.

## 사용자 피드백 반영 확인

- 상세 개요의 여섯 절을 문헌 나열식으로 바꾸지 않는다. 자료는 자체 분석의 질문과 해석을 돕는 위치에 짧게 배치한다.
- 자체 관측값, 보정값, 외부 연구 결과와 예시를 구분하고, 기간·분모·단위를 필요한 곳에 표시한다.
- BCAI 상태 지수, BCAP 행동 비교, 상대가 적응한 뒤의 최적 정책을 구별한다. 외부 논문이 현재 모형의 인과 타당성을 보증하는 것처럼 쓰지 않는다.
- 확장 분석의 완료 여부는 최신 실행 문서로 확인한다. 9월 17일 참고문헌 메모의 ‘후속 제안’ 상태를 최신 작업에 자동 적용하지 않는다.
- 경로의 외부 결과는 자체 재현과 구분하고, 모든 경로를 새로 모델링했다고 쓰지 않는다.
- 시행착오는 독자가 해석을 바꾸는 데 필요한 경우에 설명한다. 다른 논문의 성과를 임의로 실패라고 평가하지 않는다.
- 외부 원문 그림·표를 통째로 복제하지 않는다. 각 웹 출처의 총 요약 한도 200단어와 직접 인용 25단어 이내를 기준으로, 원고 세 편과 이 감사 기록을 합쳐 짧게 사용한다. 이 문서에는 긴 직접 인용을 넣지 않았다.

외부 게시·전송·Drive 업로드는 수행하지 않았다.


## 2차 원고의 독자용 해설

[한국어 해설](04_references_ko.md)을 추가했다. 이 검수 문서는 최초 열람 이력을 보존한다. 2차에서는 원문의 해당 정의·방법·결과를 재확인해 독자용 요약을 만들고, 별도의 가상 예시와 자체 분석 비교를 명확히 표시했다. 원문 전체를 번역·복제하거나 새로 원자료를 재분석한 문서는 아니다. 본문과 해설의 원문 의존 설명을 함께 고려해 제한하고, 원문 미확인 자료는 계속 제외한다.
