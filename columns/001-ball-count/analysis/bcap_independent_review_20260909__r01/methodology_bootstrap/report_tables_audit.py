"""Independent direct source-table and rendered report audit; no report generator import."""
from pathlib import Path
import sys, json, hashlib, datetime, platform, re, math
import pandas as pd
import numpy as np
ROOT=Path('C:/Users/백창현/Desktop/Baseline');OUT=Path(__file__).resolve().parent
AN=ROOT/'columns/001-ball-count/analysis';RUNS=AN/'runs';RPT=AN/'bcap_report_20260909_r01';OLD=AN/'bcap_implementation_review_20260909'
START=datetime.datetime.now(datetime.timezone.utc).isoformat();READS={};CHECKS=[];cache={}
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def touch(p):
    p=Path(p);k=p.relative_to(ROOT).as_posix()
    if k not in READS:READS[k]={'path':k,'sha256':sha(p),'bytes':p.stat().st_size}
    return p
def J(p):return json.loads(touch(p).read_text(encoding='utf-8-sig'))
def C(p):
    p=Path(p)
    if str(p) not in cache:cache[str(p)]=pd.read_csv(touch(p))
    return cache[str(p)].copy()
def check(label,a,b,field='',exact=False):
    err=None
    if pd.isna(a) or pd.isna(b):ok=bool(pd.isna(a) and pd.isna(b))
    elif isinstance(a,(int,float,np.number,bool)) and isinstance(b,(int,float,np.number,bool)) and not exact:
        if 'ESS' in field or 'weight' in field:at,rt=1e-6,1e-9
        elif 'CI' in field or 'low' in field or 'high' in field or field=='se':at,rt=1e-9,1e-8
        else:at,rt=1e-10,1e-9
        err=abs(float(a)-float(b));ok=err<=at+rt*abs(float(b))
    else:ok=bool(a==b)
    CHECKS.append({'check':label,'field':field,'status':'PASS' if ok else 'FAIL','absolute_error':err,'actual':str(a),'expected':str(b)})
def rowcheck(label,row,source,fields=None):
    if fields is None:fields=[f for f in source.index if f in row.index and f!='unit']
    exacts={'n','n_all','rows','rows_all','games','PA','pitchers','batters','arm_games0','arm_games1','replicates','N_PA','N','fit_id','state','level','policy','bin','group'}
    for f in fields:check(label+'/'+f,row[f],source[f],f,f in exacts)
def framecheck(label,a,b,fields=None):
    a=a.reset_index(drop=True);b=b.reset_index(drop=True);check(label+'/rows',len(a),len(b),exact=True)
    for i in range(min(len(a),len(b))):rowcheck(label+f'/row{i}',a.iloc[i],b.iloc[i],fields)
