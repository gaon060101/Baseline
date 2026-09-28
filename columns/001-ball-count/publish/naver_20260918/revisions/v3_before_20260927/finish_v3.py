from pathlib import Path
import re,json
D=Path(__file__).resolve().parent;C=D.parent.parent;R=C.parent.parent
def edit(p,a,b):
 s=p.read_text(encoding='utf-8');assert a in s,a[:60];p.write_text(s.replace(a,b,1),encoding='utf-8')
edit(D/'02_bcai.md','이 질문을 읽기 쉬운 숫자로 정리하기 위해 만든 지표가','카운트의 형편을 읽기 쉬운 숫자로 정리한 지표가')
edit(D/'02_bcai.md','읽는 기준은 하나다.','이 글의 W는 볼넷·안타·장타 등에 가중치를 붙인 최종 타석의 공격가치다. 그 평균을 타석 시작점과 비교해 지수로 만든다.\n\n읽는 기준은 하나다.')
edit(D/'03_bcap.md','아래 네 행을 한꺼번에 외우기보다 첫 행에서 두 값을 빼 보고, 나머지 행도 같은 순서로 읽으면 된다.','앞의 결과표 1에서도 첫 행의 두 값을 빼 보고 나머지 행을 같은 순서로 읽으면 된다.')

# The independent explanatory examples also state their lesson before the illustration.
leads={
'이해를 돕는 별도 예시: 실패가 어디에 들어가는가':'종료 타율은 타석이 계속된 스윙을 분모에 넣지 않으므로, 전체 스윙 선택의 성적과 다르다.',
'이해를 돕는 별도 예시: 크기와 빈도를 함께 보기':'한 번의 차이가 작아도 자주 발생하면 전체 비중은 커질 수 있다.',
'이해를 돕는 별도 해설: 비교 연도가 왜 중요할까?':'원하는 변화의 효과를 읽으려면 함께 바뀐 다른 조건을 최대한 구별해야 한다.',
'이해를 돕는 별도 해설: 볼이 많다는 사실만으로 평가할 수 있을까?':'전체 가치는 볼뿐 아니라 헛스윙·접촉 등 모든 가지의 빈도와 가치를 함께 봐야 한다.',
'이해를 돕는 별도 해설: 같은 이름의 두 바구니':'포함하는 공의 범위가 달라지면 같은 이름의 비교도 다른 질문이 된다.',
'이해를 돕는 별도 계산: 가지의 확률에 가치를 곱한다':'선택의 기대값은 가능한 결과마다 확률과 후속 가치를 곱해 더한 값이다.',
'왜 불확실성도 전달해야 할까?':'중간 확률과 가치가 추정값이면, 그 불확실성도 최종 판단에 전달해야 한다.',
'이해를 돕는 별도 해설: 드문 스윙의 성적을 넓히면 왜 달라질까?':'기존에 골라 친 공의 성적은 새로 휘두르게 될 공의 성적을 바로 알려주지 않는다.',
'이해를 돕는 별도 해설: 세 비율의 분모':'경계에 온 비율, 경계 공 스윙률, 지켜본 경계 공의 판정률은 각각 다른 기록을 분모로 삼는다.',
'이해를 돕는 별도 해설: 상대가 있는 최적화':'상대의 준비가 달라지면 같은 행동의 가치도 달라져, 고정된 평균만으로 최적 비율을 정할 수 없다.',
'이해를 돕는 별도 해설: 겨냥한 곳과 간 곳':'실제 도착 위치만으로는 목표 위치와 제구 오차를 분리할 수 없다.',
'목표가 달라지면 최적도 달라진다':'출루를 줄이는 전략과 가중 공격가치를 줄이는 전략은 같은 답을 보장하지 않는다.',
'이해를 돕는 별도 해설: 상태, 행동, 전이, 정책':'정책은 각 상태에서의 행동 기준이며, 그 가치는 이후 상태와 선택까지 연결해 평가한다.',
'BCAI의 관찰 평균을 넣으면 바로 정책이 될까?':'기존 행동이 섞인 BCAI 관찰 평균은 새로운 정책 아래의 상태 가치를 그대로 대신하지 못한다.',
'이해를 돕는 별도 해설: 같은 도착지, 다른 명단':'같은 카운트는 서로 다른 경로와 선수 구성을 포함하므로, 경로 차이를 순서 자체의 효과로 단정할 수 없다.'}
p=D/'04_references_ko.md';s=p.read_text(encoding='utf-8')
for h,lead in leads.items():
 needle='### '+h+'\n\n';assert needle in s,h;s=s.replace(needle,needle+'**'+lead+'**\n\n',1)
