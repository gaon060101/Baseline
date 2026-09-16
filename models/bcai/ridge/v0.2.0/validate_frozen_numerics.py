"""Post-freeze numerical instrumentation only. No feature/alpha selection and no external data."""
import sys,inspect,json,datetime
from pathlib import Path
import ridge_v02 as m
import numpy as np
import pandas as pd
from scipy import sparse
DEV='bcai_ridge__mlb_2024_2025__20260908__r02'
RUN='bcai_ridge__mlb_2024_2025__20260908__r03'
run=m.ANAL/'runs'/RUN;art=run/'artifacts'
if run.exists():raise FileExistsError(RUN)
(art/'diagnostics').mkdir(parents=True)
dev=m.ANAL/'runs'/DEV/'artifacts'
freeze=json.loads((dev/'freeze.json').read_text(encoding='utf-8'))
for rec in freeze['files']:assert m.sha(m.ROOT/rec['path'])==rec['sha256']
p=pd.read_pickle(dev/'development_PA.pkl');reach=sparse.load_npz(dev/'development_reach.npz');pr=m.prepare(p,reach)
state=json.loads((dev/'frozen_model.json').read_text(encoding='utf-8'));beta=np.array(state['beta']);alpha=state['selected_alpha']
monitor=np.zeros((12,len(beta)));obs=np.zeros(12)
for year in sorted(p.game_year.unique()):
    mask=p.game_year.eq(year).to_numpy();R=reach[mask];n=np.asarray(R.sum(0)).ravel();X=pr['design'].X[mask];q=mask.mean()
    mat=(R.T@X).toarray()/n[:,None];monitor+=q*(mat-mat[[0]])
    v=p.loc[mask,'value'].to_numpy();obs+=q*100*np.asarray(R.T@v).ravel()/n/v.mean()
lines,start=inspect.getsourcelines(m.solve);target=start+next(i for i,x in enumerate(lines) if 'if first is None and change<' in x)
trajectory=[]
def trace(frame,event,arg):
    if frame.f_code is m.solve.__code__ and event=='line' and frame.f_lineno==target:
        loc=frame.f_locals;J=obs-100*monitor@loc['beta']
        trajectory.append(dict(iteration=loc['it'],**{f'J_{c}':float(J[j]) for j,c in enumerate(m.COUNTS)}))
    return trace
sys.settrace(trace)
try:replay,di=m.solve(pr,alpha,'frozen_final_trace',art)
finally:sys.settrace(None)
assert np.max(np.abs(replay-beta))<1e-7
frame=pd.DataFrame(trajectory);m.csv(art/'count_indices_by_iteration.csv',frame)
fullpred,_,scale,flags,_=m.predict(pr,p,beta);T=m.index_table(p,reach,fullpred)
assert np.allclose(frame.iloc[-1,1:].astype(float),T[T.period.eq('combined')].J.to_numpy(),atol=1e-8)
# Unseen feature test with a copy of one row. This is a schema unit check, not fabricated baseball evidence.
unit=p.iloc[[0]].copy();oldpred=pr['design'].predict(unit,beta,pr['ym'])[0][0]
feature='batter';j=m.FEATURES.index(feature);lo,hi=pr['design'].blocks[j];idx=pr['design'].maps[j][str(unit.iloc[0][feature])]
expected=oldpred-(beta[idx]-pr['mu'][lo:hi]@beta[lo:hi]);unit[feature]='UNSEEN_TEST_ONLY'
newpred=pr['design'].predict(unit,beta,pr['ym'])[0][0];assert abs(newpred-expected)<1e-12
first=di['first_convergence_iteration'];tail=frame[frame.iteration>=first].iloc[:,1:].to_numpy()
summary=dict(frozen_coefficients_replay_maxdiff=float(np.max(np.abs(replay-beta))),exact_season_weighted_J_post_convergence_max_drift=float(np.max(np.abs(tail-tail[0]))),unseen_block_zero_effect_test=True,full_trace_rows=len(frame),final_fit_convergence=di,external_data_read=False,model_modified=False)
m.writejson(art/'validation.json',summary)
manifest=dict(run_id=RUN,model_id='BCAI-RIDGE-v0.2.0',version='0.2.0',model_status='EXPERIMENTAL',status='COMPLETE',role='frozen_development_numerical_validation',run_date='2026-09-08',completed_at=m.now(),development_run=DEV,selected_alpha=alpha,features=m.FEATURES,solver='unchanged frozen PCG, instrumented using Python trace',tolerance=1e-7,max_iterations=5000,external_data_used_for_tuning=False,inputs=[m.meta(dev/'development_PA.pkl'),m.meta(dev/'development_reach.npz'),m.meta(dev/'frozen_model.json')],code=[m.meta(Path(__file__)),m.meta(m.MODEL/'ridge_v02.py')],environment=m.environment(),convergence=summary,artifacts=[m.meta(f) for f in art.rglob('*') if f.is_file()])
m.writejson(run/'manifest.json',manifest);print(json.dumps(summary),flush=True)
