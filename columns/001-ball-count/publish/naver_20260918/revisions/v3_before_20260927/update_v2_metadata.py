from pathlib import Path
import re,json
D=Path(__file__).resolve().parent
C=D.parent.parent
R=C.parent.parent

p=D/'04_references_ko.md';s=p.read_text(encoding='utf-8')
s=s.replace('선수별 판단을 득점 가치와 불확실성으로 평가하는 틀을 제시한다.','기대득점 예측의 교차검증 개선은 RE24 대비 MSE 1.8%, RE288 대비 1.4%였다. 선수 사례에서는 가치 차이의 크기와 판단의 확실성을 구분한다.')
s=s.replace('모형 안에서 출루율 개선을 계산한다. 상대 대응을 포함한 최적화이며, 계산한 전략을 실제 경기에 적용한 실험은 아니다.','3,600개 대결의 관측 출루율 .329와 모형의 균형 출루율 .242를 비교한다. 상대 대응을 포함한 최적화의 결과이며, 실제 경기에서 전략을 바꿔 얻은 감소는 아니다.')
s=s.replace('단순·복잡 모형의 비교는 정보를 더 넣었을 때의 정책 평가다.','구종을 넣은 복잡 모형에서 투수별 정책의 유리함이 더 자주 나타났다. 이후 시뮬레이션에서는 우수 타자 집단의 뚜렷한 개선이 관찰되지 않았다.')
p.write_text(s,encoding='utf-8')

p=D/'build_preview.mjs';s=p.read_text(encoding='utf-8')
s=s.replace('다음 공을 읽는<br>세 가지 글','다음 공을 읽는<br>세 편과 문헌 해설')
s=s.replace('계산이나 용어가 궁금해질 때 BCAI·BCAP 설명 글을 참고하도록 구성했습니다.','계산이나 용어가 궁금해질 때 BCAI·BCAP 설명 글을 참고하세요. 외부 연구는 한국어 문헌 해설에서 이어 읽을 수 있습니다.')
s=s.replace("${i?'방법 해설':'본문'}","${i===3?'읽기 자료':i?'방법 해설':'본문'}")
s=s.replace('세 글의 읽기 안내','연재와 문헌 읽기 안내')
s=s.replace('네이버 블로그용 사용자 검토본입니다.','설명을 보강한 2차 사용자 검토본입니다. 갈색 상자는 해석 메모, 초록 상자는 문헌에서 인용한 부분입니다.')
p.write_text(s,encoding='utf-8')

p=D/'01_ball_count.md';s=p.read_text(encoding='utf-8')
s=s.replace('두 질문이 같다면 높은 BCAI 옆에는 높은 스윙률이 놓일 것이다. 과연 그런지','유리한 카운트에서 더 자주 휘둘렀을까. 이를 알아보려고')
p.write_text(s,encoding='utf-8')

