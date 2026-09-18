# 001. 출처와 데이터 확보 기록

## 2026-09-18 3차 문헌 배치 수정

[본문](publish/naver_20260918/01_ball_count.md)의 외부 문헌을 보라색 전용 상자로 분리했다. [한국어 해설](publish/naver_20260918/04_references_ko.md)은 기존 원문 결과·결론과 실제 인용 부분을 앞에 두고 자료·방법을 뒤에서 설명한다. 새 문헌·미열람 수치는 추가하지 않았다. 원문 링크·읽은 판본·제외 기준은 유지한다.

## 2026-09-18 독자용 한국어 문헌 해설 추가

[참고문헌 한국어 해설](publish/naver_20260918/04_references_ko.md)에 본문 사용 12건을 같은 번호로 연결했다. 저자 원문의 질문·자료·방법·결과와 칼럼에 가져온 부분을 구분하고, 별도 개념 설명·가상 예시는 원문 결과와 분리했다. 원문에 의존하는 요약은 인용 범위에 맞춰 제한하며 전문 번역을 만들지 않았다. 세 공개 연구 원고의 목표·가정·평가, 전문 매체 글의 분모·분류를 재확인했다. 원문 미확인 Mercier, Turkenkopf Part 2, MONEYBaRL 별도 보충자료는 제외를 유지한다. [수정 기록](publish/naver_20260918/revision_v2.md).

## 2026-09-18 실제 원고의 원문 재열람·사용 확정

[원문 확인 기록](publish/naver_20260918/reference_audit.md)에 이번 집필에서 다시 읽은 판본·범위·링크·주의사항을 저장했다. [본문](publish/naver_20260918/01_ball_count.md)에 실제 사용한 논문·분석 글은 12건이다. 공개 원문 본문을 확인해 사용했으며, NBER 2009는 기존 공식 PDF 사본을 직접 다시 읽었다. 초록만 확인한 Mercier 2024는 최신 사용자 지시에 따라 사용 문헌에서 제외했다. 이를 기존 개요의 ‘전문 확보 전 조건부’보다 우선하는 이번 원고 기준으로 삼는다.

Burley의 스트라이크 분류와 현재 상태 평균표를 구별했다. MONEYBaRL·Turkenkopf의 원문 내부 수치 불일치가 있는 숫자는 인용하지 않았고, Baxamusa의 경로 표는 본문에서 확인한 값만 사용하되 원본 도식 접근·표본 수 확인의 한계를 남겼다. BART는 실제 읽은 arXiv v2 판본으로 표시했다. 외부 결과와 자체 BCAP 검증을 혼합하지 않는다.

차트는 기존 OBS·S/B·SWING·STATE-DELTA 집계 파일을 읽어 만들었다. [입력 해시와 그림 목록](figures/naver_20260918/figure_manifest.json), [자체 수치 연결](publish/naver_20260918/manuscript_source_map.md)에 재사용 근거를 보관했다. 새 원본 확보·모델 재학습·재배포 조건의 새 판단·외부 업로드는 수행하지 않았다.

## 2026-09-17 후속 구현·간단한 확인 완료

[실행·입출력 해시](analysis/runs/bcap_followup__mlb_2024_2025__20260917__r01/manifest.json). 기존 2024·2025 S/B count_values.csv와 2023 values.csv를 재표시했다. 새 상태 차이는 기존 OBS의 시즌별 advantage_season_sensitivity.csv 원 W·PA 도달 분모를 사용했다. 새로운 원본이나 정제본은 만들지 않았고 기존 자료를 재수집하지 않았다. 2026 위치 측정 보류를 유지한다.

