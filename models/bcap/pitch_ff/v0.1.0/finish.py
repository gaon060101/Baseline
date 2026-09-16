"""Record final FF extension status and append a self-contained local handoff."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,shutil,sys
ROOT=Path(__file__).resolve().parents[4];CODE=Path(__file__).parent;AN=ROOT/'columns/001-ball-count/analysis'
def j(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def link(base,target,label):return '['+label+']('+Path(os.path.relpath(target,base.parent)).as_posix()+')'
def top(text,section):first,rest=text.split('\n',1);return first+'\n\n'+section.strip()+'\n\n'+rest.lstrip('\n')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--bundle',required=True);a=ap.parse_args();b=ROOT/a.bundle;plan=j(b/'analysis_plan.json')
 run=AN/'runs'/plan['new_run'];cmp=AN/'runs'/plan['comparison_run'];m=j(run/'manifest.json');cm=j(cmp/'manifest.json');s=j(cmp/'artifacts/summary.json');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
 assert m['status']==cm['status']=='COMPLETE' and not (b/'document_update.json').exists()
 changes=[]
 def write(p,text):
  old=meta(p) if p.exists() else None
  if old:
   dst=b/'document_backups'/p.relative_to(ROOT);dst.parent.mkdir(parents=True,exist_ok=True);assert not dst.exists();shutil.copy2(p,dst)
  p.write_text(text,encoding='utf-8');changes.append({'before':old,'after':meta(p),'backup':dst.relative_to(ROOT).as_posix() if old else None})
 status='2024·2025 개발 비교 완료, 외부 검증 미실시 — EXPERIMENTAL'
 p=CODE/'model_card.md'
 write(p,f'''# BCAP-PITCH-FF-v0.1.0

**{status}**. UTC {now}. DRAFT에서 실제 개발 실행 완료에 따라 갱신했다. specification.yaml의 status_at_definition은 정의 당시 기록으로 보존했다.

현재 한 구의 FF(포심) 대 non-FF(비포심)와 최종 PA 공격가치 W의 보정 연관 비교다. 같은 실제 지지 행에 양 행동을 표준화하며 가상 평균 선수나 PA 전체 순차 정책을 추정하지 않는다. 기존 BCAP-PITCH-v0.2.0의 FB/NFB 비교와 행동 내용이 달라 별도 모듈로 등록했다. 기존 버전의 상태·결과는 변경하지 않았다.

FF=FF. non-FF=SI,FC,SL,CH,ST,CU,FS,KC,SV,FA,EP,KN,FO,CS,SC. active mapping은 명세의 action_codes다. actions에 남아 있는 기존 분류 사전은 상속한 참조이며 새 A를 결정하지 않는다. 기존 eligible_pitch를 그대로 사용하고 PO/UN/결측·기존 PA 제외를 비포심에 채우지 않는다. FA/Other의 분류 한계를 유지한다.

기존 투구 전14개 입력과 직전 FB/NFB, 투수·타자 shrinkage, 3fold 경기 분리·seed20260909·훈련 안 Platt, alpha p100/m0=m1=1000을 유지했다. 새 FF용 propensity와 두 결과모형만 새 A로 적합했다. 현재 구종·위치·속도·스윙·타구 결과를 입력하지 않는다. 외부/반복 학습·튜닝·학습 정책은 없다.

전체 적격 {m['metrics']['n']:,}행, FF 자체 지지 {s['FF_own']:,}행({m['metrics']['coverage']:.2%}), FB 자체 {s['FB_own']:,}행, 공통 {s['common']:,}행이다. FF 자체 지지와 FB 지지의 교집합에서 각자의 OOF 점수를 재집계했으며 교집합으로 재학습하지 않았다. 지원은 선택확률 범위와 훈련 투수 행동 수 기준이며 선수 능력을 뜻하지 않는다.

결과: FF3-2 공통 Δ=+0.01699 W, Bonferroni255 명목95% [+0.00141,+0.03257]로 비포심 방향의 개발 단서가 있다. 구간 하한이0.01 W보다 작아 최소 실질 차이를 확보한 것은 아니다. 0-0은 두 분류의 자체·공통 구간 모두±0.01 W 안이다. FF3-0은 실질적인 분할 부호 반전이 있어 보류한다. 다른 카운트 대부분은 충분히 구분하지 못했다.

{link(p,b/'report.html','한국어 HTML 보고서')} · {link(p,b/'report.md','보고서 Markdown')} · {link(p,run/'manifest.json','새 FF 학습')} · {link(p,cmp/'manifest.json','기존 FB 재사용 및 자체/공통 비교')} · {link(p,CODE/'validation.md','기본 확인 범위')} · {link(p,b/'analysis_plan.json','추가 결과 전 기준')} · {link(p,b/'reproduction.md','재현 명령')}

선택집단·미측정 의도·품질·컨디션과 결과모형 의존성이 남는다. 고정 점수의 경기 변동 구간은 전체 재학습 불확실성·경기 간 선수 의존성·실제95% 포함률을 검증한 것이 아니다. 외부 미검증이며 인과적 투구 지시나 일반적인 구종 우열을 권고하지 않는다.
''')
 p=CODE/'validation.md'
 write(p,f'''# BCAP-PITCH-FF-v0.1.0 기본 확인과 결과 범위

**{status}**. UTC {now}.

입력 준비, 새 FF 3fold 학습, 저장 점수 자체/공통 집계의 기본 확인은 모두 PASS. 적합·Platt 보정 로그12건 모두 수렴했다. OOF MSE={m['metrics']['MSE']:.9f}, Brier={m['metrics']['Brier']:.9f}. 행동 정의와 비율이 달라 기존 FB의 Brier와 비교해 예측 개선이라고 해석하지 않는다.

확인 항목은 기존 eligible_pitch 및키·계절 W·카운트·닫힌 행동 매핑, 기존 gamefold 일치, 기존14개 입력·alpha 보존, 현재 사후 입력 배제, calibration/사전 훈련경기 한정, 새A의 투수 repertoire, 예측과AIPW 유한값 및 행별 산술, 동일 분모·부호·구종 구성 합계, 자체/공통/연도/fold 표본 합계다. 기존 FB 12카운트 Q·Δ·SE·219 구간은 저장 scores에서1e-12 이내 일치했다. FF 이외 모델을 재학습하지 않았다.

{link(p,b/'preparation.json','입력 기본 확인')} · {link(p,run/'artifacts/basic_checks.json','학습 기본 확인')} · {link(p,run/'artifacts/fit_diagnostics.csv','수렴 로그')} · {link(p,cmp/'artifacts/basic_checks.json','저장 점수 집계 기본 확인')} · {link(p,b/'plan_seal.json','결과 전 시각·SHA256')} · {link(p,b/'result_access_log.json','추가 결과 열람 기록')}

불확실성은 기존 경기 cluster 고정점수 명목 구간이다. 주48개 비교는 기존219개와 신규36개의 합집합을 고려해 Bonferroni255를 사용한다. 기존 FB219 결과는 원 출처로 보존했다. 연도2/fold3 보조240개는 개별 명목95% 내부 탐색이며 독립 검증이 아니다. 작은 범위·지원 부족·방법/분할 불안정·일관된 개발 방향·나머지 불확실의 사전 규칙을 적용했다.

기존 FB3-0의 통합 구간은 여전히0을 제외한다. 자체fold0, 공통fold0·2의 NFB ESS200미달 때문에 새 일관성 등급을 보류한 것이며, 기존 결과나 모든 분할의 양의 점추정을 뒤집은 것은 아니다. FF3-2는 모든 연도/fold 점추정이 양수지만 fold1의 명목 구간은0을 포함한다. 기본 계산 확인을 외부 재현·인과 검증·전체 독립 검수로 부르지 않는다.

각 FF fold의 nuisance.pkl, 계수·훈련 사전·중심화·calibration 행/점수·훈련 경기·seed, fold_membership, scores.pkl를 새 실행에 보존했다. 기존 FB 점수와 적합 객체는 기존 위치에 남겨두었다. 전체 재적합·정책 파일은 만들지 않았다. 외부 자료/2023·2026·KBO·bootstrap·추가seed·광범위 탐색·타자/SB 수정은 미실시다.
''')
 p=ROOT/'README.md';txt=p.read_text(encoding='utf-8-sig')
 txt=txt.replace('BCAP V2 2024·2025 개발 결과 산출·후속 검증 미실시(EXPERIMENTAL)','BCAP V2·포심/비포심 추가 개발 비교 완료·외부 검증 미실시(EXPERIMENTAL)',1)
 txt=txt.replace('│     ├─ development_v2/v0.2.0/  # V2 준비·실행·보고·문서 연결','│     ├─ development_v2/v0.2.0/  # V2 준비·실행·보고·문서 연결\n│     ├─ pitch_ff/v0.1.0/  # 포심/비포심 정의·코드·기본 확인')
 txt=txt.replace('│     │  ├─ bcap_v2_development_20260912__r01/  # V2 통합 보고·CSV·변경 기록','│     │  ├─ bcap_v2_development_20260912__r01/  # V2 통합 보고·CSV·변경 기록\n│     │  ├─ bcap_pitch_classification_20260912__r01/  # FB/NFB·FF/non-FF 비교 보고')
 intro='2026-09-12 추가 비교: '+link(p,b/'report.html','FB/NFB와 포심/비포심 보고서')+'. 기존 FB는 재학습 없이 재사용하고 FF만 새로 학습했다. 자체·공통 표본을 비교했고, 0-0의 작은 범위와3-2 비포심 방향의 제한된 개발 단서를 남겼다. 요청 범위에서 완료·종료했으며 외부 검증/추가 개선은 진행하지 않는다.\n\n'
 txt=txt.replace('## 다음 작업\n\n','## 다음 작업\n\n'+intro,1);write(p,txt)
 p=ROOT/'models/registry.md'
 sec='## 포심/비포심 추가 비교 — 2026-09-12\n\n**'+status+'**. 기존 FB/NFB의 대체 또는 검증 승격이 아니라 별도 행동 정의의 비교 모듈이다.\n\n| 모델 | 상태·역할 | 정의 | 실행·보고 |\n| --- | --- | --- | --- |\n| BCAP-PITCH-FF-v0.1.0 | EXPERIMENTAL · 포심/비포심 보정 비교 | '+link(p,CODE/'model_card.md','카드')+' · '+link(p,CODE/'specification.yaml','불변 명세')+' · '+link(p,CODE/'validation.md','기본 확인')+' | '+link(p,run/'manifest.json','FF 학습')+' · '+link(p,cmp/'manifest.json','두 분류 재집계')+' · '+link(p,b/'report.html','보고서')+' |\n\n기존 PITCH-v0.2.0의 저장 점수만 재사용하며 타자·S/B 모델과 과거 완료 실행·명세는 그대로 보존했다. 추가 결과 전255 보정·실질 차이0.01W·자체/공통 표본·중단 기준을 고정했다.'
 write(p,top(p.read_text(encoding='utf-8-sig'),sec))
 p=ROOT/'columns/001-ball-count/column.md';txt=p.read_text(encoding='utf-8-sig')
 txt=txt.replace('- 상태: BCAP V2 2024·2025 개발 결과 산출, 후속 검증 미실시(EXPERIMENTAL)','- 상태: BCAP V2·포심/비포심 추가 개발 비교 완료, 외부 검증 미실시(EXPERIMENTAL)',1)
 sec='## 최신 투수 추가 비교 — 포심/비포심, 2026-09-12\n\n'+link(p,b/'report.html','한국어 통합 보고서')+' · '+link(p,cmp/'artifacts/comparison_12counts.csv','12카운트 비교표')+' · '+link(p,b/'analysis_plan.json','결과 전 기준')+' · '+link(p,AN/'handoff_bcap_review.md','최신 인계')+'.\n\n기존 FB/NFB는 저장 점수로 재집계했고 FF/non-FF만 같은14개 특징·규제·경기3fold로 새 학습했다. 자체 지지는 FB1,395,443행·FF1,271,802행, 공통1,268,736행이다. 두 분류0-0은 구간 전체가±0.01W 안이며, FF3-2는 공통Δ+0.01699W로 비포심 방향의 개발 단서가 있다. 다만 최소0.01W 효과 하한이나 외부 재현을 확보하지는 않았다. FF3-0은 분할 반전, FB3-1은 방법 민감성·불확실성을 남겼다. FB3-0 통합 차이는 여전히 남지만 일부fold의 NFB ESS미달로 새 일관성 등급을 보류했다.\n\n타자·S/B 모델은 수정·재학습하지 않았다. 미상 구종을 비포심에 넣지 않았으며 포심/비포심을 패스트볼/변화구로 부르지 않는다. 이번 비교와 보고서에서 종료하고 외부 검증·추가 모형 탐색은 수행하지 않는다.'
 write(p,top(txt,sec))
 p=ROOT/'columns/001-ball-count/sources.md'
 prep=j(b/'preparation.json')
 sec='## 포심/비포심 추가 개발 입력 — 2026-09-12\n\n'+link(p,ROOT/plan['source'],'기존 V2 2024·2025 정제본')+'에서 동일 eligible_pitch 1,415,566행을 재사용했다. '+link(p,ROOT/prep['output']['path'],'새 FF 학습용 정제본')+'은 키·최종 PA W·기존 투구 전 특징·기존fold와 새 FF/non-FF A를 보존한 입력이다. 원본 재수집·외부 연도 적용·타자/SB 데이터 변경은 없었다.\n\n'+link(p,b/'input_code_eligibility.csv','실제 코드·적격 제외 목록')+' · '+link(p,b/'preparation.json','입력 해시·기본 확인')+' · '+link(p,b/'report.html','개발 결과')+'. 새A=FF만1, SI/FC와 기존 닫힌 나머지 유효 구종만0이다. PO·UN·결측/기존 PA 제외를0으로 채우지 않았다. FA/Other 한계를 유지한다. 새 자료 확보나 이용 조건 확인이 필요한 수집 작업은 수행하지 않았다.'
 write(p,top(p.read_text(encoding='utf-8-sig'),sec))
 p=ROOT/'models/bcap/README.md'
 sec='## 포심/비포심 추가 비교 완료 — 2026-09-12\n\n**'+status+'**. '+link(p,b/'report.html','FB/NFB·FF/non-FF 보고서')+' · '+link(p,CODE/'model_card.md','새 FF 모듈 카드')+' · '+link(p,b/'reproduction.md','실제 실행·재현 명령')+'. 기존 FB 결과·점수를 재사용하고 FF nuisance만3fold로 적합했다. 자체/공통 표본48개 주요 비교와 연도/fold 내부 탐색을 완료했다. 타자/SB 및 기존 모델은 수정·재학습하지 않았다. 요청된 비교에서 종료하며 외부 검증·분류 추가 탐색은 미실시다.'
 write(p,top(p.read_text(encoding='utf-8-sig'),sec))
 p=AN/'handoff_bcap_review.md'
 sec=f'''## 최신 인계 — FB/NFB와 포심/비포심 추가 비교 완료

UTC {now}. **{status}**. 사용자 요청은 기존 FB/NFB를 재사용하고 FF/non-FF만 추가 학습하여 자체 및 공통 표본에서12카운트 우열 또는 불명확의 이유를 판단하는 것이었다. 두 분류 비교·보고서를 완료했으며 추가 모델 개선/외부 검증을 자동으로 이어가지 않는다.

{link(p,b/'report.html','중심 한국어 HTML 보고서')} · {link(p,b/'report.md','동일 보고서 Markdown')} · {link(p,cmp/'artifacts/comparison_12counts.csv','12카운트 비교표')} · {link(p,cmp/'artifacts/primary_values.csv','48개 주요 값·판정 이유')} · {link(p,cmp/'artifacts/year_fold_values.csv','연도2/fold3 내부 탐색')} · {link(p,cmp/'artifacts/pitch_composition.csv','구종 구성')} · {link(p,b/'reproduction.md','재현 명령')}

모델: BCAP-PITCH-FF-v0.1.0(EXPERIMENTAL). FF만1, non-FF=SI·FC·SL·CH·ST·CU·FS·KC·SV·FA·EP·KN·FO·CS·SC만0이다. 미상/PO/결측 및 기존 PA 제외는 넣지 않는다. 포심/비포심이며 패스트볼/변화구가 아니다. 기존 결과변수·14개 투구 전 특징·직전FB/NFB·투타 축소·규제100/1000/1000·같은 경기3fold와 훈련 내부Platt를 유지했다. 새A의 propensity/두 결과모형만 새로 학습했으며 기존 FB 점수를 새A로 재해석하지 않았다.

- {link(p,run/'manifest.json','새 FF 학습 실행')}: COMPLETE. 적격1,415,566·지지1,271,802행, 적합/보정12개 로그 모두 수렴. 실제fold nuisance·사전·계수·calibration자료/행ID·훈련 경기·행별scores와분할 보존.
- {link(p,cmp/'manifest.json','두 분류 저장 점수 재집계 실행')}: COMPLETE. 기존FB 지지1,395,443행, 공통1,268,736행. 기존 FB12개 Q/Δ/SE/219구간은 저장 점수 재집계에서1e-12 이내 일치. 재학습0회.
- {link(p,b/'preparation.json','입력 준비')}, {link(p,run/'artifacts/basic_checks.json','새 학습 기본 확인')}, {link(p,cmp/'artifacts/basic_checks.json','재집계 기본 확인')}: 모두PASS. 별도 전면 독립 검수로 부르지 않는다.

추가 결과 전 기준: {link(p,b/'analysis_plan.json','실행 기준')} · {link(p,b/'analysis_plan.md','한국어 기준')} · {link(p,b/'plan_seal.json','시각·SHA256')} · {link(p,b/'result_access_log.json','결과 열람 이력')}. 기존219개+신규36개=255 보정으로 이번 주요48개 차이를 모두 비교했다. 기존219 구간·판정은 원본/별도열에 보존했다. 기존 결과에 노출된 개발 확장이므로 독립 사전등록/외부검증을 주장하지 않는다. 연도/fold240개는 개별명목95% 내부탐색이다.

핵심 결론: 0-0은 두 분류의 자체/공통 보정 구간이 모두 ±0.01 W 안이다. FF의 3-2는 공통 Δ +0.01699, 명목 보정 구간 [+0.00141, +0.03257] W로 비포심 방향이 두 연도와 세 fold의 점추정에서 유지되지만, 최소 0.01 W의 효과 하한을 확보한 것은 아니다. FF의 3-0은 fold별 실질 반전이 있어 불안정하다. FB의 3-1은 결과모형 +0.00685 대 AIPW −0.01165 W로 부호가 다르고 보정 구간이 0을 포함한다.

FB의 3-0은 통합 차이가 계속 남는다(자체 +0.06821 W). 새 판정의 보류는 자체 fold0의 NFB ESS 193.76, 공통 fold0/2의 ESS 176.04/187.27이 기준 200에 미달했기 때문이다. 모든 연도/fold의 점추정은 여전히 양수다. subgroup_sign_consistent=False는 코드상 ‘다섯 집단 모두 지원 + 같은 부호’를 충족하지 못했다는 뜻이며, 실제 부호 반전으로 읽지 않아야 한다. 단순 평균은 FB 쪽, 모형/AIPW는 NFB 쪽으로 갈리므로 보정 의존성도 함께 제시했다.

완료와 한계: 현재 자료와 설계로 대부분 카운트의 투구 계열 우열을 충분히 구분하지 못했다. 제한된 3-2 개발 단서는 보존하며 요청 범위에서 종료한다. 선수 보정은 의도·품질·컨디션과 사후 선택을 제거하지 못했고, 구간은 고정 점수의 경기 의존성만 반영한다. 재학습 불확실성·경기 간 선수 의존성·실제 95% 포함률·외부 재현·실제 지시 효과는 미검증이다. 타자/SB, 기존 정제본/모델/완료 실행/봉인을 덮어쓰지 않았고 새로운 2023/2026 접근·KBO·bootstrap·추가 seed·광범위 탐색·Drive/게시를 하지 않았다.

후속 작업은 이 인계의 현재 결과와추가요청범위를구분해서시작한다. {link(p,b/'document_update.json','이번 문서 전후 해시·백업')}에공유MD수정을기록했다. 이전V2/V1인계와원증거JSON은아래이력및기존위치에보존한다.
'''
 old=p.read_text(encoding='utf-8-sig').replace('## 최신 인계 추가 — BCAP V2 개발 완료, 2026-09-12','## V2 기본 개발 인계 — 2026-09-12',1)
 write(p,top(old,sec))
 (b/'document_update.json').write_text(json.dumps({'at_utc':now,'status':status,'command':[sys.executable]+sys.argv,'code':meta(Path(__file__)),'changes':changes,'scope':'Only new FF card/validation and six shared entry documents; old model definitions/runs and SWING/SB not modified'},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'status':'COMPLETE','updated_MD_files':len(changes),'record':str(b/'document_update.json')},ensure_ascii=True))
if __name__=='__main__':main()
