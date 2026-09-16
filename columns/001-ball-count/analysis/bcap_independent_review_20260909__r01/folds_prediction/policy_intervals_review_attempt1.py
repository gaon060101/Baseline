"""Independent saved policy-training conditional interval reconstruction."""
from pathlib import Path
import sys,json,hashlib,datetime,platform
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'columns/001-ball-count/analysis/runtime_ridge_v02'))
import numpy as np
import pandas as pd
import scipy
from scipy.stats import t
START=datetime.datetime.now(datetime.timezone.utc).isoformat();INPUTS={};ROWS=[];ERRORS=[]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def meta(p):
    p=Path(p);h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return dict(path=p.relative_to(ROOT).as_posix(),sha256=h.hexdigest(),bytes=p.stat().st_size)
def read(p):INPUTS[str(p)]=meta(p);return json.loads(p.read_text(encoding='utf-8-sig'))
def frame(p):INPUTS[str(p)]=meta(p);return pd.read_pickle(p)
def main():
    read(OUT.parent/'review_protocol.json')
    for variant,rid in [('pitch','bcap_pitch__mlb_2024_2025__20260909__r02'),('swing','bcap_swing__mlb_2024_2025__20260909__r01')]:
        a=ROOT/'columns/001-ball-count/analysis/runs'/rid/'artifacts';c=read(a/'specification.yaml');m=read(a.parent/'manifest.json')
        assert c['comparison_family']==m['configuration']['comparison_family']==1536
        outer=read(a/'outer_policies.json');final=read(a/'final_policy.json')
        for name,policy in [(f'outer{k}',outer[k]) for k in range(3)]+[('final_policy',final)]:
            d=frame(a/(name+'_policy_training_scores.pkl'));d=d.loc[d.support]
            # Independent difference directly from Y, A and nuisance predictions.
            observed=d.Y.to_numpy();arm=d.A.to_numpy();p=d.p.to_numpy();m0=d.mu0.to_numpy();m1=d.mu1.to_numpy()
            delta=m1-m0+np.where(arm==1,(observed-m1)/p,-(observed-m0)/(1-p))
            assert np.isfinite(delta).all()
            tab=pd.DataFrame({'state':d[c['policy_key']].astype(str).to_numpy(),'game':d.game_pk.to_numpy(),'value':delta})
            by=tab.groupby(['state','game']).value.agg(['sum','size'])
            assert set(by.index.get_level_values('state'))==set(policy['states'])
            for state,g in by.groupby(level='state'):
                n=int(g['size'].sum());G=len(g);point=float(g['sum'].sum()/n)
                # Cluster ratio residual totals, independently aggregated by game.
                centered=g['sum'].to_numpy()-point*g['size'].to_numpy()
                se=float(np.sqrt(G/(G-1)*np.dot(centered,centered))/n)
                crit=float(t.ppf(1-.05/(2*c['comparison_family']),G-1))
                low=point-crit*se;high=point+crit*se;saved=policy['states'][state]
                values=np.array([low,high]);target=np.array([saved['conditional_low'],saved['conditional_high']])
                errors=np.abs(values-target);good=np.isclose(values,target,atol=1e-9,rtol=1e-8)
                rec=dict(run_id=rid,policy=name,state=state,n=n,games=G,degrees_of_freedom=G-1,family=c['comparison_family'],delta=point,se=se,t_critical=crit,conditional_low=low,conditional_high=high,stored_low=target[0],stored_high=target[1],absolute_error_low=errors[0],absolute_error_high=errors[1],relative_error_low=errors[0]/max(abs(target[0]),1e-300),relative_error_high=errors[1]/max(abs(target[1]),1e-300),status='PASS' if good.all() else 'FAIL')
                ROWS.append(rec)
                if not good.all():ERRORS.append(rec)
            print(now(),rid,name,'complete',flush=True)
    pd.DataFrame(ROWS).to_csv(OUT/'policy_interval_comparisons.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(ERRORS).to_csv(OUT/'policy_interval_mismatches.csv',index=False,encoding='utf-8-sig')
    result=dict(started_at_utc=START,finished_at_utc=now(),scope='Outer0/1/2 and final development policy-training conditional_low/high only; no refitting or new external evaluation',independent_method='Reconstruct delta directly from Y/A/p/mu; per-state per-game totals; G/(G-1) ratio sandwich; t(G-1), Bonferroni family1536',tolerances={'absolute':1e-9,'relative':1e-8},policy_states=len(ROWS),interval_endpoints=2*len(ROWS),mismatched_states=len(ERRORS),maximum_absolute_error=max(max(x['absolute_error_low'],x['absolute_error_high']) for x in ROWS),maximum_relative_error=max(max(x['relative_error_low'],x['relative_error_high']) for x in ROWS),status='PASS' if not ERRORS else 'FAIL',family=1536,production_functions_imported=False)
    (OUT/'policy_interval_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    report=f'''# 정책 훈련 조건부 구간 추가 독립 검수

기존 하위 보고서가 미재계산으로 명시했던 outer0/1/2 및 final 정책 JSON의 `conditional_low/high`를 추가 검산했다. 원 보고서의 해당 미검증 범위를 이 추가 보고서로 갱신한다.

- 범위: PITCH/SWING 개발 각 4개 정책, {len(ROWS)}개 상태, {2*len(ROWS)}개 구간 끝점.
- 판정: **{result['status']}**, 불일치 상태 {len(ERRORS)}개.
- 최대 절대오차: {result['maximum_absolute_error']:.17g}. 최대 상대오차: {result['maximum_relative_error']:.17g}.
- 허용오차: 결과 전 프로토콜의 구간 atol1e-9, rtol1e-8.
- 시간: {START} ~ {result['finished_at_utc']}.

저장 phi의 평균을 재사용하지 않고 Y/A/p/mu에서 행별 행동 차이를 재구성했다. 정책 허용 상태별로 경기 합계와 행 수를 집계한 뒤, 경기 잔차 총합의 제곱합에 G/(G−1)을 적용하고 전체 행 수로 나누어 표준오차를 구했다. 자유도는 G−1, 임계값은 t(1−.05/(2×1536),G−1)이다. 이는 생산 코드 `models/bcap/run.py:139`의 고정 점수 조건부 경기군집 공식과 `:153`의 정책 훈련 구간 정의를 독립 구현한 것이다. 두 실행의 봉인 명세와 manifest에서 family=1536이 일치했다.

이 검사는 저장된 정책 훈련 점수의 산술 구간 재현이다. 정책·nuisance 학습 불확실성, 경기 간 선수/시리즈 의존성, 인과 식별 또는 행동 권고 유효성을 추가로 검증하지 않는다. 기존 모델의 재학습이나 외부의 새 모델 평가를 수행하지 않았다.

상태별 n/G/df/delta/se/임계값/양 끝점/오차는 `policy_interval_comparisons.csv`, 실행환경과 입력·코드·산출물 해시는 `policy_interval_evidence_manifest.json`에 있다.
'''
    (OUT/'policy_interval_addendum.md').write_text(report,encoding='utf-8')
    evidence=dict(started_at_utc=START,finished_at_utc=now(),environment=dict(python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,scipy=scipy.__version__,executable=sys.executable,argv=sys.argv,python_bytecode_writing=False),inputs=list(INPUTS.values()),code=meta(Path(__file__)),outputs=[meta(OUT/name) for name in ['policy_interval_comparisons.csv','policy_interval_mismatches.csv','policy_interval_validation.json','policy_interval_addendum.md']])
    (OUT/'policy_interval_evidence_manifest.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
