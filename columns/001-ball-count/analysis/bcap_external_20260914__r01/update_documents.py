"""Register completed external scope, retaining every earlier document snapshot."""
from pathlib import Path
import datetime,hashlib,json,shutil
import pandas as pd
B=Path(__file__).resolve().parent;ROOT=B.parents[3];AN=B.parent;COL=AN.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def meta(p):return dict(path=Path(p).relative_to(ROOT).as_posix(),sha256=hashlib.sha256(Path(p).read_bytes()).hexdigest())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    assert (B/'final_report.html').exists() and read(B/'primary_verification.json')['status']=='PASS'
    assert not (B/'document_update.json').exists();plan=read(B/'plan.json');updated=[];back=B/'prior_documents';assert not back.exists();back.mkdir()
    for year,models in plan['runs'].items():
        for name,task in models.items():
            m=read(AN/'runs'/task['run_id']/'manifest.json')
            assert m['status']==('WITHHELD_MEASUREMENT' if task['measurement_hold'] else 'COMPLETE')
    scope='2023 네 모델·2026 구종 두 모델의 외부 패턴 재현 완료, 2026 S/B·타자는 측정 보류 — EXPERIMENTAL'
    shared='고정한 개발 규제값·학습 절차로 각 외부 연도 안에서 경기 3분할 보조 모형을 적합했다. 단일 고정 개발 예측모델의 시험이나 정책·인과 효과 검증은 아니다. 2023은 과거 연도 재현, 2026은 9월 7일까지의 개발 이후 자료다. 두 자료 모두 과거 BCAI/V1 노출 이력이 있다.'
    sb='2023 S/B 0-2·1-2의 S−B는 +0.034266·+0.024117 W, 주4개 보정 구간은 [0.022304,0.046228]·[0.014006,0.034228]이다. 두 하한이0.01W를 넘고 별도 산술74항목이PASS다. 2026 S/B는 좌표 기준면·존 정의 변경으로 측정 보류다.'
    swing='2023 타자 가운데12카운트 모두 스윙 쪽 점추정이며3-0·3-1은 불명확하다. 밖 지원44셀은 모두 테이크 방향,3-0 밖4셀은자료부족이다. 2026 타자는 측정 보류다.'
    def change(path,newtext):
        old=path.read_text(encoding='utf-8');dest=back/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
        before=meta(path);path.write_text(newtext(old),encoding='utf-8');updated.append(dict(before=before,after=meta(path),backup=meta(dest)))
    def prepend(path,section):
        change(path,lambda old:old.split('\n',1)[0]+'\n\n'+section+'\n\n以下'.replace('以下','아래는 이전 작업 시점의 기록이며 당시의 미실시 범위를 보존한다.')+'\n\n'+old.split('\n',1)[1].lstrip('\n'))
    rootbase='columns/001-ball-count/analysis/bcap_external_20260914__r01/'
    change(ROOT/'README.md',lambda old:old.replace('BCAP V2·포심/비포심 추가 개발 비교 완료·외부 검증 미실시(EXPERIMENTAL)', 'BCAP 외부 패턴 재현 완료(2023 네 모델·2026 구종, 2026 위치 보류/EXPERIMENTAL)'))
    prepend(ROOT/'models/registry.md','## BCAP 외부 패턴 재현 — 2026-09-14\n\n**'+scope+'**. 네 대상 모델의 기존 상태는 유지한다.\n\n[최종 보고서](../'+rootbase+'final_report.html) · [실행 전 계획](../'+rootbase+'plan.md) · [최신 인계](../columns/001-ball-count/analysis/handoff_bcap_review.md).\n\n'+shared+' '+sb+' '+swing)
    prepend(ROOT/'models/bcap/README.md','## 외부 패턴 재현 완료 — 2026-09-14\n\n**'+scope+'**. [최종 한국어 보고서](../../'+rootbase+'final_report.html) · [칼럼 결론](../../'+rootbase+'final_column_conclusion.md) · [재현 안내](../../'+rootbase+'reproduction.md).\n\n'+shared+' '+sb+' '+swing)
    prepend(COL/'column.md','## 최종 BCAP 외부 재현 — 2026-09-14\n\n**'+scope+'**. [개발/2023/2026 보고서](analysis/bcap_external_20260914__r01/final_report.html) · [칼럼에 사용할 최종 문단](analysis/bcap_external_20260914__r01/final_column_conclusion.md) · [실행·인계](analysis/handoff_bcap_review.md).\n\n'+sb+' '+swing+'\n\n'+shared+' 구종별 보조 결과와 불명확·반대 방향·지원 부족은 보고서에 그대로 제시한다. 이번 외부 비교와 보고서에서 종료하며 추가 모델 개선·자료 확보·KBO·게시를 진행하지 않았다.')
    # The old status line is historical, but keep the visible overview consistent.
    column=COL/'column.md';old=column.read_text(encoding='utf-8');column.write_text(old.replace('- 상태: BCAP V2·포심/비포심 추가 개발 비교 완료, 외부 검증 미실시(EXPERIMENTAL)', '- 상태: BCAP 외부 패턴 재현 완료(2023 네 모델·2026 구종, 2026 위치 보류/EXPERIMENTAL)'),encoding='utf-8')
    updated[-1]['after']=meta(column)
    prepend(COL/'sources.md','## BCAP 외부 자료 재사용 — 2026-09-14\n\n기존2023-03-30~10-01(720,684구·2,430경기),2026-03-25~09-07(639,042구·2,165경기)의 V1 정제본을 재사용했다. 새 수집·기간 확장은 없다. [입력·설정 봉인](analysis/bcap_external_20260914__r01/plan_seal.json), [2023 준비](analysis/bcap_external_20260914__r01/preparation_2023/preparation.json), [2026 준비](analysis/bcap_external_20260914__r01/preparation_2026/preparation.json), [측정 확인](analysis/bcap_external_20260914__r01/measurement_review.md), [최종 보고서](analysis/bcap_external_20260914__r01/final_report.html).\n\n새 정제본은 data/processed/bcap_external_v2_2023_20260914__r01.pkl 및 bcap_external_v2_2026_20260914__r01.pkl이다. 기존 키·완료PA 제외·최종W·미해결 카운트 예외는 보존하고 직전FB/NFB·FF·2023S/B 라벨만 최소 추가했다. 2026 S/B와타자는미실행이며 준비본의 미지원 표시는 측정보류를뜻한다. 2023은기존2023 W,2026은2025 W고정이며 계수 차이로 연도간 크기 직접비교에는한계가있다.\n\n2026 plate_x/z기준면과sz_top/bot정의변경을 [공식 필드 설명](https://baseballsavant.mlb.com/csv-docs)에서재확인했다. 임의변환·심판판정대체·위치없는대리분석은하지않았다. 자료의과거노출이력을유지하며처음보는시험자료라고부르지않는다.')
    table=['| 모델 | 2023 | 2026-09-07까지 |','| --- | --- | --- |']
    for model in ['pitch_sb','swing','pitch','pitch_ff']:
        task=plan['runs']['2023'][model];mid=read(ROOT/task['definition'])['model_id']
        links=[]
        for y in ['2023','2026']:
            t=plan['runs'][y][model];label='측정 보류' if t['measurement_hold'] else '완료';links.append(f'[{label}](runs/{t["run_id"]}/manifest.json)')
        table.append('| '+mid+' | '+' | '.join(links)+' |')
    prepend(AN/'handoff_bcap_review.md','## 최신 인계 — 2026-09-14 외부 패턴 재현 종료\n\n**'+scope+'**. [최종 HTML](bcap_external_20260914__r01/final_report.html) · [칼럼 결론](bcap_external_20260914__r01/final_column_conclusion.md) · [계획](bcap_external_20260914__r01/plan.md) · [SHA256·시각](bcap_external_20260914__r01/plan_seal.json) · [측정 보류 근거](bcap_external_20260914__r01/measurement_review.md) · [독립 주수치 검산](bcap_external_20260914__r01/primary_verification.json) · [재현 명령](bcap_external_20260914__r01/reproduction.md).\n\n'+shared+'\n\n'+sb+' '+swing+'\n\n'+'\n'.join(table)+'\n\n구종 자체·공통 표본 비교도 두 연도에서 완료했다. 보정 범위는 주4·보조236으로결과전고정했고개발219/255구간은보존했다. 표본·ESS·포함률·추정방식민감성은각표에있다. 고정점수경기군집구간이며전체재학습/경기간선수의존성·실제행동변경효과는검증하지않았다. 원본·기존정제본·모델명세·완료실행·보고서는덮어쓰지않았고,현재문서의이전사본은[문서변경기록](bcap_external_20260914__r01/document_update.json)에연결한다. 측정미확보모듈을재현실패나자료부족으로바꾸지않는다. 가능한비교와보고서를완료했으므로이번범위에서종료한다.')
    for model in ['pitch_sb','swing','pitch','pitch_ff']:
        spec=ROOT/plan['runs']['2023'][model]['definition'];folder=spec.parent
        specific=sb if model=='pitch_sb' else swing if model=='swing' else '2023·2026의자체/공통지원표본12카운트외부보정비교를완료했다. 구종우열은지원·보정구간·방법민감성을함께읽으며비유의성을동등성으로해석하지않는다. 세부값·3-0/3-1/3-2판정은보고서가기준이다.'
        section='## 현재 검증 범위 — 2026-09-14\n\n**EXPERIMENTAL 유지.** '+specific+'\n\n'+shared+'\n\n[외부 보고서](../../../../'+rootbase+'final_report.html) · [계획/규제/판정](../../../../'+rootbase+'plan.md) · [실행/재현](../../../../'+rootbase+'reproduction.md) · [제한적 개발 검수](../../../../columns/001-ball-count/analysis/bcap_column_light_review.md). 외부적합은대상모델당연도별3fold1회,선택된개발규제값고정·외부튜닝0회다. 구간은조건부경기군집구간이며전체학습변동은미검증이다. 명세와이전완료실행은수정하지않았다.'
        for name in ['model_card.md','validation.md']:prepend(folder/name,section)
    (B/'document_update.json').write_text(json.dumps(dict(updated_at_utc=now(),scope='Documentation scope/status updates only; specs/old runs/reports immutable',files=updated,code=meta(__file__)),ensure_ascii=False,indent=2),encoding='utf-8')
    accesses=[]
    for y in ['2023','2026']:
        accesses.append(read(B/f'preparation_access_{y}.json'))
        for model,task in plan['runs'][y].items():
            if not task['measurement_hold']:accesses.append(read(AN/'runs'/task['run_id']/'artifacts/external_access_log.json'))
    (B/'result_access_log.json').write_text(json.dumps(dict(plan_sealed_at_utc=read(B/'plan_seal.json')['sealed_at_utc'],prior_exposure=plan['prior_exposure'],recorded_access_events=accesses,first_primary_root_read=read(B/'first_primary_result_access.json'),primary_independent_read_at_utc=read(B/'primary_verification.json')['first_result_read_at_utc'],note='Preparation and per-model row access recorded before use. Model manifests bound later aggregate computation by completion; no results-driven changes to sealed code/plan.'),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Updated',len(updated),'documents; previous snapshots preserved')

if __name__=='__main__':main()