기존 [모델 발전 검토](model_research_followup_20260917.md)를 구현 기준으로 재사용했다. 지정 공개 원고의 BART §2.2·3·5.1, Douglas의 3-0 목표·구종별 Gaussian/카운트 공통 오차 가정, MONEYBaRL §4.1의 완전 구종 인식과 §4.2의 오류 시뮬레이션 구분을 확인했다. [BART v2](https://arxiv.org/html/2305.05752v2) · [Douglas v1](https://arxiv.org/html/2110.04321v1) · [MONEYBaRL v1](https://arxiv.org/html/1407.8392v1). 논문 재현·정책 효과 검증을 수행한 것은 아니다. 새 분해 실행은 명시적 모의 자료이며 실제 MLB 분석 결과와 구분한다.

새 산출물은 코드·모델 정의·문서·소형 집계 및 명시적 모의 예제다. 새 공유 제외 대상은 없으므로 guides/excluded_files.json은 변경하지 않았다.

아래는 앞선 자료 확인 시점의 기록이다.

## 2026-09-17 실사용 문헌 원문 접근 재확인

[실사용 문헌·상세 해설](references_in_use_20260917.md)의 확인표를 현재 접근 상태로 사용한다. 본문 12편·KBO 후속 1편·정의/자료 5건의 본문을 확인했다. 조건부 본문 1편인 Mercier (2024)는 출판사 초록 확인에 머물며, 출판사와 저자 공유 링크의 전문 요청이 차단됐다. 유료·만료 여부는 확정하지 않는다.

NBER 2009 문헌은 웹 열람 경로의 차단과 달리 공식 PDF 요청이 성공했고 본문·표·결론을 읽었다. BART는 arXiv v2, Douglas·MONEYBaRL은 v1 공개 원고 기준이다. 본문 확인은 원자료·코드 재현 또는 재배포 권한 확보를 뜻하지 않는다. 이번에는 공개 문헌만 열람했으며 투구 데이터·기존 실행을 새로 만들지 않았다.

원문 재확인 대상: R02·03·08·09·12·13·14·16·19·23·24·26·29·42와 정의/자료 R04·07·39·40·41. 전체 45건의 사용·제외 분류는 실사용 해설에 기록했다. 이전 날짜의 접근 기록은 당시 이력이다.

## 2026-09-17 참고문헌 결과·결론 재확인

[한국어 상세 해설집](reading_references_ko.md)의 45건을 내용·결과·저자 결론·칼럼 활용으로 개정했다. 핵심 10편의 실제 수치와 비교 조건을 보강했다. MONEYBaRL, Extensive-Form Duel, 프레이밍 v1, KBO ABS v2, KBO 맥락 편향 v1은 공개 본문 확인 범위를 갱신했고 해당 본문 링크와 버전은 해설 항목에 기록했다. 초록만 확인한 자료는 그 범위를 유지했다. 공식 규정·지표·도구에는 연구 결과를 만들어 붙이지 않았다. 새로운 데이터 수집·모델 실행은 없다.

읽기 안내(2026-09-17 심화 개정): [참고문헌 한국어 상세 해설집](reading_references_ko.md) · [미리보기](reading_references_ko.html). 45건의 한국어 설명·실제 결과·결론·칼럼 활용 위치를 정리했다. 일부 공개 본문을 추가 확인했으며 초록만 확인한 자료와 구별한다. 원문 전체의 직역본은 아니다. 서지·접근 범위의 기준은 아래 각 항목과 해설에 적은 버전이다.

<a id="ball-count-research-20260915"></a>

## 볼카운트 종합 문헌 조사 — 2026-09-15

사용자 요청에 따라 0-2 중심의 기존 개요를 넘어 **12카운트 전체**의 가치·투타 선택·구종·위치·경로·파울·인지·판정·ABS까지 조사했다. [주제별 자료집과 12카운트 색인](research_ball_counts_20260915.md).

아래 45건은 학술지 논문, 학회 자료, 공개 연구 원고, 전문 분석 및 공식 설명을 합한 수다. 모든 링크의 확인일은 2026-09-15다. ‘본문’은 관련 본문 확인이며 전체 부록·코드 재현을 뜻하지 않는다. 초록·발췌만 확인한 자료는 그렇게 표시했다. 원문을 재배포하지 않고 서지·요약·링크를 기록했다. 새 투구 데이터 수집이나 별도의 대량 수집·재배포 이용 조건 확인은 수행하지 않았다. 기존 원본·실행과 모델 검증 상태는 보존했다.

<a id="bc-r01"></a>

### R01. Stanley M. Katz (1986)

**[Study of ‘The Count’ Yields Fascinating Data](https://sabr.org/journal/article/study-of-the-count-yields-fascinating-data/)**

- 자료 유형·확인 범위: SABR 연구 글 · 본문.
- 내용·활용: 12카운트의 결과와 전이를 정리한 초기 연구. 오늘의 카운트 가치표를 역사 속에 놓는 데 유용하다.
- 해석·접근 한계: 당시 수집 표본과 평가 기준이다. 현재 MLB의 수치나 BCAI와 동일한 지표로 인용하지 않는다.

<a id="bc-r02"></a>

### R02. Dean Stotz·J. Eric Bickel (2002)

**[Batting Average by Count and Pitch Type](https://sabr.org/journal/article/batting-average-by-count-and-pitch-type/)**

- 자료 유형·확인 범위: SABR 연구 글 · 본문.
- 내용·활용: Stanford 1998~2001년 대학야구 자료. 카운트별 타율과 구종을 함께 살피며 타석이 끝난 카운트로 계산한 타율의 해석 문제를 보여준다.
- 해석·접근 한계: 초구에 끝난 타수에는 삼진이 들어갈 수 없다. 초구 타율이 높다는 사실만으로 초구 스윙 확대의 효과를 결론 내릴 수 없다.

<a id="bc-r03"></a>

### R03. Craig Burley (2004)

**[The Importance Of Strike One (and Two, and Three…), Part 2](https://tht.fangraphs.com/the-importance-of-strike-one-part-two/)**

- 자료 유형·확인 범위: The Hardball Times 분석 · 본문.
- 내용·활용: 2003 MLB 자료로 카운트에 따라 공 하나의 가치가 달라지는 문제를 다룬다. 한 번의 가치와 자주 발생해서 생기는 총가치를 구별하는 참고자료다.
- 해석·접근 한계: 스트라이크·인플레이·파울 처리와 표본 조건을 확인해야 한다. 현재의 인과 효과 추정치가 아니다.

<a id="bc-r04"></a>

### R04. FanGraphs

**[wOBA](https://library.fangraphs.com/offense/woba/)**

- 자료 유형·확인 범위: 공식 지표 설명 · 본문.
- 내용·활용: 타격 결과에 서로 다른 가중치를 부여하는 이유와 공식 wOBA의 정의를 확인하는 기준.
- 해석·접근 한계: 자체 BCAI의 W는 공식 wOBA와 분모·처리가 다르다. 명칭이나 수치를 그대로 호환하지 않는다.

<a id="bc-r05"></a>

### R05. FanGraphs

**[RE24](https://library.fangraphs.com/misc/re24/)**

- 자료 유형·확인 범위: 공식 지표 설명 · 본문.
- 내용·활용: 주자·아웃 상황의 기대득점 변화라는 관점. 타석 결과 가치와 경기 상황 가치를 구별할 때 필요하다.
- 해석·접근 한계: 24는 주자·아웃 상태 수다. 12카운트를 자동으로 포함하는 지표가 아니며 승리확률과도 다르다.

<a id="bc-r06"></a>

### R06. Baseball Savant

**[Run Value (기존 swing-take 주소)](https://baseballsavant.mlb.com/leaderboard/swing-take)**

- 자료 유형·확인 범위: 공식 대시보드 · 설명 확인.
- 내용·활용: 투구 결과의 득점 가치를 확인할 수 있다. 조회 시점에는 Run Value 화면과 context-neutral·leveraged 구분을 제공한다.
- 해석·접근 한계: 주소 이름만 보고 과거 Swing/Take·Heart/Shadow 화면이라고 소개하지 않는다. leveraged를 곧바로 WPA라고 부르지 않는다.

<a id="bc-r07"></a>

### R07. FanGraphs

**[Plate Discipline](https://library.fangraphs.com/offense/plate-discipline/)**

- 자료 유형·확인 범위: 공식 지표 설명 · 본문.
- 내용·활용: O-Swing·Z-Swing·Contact·SwStr의 정의와 분모를 확인할 자료.
- 해석·접근 한계: 존 밖 스윙은 헛스윙과 다르다. 스윙 중 헛스윙 비율과 전체 투구 중 헛스윙 비율도 구별해야 한다.

<a id="bc-r08"></a>

### R08. Ryan Yee·Sameer K. Deshpande (2023 원고; 2024 학술지)

**[Evaluating plate discipline in Major League Baseball with Bayesian Additive Regression Trees](https://arxiv.org/html/2305.05752v2)**

- 자료 유형·확인 범위: JQAS 20(1):5–20 · 공개 원고 본문·방법·한계.
- 내용·활용: 테이크 시 스트라이크 확률, 스윙 시 접촉 확률, 이후 기대득점을 결합한다. 판정·접촉은 2019년, 득점 모형은 2015~2018년 자료를 사용한다. 선택별 기대값에 불확실성을 함께 표시한다.
- 해석·접근 한계: DOI: 10.1515/jqas-2023-0048. 기대득점 기준의 판단이며 다른 목적이면 답이 달라진다. 위치만 쓰는 대안 대비 예측 향상이 큰 것은 아니라는 저자 설명도 있다.

<a id="bc-r09"></a>

### R09. Connor Douglas·Everett Witt·Mia Bendy·Yevgeniy Vorobeychik (2021)

**[Computing an Optimal Pitching Strategy in a Baseball At-Bat](https://arxiv.org/html/2110.04321v1)**

- 자료 유형·확인 범위: 공개 연구 원고 · 본문·방법 (별도 게재 상태 미확인).
- 내용·활용: 2015~2018 MLB 약 270만 구. 투수의 의도와 실제 도착 위치의 분포, 타자의 반응을 확률게임으로 구성해 출루 억제 전략을 계산한다.
- 해석·접근 한계: 목적은 출루확률이다. 장타별 가중 W와 다르며, 예측된 개선은 실제 경기에서 실행한 전략의 효과가 아니다.

<a id="bc-r10"></a>

### R10. J. Eric Bickel (2009)

**[On the Decision to Take a Pitch](https://pubsonline.informs.org/doi/10.1287/deca.1090.0145)**

- 자료 유형·확인 범위: Decision Analysis 6(3):186–193 · 출판사 초록.
- 내용·활용: 공을 보기 전에 무조건 지켜보겠다고 정하는 선택과 투구를 판단한 뒤 스윙 여부를 정하는 선택을 의사결정 문제로 구분한다.
- 해석·접근 한계: DOI: 10.1287/deca.1090.0145. 초록 범위로 활용한다. 실제 기록의 take에는 여러 의도가 섞여 있으므로 모두 ‘기다리라는 작전’으로 해석하지 않는다.

<a id="bc-r11"></a>

### R11. Driveline Baseball (2019)

**[Quantifying Swing Decisions: An Individualized Approach](https://drivelinebaseball.com/blogs/blog/quantifying-swing-decisions-an-individualized-approach)**

- 자료 유형·확인 범위: 분석 기관 자체 연구 · 본문.
- 내용·활용: 2015~2018 자료를 활용한 선수별 스윙 판단 접근. 타격 능력과 카운트 구성이 다른 타자에게 같은 선구안 기준을 적용하는 문제를 논의한다.
- 해석·접근 한계: 학술지 논문은 아니다. 선수별 가치 평가의 아이디어와 실제 검증 수준을 구별한다.

<a id="bc-r12"></a>

### R12. Carmen Ciardiello (2021)

**[How Should Pitchers Approach 0-2 Counts?](https://blogs.fangraphs.com/how-should-pitchers-approach-0-2-counts/)**

- 자료 유형·확인 범위: FanGraphs 분석 · 본문·결과.
- 내용·활용: 2019~2020 자료에서 존 밖 0-2 투구와 이후 성적을 비교한다. 과거의 아주 멀리 빠진 공과 달리 존 밖 전체를 waste로 정의한다.
- 해석·접근 한계: 정의 차이 때문에 ‘유인구가 유리하다’와 ‘완전히 버리는 공은 손해다’가 공존할 수 있다. 관측된 위치 비교를 목표 위치를 바꾼 효과로 단정하지 않는다.

<a id="bc-r13"></a>

### R13. Dan Turkenkopf (2009)

**[A pitch is a terrible thing to waste. Or is it? (Part 1)](https://tht.fangraphs.com/a-pitch-is-a-terrible-thing-to-waste-or-is-it-part-1/)**

- 자료 유형·확인 범위: The Hardball Times 분석 · 본문.
- 내용·활용: 2008 MLB의 0-2 투구에서 매우 멀리 벗어난 공의 빈도를 살핀다. waste pitch를 어떻게 정의하느냐가 핵심이다.
- 해석·접근 한계: 존 밖 전체를 뜻하지 않는다. 이 글은 빈도 중심의 Part 1이므로 전략 효과의 최종 결론을 이 글만으로 인용하지 않는다.

<a id="bc-r14"></a>

### R14. James Gentile (2013)

**[Taking the close pitch with two strikes](https://tht.fangraphs.com/Taking-the-close-pitch-with-two-strikes/)**

- 자료 유형·확인 범위: The Hardball Times 분석 · 본문.
- 내용·활용: 같은 2스트라이크라도 볼 수에 따라 경계 투구를 지켜보는 빈도가 달라지는 현상을 다룬다.
- 해석·접근 한계: 경계 구역의 정의와 당시 판정 환경에 의존한다. 2스트라이크 전체를 한 행동 규칙으로 묶지 않는 근거로 쓴다.

<a id="bc-r15"></a>

### R15. Drew Fairservice (2014)

**[Changing Up With the Count 3-0](https://blogs.fangraphs.com/changing-up-with-the-count-3-0/)**

- 자료 유형·확인 범위: FanGraphs 분석 · 본문.
- 내용·활용: 3-0에서 타자의 기다림과 투수의 구종 선택이 맞물리는 사례. 카운트의 기대가치와 실제 행동의 간극을 설명하기 좋다.
- 해석·접근 한계: 특정 사례·당시 빈도를 현재 리그의 일반적 최적 전략으로 옮기지 않는다.

<a id="bc-r16"></a>

### R16. Neil Weinberg (2015)

**[Should One Strike Make This Much Difference?](https://tht.fangraphs.com/should-one-strike-make-this-much-difference/)**

- 자료 유형·확인 범위: The Hardball Times 분석 · 본문.
- 내용·활용: 3-0과 3-1 사이의 스윙 행동 차이를 12카운트 자료와 함께 살핀다. 스트라이크 하나가 만드는 행동 변화의 소재다.
- 해석·접근 한계: 행동 차이가 크다고 비합리성이 입증되는 것은 아니다. 구종·위치·선수·작전의 구성도 달라질 수 있다.

<a id="bc-r17"></a>

### R17. Scott Powers·Ronald Yurko (2025)

**[Swinging, Fast and Slow: Interpreting variation in baseball swing tracking metrics](https://arxiv.org/html/2507.01238v1)**

- 자료 유형·확인 범위: 프리프린트 · 본문·방법·가정.
- 내용·활용: 카운트별 타격 의도와 관측된 배트 속도를 구분한다. 계층모형·도구변수·카운트 전이를 이용해 접촉과 장타의 상충을 분석한다.
- 해석·접근 한계: 카운트 기반 의도를 도구변수로 쓰는 가정에 의존하며 논문도 독립성의 한계를 인정한다. ‘배트 속도를 낮추면 모든 타자가 좋아진다’는 근거가 아니다.

<a id="bc-r18"></a>

### R18. Mike Petriello (2024)

**[Do hitters have a 2-strike approach? Data says Yes!](https://www.mlb.com/news/mlb-hitters-have-a-two-strike-approach-at-the-plate)**

- 자료 유형·확인 범위: MLB 해설 · 본문 확인.
- 내용·활용: 2스트라이크 때 배트 속도 변화의 대중적 소개.
- 해석·접근 한계: 동작 연구의 도입 사례용.

<a id="bc-r19"></a>

### R19. Sal Baxamusa (2007)

**[Thanks for the memories](https://tht.fangraphs.com/thanks-for-the-memories/)**

- 자료 유형·확인 범위: The Hardball Times 분석 · 본문.
- 내용·활용: 2006 Retrosheet 자료로 같은 카운트에 도달한 순서에 따라 이후 결과가 달라지는지 검토한다. 1-1의 BS·SB가 대표 질문이다.
- 해석·접근 한계: 일부 카운트의 차이를 모든 경로의 효과로 확대하지 않는다. 글에서도 풀카운트·3-1에 같은 결과가 일관되게 나타나지는 않는다.

<a id="bc-r20"></a>

### R20. John Z. Clay (2023)

**[Strategic Pitch Location: The Role of Two-Pitch Sequences in Pitching Success](https://sabr.org/journal/article/strategic-pitch-location-the-role-of-two-pitch-sequences-in-pitching-success/)**

- 자료 유형·확인 범위: SABR 연구 글 · 본문.
- 내용·활용: 2019 AL 87명 투수의 두 공 위치 전이를 군집화하고 성과와 연결한다. 단일 공 위치에서 위치 조합으로 질문을 넓힌다.
- 해석·접근 한계: 투구 수 기준으로 고른 표본이며 군집·성과의 관련성을 다룬다. 특정 조합으로 바꾸면 성적이 개선된다는 실험이 아니다.

<a id="bc-r21"></a>

### R21. Glenn Healey·Shiyuan Zhao (2017)

**[Using PITCHf/x to model the dependence of strikeout rate on the predictability of pitch sequences](https://journals.sagepub.com/doi/10.3233/JSA-170103)**

- 자료 유형·확인 범위: Journal of Sports Analytics · 본문.
- 내용·활용: 7시즌 약 300만 구에서 연속 투구의 위치·구속·움직임의 관련성과 삼진율을 분석한다. 구종 이름 외의 예측 가능성을 다룬다.
- 해석·접근 한계: DOI: 10.3233/JSA-170103. 순서 특성과 성적의 관련성이며 임의로 구종을 섞는 정책의 인과 효과는 아니다.

<a id="bc-r22"></a>

### R22. Jeffrey N. Howard (2018)

**[Hit Probability as a Function of Foul-Ball Accumulation](https://sabr.org/journal/article/hit-probability-as-a-function-of-foul-ball-accumulation/)**

- 자료 유형·확인 범위: SABR 연구 글 · 본문.
- 내용·활용: 파울 누적과 이후 안타 확률을 다룬다. 같은 2스트라이크에 머무는 공들도 서로 다른 정보가 될 수 있다는 질문을 제공한다.
- 해석·접근 한계: Retrosheet의 1945~2015 범위를 사용하지만 전 기간의 투구 기록이 완전하다는 뜻은 아니다. 표본·분모 문제 때문에 효과 크기나 피로의 인과 근거로 쓰지 않는다.

<a id="bc-r23"></a>

### R23. Kenneth Kovash·Steven D. Levitt (2009)

**[Professionals Do Not Play Minimax: Evidence from Major League Baseball and the National Football League](https://www.nber.org/papers/w15347)**

- 자료 유형·확인 범위: NBER Working Paper 15347 · 2026-09-17 공식 PDF 본문·표·결론 확인.
- 내용·활용: 프로 선수의 전략 빈도와 연속성이 혼합전략 균형의 예측과 맞는지 검토한다. 배합을 상대의 예상과 연결하는 고전적 논쟁이다.
- 해석·접근 한계: [공식 PDF](https://www.nber.org/system/files/working_papers/w15347/w15347.pdf) 확인. MLB 부분의 구종 선택·종료 결과 척도·순서 검정을 사용한다. 직구 비중 변경의 추산 이익은 상대 반응 전의 상한이다. 2024 연구와 시간 변화만으로 비교하지 않는다.

<a id="bc-r24"></a>

### R24. Gagan Sidhu·Brian Caffo (2014)

**[MONEYBaRL: Exploiting pitcher decision-making using Reinforcement Learning](https://arxiv.org/abs/1407.8392)**

- 자료 유형·확인 범위: 학술지 연구의 공개 원고 · v1 본문·방법·결과 추가 확인.
- 내용·활용: 카운트와 직전 투구 선택·타자 행동·결과를 마르코프 의사결정 과정의 상태에 넣는 연구. 순차적 분석 설계의 선행 사례다.
- 해석·접근 한계: DOI: 10.1214/13-AOAS712. 2026-09-17 공개 v1 본문 추가 확인. 150개 비교 중 87개는 더 좋거나 같은 경우이며 모두 엄격한 우위가 아니다. 해당 정책 평가의 현재 구종을 정확히 안다는 가정과 후속 궤적 인식 시뮬레이션을 구분한다. 모형별 검정이 모두 유의한 것은 아니며 실전 개선 확률로 해석하지 않는다.

<a id="bc-r25"></a>

### R25. Peter L’Oiseau (2019)

**[Investigating the Importance of Pitch Selection with Clustering](https://tht.fangraphs.com/investigating-the-importance-of-pitch-selection-with-clustering/)**

- 자료 유형·확인 범위: The Hardball Times 분석 · 본문.
- 내용·활용: 타자·투수를 묶어 희소한 맞대결 문제를 줄이고 구종 선택을 비교한다.
- 해석·접근 한계: 군집이 다른 선수의 반응을 얼마나 공유할 수 있는지가 핵심 가정이다. 최적 배합이 입증된 결과로 쓰지 않는다.

<a id="bc-r26"></a>

### R26. Josh Weinstock (2011)

**[Commanding the Zone](https://blogs.fangraphs.com/commanding-the-zone/)**

- 자료 유형·확인 범위: FanGraphs 분석 · 본문.
- 내용·활용: 인플레이 외 투구의 가치를 누적해 카운트 싸움의 과정적 기여를 평가하는 발상.
- 해석·접근 한계: 투구량과 공당 능력을 구별해야 하며 실제 목표 위치를 관측한 제구 지표는 아니다.

<a id="bc-r27"></a>

### R27. Ryota Takamido·Hiroki Nakamoto (2026-06-15)

**[Counterfactual Optimization of Baseball Pitch Sequences and Estimation of Its Impact on Season-Level Statistics](https://arxiv.org/abs/2606.17345)**

- 자료 유형·확인 범위: 프리프린트 · v1 본문·계산 예시·단순화 가정 추가 확인.
- 내용·활용: 투구 순서를 모델링하고 구종을 바꾸는 가상 비교를 시즌 수준 성적과 연결한다. 최신 순차 최적화 연구의 방향을 보여준다.
- 해석·접근 한계: 인플레이와 삼진 관련 목표가 전체 공격가치 W와 같지 않다. 예상 개선을 실제 시즌에서 검증한 개선으로 쓰지 않는다.

<a id="bc-r28"></a>

### R28. Sebastian E. Ferrando·Eli Kohn (2026-07-31)

**[Baseball, An Extensive-Form Game-Theoretic Duel](https://arxiv.org/abs/2607.29041)**

- 자료 유형·확인 범위: 프리프린트 · 초록.
- 내용·활용: 12카운트를 정보가 불완전한 투타 게임으로 구성하고 타석 종료 이후 가치까지 연결하는 이론적 접근.
- 해석·접근 한계: 2026-09-17 공개 v1 본문 확인. 정규 12카운트 재귀 계산과 3볼·2스트라이크 축소 게임의 예시를 구별한다. 2스트라이크 파울도 단순화한다.

<a id="bc-r29"></a>

### R29. Jean-François Mercier (2024)

**[Professionals do play Minimax: Revisiting the Nash equilibrium in Major League Baseball](https://www.sciencedirect.com/science/article/pii/S2773161824000168)**

- 자료 유형·확인 범위: Sports Economics Review 7:100039 · 출판사 초록·공개 발췌.
- 내용·활용: 스윙/테이크와 존 안/밖의 2×2 게임을 구성한다. 다수 선수에서 보수 균등성과 행동의 연속성에 관한 균형 예측이 성립한다는 결과를 제시한다.
- 해석·접근 한계: DOI: 10.1016/j.serev.2024.100039. 2026-09-17 출판사·저자 공유 링크 모두 전문 요청 차단; 전문 미확보. 초록 범위를 넘는 상세 인용은 보류한다. Kovash·Levitt와 행동 구분·모형이 달라 15년간 시스템화의 증거로 단정하지 않는다.

<a id="bc-r30"></a>

### R30. Rob Gray·Rouwen Cañal-Bruland (2018)

**[Integrating visual trajectory and probabilistic information in baseball batting](https://www.sciencedirect.com/science/article/pii/S1469029217306775)**

- 자료 유형·확인 범위: Psychology of Sport and Exercise 36:123–131 · 초록·공개 방법 발췌.
- 내용·활용: 대학 타자의 시뮬레이션에서 시각 정보와 사전 확률의 결합을 연구한다. 볼 수 있는 시간이 줄면 사전 정보의 역할이 커진다는 설명과 연결된다.
- 해석·접근 한계: DOI: 10.1016/j.psychsport.2018.02.009. 실제 MLB의 특정 카운트 효과를 직접 측정한 연구가 아니다.

<a id="bc-r31"></a>

### R31. Rob Gray (2002)

**[‘Markov at the Bat’: A Model of Cognitive Processing in Baseball Batters](https://journals.sagepub.com/doi/10.1111/1467-9280.00495)**

- 자료 유형·확인 범위: Psychological Science 13(6) · 출판사 초록.
- 내용·활용: 대학 선수 6명의 시뮬레이션 자료로 타자의 기대 상태와 인지 처리를 모형화한다. 직전 정보가 다음 대응에 연결되는 설명이다.
- 해석·접근 한계: DOI: 10.1111/1467-9280.00495. 작은 실험 표본이며 프로 경기의 배합 효과 크기로 옮길 수 없다.

<a id="bc-r32"></a>

### R32. Clare MacMahon·Janet L. Starkes (2008)

**[Contextual influences on baseball ball-strike decisions in umpires, players, and controls](https://vuir.vu.edu.au/3800/)**

- 자료 유형·확인 범위: Journal of Sports Sciences 26(7):751–760 · 기관 저장소·초록.
- 내용·활용: 심판·선수·대조군의 볼/스트라이크 판단을 맥락과 연결한다. 판정 기준 자체가 상황에 영향을 받을 수 있다는 실험 연구.
- 해석·접근 한계: DOI: 10.1080/02640410701813050. 실험 과제와 실제 경기 추적 자료의 차이를 명시한다.

<a id="bc-r33"></a>

### R33. Etan Green·David Daniels (2014)

**[What Does it Take to Call a Strike? Three Biases in Umpire Decision Making](https://www.sloansportsconference.com/research-papers/what-does-it-take-to-call-a-strike-three-biases-in-umpire-decision-making)**

- 자료 유형·확인 범위: MIT Sloan 학회 연구 · 공개 요약.
- 내용·활용: 카운트에 따른 판정 구역 변화와 연속 판정 편향을 다룬다. 같은 경계 공도 테이크 가치가 달라질 수 있다는 근거다.
- 해석·접근 한계: 학회 연구이며 투구 위치·카운트·판정 순서의 효과를 구별해야 한다. 의도적인 봐주기를 증명한 것으로 쓰지 않는다.

<a id="bc-r34"></a>

### R34. Daniel L. Chen·Tobias J. Moskowitz·Kelly Shue (2016)

**[Decision Making Under the Gambler’s Fallacy: Evidence from Asylum Judges, Loan Officers, and Baseball Umpires](https://academic.oup.com/qje/article/131/3/1181/2590011)**

- 자료 유형·확인 범위: Quarterly Journal of Economics 131(3) · 본문.
- 내용·활용: 여러 의사결정 영역과 함께 MLB 판정의 연속성을 분석한다. 직전 판정 후 반대 판정이 나타나는 경향을 통제변수와 함께 검토한다.
- 해석·접근 한계: 카운트에 따른 판정 변화와 직전 콜의 영향은 별개 질문이다. 모든 개별 오심의 원인을 설명하는 연구가 아니다.

<a id="bc-r35"></a>

### R35. Sameer K. Deshpande·Abraham J. Wyner (2017)

**[A Hierarchical Bayesian Model of Pitch Framing](https://arxiv.org/abs/1704.00823)**

- 자료 유형·확인 범위: JQAS 서지 확인 · SAFE2라는 제목의 공개 v1 본문·결과 추가 확인.
- 내용·활용: 위치·카운트와 심판·선수 효과를 함께 고려하는 프레이밍 평가. 판정 확률의 차이를 득점 가치로 연결한다.
- 해석·접근 한계: DOI: 10.1515/jqas-2015-0027. 2026-09-17 공개 v1 본문(SAFE2: A Hierarchical Model of Pitch Framing)을 추가 확인했다. v2·학술지 제목과 버전을 구별하고 ABS에 그대로 적용하지 않는다.

<a id="bc-r36"></a>

### R36. Kichang Lee·Kyungsik Han·JeongGil Ko (2024; 2025 개정)

**[Analyzing the Impact of the Automatic Ball Strike System in Professional Baseball through a Case Study on KBO League Data](https://arxiv.org/abs/2407.15779)**

- 자료 유형·확인 범위: 프리프린트 · 2025년 개정 v2 본문·결과·한계 추가 확인.
- 내용·활용: KBO ABS 전환과 경계 판정의 변화를 다룬다. 인간 심판 연구를 다른 판정 제도와 비교하는 자료다.
- 해석·접근 한계: 2026-09-17 개정 v2 본문 확인. 2차원 위치와 리그 평균 존 높이의 한계, 제도 전후 비교의 인과 해석 한계를 명시한다. 자체 KBO 검증을 대신하지 않는다.

<a id="bc-r37"></a>

### R37. Kichang Lee·JeongGil Ko (2026-09-03)

**[Auditing Contextual Bias in Human Ball-Strike Calls Using KBO’s Automated Umpiring Transition](https://arxiv.org/abs/2609.03786)**

- 자료 유형·확인 범위: 프리프린트 · v1 본문·방법·결과 추가 확인.
- 내용·활용: KBO의 인간 판정과 자동 판정 전환을 이용해 카운트 등 상황 편향을 조사한다. 0-2·3-0을 포함한 카운트별 비교가 직접 관련된다.
- 해석·접근 한계: 2026-09-17 공개 v1 본문 확인. 0.25피트 경계의 지켜본 공, 2022~2023 인간 기준, 0-0 대비 조정된 확률 차이를 명시한다. 매우 최근 프리프린트이며 전환은 무작위 실험이 아니다.

<a id="bc-r38"></a>

### R38. KBO (2025)

**[2025 리그 규정·주요 변경 사항](https://www.koreabaseball.com/Kbo/League/GameManage2025.aspx)**

- 자료 유형·확인 범위: 공식 규정 · 본문.
- 내용·활용: 2025 ABS 존 조정과 경기 운영 제도 변화를 확인하는 원자료.
- 해석·접근 한계: 2025 설명을 2026 규정이라고 부르지 않는다. 여러 해를 묶는 판정 분석에서는 해당 연도 규정을 따로 확인한다.

<a id="bc-r39"></a>

### R39. Baseball Savant

**[Statcast CSV Documentation](https://baseballsavant.mlb.com/csv-docs)**

- 자료 유형·확인 범위: 공식 데이터 사전 · 본문.
- 내용·활용: balls/strikes의 투구 전 상태, type의 B/S/X 결과 구분, 위치·존 필드를 확인한다. 2026 위치 기준면·존 정의 변경도 명시한다.
- 해석·접근 한계: type의 S는 존 안 위치를 의미하지 않는다. delta_run_exp와 승리확률 변화도 구별한다. 필드 설명 열람은 대량 재배포 허가 확인을 뜻하지 않는다.

<a id="bc-r40"></a>

### R40. Retrosheet

**[Event Files](https://www.retrosheet.org/eventfile.htm)**

- 자료 유형·확인 범위: 공식 기록 형식 · 본문.
- 내용·활용: 타석 사건과 투구 문자열을 읽는 기준. 순서·파울·알 수 없는 투구 처리에 필요하다.
- 해석·접근 한계: 옛 경기 모두에 투구 단위 기록이 있는 것은 아니다. 실제 수집 전 대상 시즌의 완전성과 제공·이용 조건을 따로 점검한다.

<a id="bc-r41"></a>

### R41. FanGraphs

**[Player Splits Tool](https://library.fangraphs.com/features/player-splits-tool/)**

- 자료 유형·확인 범위: 공식 조회 도구 설명 · 본문.
- 내용·활용: 카운트·상황 분할 자료를 읽고 기존 표와 비교할 때의 출발점.
- 해석·접근 한계: 도달 카운트인지 종료 카운트인지 먼저 확인한다. 조건부 표본의 FIP 등은 전체 시즌 지표와 같은 의미가 아닐 수 있다.

<a id="bc-r42"></a>

### R42. Woody Eckard (2022)

**[The Impact of the One-Off 1887 Four-Strike Strikeout](https://sabr.org/journal/article/the-impact-of-the-one-off-1887-four-strike-strikeout/)**

- 자료 유형·확인 범위: SABR 연구 글 · 본문.
- 내용·활용: 1887년의 4스트라이크 삼진 제도를 다룬다. 현재 카운트 구조가 규칙의 산물임을 보여주는 역사 소재.
- 해석·접근 한계: 동시에 바뀐 규칙이 있으므로 오늘날 스트라이크 하나의 순수한 효과를 추정한 자연실험처럼 소개하지 않는다.

<a id="bc-r43"></a>

### R43. 김주학·강지연·조선미·노갑택 (2023)

**[순차패턴마이닝 기법을 활용한 상황별 볼넷 구종패턴 분석](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002951027)**

- 자료 유형·확인 범위: 한국체육측정평가학회지 25(1):77–87 · KCI 초록.
- 내용·활용: 류현진의 볼넷 209개 투구 시퀀스를 상황별로 분석한다. 국내의 카운트·순서 연구 사례다.
- 해석·접근 한계: DOI: 10.21797/ksme.2023.25.1.007. 모두 볼넷으로 끝난 표본이므로 특정 배합의 볼넷 발생 확률을 입증하지 않는다.

<a id="bc-r44"></a>

### R44. 조선미·김주학·강지연·김상균 (2023)

**[머신러닝(XGBoost)기반 미국프로야구(MLB)의 투구별 안타 및 홈런 예측 모델 개발](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002951025)**

- 자료 유형·확인 범위: 한국체육측정평가학회지 25(1):65–76 · KCI 초록.
- 내용·활용: 2022 MLB의 카운트·구종·위치 등을 이용한 안타·홈런 예측 연구. 카운트를 다른 투구 조건과 결합하는 국내 사례다.
- 해석·접근 한계: DOI: 10.21797/ksme.2023.25.1.006. 분류 표본·검증 분할의 전문 확인 전에는 정확도를 BCAP와 직접 비교하지 않는다. 예측과 행동 효과도 다르다.

<a id="bc-r45"></a>

### R45. Baseball Savant

**[ABS Challenge Dashboard](https://baseballsavant.mlb.com/abs)**

- 자료 유형·확인 범위: 공식 대시보드 · 화면·설명.
- 내용·활용: MLB ABS 챌린지 관련 자료의 공식 출발점. 인간 판정과 자동 확인이 공존하는 환경을 구별하는 데 쓰인다.
- 해석·접근 한계: KBO의 전면 ABS와 같은 제도로 취급하지 않는다. 챌린지된 공만 분석하면 선택된 표본이라는 문제가 생긴다.

---


## BCAP 외부 자료 재사용 — 2026-09-14

기존2023-03-30~10-01(720,684구·2,430경기),2026-03-25~09-07(639,042구·2,165경기)의 V1 정제본을 재사용했다. 새 수집·기간 확장은 없다. [입력·설정 봉인](analysis/bcap_external_20260914__r01/plan_seal.json), [2023 준비](analysis/bcap_external_20260914__r01/preparation_2023/preparation.json), [2026 준비](analysis/bcap_external_20260914__r01/preparation_2026/preparation.json), [측정 확인](analysis/bcap_external_20260914__r01/measurement_review.md), [최종 보고서](analysis/bcap_external_20260914__r01/final_report.html).

새 정제본은 data/processed/bcap_external_v2_2023_20260914__r01.pkl 및 bcap_external_v2_2026_20260914__r01.pkl이다. 기존 키·완료PA 제외·최종W·미해결 카운트 예외는 보존하고 직전FB/NFB·FF·2023S/B 라벨만 최소 추가했다. 2026 S/B와타자는미실행이며 준비본의 미지원 표시는 측정보류를뜻한다. 2023은기존2023 W,2026은2025 W고정이며 계수 차이로 연도간 크기 직접비교에는한계가있다.

2026 plate_x/z기준면과sz_top/bot정의변경을 [공식 필드 설명](https://baseballsavant.mlb.com/csv-docs)에서재확인했다. 임의변환·심판판정대체·위치없는대리분석은하지않았다. 자료의과거노출이력을유지하며처음보는시험자료라고부르지않는다.

아래는 이전 작업 시점의 기록이며 당시의 미실시 범위를 보존한다.

## 포심/비포심 추가 개발 입력 — 2026-09-12

[기존 V2 2024·2025 정제본](data/processed/bcap_dev_v2_20260912__r01.pkl)에서 동일 eligible_pitch 1,415,566행을 재사용했다. [새 FF 학습용 정제본](data/processed/bcap_pitch_ff_dev_20260912__r01.pkl)은 키·최종 PA W·기존 투구 전 특징·기존fold와 새 FF/non-FF A를 보존한 입력이다. 원본 재수집·외부 연도 적용·타자/SB 데이터 변경은 없었다.

[실제 코드·적격 제외 목록](analysis/bcap_pitch_classification_20260912__r01/input_code_eligibility.csv) · [입력 해시·기본 확인](analysis/bcap_pitch_classification_20260912__r01/preparation.json) · [개발 결과](analysis/bcap_pitch_classification_20260912__r01/report.html). 새A=FF만1, SI/FC와 기존 닫힌 나머지 유효 구종만0이다. PO·UN·결측/기존 PA 제외를0으로 채우지 않았다. FA/Other 한계를 유지한다. 새 자료 확보나 이용 조건 확인이 필요한 수집 작업은 수행하지 않았다.

## BCAP V2 개발 자료 재사용 — 2026-09-12

[기존 2024·2025 정제본](data/processed/bcap_dev_v010_20260909_r01.pkl)의 1,424,427행·4,859경기를 재사용했다. [새 V2 정제본](data/processed/bcap_dev_v2_20260912__r01.pkl)에 직전 FB/NFB·실제 S/B·기존 카운트 예외 표시만 추가했다. 원본 재수집·기존 정제본 덮어쓰기와 2023/2026 데이터 적용은 없었다. [입출력 해시·기본 확인](analysis/bcap_v2_development_20260912__r01/preparation/preparation.json) · [개발 보고서](analysis/bcap_v2_development_20260912__r01/report.html).

S/B와 타자 5개 보고 구역은 2024·2025의 plate_x/z 및 sz_bot/top을 이용한 공 중심 기하 기준이다. 좌우는 타자 방향을 반영한 몸쪽/바깥쪽, 모서리는 두 구역 포함이다. [Savant 공식 CSV 필드 설명](https://baseballsavant.mlb.com/csv-docs)의 좌표 설명만 확인했고 신규 투구 데이터를 수집하지 않았다. 기존 출처·이용 조건 이력은 아래에 보존한다. 이번 버전의 상태는 2024·2025 개발 결과 산출, 후속 검증 미실시다.

## Ridge v0.2 외부 검증 확보 결과 — 2026-09-09 확인

| 시즌·역할 | 기간 | 원본 행 | 완료 경기 | 전체 관측 PA | 유효 PA | 검증 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 2023 외부 재현 | 2023-03-30~2023-10-01 | 720,684 | 2,430 | 184,478 | 183,534 | 일정 누락0·중복 투구 키0 |
| 2026 외부 시간 순방향 | 2026-03-25~2026-09-07 | 639,042 | 2,165 | 164,281 | 163,327 | 보충 후 일정 누락0·중복 투구 키0 |

- 2023 원본: `data/raw/mlb/2023/snapshot_20260908_ridge_v02/`.2026 최초 원본: `data/raw/mlb/2026/snapshot_20260908_ridge_v02/`, 보충: `data/raw/mlb/2026/supplement_20260909_ridge_v02/`.2024·2025 원본·정제본은 재수집·덮어쓰기하지 않았다.
- 2026 최초 확보는635,803행·2,154경기로, 공식 완료된9월7일11경기 누락을 발견해 평가 전에 FAILED로 중단했다.9월9일 요청의 계속 진행 과정에서 누락 경기3,239행을 별도 파일로 보충했다. 최초 원본·일정·실패 manifest는 보존했다. 종료일과 모델은 변경하지 않았고2026 첫 성능 평가는 보충 후1회만 수행했다.
- 2023 제외: 고의볼넷474, truncated272, 최종 결과 결측102, 타격방해96.2026 제외: 고의볼넷489, truncated292, 결측96, 타격방해77. 사건별 규칙은 기존 OBS와 동일하다.
- 공식 요청 URL·확보 시각·경기 키·파일별 행수/바이트/SHA256은 각 원본 폴더의 acquisition_audit.json과 완료 실행의 입력 목록에 보존했다.2026 완성 목록은 보충 폴더의 audit 및 아래 완료 실행이 기준이다. 기존 실패 audit를 완성본으로 덮어쓰지 않았다.
- 실행: [2023 manifest](analysis/runs/bcai_ridge__mlb_2023__20260908__r01/manifest.json), [2026 manifest](analysis/runs/bcai_ridge__mlb_2026_ytd_20260907__20260909__r01/manifest.json), [2026 보충 수집 코드·해시](analysis/runs/bcai_ridge__mlb_2026_ytd_20260907__20260909__r01/manifest_extension.json).
- 두 외부 자료 모두 개발 모델·α·평가 규칙 고정 뒤 확보·평가했다.2026은2025 가중치 고정이며 시즌 최종 검증은 미실시다. 신규 결과는 [v0.2 보고서](analysis/ridge_v02_validation_report.md)에 있다. 아래 이용 조건 확인 상태를 유지하며 원본 재배포·Drive/Docs 업로드·KBO 작업은 하지 않았다.

## Ridge v0.2 외부 검증 확보 계획 — 2026-09-08

- 2024·2025 기존 자료만으로 개발 후 모델을 고정했다. 개발 실행은 `analysis/runs/bcai_ridge__mlb_2024_2025__20260908__r02/manifest.json`. 2023·2026 자료는 개발에 사용하지 않았으며 로컬 원본 폴더가 없음을 확인했다.
- 확보 대상: 2023 정규시즌 전체와 2026-09-07 공식 경기일까지의 완료 정규시즌. MLB Baseball Savant 공식 Statcast CSV와 MLB Stats API 일정으로 범위·완료 상태·구장 ID를 확인한다. 원본은 연도별 새 snapshot 하위 폴더에 보존하고 행수 상한·중복·누락을 점검한다.
- 2026-09-08 [CSV 공식 설명](https://baseballsavant.mlb.com/csv-docs)에서 count와 상황 필드를 재확인했다. 2026 plate_x/plate_z 정의 변경이 있어 이번 모델에서 위치 변수를 제외한다.
- [MLB 이용약관](https://www.mlb.com/official-information/terms-of-use): 자동 수집 제한 조항 확인. 별도 허가·원본 재배포 권한은 미확인. 이번 요청의 로컬 분석 자료로만 다룬다.
- [FanGraphs 시즌 상수](https://www.fangraphs.com/tools/guts?type=cn), 열람일 2026-09-08. 2023 wBB .696, wHBP .726, w1B .883, w2B 1.244, w3B 1.569, wHR 2.004를 사전 고정했다. 2026 검증은 요청대로 2025 가중치를 고정 사용하며 2026 잠정 상수로 튜닝하지 않는다.
- 실제 확보 성공·경기수·행수·마지막 경기일·해시는 완료 후 해당 외부 실행 manifest와 acquisition_audit를 기준으로 추가 기록한다. 이 계획은 확보 성공을 뜻하지 않는다. KBO 수집·Drive/Docs 반영은 하지 않는다.

2024·2025 MLB 정규시즌 전체 자료를 확보하고 하나의 표본으로 통합했다. 아래에 출처, 확보 범위와 통합 결과 산출물을 기록한다.

## 분석 가능성 사전 확인 — 2026-09-06

- 출처: MLB Baseball Savant [Statcast Search](https://baseballsavant.mlb.com/statcast_search), [CSV 공식 설명](https://baseballsavant.mlb.com/csv-docs). 저자·기관: MLB / Baseball Savant. 문서 게시일 미표시, 열람일 2026-09-06.
- 확인 목적: 사용자 초안의 12개 카운트별 구종·스윙·투구 결과·최종 타석 결과·경기 상황 및 카운트 경로 분석 가능성 검토. 아직 본문 수치의 근거는 아님.
- 제공 필드: 투구 전 balls/strikes, pitch_type/pitch_name, description/type, 타석 결과 events, game_pk/at_bat_number/pitch_number, pitcher/batter, stand/p_throws, 주자 on_1b/on_2b/on_3b, outs_when_up/inning, 투구 전 bat_score/fld_score, plate_x/plate_z/sz_top/sz_bot.
- 정의 주의: type은 B/S/X(볼/스트라이크/인플레이)로, 존 안팎이나 투수 의도를 뜻하지 않는다. 스윙은 description의 실제 값 목록을 확인해 분류한다. 최종 타석 결과는 타석 식별자로 연결하며 미종료·누락 기록을 별도 점검한다.
- 측정 차이: 공식 설명상 2026년부터 plate_x/plate_z의 기준 위치 및 sz_top/sz_bot의 존 정의가 변경됨. 시즌을 섞는 위치 분석은 정의 차이를 반영해야 한다.
- 확보 방식 검토: 공식 검색 화면의 CSV 내려받기 기능 확인. 2026-09-01 정규시즌 하루를 기능 확인용 검색 범위로 사용하며, 본 분석 기간으로 확정한 것은 아님.
- 이용 조건: [MLB 이용약관](https://www.mlb.com/official-information/terms-of-use) 열람. 자동 수집 제한 조항이 있어 대량 자동 수집 및 원본 재배포 허용은 확인되지 않은 상태로 둔다. CSV 제공 자체를 모든 이용·재배포의 허가로 해석하지 않는다.
- KBO: 이번 확인 대상은 MLB이며 KBO의 투구별 제공 범위·구종·이용 조건은 미확인.

## 데이터 목록

| 리그 | 파일·저장 위치 | 원출처·URL | 대상 기간 | 확보일·방식 | 이용 조건 확인 | 결측·주의사항 |
| --- | --- | --- | --- | --- | --- | --- |
| MLB | `data/raw/mlb/statcast_2026-09-01_feasibility.csv` | [Statcast Search](https://baseballsavant.mlb.com/statcast_search?hfGT=R%7C&hfSea=2026%7C&player_type=pitcher&game_date_gt=2026-09-01&game_date_lt=2026-09-01&group_by=name&min_pitches=0&min_results=0&min_pas=0&sort_col=pitches&sort_order=desc#results) | 2026-09-01 정규시즌 | 2026-09-06, 공식 화면의 Download Data as Comma Separated Values File 클릭 후 내려받은 원본 복사 | 위 사전 확인 참조. 원본 외부 공유는 미실시 | 기능 확인용 하루 표본. 4,681행, 자동 볼·스트라이크 포함. 시즌 추정에 사용하지 않음 |

### 표본 점검 결과 — 2026-09-06

- CSV game_date는 모두 2026-09-01. 15개 game_pk, 1,196개 (game_pk, at_bat_number) 조합 확인.
- 12개 투구 전 카운트 모두 존재. (game_pk, at_bat_number, pitch_number) 중복 없음.
- description에서 볼, 블로킹된 볼, 루킹 스트라이크, 헛스윙, 파울, 파울 번트, 파울 팁, 인플레이, 몸에 맞는 공 및 자동 판정 기록을 확인.
- automatic_ball 9행, automatic_strike 2행. pitch_type 결측은 11행이며 실제 투구 분석과 자동 판정을 구분해야 함. pitcher 식별자 결측 없음.
- events가 모두 비어 있는 타석 식별자 1개 존재. 미완료 타석 또는 기록 누락인지 추가 확인 전 최종 결과를 임의 부여하지 않음.
- 경기·타석 식별자와 투구 번호로 경로 재구성 가능한 구조임을 확인. 경로 전체의 연속성, 타석 결과 대조, 구종별 결측 및 분석 지표 검증은 아직 미실시.
- 위 수치는 내려받은 CSV의 구조 점검 결과이며 카운트별 야구 성과에 대한 본 분석 결과가 아님.

## 참고 문헌

문헌을 실제로 확인한 뒤 제목, 저자·기관, 발표일, URL, 열람일, 뒷받침하는 주장과 관련 원고 위치를 기록한다.

### 카운트 유불리 판정 분석 — 2026-09-07

- FanGraphs, [Guts! Seasonal Constants](https://www.fangraphs.com/tools/guts?type=cn). 게시일 미표시, 열람일 2026-09-07. 2024/2025의 wBB·wHBP·w1B·w2B·w3B·wHR 및 wOBA scale·리그 R/PA를 직접 확인했다. 확인 값은 [분석 보고서 2절](analysis/count_advantage_2024_2025.md)과 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_audit.json`에 저장했다. 시즌 가중치 및 득점 환경 보조 환산의 근거다. 별도의 플레이 데이터는 내려받지 않았다.
- FanGraphs Sabermetrics Library, [wOBA](https://library.fangraphs.com/offense/woba/). 열람일 2026-09-07. 결과별 선형가중치와 공식 분모의 개념 확인. 이번 분석은 희생번트를 포함한 유효 완료 PA가 분모이므로 공식 wOBA가 아닌 카운트 공격가치 지수로 명명했다.
- MLB Baseball Savant, [Statcast Search CSV Documentation](https://baseballsavant.mlb.com/csv-docs). 열람일 2026-09-07. 투구 전 카운트·투구 결과·선수·상황 필드 정의 재확인. FB(포심+싱커+커터) 및 스윙/헛스윙 묶음은 프로젝트의 명시적 분석 정의이며 공식 단일 지표라고 주장하지 않는다.
- 실제 계산은 기존 2024·2025 원본 CSV와 통합 정제표를 읽었다. 구장은 보존된 `schedule_2024.json`, `schedule_2025.json`의 venue ID로 연결했다. 기존 MLB 자료 이용 조건·원본 재배포 미확인 상태는 유지한다. 신규 원본 확보나 외부 업로드는 수행하지 않았다.
- 표본: 364,124 유효 PA, 4,859경기. 결측 221·truncated 635·고의볼넷 1,065·타격방해 186 제외. 이벤트별 기록은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_event_audit.csv`, 입력 경로·SHA256·가중치·실행 설정은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_audit.json`, 재집계·해시 검증은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_validation.json`에 저장한다.
- 결과 산출물은 `analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_*`(캐시는 기존 `analysis/advantage_input_cache.pkl`) 및 `analysis/count_advantage_2024_2025.md`에 두고, 원본·기존 통합 정제본을 덮어쓰지 않았다. KBO 제공 범위·시즌 상수·이용 조건은 여전히 미확인이다.

## 데이터 정의·변경 이력

### BCAP 검수 인계 출처 확인 — 2026-09-09

- MLB Baseball Savant, [Statcast CSV Documentation](https://baseballsavant.mlb.com/csv-docs), 게시일 미표시, 열람 2026-09-09. balls/strikes의 투구 전 기준, 구종의 Statcast 유도 분류, plate_x/z의 2026 기준면 변화와 sz_top/bot의 ABS 존 정의를 확인했다. 좌표 변환·시즌 정합성 검증은 미실시이며 위치 기반 외부 검증의 해결 과제로 남긴다.
- Dudík, Langford, Li (2011), [Doubly Robust Policy Evaluation and Learning](https://arxiv.org/abs/1103.4601), 열람 2026-09-09. 공개 초록의 DR 정책 평가·학습 범위를 확인했다. 본 프로젝트의 MLB 교란 제거를 보장하는 근거는 아니다.
- Athey, Wager, [Policy Learning with Observational Data](https://arxiv.org/abs/1702.02896) (2017 사전논문, 2021 Econometrica 출판), 열람 2026-09-09. 관찰 자료의 정책 학습과 정책 클래스에 관한 공개 초록을 확인했다.
- Nie, Brunskill, Wager (2019 사전논문), [Learning When-to-Treat Policies](https://arxiv.org/abs/1905.09751), 열람 2026-09-09. 순차적 정책에는 별도 식별·평가 설계가 필요함을 검토하는 참고 자료다. 공개 초록 확인이며 상세 정리·증명을 독립 검증한 것은 아니다.
- 적용 위치: [BCAP 검수 인계](analysis/handoff_bcap_review.md). 방법론 수정은 프로젝트 설계 판단이며 논문이 해당 야구 모델을 검증했다고 표현하지 않는다. 신규 원본 수집·재배포·Drive 업로드는 없고 기존 이용 조건 미확인 범위도 유지한다.

구종 분류, 구속 단위, 카운트 전후 기준, 측정 방식 등 해당 칼럼에 필요한 출처별 차이와 정정 사항을 기록한다.

## 2025 정규시즌 전체 확보 작업

- 사용자 요청: 2025 정규시즌 전체 투구, 모든 카운트·선수 포함. 포스트시즌 제외.
- 전체 검색 CSV가 25,000행(9월 23~28일)으로 잘려 반환되는 것을 확인하여 전체본으로 채택하지 않음.
- 완료: 날짜 분할 CSV 38개를 `data/raw/mlb/2025/`에 보존. 일정 JSON을 포함한 총 39개 파일, 491,041,383바이트(약 468.3 MiB).
- 검증 결과: 712,528행, 2,430경기, 183,362타석. 공식 완료 경기 목록 대비 누락 0·추가 0, `(game_pk, at_bat_number, pitch_number)` 중복 0, 12개 카운트 모두 존재.
- 다운로드·파일별 해시·카운트별 행 수·검증 기록: `analysis/download_2025_status.json` (`status: complete`).
- 공개 CSV 주소 구성 참고: https://github.com/jldbc/pybaseball/blob/master/pybaseball/statcast.py. 위 MLB 이용 조건 확인과 재배포 미확인 상태는 유지한다.

## 2024 정규시즌 전체 확보 — 2026-09-07

- 출처와 확보 방식: 2025년과 동일한 MLB Baseball Savant Statcast Search CSV와 MLB Stats API 정규시즌 일정을 사용하고 날짜별로 분할 확보했다.
- 원본: 날짜 분할 CSV 39개와 `schedule_2024.json`을 `data/raw/mlb/2024/`에 보존. 총 485,572,494바이트(약 463.1 MiB).
- 검증: 711,899행, 실제 완료 2,429경기, 182,869타석. 일정 대비 누락 0·추가 0, 중복 투구 키 0, 12개 카운트 모두 존재.
- 일정 예외: gamePk 746577은 일정 응답의 상위 상태가 Final이지만 상세 상태가 `Cancelled`, 사유가 `Rain`인 2024-09-29 휴스턴–클리블랜드전이라 완료 경기에서 제외했다.
- 분석 대상: 실제 구종이 확인되는 709,226투구. 자동 판정 2,387건과 구종 결측은 구종 선택 분석에서 제외했다. 최종 결과 미확인 타석은 104개다.
- 재현·검증: `analysis/download_2024.py`, `download_2024_status.json`.
- 이용 조건과 해석 제한은 2025 자료와 동일하다. 원본 외부 공유 허용은 확인하지 않았으며, 비교 결과는 통제 전 관찰 통계다.

## 2024·2025 통합 분석 — 2026-09-07

- 사용자 결정: 시즌별 주요 결과의 차이가 작아 두 시즌을 하나의 표본으로 합쳐 이후 분석의 중심 데이터로 사용한다.
- 통합 범위: 4,859경기, 원본 1,424,427행, 실제 구종 확인 1,419,135투구, 366,231타석.
- 원본 관리: 연도별 원본 폴더를 합치거나 덮어쓰지 않는다. 통합 분석 코드가 두 폴더를 읽어 정제본을 재생성한다.
- 상세 결과: `analysis/count_analysis_2024_2025.md`.
- 통합 정제본: `data/processed/count_summary_2024_2025.csv`, `count_pitch_mix_2024_2025.csv`, `count_next_pitch_outcomes_2024_2025.csv`, `count_immediate_results_2024_2025.csv`, `count_plate_appearance_results_2024_2025.csv`, `count_game_context_2024_2025.csv`, `count_context_pitch_choices_2024_2025.csv`.
- 재현·검증: `analysis/analyze_counts_2024_2025_combined.py`, `count_analysis_2024_2025_combined_summary.json`.
- 2026-09-07 정리: 시즌별 정제본과 비교표·비교 보고서·비교 코드는 사용자 결정에 따라 제거했다. 통합 정제 데이터 7개만 유지한다.


## 모델 등록 및 구조 변경 — 2026-09-08

- 주 모델: [BCAI-OBS-v1.0.0](../../models/bcai/observed/v1.0.0/model_card.md), VALIDATED.
- 탐색 모델: [BCAI-RIDGE-v0.1.0](../../models/bcai/ridge/v0.1.0/model_card.md), EXPERIMENTAL. 인과·미래 예측 모델 아님.
- [OBS 실행](analysis/runs/bcai_obs__mlb_2024_2025__20260907__r01/README.md)과 [Ridge 실행](analysis/runs/bcai_ridge__mlb_2024_2025__20260907__r01/README.md)은 2026-09-07 공동 계산의 사후 등록이다. 결과는 OBS artifacts에 한 번만 저장하고 Ridge 열과 audit.model을 구분한다.
- 원본·정제본·캐시·기존 코드·통합 보고서의 위치는 유지했다. 결과 경로만 변경했으며 수치 재계산·KBO 분석·Drive/Docs 수정은 하지 않았다. 로컬 문서와 이미 업로드된 사본은 자동 동기화되지 않는다.
- [모델 레지스트리](../../models/registry.md), [새 실행 및 재현 절차](../../models/bcai/README.md)를 따른다.



## BCAP 실제 구현·평가 반영 — 2026-09-09

기록 2026-09-09T08:49:31.268706+00:00. 신규 원본 수집 없이 기존 2024·2025 및 BCAI/Ridge용 2023·2026 스냅샷을 재사용했다. 기존 원본·정제본·실행은 덮어쓰지 않고 새 BCAP 정제본과 실행 디렉터리를 만들었다. 기존 MLB 이용 조건과 원본 재배포 권한 미확인 범위는 그대로다.

| 시즌 | 원본 행 | 유효 PA | PITCH 적격 행 | SWING 라벨 적격 행 | 출처·제외·키·해시 | 출력 |
| --- | --- | --- | --- | --- | --- | --- |
| 2024·2025 | 1,424,427 | 364,124 | 1,415,566 | 1,416,043 | [정제 감사](analysis/bcap_preparation_20260909_r01/preparation_audit.json) | [새 정제본](data/processed/bcap_dev_v010_20260909_r01.pkl) |
| 2023 | 720,684 | 183,534 | 716,113 | 716,385 | [정제 감사](analysis/runs/bcap_pitch__mlb_2023__20260909__r01/artifacts/preparation/preparation_audit.json) | [새 정제본](data/processed/bcap_2023_v010_bcap_pitch__mlb_2023__20260909__r01.pkl) |
| 2023 | 720,684 | 183,534 | 716,113 | 716,385 | [정제 감사](analysis/runs/bcap_swing__mlb_2023__20260909__r01/artifacts/preparation/preparation_audit.json) | [새 정제본](data/processed/bcap_2023_v010_bcap_swing__mlb_2023__20260909__r01.pkl) |
| 2026 | 639,042 | 163,327 | 635,095 | 635,451 | [정제 감사](analysis/runs/bcap_pitch__mlb_2026_ytd_20260907__20260909__r01/artifacts/preparation/preparation_audit.json) | [새 정제본](data/processed/bcap_2026_v010_bcap_pitch__mlb_2026_ytd_20260907__20260909__r01.pkl) |

정제 감사의 SWING 라벨 적격 수와 실제 위치 기반 모형 평가 완료는 다르다. 2026 SWING 모델 평가 자체는 보류했으며 PITCH 정제 과정에서 행동 라벨을 만들었다고 SWING 외부 검증을 수행한 것으로 세지 않는다.

2026 결과 가중치는 기존 2025값 고정이다. 최종 봉인 [모델·코드·정책·입력 SHA256](../../models/bcap/external_seal_20260909_r01.json) 이후 이번 BCAP 외부 결과에 접근한 시각은 [실행 증거](analysis/bcap_execution_evidence_20260909.json)를 따른다. 2023·2026은 앞선 BCAI/Ridge에서 이미 사용한 자료라는 노출 이력을 유지한다.

일차 공개 근거는 [BCAP 측정·규칙 검토](../../models/bcap/measurement_review.md)에 저장했다. [MLB Savant CSV 설명](https://baseballsavant.mlb.com/csv-docs)의 2026 plate 앞면→중간면 및 운영자→ABS 존 변경을 확인했고, [MLB 공식 2026 ABS 안내](https://img.mlbstatic.com/opprops-images/image/upload/opprops/jgdgj1bak2bgiskwpdnm.pdf)와 [2023 공식 규칙](https://img.mlbstatic.com/mlb-images/image/upload/mlb/wqn5ah4c3qtivwx3jatm.pdf)의 HBP·번트 정의를 참조했다. 열람일 2026-09-09. 미분류 행동을 Take로 채우지 않으며 번트 포함 공격 시도와 순수 full swing을 구분한다.

이 변경은 로컬 기록에만 적용했다. KBO 수집·분석, Drive/Docs 업로드, 외부 전송·게시·원본 재배포는 하지 않았다.
