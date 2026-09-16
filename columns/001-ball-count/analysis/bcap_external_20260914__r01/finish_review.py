"""Final read-only artifact checks and presentation addendum. No estimation."""
from pathlib import Path
from html.parser import HTMLParser
import datetime,hashlib,json,html
import numpy as np
import pandas as pd
B=Path(__file__).resolve().parent;ROOT=B.parents[3];AN=B.parent
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return dict(path=Path(p).relative_to(ROOT).as_posix(),sha256=sha(p))
def main():
    assert not (B/'delivery_validation.json').exists() and not (B/'final_report.html').exists()
    plan=read(B/'plan.json');seal=read(B/'plan_seal.json');checks=[];runs=[]
    def ck(name,okay,detail=None):
        checks.append(dict(check=name,status='PASS' if bool(okay) else 'FAIL',detail=detail))
        if not okay:raise AssertionError(name)
    for x in seal['files']:ck('sealed:'+x['path'],sha(ROOT/x['path'])==x['sha256'])
    for year,modules in plan['runs'].items():
        for model,task in modules.items():
            run=AN/'runs'/task['run_id'];m=read(run/'manifest.json');expected='WITHHELD_MEASUREMENT' if task['measurement_hold'] else 'COMPLETE'
            ck('status:'+run.name,m['status']==expected)
            ck('fixed_alpha:'+run.name,m['configuration']['fixed_alpha']==task['fixed_alpha'])
            if not task['measurement_hold']:
                art=run/'artifacts';basic=read(art/'basic_checks.json');logs=pd.read_csv(art/'fit_diagnostics.csv');splits=read(art/'fold_records.json')
                ck('basic:'+run.name,basic['status']=='PASS' and all(c['status']=='PASS' for c in basic['checks']))
                ck('fit_logs:'+run.name,len(logs)==12 and logs.converged.all() and not logs.fit_id.str.contains('tune').any())
                ck('solver_gradient:'+run.name,logs.relative_gradient.dropna().lt(1e-7).all())
                for s in splits:
                    tr=set(s['train_games']);ev=set(s['evaluation_games']);ck(run.name+':'+s['fit_id'],not tr&ev)
                    if '/' in s['fit_id']:
                        parent=next(p for p in splits if p['fit_id']==s['fit_id'].split('/')[0]);ck(run.name+':parent:'+s['fit_id'],(tr|ev)<=set(parent['train_games']))
                for item in m['outputs']:ck('output_hash:'+item['path'],sha(ROOT/item['path'])==item['sha256'])
            runs.append(dict(year=int(year),model=model,status=m['status']))
    verification=read(B/'primary_verification.json');ck('independent_SB',verification['status']=='PASS' and len(verification['checks'])==74)
    report=read(B/'report_manifest.json')
    for x in report['outputs']:ck('report_output:'+x['path'],sha(ROOT/x['path'])==x['sha256'])
    values=pd.read_csv(B/'comparison.csv');ck('240_rows',len(values)==240 and not values.duplicated(['year','model','count','region','population']).any())
    held=values.measurement_hold;ck('72_measurement_holds',held.sum()==72 and values.loc[held,['delta','Q0','Q1','n','ESS0','ESS1','adjusted95_low','adjusted95_high']].isna().all().all())
    ck('families',values.loc[values.is_primary,'family'].eq(4).all() and values.loc[~values.is_primary,'family'].eq(236).all())
    ck('Q_difference',np.allclose(values.loc[~held,'Q1']-values.loc[~held,'Q0'],values.loc[~held,'delta'],atol=1e-12,rtol=0))
    references=[]
    for year in [2023,2026]:
        for model in ['pitch_sb','swing']:
            task=plan['runs'][str(year)][model]
            if not task['measurement_hold']:references.append(pd.read_csv(AN/'runs'/task['run_id']/'artifacts/values.csv'))
        references.append(pd.read_csv(AN/'runs'/plan['comparison_runs'][str(year)]/'artifacts/values.csv'))
    raw=pd.concat(references).set_index(['year','model','count','region','population']).sort_index()
    presented=values.loc[~held].set_index(['year','model','count','region','population']).sort_index()
    cols=['delta','Q0','Q1','adjusted95_low','adjusted95_high','n','n_all','ESS0','ESS1','coverage','naive_delta','gcomp_delta']
    ck('report_matches_original_csv',raw.index.equals(presented.index) and np.allclose(raw[cols],presented[cols],rtol=0,atol=1e-12,equal_nan=True))
    flags=values[['year','model','count','region','population','measurement_hold','support_gate']].copy()
    flags['interval_within_001_W']=pd.array(np.where(held,None,values.support_gate.fillna(False)&values.adjusted95_low.ge(-.01)&values.adjusted95_high.le(.01)),dtype='boolean')
    flags.to_csv(B/'prespecified_margin_flags.csv',index=False)
    pitch=values[values.model.isin(['pitch','pitch_ff'])];small=(pitch.support_gate&pitch.adjusted95_low.ge(-.01)&pitch.adjusted95_high.le(.01));ck('no_pitch_small_range_cells',not small.any(),dict(comparisons=len(pitch)))
    folded=[]
    for year in [2023,2026]:
        f=pd.read_csv(AN/'runs'/plan['comparison_runs'][str(year)]/'artifacts/fold_values.csv');g=f[f.model.eq('pitch')&f['count'].eq('3-0')].copy();folded.append(g)
    folds=pd.concat(folded);ck('FB30_fold_qualification',len(folds)==12 and not folds.support_gate.any() and folds.delta.gt(0).all())
    folds.to_csv(B/'FB_3_0_fold_support.csv',index=False)
    notes=[
        '주요 S/B 0-2·1-2의 2023 값은 원 생성 함수를 호출하지 않는 별도 산술 검산 74개 항목을 통과했다. 저장된 선택확률·양 행동 예측·행동·최종 W에서 AIPW 점수와 경기 군집 구간을 다시 계산했다. 전체 재학습 불확실성의 검증은 아니다.',
        '두 구종 분류의 두 외부 연도 자체·공통 표본 96개 비교 중, 보정 구간 전체가 ±0.01 W 안에 든 비교는 0개다. 따라서 대부분 불명확하다는 결론을 “구종 차이는 작다” 또는 “동등하다”로 바꾸지 않는다.',
        'FB/NFB 3-0의 통합 보정 차이는 두 외부 연도에도 남았다. 그러나 두 연도·자체/공통 표본의 모든 12개 분할 진단에서 NFB 지원 기준이 부족했다. 점추정은 모두 같은 방향이며, 부호 반전 때문에 보류한 것이 아니다. NFB ESS는 분할별 약75~114로 기준200보다 작고, 일부는 행동별 경기 수도 부족하다. 특히 2026은 단순 평균과 보정값의 방향이 갈린다. 이 예외를 보편적인 구종 지침으로 확대하지 않는다.'
    ]
    links='[독립 S/B 검산](primary_verification.json) · [사전 지정 ±0.01 W 범위 표시](prespecified_margin_flags.csv) · [FB/NFB 3-0 분할 지원](FB_3_0_fold_support.csv)'
    (B/'final_notes.md').write_text('# 최종 확인과 해석 보충\n\n'+'\n\n'.join(notes)+'\n\n'+links+'\n',encoding='utf-8')
    note_html='<section id="final-checks"><h2>최종 확인과 구종 해석</h2>'+''.join('<p>'+html.escape(n)+'</p>' for n in notes)+'<p><a href="primary_verification.json">독립 S/B 검산</a> · <a href="prespecified_margin_flags.csv">±0.01 W 범위 확인</a> · <a href="FB_3_0_fold_support.csv">3-0 분할 지원</a></p></section>'
    original=(B/'report.html').read_text(encoding='utf-8');ck('html_insert_target',original.count('<section id="method">')==1)
    final=original.replace('<section id="method">',note_html+'<section id="method">').replace('href="column_conclusion.md"','href="final_column_conclusion.md"')
    (B/'final_report.html').write_text(final,encoding='utf-8')
    conclusion=(B/'column_conclusion.md').read_text(encoding='utf-8')
    (B/'final_column_conclusion.md').write_text(conclusion+'\n구종 비교의 대부분이 불명확하다는 것은 두 행동의 차이가 작거나 없다는 뜻은 아니다. FB/NFB 3-0은 두 외부 연도에서 보정 차이가 남았지만, 모든 분할에서 NFB 지원 기준이 부족하고 보정 의존성도 있어 일반적인 구종 선택 지침으로 확대하지 않는다.\n',encoding='utf-8')
    assert all(x['status']=='PASS' for x in checks)
    result=dict(status='PASS',at_utc=now(),checks=checks,completed_model_years=6,measurement_holds=2,fits=72,independent_primary_checks=74,comparison_rows=240,executed_comparisons=168,held_comparisons=72,runs=runs,code=meta(__file__),outputs=[meta(B/n) for n in ['final_report.html','final_column_conclusion.md','final_notes.md','prespecified_margin_flags.csv','FB_3_0_fold_support.csv']],scope='Preservation, recorded execution checks, table arithmetic and final presentation; no new fitting or estimator changes')
    (B/'delivery_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','completed_model_years','measurement_holds','fits','comparison_rows','executed_comparisons']},ensure_ascii=True))

if __name__=='__main__':main()