def formatnum(v,places=4):return '미산출' if pd.isna(v) else f'{float(v):,.{places}f}'
def main():
    protocol=J(OUT.parent/'review_protocol.json');manifest=J(RPT/'report_manifest.json')
    tables={r['number']:C(ROOT/r['path']) for r in manifest['tables']}
    check('report/16tables',len(tables),16,exact=True)
    for r in manifest['tables']:check(f'table{r["number"]}/manifest_rows',len(tables[r['number']]),r['rows'],exact=True)
    for meta in manifest['inputs']+manifest['outputs']:
        check('report/declared_hash/'+meta['path'],sha(touch(ROOT/meta['path'])),meta['sha256'],exact=True)
    runs={r['run_id']:r for r in manifest['source_runs']};dev={r['variant']:rid for rid,r in runs.items() if r['period']=='2024_2025'}
    policies={v:J(RUNS/rid/'artifacts/final_policy.json') for v,rid in dev.items()}
    def artifact(rid,name):return C(RUNS/rid/'artifacts'/f'{name}.csv')
    def action(rid):return artifact(rid,'action_values')
    def selected(a,level,state):return a[a.level.eq(level)&a.state.eq(state)].iloc[0]
    # 1: OBS and Ridge retain their own measures and intervals.
    obs=C(RUNS/'bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_count_results.csv').set_index('count')
    ridge=C(RUNS/'bcai_ridge__mlb_2024_2025__20260908__r02/artifacts/count_indices.csv');ridge=ridge[ridge.period.eq('combined')].set_index('count')
    mapping={'OBS_I':'index','OBS_CI95_low':'CI95_low','OBS_CI95_high':'CI95_high','OBS_simultaneous95_low':'simultaneous95_low','OBS_simultaneous95_high':'simultaneous95_high','OBS_confirmed_grade':'confirmed_grade','OBS_N_PA':'N_PA'}
    for _,r in tables[1].iterrows():
        for a,b in mapping.items():check('table1/'+r['count']+'/'+a,r[a],obs.loc[r['count'],b],a)
        for a,b in {'Ridge_N_PA':'N','Ridge_v02_J':'J','Ridge_J_minus_I':'shift'}.items():check('table1/'+r['count']+'/'+a,r[a],ridge.loc[r['count'],b],a)
    # 2-9 are development projections, with independent complement/policy checks.
    for t in range(2,10):
        variant='pitch' if t<6 else 'swing';src=action(dev[variant]);src=src[src.level.eq('count') if variant=='pitch' else src.level.eq('cell') if t==6 else src.level.isin(['count','cell'])]
        framecheck(f'table{t}',tables[t],src)
        for _,r in tables[t].iterrows():
            s=selected(src,r.level,r.state);lab=f'table{t}/{r.state}'
            for f,base in [('action0_rate_all','action1_rate_all'),('action0_rate_support','action1_rate')]:
                if f in r:check(lab+'/'+f,r[f],1-s[base],f)
            if 'evaluation_contrast_direction' in r:check(lab+'/direction',r.evaluation_contrast_direction,s.get('candidate_direction'),exact=True)
            if 'saved_development_policy_p1' in r:
                expected=policies[variant]['states'].get(r.state,{'p1':.5})['p1'] if (variant=='pitch' or r.level=='cell') else np.nan
                check(lab+'/final_policy',r.saved_development_policy_p1,expected)
    for rid,run in runs.items():
        if run['execution_status']=='WITHHELD':
            for t in [10,11,12,14,15,16]:
                sub=tables[t][tables[t].run_id.eq(rid)];check(f'table{t}/withheld_count',len(sub),1,exact=True)
                for _,r in sub.iterrows():
                    check(f'table{t}/withheld_grade',pd.isna(r.grade),True,exact=True)
                    check(f'table{t}/withheld_status',r.execution_status,'WITHHELD',exact=True)
                    for f in ['n','n_all','Q0','Q1','delta','gain','value']:
                        if f in r:check(f'table{t}/withheld_no_{f}',pd.isna(r[f]),True,exact=True)
            continue
        a=action(rid);p=artifact(rid,'policy_values');base=RUNS/rid/'artifacts'
        framecheck('table10/'+rid,tables[10][tables[10].run_id.eq(rid)],p)
        diag=tables[11][tables[11].run_id.eq(rid)]
        for name in ['propensity_overlap','calibration','support_exclusions','fit_diagnostics']:
            framecheck('table11/'+rid+'/'+name,diag[diag.record_type.eq(name)],artifact(rid,name))
        metrics=J(base/'metrics.json');framecheck('table11/'+rid+'/metrics',diag[diag.record_type.eq('aggregate_nuisance_prediction_metrics')],pd.DataFrame([metrics]))
        known=tables[12][tables[12].run_id.eq(rid)]
        framecheck('table12/'+rid+'/evaluation',known[~known.evaluation_method.eq('fixed_development_prediction_only')],artifact(rid,'known_unseen'))
        framecheck('table15/'+rid,tables[15][tables[15].run_id.eq(rid)],artifact(rid,'sensitivity'))
        framecheck('table16/'+rid,tables[16][tables[16].run_id.eq(rid)],a)
        if run['period']!='2024_2025':
            fixed=base/'fixed_prediction_diagnostics';fm=J(fixed/'metrics.json')
            framecheck('table11/'+rid+'/fixedmetrics',diag[diag.record_type.eq('aggregate_fixed_development_prediction_metrics')],pd.DataFrame([fm]))
            framecheck('table11/'+rid+'/fixedcal',diag[diag.record_type.eq('fixed_development_calibration')],C(fixed/'calibration.csv'))
            framecheck('table12/'+rid+'/fixed',known[known.evaluation_method.eq('fixed_development_prediction_only')],C(fixed/'known_unseen.csv'),['group','n','games','coverage','MSE','Brier'])
            t=13 if run['period']=='2023' else 14;ext=tables[t][tables[t].run_id.eq(rid)];framecheck(f'table{t}/'+rid,ext,a)
            for _,r in ext.iterrows():
                for name in ['observed','learned','conservative','always_0','always_1','stochastic_half']:
                    match=p[p.level.eq(r.level)&p.state.eq(r.state)&p.policy.eq(name)]
                    for f in ['value','gain','gain_low','gain_high']:check(f'table{t}/{rid}/{r.state}/{name}/{f}',r[name+'_'+f],match.iloc[0][f] if len(match) else np.nan,f)
                for prefix,ms in [('fixed_development_prediction_',fm),('external_CF_nuisance_',metrics)]:
                    for f,val in ms.items():check(f'table{t}/{rid}/{r.state}/{prefix}{f}',r[prefix+f],val if r.level=='overall' else np.nan,f)
    for boot in manifest['bootstrap_diagnostics']:
        rid=boot['run_id'];framecheck('table15/'+rid,tables[15][tables[15].run_id.eq(rid)],artifact(rid,'stability_summary'))
    check('table16/full_learning_status_rows',int(tables[16].record_type.eq('uncertainty_scope').sum()),2,exact=True)
    check('table16/joint_not_designed_rows',int(tables[16].record_type.eq('joint_model_not_designed').sum()),1,exact=True)
    for t in [5,9,16]:check(f'table{t}/no_recommendation',tables[t].suggested_action.notna().sum(),0,exact=True)
    # Decoded count/zone/group and model tags are separate from copied values.
    for t,tab in tables.items():
        if t==1:continue
        for i,r in tab.iterrows():
            if 'state' in r and pd.notna(r.state) and 'count' in r and pd.notna(r['count']):
                expected=r.state.split('|')[0] if r.get('level')=='cell' else r.state
                check(f'table{t}/{i}/decoded_count',r['count'],expected,exact=True)
            if 'run_id' in r and r.run_id in runs:
                run=runs[r.run_id]
                for f in ['model_id','variant','execution_status']:check(f'table{t}/{i}/{f}',r[f],run[f],exact=True)
    # Rendered 12-count prose and every Swing cell table at printed precision.
    prose=touch(AN/'bcap_v010_report_20260909.md').read_text(encoding='utf-8-sig');sections=re.split(r'^### ([0-3]-[0-2])\s*$',prose,flags=re.M)
    check('prose/count_sections',(len(sections)-1)//2,12,exact=True)
    section_dict={sections[i]:sections[i+1] for i in range(1,len(sections),2)}
    for state,text in section_dict.items():
        check('prose/'+state+'/OBS',f'I={formatnum(obs.loc[state,"index"],2)}' in text,True,exact=True)
        check('prose/'+state+'/Ridge',f'J={formatnum(ridge.loc[state,"J"],2)}' in text,True,exact=True)
        for variant,label in [('pitch','투수'),('swing','타자')]:
            r=selected(action(dev[variant]),'count',state);line=next(x for x in text.splitlines() if x.startswith(label+' 개발:'))
            tests=[formatnum(r.action1_rate_all*100,1)+'%',f'{formatnum(r.n,0)}/{formatnum(r.n_all,0)}행({formatnum(r.coverage*100,1)}%)',f'{formatnum(r.games,0)}경기·{formatnum(r.PA,0)}PA',f'Q={formatnum(r.Q0)}',f'Q={formatnum(r.Q1)}',f'={formatnum(r.delta)} W',f'[{formatnum(r.simultaneous95_low)}, {formatnum(r.simultaneous95_high)}]',f'ESS={formatnum(r.ESS0,0)}/{formatnum(r.ESS1,0)}',f'판정 {r.grade}']
            for j,s in enumerate(tests):check(f'prose/{state}/{variant}/{j}',s in line,True,exact=True)
        cells=action(dev['swing']);cells=cells[cells.level.eq('cell')&cells.state.str.startswith(state+'|')]
        cell_lines=[x for x in text.splitlines() if re.match(r'^\| (INNER|OUT|BOUNDARY|MISSING) \|',x)]
        check('prose/'+state+'/cells',len(cell_lines),len(cells),exact=True)
        for line in cell_lines:
            cols=[x.strip() for x in line.strip('|').split('|')];key=state+'|'+cols[0]+'|'+cols[1];r=selected(cells,'cell',key)
            e=action(next(rid for rid,v in runs.items() if v['variant']=='swing' and v['period']=='2023'));e=e[e.level.eq('cell')&e.state.eq(key)]
            exp=[f'{formatnum(r.n,0)}/{formatnum(r.n_all,0)}',formatnum(r.action1_rate_all*100,1)+'%',formatnum(r.Q0),formatnum(r.Q1),formatnum(r.delta),f'[{formatnum(r.simultaneous95_low)}, {formatnum(r.simultaneous95_high)}]',r.grade,formatnum(e.iloc[0].delta) if len(e) else '미산출']
            for j,val in enumerate(exp):check('prose/cell/'+key+'/'+str(j),cols[j+2],val,exact=True)
        for rid,rn in runs.items():
            if rn['period']=='2024_2025' or rn['execution_status']!='COMPLETE':continue
            r=selected(action(rid),'count',state);pol=artifact(rid,'policy_values');p=pol[pol.level.eq('count')&pol.state.eq(state)&pol.policy.eq('learned')].iloc[0]
            label='투수' if rn['variant']=='pitch' else '타자';line=next(x for x in text.splitlines() if x.startswith(label+' 외부:'))
            segment=re.search(re.escape(rn['period'])+r': Δ (.*?)(?=2026:|2026 SWING:|$)',line).group(1)
            for s in [formatnum(r.delta)+' W',f'[{formatnum(r.simultaneous95_low)}, {formatnum(r.simultaneous95_high)}]',f'{formatnum(r.n,0)}/{formatnum(r.n_all,0)}행({formatnum(r.coverage*100,1)}%)',r.grade,formatnum(p.gain)+' W',f'[{formatnum(p.gain_low)}, {formatnum(p.gain_high)}]']:check(f'prose/external/{rid}/{state}/{s}',s in segment,True,exact=True)
    # Behavior tables: rebuild d from outer/final policy and compare source supplements plus Markdown.
    bm=J(OLD/'behavior_comparison_manifest.json');bd=touch(OLD/'behavior_comparison.md').read_text(encoding='utf-8-sig');bl=[x for x in bd.splitlines() if re.match(r'^\| [0-3]-[0-2] \|',x)];check('behavior/rows',len(bl),60,exact=True);behavior=[]
    for table_index,item in enumerate(bm['tables']):
        rid=item['source_run'];rn=runs[rid];source=C(ROOT/item['source_csv']);source=source[source.stage.eq('evaluation_nuisance')&source.level.eq('count')].set_index('state')
        scores=pd.read_pickle(touch(RUNS/rid/'artifacts/scores.pkl'))
        if rn['period']=='2024_2025':
            outer=J(RUNS/rid/'artifacts/outer_policies.json');d=np.zeros(len(scores))
            for k,policy in enumerate(outer):
                sel=scores.fold.eq(k).to_numpy();states=scores.loc[sel,policy['key']].astype(str);d[sel]=states.map({s:v['p1'] for s,v in policy['states'].items()}).fillna(policy['fallback_p1'])
        else:
            policy=policies[rn['variant']];d=scores[policy['key']].astype(str).map({s:v['p1'] for s,v in policy['states'].items()}).fillna(policy['fallback_p1']).to_numpy()
        check('behavior/'+rid+'/saved_d_maxerror',float(np.max(np.abs(d-scores.policy_p1))),0.)
        for pos,state in enumerate([f'{b}-{s}' for b in range(4) for s in range(3)]):
            mask=scores['count'].eq(state)&scores.support;sub=scores[mask];p1=d[mask];a=sub.A.to_numpy();actual=float(a.mean());candidate=float(p1.mean());disagreement=float(np.mean(np.where(a==1,1-p1,p1)))
            vals={'rows_all':int(scores['count'].eq(state).sum()),'rows':len(sub),'PA':len(sub[['game_pk','at_bat_number']].drop_duplicates()),'games':sub.game_pk.nunique(),'actual_action1_rate':actual,'candidate_expected_action1_share':candidate,'candidate_share_minus_actual':candidate-actual,'candidate_expected_disagreement':disagreement,'conservative_change_region_share':0.,'conservative_expected_action1_share':actual,'conservative_expected_disagreement':0.}
            for f,v in vals.items():check(f'behavior/{rid}/{state}/{f}',source.loc[state,f],v,f)
            cols=[x.strip() for x in bl[table_index*12+pos].strip('|').split('|')]
            expected=[state,f'{len(sub):,}/{vals["rows_all"]:,}',f'{vals["PA"]:,}',f'{vals["games"]:,}',f'{100*actual:.2f}',f'{100*candidate:.2f}',f'{100*(candidate-actual):+.2f}',f'{100*disagreement:.2f}']
            for j,v in enumerate(expected):check(f'behavior/render/{rid}/{state}/{j}',cols[j],v,exact=True)
            behavior.append({'run_id':rid,'state':state,**vals})
        del scores,d
    # Post-seal paired estimates and correlations are rebuilt from primary action files.
    pc=OLD/'postseal_descriptive_comparison';pair=C(pc/'paired_count_and_cell_estimates.csv');summary=C(pc/'direction_and_correlation_summary.csv');rebuilt=[]
    for _,r in pair.iterrows():
        a=selected(action(r.development_run),r.level,r.state);b=selected(action(r.external_run),r.level,r.state);rec=r.to_dict()
        for prefix,src in [('development_',a),('external_',b)]:
            for f in ['n_all','n','coverage','games','PA','ESS0','ESS1','Q0','Q1','delta','grade']:check('postseal/paired/'+r.state+'/'+prefix+f,r[prefix+f],src[f],f)
        have=a.n>0 and b.n>0 and np.isfinite(a.delta) and np.isfinite(b.delta);gate=have and a.grade!='NO_SUPPORT' and b.grade!='NO_SUPPORT';nz=have and a.delta!=0 and b.delta!=0
        derived={'both_have_supported_rows':have,'both_meet_empirical_support_gate':gate,'direction_comparable_nonzero':nz,'delta_direction_agreement':(a.delta*b.delta>0) if nz else np.nan,'delta_external_minus_development':b.delta-a.delta if have else np.nan}
        pp=policies[r.model]['states'].get(r.state,{'p1':.5})['p1'] if r.model=='pitch' or r.level=='cell' else np.nan
        derived['frozen_policy_action1_probability']=pp;derived['frozen_policy_matches_external_estimated_direction']=(pp==(int(b.delta<0) if r.model=='pitch' else int(b.delta>0))) if have and b.delta!=0 and pp in [0,1] else np.nan
        for f,v in derived.items():check('postseal/derived/'+r.state+'/'+f,r[f],v,f);rec[f]=v
        rebuilt.append(rec)
    rebuilt=pd.DataFrame(rebuilt)
    def corr(x,y):
        x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float);x=x-x.mean();y=y-y.mean();return float(np.dot(x,y)/math.sqrt(np.dot(x,x)*np.dot(y,y)))
    for _,r in summary.iterrows():
        part=rebuilt[(rebuilt.model==r.model)&(rebuilt.external_year==r.external_year)&(rebuilt.level==r.level)];part=part[part[r['filter']]];nonzero=part[part.direction_comparable_nonzero];p=part.frozen_policy_matches_external_estimated_direction.dropna()
        ex={'paired_states':len(part),'direction_comparable_states':len(nonzero),'direction_agree_states':int(nonzero.delta_direction_agreement.sum()),'direction_agree_fraction':nonzero.delta_direction_agreement.mean(),'Pearson_delta_unweighted_states':corr(part.development_delta,part.external_delta),'Spearman_delta_average_tie_ranks_unweighted_states':corr(part.development_delta.rank(method='average'),part.external_delta.rank(method='average')),'frozen_policy_direction_comparable_states':len(p),'frozen_policy_matches_external_estimated_direction_states':int(p.sum()),'frozen_policy_estimated_direction_match_fraction':p.mean() if len(p) else np.nan}
        for f,v in ex.items():check(f'postseal/summary/{r.model}/{r.external_year}/{r.level}/{r["filter"]}/{f}',r[f],v,f)
    failures=[x for x in CHECKS if x['status']=='FAIL'];errors=[r['absolute_error'] for r in CHECKS if r['absolute_error'] is not None]
    with (OUT/'report_tables_comparisons.csv').open('x',encoding='utf-8-sig',newline='') as f:pd.DataFrame(CHECKS).to_csv(f,index=False)
    with (OUT/'behavior_independent_rates.csv').open('x',encoding='utf-8-sig',newline='') as f:pd.DataFrame(behavior).to_csv(f,index=False)
    result={'status':'PASS' if not failures else 'FAIL','checks':len(CHECKS),'failures':len(failures),'max_absolute_error':max(errors),'tables_checked':16,'count_sections_checked':12,'behavior_count_rows_checked':60,'postseal_paired_rows_checked':len(pair),'postseal_summaries_checked':len(summary),'scope':'Direct comparison against existing original run aggregates; behavior rates independently reconstructed from saved A/support and outer/final policy; no model refit or new external evaluation','limitations':['Table-copy agreement does not independently validate original nuisance fits or model identification','Prose numeric source matches checked at printed precision; methodology assessed separately'],'failure_details':failures,'started_at_utc':START,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    with (OUT/'report_tables_validation.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    outs=[p for p in OUT.glob('report_tables*') if p.is_file()]+[OUT/'behavior_independent_rates.csv']
    evidence={'command':[sys.executable,'-B',str(Path(__file__).resolve())],'started_at_utc':START,'finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'environment':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'bytecode_disabled':sys.dont_write_bytecode},'inputs':list(READS.values()),'code':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(__file__)},'outputs':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in outs]}
    with (OUT/'report_tables_evidence_manifest.json').open('x',encoding='utf-8') as f:json.dump(evidence,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:result[k] for k in ['status','checks','failures','max_absolute_error']},ensure_ascii=False))
if __name__=='__main__':main()