s=s.replace('**연구가 던진 질문부터, 이번 칼럼에 가져온 부분까지**','**연구의 결론부터 읽고, 인용 부분과 방법을 이어 확인하기**')
s=s.replace('영어 제목 옆에 링크만 있으면,','**이 문서는 참고문헌 12건의 결과·결론과 실제 인용 부분을 먼저 보여주고, 자료·방법·개념을 뒤에서 설명한다.**\n\n영어 제목 옆에 링크만 있으면,',1)
s=s.replace('**초록색 ‘칼럼에서 가져온 부분’ 상자**','**보라색 ‘참고문헌’ 상자**는 원문과 판본을 표시한다. **초록색 ‘칼럼에서 가져온 부분’ 상자**',1)
p.write_text(s,encoding='utf-8')

# State the persistent writing preference in its single shared home.
p=R/'guides/writing.md';s=p.read_text(encoding='utf-8')
s=s.replace('- 원고는 질문 → MLB에서 발견한 패턴과 가설 → KBO 검증 → 해석과 한계의 흐름을 기본으로 하되 주제에 맞게 조정한다.','- 모든 설명은 두괄식으로 쓴다. 글 전체와 각 절·소주제의 결과 또는 핵심 뜻을 먼저 제시한 뒤, 근거·계산 방법·이유·해석 범위를 설명한다. 결과를 뒤로 미루며 궁금증을 유도하는 순서보다 이 원칙을 우선한다. MLB 발견과 KBO 검증은 실제 완료 범위를 구분한다.')
s+='''
## 결과·설명·문헌의 위계 — 2026-09-18 사용자 피드백

- 모델 해설은 결과 전체를 앞쪽에 모으고 요약표·세부 결과표·그림을 별도 결과 영역에 둔다. 계산 중간에 결과가 묻히지 않게 한다.
- 설명은 BCAP 해설처럼 용어를 풀고 예시를 이어 붙인다. 설명의 순서는 결과·핵심 → 자세한 풀이로 유지한다.
- 본문에서 BCAI·BCAP를 처음 쓰기 전에 역할을 짧게 소개하고, 각 사용 지점에서도 사용한 도구와 비교 대상을 한두 문장으로 표시한다.
- 큰 제목·작은 제목·단계 번호로 내용의 상하 관계를 표시한다. 결과 요약, 해석 메모, 참고문헌은 제목과 별도 서식을 함께 사용해 구별한다.
- 해석 메모를 적극적으로 사용한다. 결과의 단위·분모·불명확·자료 부족·적용 범위는 본문과 구별하되 읽기 어렵게 숨기지 않는다.
- 참고문헌은 자체 결과와 다른 전용 양식으로 소개한다. 외부 연구의 핵심과 현재 글의 사용 범위, 원문·한국어 해설 연결을 함께 둔다.
'''
p.write_text(s,encoding='utf-8')

