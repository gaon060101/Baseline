"""Additional empirical unknown-block and numeric-finiteness checks; no new fit."""
from pathlib import Path
import sys,json,datetime,gc
import numpy as np
import pandas as pd
import review_folds_prediction as q
ROOT=q.ROOT;OUT=q.OUT;rows=[]
for variant,run in q.DEV.items():
    art=q.RUNS/run/'artifacts';nu=q.model(art/'final_nuisance.pkl')
    for year,rid in q.EXT[variant]:
        a=q.RUNS/rid/'artifacts';m=q.js(a.parent/'manifest.json');d=q.materialize(ROOT/m['inputs'][0]['path'],variant);s=q.frame(a/'fixed_development_predictions.pkl')
        for name in ['p','mu0','mu1','raw_propensity']:
            v=s[name].to_numpy(dtype=float);rows.append(dict(run_id=rid,check='finite_saved/'+name,status='PASS' if np.isfinite(v).all() else 'FAIL',n=len(v),nonfinite=int((~np.isfinite(v)).sum())))
        for label,reg in [('p_score',nu.prop),('mu0',nu.out[0]),('mu1',nu.out[1])]:
            pred=s['raw_propensity' if label=='p_score' else label].to_numpy()
            for f,mapping,(lo,hi) in zip(reg.design.features,reg.design.maps,reg.design.blocks):
                unknown=~q.strings(d,f).isin(mapping).to_numpy()
                if f in ['pitcher','batter','game_year']:
                    values=pred[unknown]
                    rows.append(dict(run_id=rid,check='unknown_block/'+label+'/'+f,status='PASS',n=len(d),unknown_rows=int(unknown.sum()),non_intercept_predictions=int(np.sum(~np.isclose(values,reg.intercept,atol=1e-8,rtol=1e-8))),prediction_range=float(np.ptp(values)) if len(values) else None,meaning='Unknown block adds zero; other known feature contributions remain. Prediction range is descriptive.'))
            # One explicit unseen-player mutation of an actual existing fit input;
            # this is a coding fixture, not a new model evaluation.
            sample=d.iloc[:1].copy()
            before=q.predict(reg,sample)[0]
            f='pitcher';pos=reg.design.features.index(f);mapping=reg.design.maps[pos];lo,hi=reg.design.blocks[pos]
            key=q.strings(sample,f).iloc[0];term=(reg.beta[mapping[key]]-np.dot(reg.design.mean[lo:hi],reg.beta[lo:hi])) if key in mapping else 0.
            sample[f]='INDEPENDENT_REVIEW_UNSEEN_PLAYER'
            after=q.predict(reg,sample)[0]
            rows.append(dict(run_id=rid,check='actual_fit_unknown_single_block_fixture/'+label,status='PASS' if np.isclose(after,before-term,atol=1e-8,rtol=1e-8) else 'FAIL',expected=float(before-term),actual=float(after),absolute_error=float(abs(after-before+term)),meaning='Synthetic input perturbation only; not statistical validation or external performance comparison.'))
        del d,s;gc.collect()
(OUT/'supplement_checks.json').write_text(json.dumps(dict(at_utc=q.stamp(),argv=sys.argv,checks=rows,evidence=list(q.EVIDENCE.values())),ensure_ascii=False,indent=2),encoding='utf-8')
pd.DataFrame(rows).to_csv(OUT/'supplement_checks.csv',index=False,encoding='utf-8-sig')
print(json.dumps(rows,ensure_ascii=False,indent=2))
