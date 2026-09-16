"""Limited read-only BCAP column check. Never imports a production estimator.

Run with --output pointing to a NEW json path. No fitting, resampling, or raw data.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse, datetime, hashlib, json, sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
AN = ROOT / 'columns/001-ball-count/analysis'
sys.path.insert(0, str(AN / 'runtime_ridge_v02'))
from scipy.stats import t

INPUTS = {}
CHECKS = []
def tracked(path):
    path = Path(path)
    if not path.is_absolute(): path = AN / path
    with path.open('rb') as f: digest = hashlib.file_digest(f, 'sha256').hexdigest()
    INPUTS[path.relative_to(ROOT).as_posix()] = dict(sha256=digest, bytes=path.stat().st_size)
    return path
def readj(path): return json.loads(tracked(path).read_text(encoding='utf-8-sig'))
def readcsv(path): return pd.read_csv(tracked(path))
def ck(name, condition, detail=None):
    CHECKS.append(dict(check=name, status='PASS' if bool(condition) else 'FAIL', detail=detail))
def close(a,b): return np.allclose(a,b,rtol=0,atol=1e-12,equal_nan=True)
def interval(r, prefix): return f'[{r[prefix+"_low"]:+.3f}, {r[prefix+"_high"]:+.3f}]'

class TableReader(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.row=None; self.cell=None; self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=='table': self.tables.append([])
        if tag=='tr': self.row=[]
        if tag in ('td','th'): self.cell=[]
    def handle_data(self,text):
        self.text.append(text)
        if self.cell is not None: self.cell.append(text)
    def handle_endtag(self,tag):
        if tag in ('td','th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell=None
        if tag=='tr' and self.row is not None:
            self.tables[-1].append(self.row); self.row=None

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True); args=parser.parse_args()
    output=Path(args.output).resolve()
    if not output.is_relative_to(ROOT): raise ValueError('Output must stay in project')
    if output.exists(): raise FileExistsError('Preserve previous checks: choose a new output name')
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    runs={m: f'runs/bcap_{m}__mlb_2024_2025__20260912__r01' for m in ['pitch','pitch_sb','swing','pitch_ff','pitch_compare']}
    paths={m: runs[m]+'/artifacts/' for m in runs}
    sb=readcsv(paths['pitch_sb']+'count_values.csv')
    sw=readcsv(paths['swing']+'count_values.csv')
    zones=readcsv('bcap_v2_development_20260912__r01/batter_five_regions.csv')
    canonical=readcsv(paths['swing']+'region_values.csv')
    mix=readcsv(paths['pitch_compare']+'primary_values.csv')
    subgroup=readcsv(paths['pitch_compare']+'year_fold_values.csv')
    report=tracked('bcap_reader_20260914/report.html')
    reader=TableReader(); reader.feed(report.read_text(encoding='utf-8'))
    rm=readj('bcap_reader_20260914/report_manifest.json')
    ck('reader_manifest_output_hash', hashlib.sha256(report.read_bytes()).hexdigest()==rm['output_sha256'])
    for path,digest in rm['inputs'].items():
        actual=tracked(path)
        ck('reader_input_hash:'+path,INPUTS[actual.relative_to(ROOT).as_posix()]['sha256']==digest)
    ck('reader_table_shapes',[len(x) for x in reader.tables]==[13,13,13,13,7])
    for name,df in [('SB',sb),('SWING',sw),('regions',zones),('classification',mix)]:
        residual=float(np.max(np.abs(df.Q1-df.Q0-df.delta)))
        ck(name+'_Q1_minus_Q0',close(df.Q1-df.Q0,df.delta),dict(rows=len(df),max_abs_error=residual))
        ck(name+'_action_denominator',df.rows0.add(df.rows1).eq(df.n).all())
    ck('five_regions_copy_matches_run',canonical.shape==zones.shape and all(
        np.allclose(canonical[c],zones[c],rtol=0,atol=1e-8 if c.startswith('ESS') else 1e-12,equal_nan=True) if pd.api.types.is_numeric_dtype(canonical[c]) else
        canonical[c].fillna('').eq(zones[c].fillna('')).all() for c in canonical.columns))
    for table,df,label in [(reader.tables[0],sb,'SB'),(reader.tables[2],sw,'SWING')]:
        for actual,(_,r) in zip(table[1:],df.iterrows()):
            expected=[r['count'],f'{r.Q0:.3f}',f'{r.Q1:.3f}',f'{r.delta:+.3f}',interval(r,'family95'),r.point_direction+' · '+r.evidence]
            expected.append(f'{int(r.n):,} / {r.coverage*100:.1f}%' if label=='SB' else f'{int(r.n):,}')
            ck('HTML_'+label+'_'+r['count'],actual==expected, None if actual==expected else dict(actual=actual,expected=expected))
    common=mix[mix.population.eq('common')]
    for actual in reader.tables[1][1:]:
        count=actual[0]; expected=[count]
        for scheme in ['FB','FF']:
            r=common[common['count'].eq(count)&common.scheme.eq(scheme)].iloc[0]
            expected += [f'{r.delta:+.3f} '+interval(r,'adjusted95'),r.judgment]
        ck('HTML_classification_'+count,actual==expected)
    for actual in reader.tables[3][1:]:
        count=actual[0]
        for column,region in enumerate(['HIGH','LOW','INSIDE','OUTSIDE','CENTER'],1):
            r=zones[zones['count'].eq(count)&zones.region.eq(region)].iloc[0]
            label=('스윙' if r.delta>0 else '테이크')+(' · 불명확' if r.evidence!='관찰상 방향 뚜렷' else '')
            start=label+f'{r.delta:+.3f} W'+interval(r,'family95') if r.support_gate else '자료 부족—'
            expected=start+f'투구 {r.fraction_of_count_all*100:.1f}% · 스윙 {r.action1_rate_all*100:.1f}%'
            ck('HTML_region_'+count+'_'+region,actual[column]==expected)
            count_n=int(sw.loc[sw['count'].eq(count),'n_all'].iloc[0])
            ck('region_frequency_denominator_'+count+'_'+region,close(r.fraction_of_count_all,r.n_all/count_n))
    center=zones[zones.region.eq('CENTER')]; outside=zones[~zones.region.eq('CENTER')]
    ck('CENTER_12_positive_3_0_unclear',len(center)==12 and center.delta.gt(0).all() and center.support_gate.all() and center.loc[center.evidence.ne('관찰상 방향 뚜렷'),'count'].tolist()==['3-0'])
    ck('outside_44_supported_negative_4_unsupported_3_0',outside.support_gate.sum()==44 and outside.loc[outside.support_gate,'delta'].lt(0).all() and outside.loc[~outside.support_gate,'count'].eq('3-0').all())
    ck('SB_two_B_nine_S_one_unclear',sb.support_gate.all() and sb.loc[sb.evidence.eq('차이 불명확'),'count'].tolist()==['0-1'] and sb.loc[sb.evidence.eq('관찰상 방향 뚜렷')&sb.delta.gt(0),'count'].tolist()==['0-2','1-2'] and int((sb.evidence.eq('관찰상 방향 뚜렷')&sb.delta.lt(0)).sum())==9)

    # This is a separate AIPW and game-cluster calculation, using saved predictions.
    spec=readj(ROOT/'models/bcap/pitch_sb/v0.1.0/specification.yaml')
    scores=pd.read_pickle(tracked(paths['pitch_sb']+'scores.pkl'))
    ck('SB_saved_score_keys_unique',not scores.duplicated(['game_pk','at_bat_number','pitch_number']).any())
    ck('SB_one_saved_fold_per_game',scores.groupby('game_pk').fold.nunique().eq(1).all())
    ck('SB_saved_years',set(scores.game_year.unique())=={2024,2025})
    membership=readcsv(paths['pitch_sb']+'fold_membership.csv')
    cols=['row_id','game_pk','at_bat_number','pitch_number','game_year','A','fold']
    ck('SB_scores_membership_match',np.array_equal(scores[cols].sort_values('row_id').to_numpy(),membership[cols].sort_values('row_id').to_numpy()))
    recomputed=[]
    for count in ['0-2','1-2']:
        whole=scores[scores['count'].eq(count)]; selected=whole[whole.support].copy()
        a=selected.A.to_numpy(); p=selected.p.to_numpy(); y=selected.Y.to_numpy()
        v0=selected.mu0.to_numpy().copy(); v1=selected.mu1.to_numpy().copy()
        m0=a==0; m1=a==1
        v0[m0]+=(y[m0]-v0[m0])/(1-p[m0]); v1[m1]+=(y[m1]-v1[m1])/p[m1]
        ck('SB_'+count+'_phi_from_saved_predictions',close(v0,selected.phi0) and close(v1,selected.phi1))
        delta=v1-v0; point=float(delta.mean()); n=len(selected)
        frame=pd.DataFrame({'game':selected.game_pk.to_numpy(),'centered':delta-point})
        sums=frame.groupby('game',sort=True).centered.sum().to_numpy(); games=len(sums)
        se=float(np.linalg.norm(sums)/n*np.sqrt(games/(games-1)))
        q=t.ppf([.975,1-.05/(2*spec['comparison_family'])],games-1)
        values=dict(count=count,n_all=len(whole),n=n,coverage=n/len(whole),games=games,Q0=float(v0.mean()),Q1=float(v1.mean()),delta=point,SE=se,
            nominal95_low=point-q[0]*se,nominal95_high=point+q[0]*se,family95_low=point-q[1]*se,family95_high=point+q[1]*se)
        for arm,mask,prob in [(0,m0,1-p),(1,m1,p)]:
            w=1/prob[mask]; group=pd.DataFrame({'game':selected.game_pk.to_numpy()[mask],'weight':w}).groupby('game').weight.sum()
            values.update({f'rows{arm}':int(mask.sum()),f'ESS{arm}':float(w.sum()**2/(w@w)),f'games{arm}':len(group),f'max_game_share{arm}':float(group.max()/w.sum())})
        values['support_gate']=bool(n>=spec['min_rows'] and values['coverage']>=spec['min_coverage'] and all(values[f'ESS{k}']>=spec['min_ess'] and values[f'games{k}']>=spec['min_arm_games'] and values[f'max_game_share{k}']<=spec['max_game_share'] for k in [0,1]))
        original=sb[sb['count'].eq(count)].iloc[0]
        differences={k:float(values[k]-original[k]) for k in values if k not in ['count','support_gate']}
        # ESS can accumulate floating-point roundoff beyond 1e-12 on ~100k rows.
        ck('SB_'+count+'_independent_aggregate',all(abs(v)<= (1e-8 if k.startswith('ESS') else 1e-12) for k,v in differences.items()) and values['support_gate']==bool(original.support_gate),differences)
        recomputed.append(values)

    # Record checks are explicitly not a replay of preprocessing, fitting, or labels.
    records=[]
    for model in ['pitch','pitch_sb','swing','pitch_ff']:
        manifest=readj(runs[model]+'/manifest.json'); basic=readj(paths[model]+'basic_checks.json')
        logs=readcsv(paths[model]+'fit_diagnostics.csv'); split=readj(paths[model]+'fold_records.json')
        intersections=[]
        for rec in split:
            tr=set(rec['train_games']); ev=set(rec['evaluation_games']); cross=tr&ev
            ck(model+'_'+rec['fit_id']+'_record_disjoint',not cross)
            if '/' in rec['fit_id']:
                parent=next(r for r in split if r['fit_id']==rec['fit_id'].split('/')[0])
                ck(model+'_'+rec['fit_id']+'_inside_recorded_outer_training',(tr|ev)<=set(parent['train_games']) and not (tr|ev)&set(parent['evaluation_games']))
            elif model=='pitch_sb':
                fold=int(rec['fit_id'].replace('fold',''))
                ck('SB_'+rec['fit_id']+'_evaluation_matches_scores',ev==set(scores.loc[scores.fold.eq(fold),'game_pk']))
            intersections.append(dict(fit_id=rec['fit_id'],train_games=len(tr),evaluation_games=len(ev),intersection=len(cross)))
        ck(model+'_existing_basic_PASS',basic['status']=='PASS')
        ck(model+'_recorded_convergence',logs.converged.eq(True).all())
        records.append(dict(model=manifest['model_id'],model_status=manifest.get('model_status'),run_status=manifest['status'],recorded_fit_logs=len(logs),recorded_converged=int(logs.converged.eq(True).sum()),splits=intersections))
    prep=readj('bcap_v2_development_20260912__r01/preparation/preparation.json')
    ck('existing_preparation_PASS',prep['status']=='PASS')
    for file in ['models/bcap/development_v2/v0.2.0/engine.py','models/bcap/development_v2/v0.2.0/run.py','models/bcap/development_v2/v0.2.0/prepare.py','models/bcap/swing/v0.2.0/specification.yaml','models/bcap/pitch/v0.2.0/specification.yaml','models/bcap/pitch_ff/v0.1.0/specification.yaml']:
        tracked(ROOT/file)
    evidence=dict(SB=sb.to_dict('records'),classification=common.to_dict('records'),classification_exceptions=mix[mix['count'].isin(['3-0','3-1','3-2'])].to_dict('records'),year_fold_exceptions=subgroup[subgroup['count'].isin(['3-0','3-1','3-2'])].to_dict('records'))
    result=dict(scope='Limited column review: direct HTML/CSV arithmetic and saved SB 0-2/1-2 score aggregation; other model fitting/labels checked in existing records only',started_at_utc=started,finished_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='PASS' if all(c['status']=='PASS' for c in CHECKS) else 'FAIL',checks=CHECKS,SB_recomputed=recomputed,existing_records=records,evidence=evidence,inputs=INPUTS,code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),command=[sys.executable,'-B',str(Path(__file__).resolve()),'--output',str(output)],not_run=['fitting','bootstrap','new seeds','new data','external years','KBO','raw audit','full V2 validation','full-learning uncertainty','policy evaluation'])
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f: json.dump(result,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))
    print(json.dumps(dict(status=result['status'],checks=len(CHECKS),failures=[c for c in CHECKS if c['status']=='FAIL'],SB_recomputed=recomputed),ensure_ascii=True,indent=2))

if __name__=='__main__': main()