revision='''# 3차 수정 — 결과부터 읽는 두괄식 원고

2026-09-18 사용자 최신 피드백 9개를 반영했다. 이전 2차의 질문·결과 발견 순서보다 **모든 설명을 두괄식으로** 하라는 최신 요청을 우선한다.

## 무엇을 바꿨나

| 대상 | 반영한 변화 |
| --- | --- |
| [본문 MD](01_ball_count.md) | 첫 화면에 BCAI·BCAP의 역할과 네 가지 결과 요약. 각 절·소주제는 핵심 먼저. 각 모델 사용 지점에 도구·비교 설명. 외부 문헌은 독립 상자 |
| [BCAI MD](02_bcai.md) | 열두 카운트 주 결과, 보정 요약, 상태 평균 차이를 앞쪽에 모은 뒤 재료·분모·계산·구간 설명 |
| [BCAP MD](03_bcap.md) | 위치·타자·구종 요약과 세부 결과를 첫 절에 집약. 이후 결과 해석, 정의, 계산 네 단계, 지원·검증·시행착오 순서 |
| [문헌 해설 MD](04_references_ko.md) | 원문 결과·결론과 인용 부분을 앞에 배치. 독립된 문헌 양식. 개념 예시도 핵심 문장을 먼저 제시 |
| [집필 지침](../../../../guides/writing.md) | 두괄식 우선, 결과 영역 분리, 모델 사용 지점 설명, 해석 메모·문헌 양식의 공통 원칙 |
| [원고 안내](README.md) | 3차 읽기 순서, 서식 구분, 네이버 이전 시 제목·상자 유지 안내 |
| [프로젝트 README](../../../../README.md)·[칼럼 문서](../../column.md)·[출처 기록](../../sources.md)·[반영표](manuscript_source_map.md) | 현재 3차 상태, 최신 피드백 우선순위, 결과·문헌 연결 기록 |

## 서식 체계

- 청록 결과 요약: 자체 분석의 결론. 결과 영역의 표도 별도 테두리로 구분.
- 갈색 해석 메모: 분모·단위·적용 범위·자료 부족 등의 해석. 기존 바탕 계열 글꼴 유지.
- 보라 참고문헌: 외부 연구와 원문·판본·연결 설명.
- 초록 인용 부분: 문헌 해설에서 이번 칼럼에 가져온 대목.
- 큰 번호 제목: 주제. 작은 번호 제목과 목차 들여쓰기: 해당 주제 아래의 설명.

## 보존과 확인

2차 원고 4개와 표시본, 표시 생성·검사 파일을 `revisions/v2/`에 보관했다. 이전 v1도 보존한다. 원본·집계·모델·실행은 변경하지 않았다. 기존 수치표는 순서·표 번호만 조정하고 새 요약표는 기존 결과에서 작성했다. 원인에 대한 가능한 설명과 실제 추정한 결과를 구분했다.

이번 작업은 기존에 확인한 문헌 내용의 편집이며 새로운 논문이나 미열람 수치를 추가하지 않았다. 네이버 게시·Drive/Docs 업로드는 수행하지 않았다. 표시·링크 확인은 `visual_check.json`, 기존 표 보존과 순서는 `revision_v3_check.json`에 기록한다.
'''
(D/'revision_v3.md').write_text(revision,encoding='utf-8')

for path,entry in [
(R/'README.md','''## 2026-09-18 3차 원고 — 결과 우선·두괄식·서식 분리

001의 [읽기 화면](columns/001-ball-count/publish/naver_20260918/index.html)을 두괄식으로 갱신했다. BCAI·BCAP는 결과를 앞쪽에 모으고 계산을 뒤에서 설명한다. 본문 첫머리에 모델의 역할과 결과 요약을 두었으며, 결과·해석 메모·참고문헌을 독립 서식으로 구분했다. [수정 내역과 MD 목록](columns/001-ball-count/publish/naver_20260918/revision_v3.md). 최신 두괄식 요청이 이전 질문 우선 순서에 우선한다. 2차 원고는 `revisions/v2/`에 보관했고 사용자 검토 대기·외부 미게시 상태다.
'''),
(C/'column.md','''## 2026-09-18 최신 결정 — 모든 설명을 두괄식으로

결과를 먼저 말한 뒤 근거·계산·이유를 설명한다. 이전의 결과를 뒤에서 발견하는 구성보다 최신 요청을 우선한다. [3차 수정 기록](publish/naver_20260918/revision_v3.md) · [읽기 화면](publish/naver_20260918/index.html). BCAP의 자세한 풀이와 해석 메모를 유지하면서 모델별 결과를 앞쪽에 모았다. 본문에서도 BCAI·BCAP를 초기에 소개하고 사용 지점마다 짧게 설명한다. 결과·문헌·해석 메모와 제목 위계를 서식으로 구분한다. 분석 결과·모델 상태는 유지하며 사용자 검토 대기다.
'''),
(C/'sources.md','''## 2026-09-18 3차 문헌 배치 수정

[본문](publish/naver_20260918/01_ball_count.md)의 외부 문헌을 보라색 전용 상자로 분리했다. [한국어 해설](publish/naver_20260918/04_references_ko.md)은 기존 원문 결과·결론과 실제 인용 부분을 앞에 두고 자료·방법을 뒤에서 설명한다. 새 문헌·미열람 수치는 추가하지 않았다. 원문 링크·읽은 판본·제외 기준은 유지한다.
''')]:
 s=path.read_text(encoding='utf-8');head,body=s.split('\n',1);path.write_text(head+'\n\n'+entry+'\n'+body.lstrip(),encoding='utf-8')