revision='''# 2026-09-18 2차 원고 수정 기록

사용자 피드백: 기존 구조·문체 유지, 설명 속도 완화, 독자와 함께 결과를 발견하는 순서, 통계·해석 주의 문장 구별, 상세 한국어 문헌 해설 추가.

## 반영 내용

- 본문 여섯 절은 유지했다. 투수·타자·구종 소제목과 그림 3종의 제목을 결과 예고에서 질문·비교 대상으로 바꿨다.
- 각 결과 앞에 비교 목적, 분모·단위, 그림의 축·색·빈칸을 읽는 순서를 보강했다. 문헌 설명은 분모, 분류, 기대값, 상대 반응, 타석 정책으로 나눴다.
- BCAI에는 가중치 평균의 가상 계산, 도달 타석 집계, 시즌 혼합, 경기 재표집, 차이의 구간 설명을 보강했다.
- BCAP에는 표준화, 결과·행동 확률 모형, AIPW, 경기 교차적합, 공통 지원을 단계별로 보강했다. 새 예시는 모두 가상임을 표시했다.
- 해석 범위·불확실성·자료 부족의 주의 문장은 `해석 메모`로 분리했다. HTML에서는 갈색 배경·왼쪽 테두리·바탕 계열 글꼴로 표시한다. 기본 개념을 정의하는 설명과 자료 캡션은 해당 자리에서 읽도록 유지했다.
- [참고문헌 한국어 해설](04_references_ko.md)을 추가했다. 원문 12건의 질문·방법·결과, 실제 인용 부분, 별도 개념 해설·가상 계산을 구분했다. 초록 상자는 칼럼에서 가져온 부분이다. 본문 인용마다 해당 해설 절로 이동할 수 있다.
- 최초 세 원고의 MD·HTML은 `revisions/v1/`에 보존했다. 초기 HTML의 상대 링크는 이전 표시 기록이므로 현재 읽기에는 상위 폴더의 HTML을 사용한다.

## 확인 범위

기존 분석 집계와 모델은 변경하지 않았다. 수정된 차트는 제목만 바꿔 같은 저장 데이터에서 다시 표시했다. 세 원고의 기존 결과표·수치는 보존하고, 설명용 숫자는 예시로 표시했다. 원문의 수치·분류·버전은 재확인했으며 원문 미확인 자료는 추가하지 않았다.

문헌 해설은 전문 번역이나 논문 재현 보고서가 아니다. 원문에 의존한 요약과 직접 만든 개념 설명을 분리했다. 원문의 다른 논문 인용을 이번에 직접 읽은 자료로 확대하지 않았다.

검사 결과는 [링크·원고 확인](render_check.json), [화면 확인](visual_check.json), [최종 파일 확인](delivery_check.json)에 기록한다. 외부 게시·Drive/Docs 수정은 수행하지 않았다.
'''
(D/'revision_v2.md').write_text(revision,encoding='utf-8')

p=D/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('## 먼저 읽을 파일','''## 2차 수정본 — 설명 확장과 문헌 해설

기존 구조·문체를 유지하면서 결과 앞의 질문·비교·그림 읽기를 보강했다. 통계·해석상 주의점은 **해석 메모** 상자로 분리했다. HTML에서는 갈색 배경과 바탕 계열 글꼴이며, 문헌의 실제 인용 부분은 초록 상자다. [수정 기록](revision_v2.md).

네이버에 옮길 때도 `해석 메모`라는 제목을 남기고 인용구 또는 배경색 상자로 구분한다. 글꼴만 바꾸는 것보다 제목·테두리·색을 함께 유지하는 편이 구별하기 쉽다. HTML의 스타일이 네이버에 자동 보존된다고 전제하지 않는다.

## 먼저 읽을 파일''')
s=s.replace('- [차트·도식 PNG 8장 묶음]','- 부록 [참고문헌 한국어 해설](04_references_ko.html) · [수정할 MD](04_references_ko.md)\n- [차트·도식 PNG 8장 묶음]')
s=s.replace('소제목, 표 12개, 차트·도식 8종','소제목, 본문·방법 해설의 표 12개와 별도 문헌 해설 표, 차트·도식 8종')
s=s.replace('현재는 로컬 파일 링크다.','문헌 해설을 게시하면 본문의 문헌별 연결도 해당 공개 주소로 바꾼다. 현재는 로컬 파일 링크다.')
s+='\n## 수정본 보관\n\n- 현재 읽기·수정 대상: 이 폴더의 세 원고와 `04_references_ko.md`, 같은 이름의 HTML.\n- `revisions/v1/`: 수정 전 세 원고의 MD·HTML 보관본.\n- `revision_v2.md`: 이번 피드백과 수정 범위.\n'
p.write_text(s,encoding='utf-8')

for p,body in [
 (R/'README.md','''## 2026-09-18 2차 집필 수정 — 설명 확장·문헌 해설 추가

001의 [읽기 화면](columns/001-ball-count/publish/naver_20260918/index.html)을 갱신했다. 세 원고의 기존 구조를 유지하면서 질문·비교·그림 읽기를 자세히 풀고, 해석 메모를 별도 상자로 표시했다. [참고문헌 한국어 해설](columns/001-ball-count/publish/naver_20260918/04_references_ko.md)은 원문 12건의 연구 내용·칼럼 인용 부분·개념 예시를 구분한다. [수정 기록](columns/001-ball-count/publish/naver_20260918/revision_v2.md). 이전 세 원고는 `publish/naver_20260918/revisions/v1/`에 보관했다. 사용자 검토 대기이며 분석·모델 상태와 외부 미게시 상태는 유지한다.
'''),
 (C/'column.md','''## 2026-09-18 사용자 피드백 반영 — 2차 원고

세 원고의 큰 구조와 문체는 유지하고 설명 속도를 늦췄다. 결과를 예고하는 제목 대신 질문을 세우고, 비교 기준과 그림을 읽은 다음 결과를 확인하는 순서로 바꿨다. 해석상 주의 문장은 별도 `해석 메모`로 표시한다. [한국어 문헌 해설](publish/naver_20260918/04_references_ko.md)에 원문 12건의 질문·방법·결과와 실제 인용 부분을 정리하고 개념 예시를 보강했다. [읽기 화면](publish/naver_20260918/index.html) · [수정 이력](publish/naver_20260918/revision_v2.md). 기존 세 원고는 `revisions/v1/`에 보존했다. 사용자 검토 대기이며 외부 게시·공동 Docs 갱신은 수행하지 않았다.
'''),
 (C/'sources.md','''## 2026-09-18 독자용 한국어 문헌 해설 추가

[참고문헌 한국어 해설](publish/naver_20260918/04_references_ko.md)에 본문 사용 12건을 같은 번호로 연결했다. 저자 원문의 질문·자료·방법·결과와 칼럼에 가져온 부분을 구분하고, 별도 개념 설명·가상 예시는 원문 결과와 분리했다. 원문에 의존하는 요약은 인용 범위에 맞춰 제한하며 전문 번역을 만들지 않았다. 세 공개 연구 원고의 목표·가정·평가, 전문 매체 글의 분모·분류를 재확인했다. 원문 미확인 Mercier, Turkenkopf Part 2, MONEYBaRL 별도 보충자료는 제외를 유지한다. [수정 기록](publish/naver_20260918/revision_v2.md).
''')]:
    s=p.read_text(encoding='utf-8');head,rest=s.split('\n',1);p.write_text(head+'\n\n'+body+'\n'+rest.lstrip(),encoding='utf-8')

p=R/'README.md';s=p.read_text(encoding='utf-8').replace('# 본문·BCAI·BCAP MD/HTML, 근거표, 원문 재열람, 첨부 그림 묶음','# 세 원고·문헌 해설 MD/HTML, 근거표, 그림 묶음, revisions/v1 이전본');p.write_text(s,encoding='utf-8')
p=D/'manuscript_source_map.md';s=p.read_text(encoding='utf-8');s+='\n\n## 2차 피드백 반영\n\n[수정 기록](revision_v2.md)의 다섯 요청을 세 원고와 [한국어 문헌 해설](04_references_ko.md)에 반영했다. 기존 결과표·수치·분석 연결은 유지했다. 결과 제목을 질문형으로 바꾸고 비교의 중간 단계를 보강했으며 해석 메모는 별도 서식으로 표시한다.\n';p.write_text(s,encoding='utf-8')
p=D/'reference_audit.md';s=p.read_text(encoding='utf-8');s+='\n\n## 2차 원고의 독자용 해설\n\n[한국어 해설](04_references_ko.md)을 추가했다. 이 검수 문서는 최초 열람 이력을 보존한다. 2차에서는 원문의 해당 정의·방법·결과를 재확인해 독자용 요약을 만들고, 별도의 가상 예시와 자체 분석 비교를 명확히 표시했다. 원문 전체를 번역·복제하거나 새로 원자료를 재분석한 문서는 아니다. 본문과 해설의 원문 의존 설명을 함께 고려해 제한하고, 원문 미확인 자료는 계속 제외한다.\n';p.write_text(s,encoding='utf-8')

print(json.dumps({p.name:len(p.read_text(encoding='utf-8')) for p in D.glob('0*.md') if 'evidence' not in p.name}))