p=D/'README.md';s=p.read_text(encoding='utf-8');head,body=s.split('\n',1)
lead='''
## 현재 읽기 대상: 3차 수정본

**결과를 먼저 읽고 계산과 이유를 뒤에서 확인하는 두괄식**으로 고쳤다. 아래의 2차 기록은 이전 수정 이력이다. 최신 기준은 [3차 수정 기록](revision_v3.md)이며 공통 원칙은 [집필 지침](../../../../guides/writing.md)에 저장했다.

청록색 결과 요약, 갈색 해석 메모, 보라색 참고문헌, 초록색 실제 인용 부분을 구분한다. 큰 번호 제목과 작은 번호 제목은 상하 관계를 표시한다. 네이버로 옮길 때도 색상뿐 아니라 상자 제목과 제목 단계를 함께 유지한다.

BCAP의 결과는 첫 절에 모았다. BCAI는 전체 카운트 결과와 보조 결과가 계산 설명보다 앞에 있다. 본문은 모델 역할과 결과 네 가지를 먼저 제시한다. 기존 결과표는 보존했고 요약표를 추가했다. 현재 표 수는 `render_check.json`을 기준으로 한다.

2차 원고는 `revisions/v2/`에 보관했다. 과거 HTML은 보관본이므로 실제 읽기에는 현재 폴더의 HTML을 사용한다.

'''
s=head+'\n'+lead+body.lstrip();s=s.replace('1편 그림 4·3편 그림 1','1편 그림 4·3편 그림 2').replace('1편 그림 5·3편 그림 2','1편 그림 5·3편 그림 1');p.write_text(s,encoding='utf-8')
p=D/'manuscript_source_map.md';s=p.read_text(encoding='utf-8')+'\n\n## 3차 피드백 반영\n\n[수정 기록](revision_v3.md)에 9개 피드백의 반영 위치를 정리했다. 결과 우선·두괄식이 이전 질문 우선 구성에 우선한다. 기존 수치 근거는 유지하며 요약표·모델 사용 설명·독립 문헌 서식·제목 위계를 추가했다.\n';p.write_text(s,encoding='utf-8')
p=R/'README.md';s=p.read_text(encoding='utf-8').replace('revisions/v1 이전본','revisions/v1·v2 이전본');p.write_text(s,encoding='utf-8')

# Verify the old detailed table blocks survive unchanged despite new order/summary tables.
checks={}
for name in ['01_ball_count','02_bcai','03_bcap','04_references_ko']:
 old=(D/'revisions/v2'/f'{name}.md').read_text(encoding='utf-8')
 new=(D/f'{name}.md').read_text(encoding='utf-8')
 tables=re.findall(r'^\|.*(?:\n\|.*)*',old,flags=re.M)
 checks[name]={'old_tables':len(tables),'unchanged_tables':sum(t in new for t in tables),'notes':new.count('**해석 메모 |'),'result_boxes':new.count('**결과 요약 |'),'reference_boxes':new.count('**참고문헌 |')}
 assert all(t in new for t in tables),name
checks['result_before_method']={
 'BCAI':(D/'02_bcai.md').read_text(encoding='utf-8').index('| 3-2 |')<(D/'02_bcai.md').read_text(encoding='utf-8').index('## 3. 계산'),
 'BCAP':(D/'03_bcap.md').read_text(encoding='utf-8').index('96개 보고 비교 중 92개')<(D/'03_bcap.md').read_text(encoding='utf-8').index('## 6. 계산')}
(D/'revision_v3_check.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(checks,ensure_ascii=False))
