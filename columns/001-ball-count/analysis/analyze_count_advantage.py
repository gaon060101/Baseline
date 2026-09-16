"""Run inspect_advantage.py first. Set BCAI_OUTPUT_DIR to new run artifacts; source files are read only."""
from pathlib import Path
import json, hashlib, platform
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
from bcai_paths import CACHE, output_dir
OUT=output_dir(writable=True)
COUNTS=[f'{b}-{s}' for b in range(4) for s in range(3)]
WEIGHTS={2024:dict(BB=.689,HBP=.720,**{'1B':.882,'2B':1.254,'3B':1.590,'HR':2.050}),
         2025:dict(BB=.691,HBP=.722,**{'1B':.882,'2B':1.252,'3B':1.584,'HR':2.037})}
SCALE={2024:1.242,2025:1.232}
RPA={2024:.117,2025:.118}
MAP={'single':'1B','double':'2B','triple':'3B','home_run':'HR','walk':'BB','hit_by_pitch':'HBP',
     'strikeout':'K','strikeout_double_play':'K',
     **{x:'OUT' for x in ['field_out','force_out','grounded_into_double_play','double_play','fielders_choice_out','sac_fly','sac_bunt','sac_fly_double_play','sac_bunt_double_play','triple_play']},
     'field_error':'OTHER','fielders_choice':'OTHER'}
def save(d,name): d.to_csv(OUT/name,index=False,encoding='utf-8-sig')
def grade(x,a=5,b=15):
    if x>=100+b:return '타자 매우 유리'
    if x>=100+a:return '타자 유리'
    if x<=100-b:return '투수 매우 유리'
    if x<=100-a:return '투수 유리'
    return '중립'

d=pd.read_pickle(CACHE).reset_index(drop=True)
keys=['game_pk','at_bat_number']
assert not d.duplicated(keys+['pitch_number']).any()
d['count']=d.balls.astype(int).astype(str)+'-'+d.strikes.astype(int).astype(str)
assert set(d['count'])==set(COUNTS)
d['pa_id']=pd.factorize(pd.MultiIndex.from_frame(d[keys]))[0]
first=d.drop_duplicates('pa_id').set_index('pa_id')
last=d.drop_duplicates('pa_id',keep='last').set_index('pa_id')
# Only the last chronological record may supply the final event. Never use backward CSV order.
pa=first.copy()
pa['event']=last.events
pa['result']=pa.event.map(MAP)
pa['exclusion']=np.select([pa.event.isna(),pa.event.eq('intent_walk'),pa.event.eq('catcher_interf'),pa.event.eq('truncated_pa'),pa.result.isna(),pa['count'].ne('0-0')],
                         ['missing_final','intentional_walk','catcher_interference','truncated','unknown_event','no_observed_0_0'],default='included')
save(pa.groupby(['game_year','event','exclusion'],dropna=False).size().rename('PA').reset_index(),'advantage_event_audit.csv')
eligible=pa.exclusion.eq('included')
p=pa.loc[eligible].copy()
p['value']=[WEIGHTS[int(y)].get(e,0.) for y,e in zip(p.game_year,p.result)]
base=p.groupby('game_year').value.mean()
q=p.groupby('game_year').size()/len(p)
p['z']=p.value/p.game_year.map(base)
reached=d.drop_duplicates(['pa_id','count'])[['pa_id','count']].merge(p[['game_pk','game_year','result','event','value','z']],left_on='pa_id',right_index=True)
reached['ci']=reached['count'].map(dict(zip(COUNTS,range(12))))
print('Eligible PA',len(p),'base',base.to_dict(),flush=True)

# Stratified whole-game bootstrap, shared resampling across all counts and baseline.
rng=np.random.default_rng(20260907)
B=2000
boots=np.zeros((B,12)); bootruns=np.zeros((B,12)); season=[]
for year in (2024,2025):
    r=reached[reached.game_year.eq(year)]
    games=np.sort(r.game_pk.unique()); gi=pd.Index(games).get_indexer(r.game_pk)
    n=np.zeros((len(games),12)); v=np.zeros_like(n)
    np.add.at(n,(gi,r.ci),1); np.add.at(v,(gi,r.ci),r.value)
    means=v.sum(0)/n.sum(0); ix=100*means/means[0]
    for j,c in enumerate(COUNTS):season.append(dict(year=year,count=c,N=int(n[:,j].sum()),value=means[j],index=ix[j]))
    # Batch to limit memory and avoid a large temporary bootstrap tensor.
    for start in range(0,B,100):
        w=rng.multinomial(len(games),np.full(len(games),1/len(games)),size=min(100,B-start))
        m=(w@v)/(w@n)
        boots[start:start+len(w)]+=q[year]*100*m/m[:,[0]]
        bootruns[start:start+len(w)]+=q[year]*100*(m-m[:,[0]])/SCALE[year]
season=pd.DataFrame(season);save(season,'advantage_season_sensitivity.csv')
point=sum(q[y]*season[season.year.eq(y)].set_index('count').loc[COUNTS,'index'].to_numpy() for y in (2024,2025))
lo,hi=np.quantile(boots,[.025,.975],axis=0)
se=boots.std(0,ddof=1); se[0]=1
maxdev=np.max(np.abs((boots-point)/se)[:,1:],axis=1)
critical=np.quantile(maxdev,.95)
simlo=point-critical*se;simhi=point+critical*se
lo[0]=hi[0]=simlo[0]=simhi[0]=100
result=pd.DataFrame({'count':COUNTS,'index':point,'CI95_low':lo,'CI95_high':hi,'simultaneous95_low':simlo,'simultaneous95_high':simhi})
result['grade']=result['index'].map(grade)
result['grade_certainty']=[('확정 기준점' if c=='0-0' else ('등급 안정' if grade(l)==grade(h) else '등급 경계 불확실')) for c,l,h in zip(COUNTS,simlo,simhi)]
def confirmed(l,h):
    if l>=115:return '타자 매우 유리'
    if l>=105:return '타자 유리' if h<115 else '타자 유리·강도 경계'
    if h<=85:return '투수 매우 유리'
    if h<=95:return '투수 유리' if l>85 else '투수 유리·강도 경계'
    if l>95 and h<105:return '중립'
    return '투수 유리/중립 경계' if h<100 else ('타자 유리/중립 경계' if l>100 else '방향 미확정')
result['confirmed_grade']=[confirmed(l,h) for l,h in zip(simlo,simhi)]
result['runs_above_base_per100PA']=sum(q[y]*100*(season[season.year.eq(y)].value.to_numpy()-base[y])/SCALE[y] for y in (2024,2025))
result['run_environment_index']=100+sum(q[y]*100*(season[season.year.eq(y)].value.to_numpy()-base[y])/SCALE[y]/RPA[y] for y in (2024,2025))
result['grade_narrow']=result['index'].map(lambda x:grade(x,2.5,10))
result['grade_wide']=result['index'].map(lambda x:grade(x,7.5,20))

# Descriptive event rates use the same eligible PA cohort; XBH overlaps H.
events=pd.crosstab(reached['count'],reached.result).reindex(COUNTS,fill_value=0)
for e in ['1B','2B','3B','HR','BB','HBP','K','OUT','OTHER']:
    if e not in events:events[e]=0
events['N_PA']=events.sum(axis=1)
for e in ['1B','2B','3B','HR','BB','HBP','K','OUT','OTHER']:events[e+'%']=100*events[e]/events.N_PA
events['H%']=events[['1B%','2B%','3B%','HR%']].sum(axis=1)
events['XBH%']=events[['2B%','3B%','HR%']].sum(axis=1)
save(events.reset_index(),'advantage_pa_outcomes.csv')
result=result.merge(events.reset_index()[['count','N_PA','H%','XBH%','BB%','HBP%','K%','OUT%','OTHER%']],on='count')

# Existing pitch summaries deliberately retain all identified actual pitches, including repeated fouls.
basic=pd.read_csv(ROOT/'data/processed/count_summary_2024_2025.csv')
mix=pd.read_csv(ROOT/'data/processed/count_pitch_mix_2024_2025.csv')
pitch=basic[['count','pitches','strike_result_pct','balls_pct','in_play_pct','swings_pct','whiff_per_swing_pct','hbp_pct']].rename(columns={'strike_result_pct':'S%','balls_pct':'B%','in_play_pct':'BIP%','swings_pct':'Swing%','whiff_per_swing_pct':'Whiff/Swing%','hbp_pct':'pitch_HBP%'})
fast={'4-Seam Fastball','Sinker','Cutter'}
for c in COUNTS:
    m=mix[mix['count'].eq(c)].sort_values('pitches',ascending=False)
    fb=m.loc[m.pitch_name.isin(fast),'selection_pct'].sum()
    pitch.loc[pitch['count'].eq(c),'FB%']=fb
    pitch.loc[pitch['count'].eq(c),'NFB%']=100-fb
    pitch.loc[pitch['count'].eq(c),'top3']='; '.join(f'{r.pitch_name} {r.selection_pct:.2f}%' for r in m.head(3).itertuples())
save(pitch,'advantage_pitch_explanators.csv')

# Venue IDs are from the already-downloaded schedule, including overseas games.
venue={}
for year in (2024,2025):
    sch=json.loads((ROOT/f'data/raw/mlb/{year}/schedule_{year}.json').read_text(encoding='utf-8-sig'))
    for day in sch['dates']:
        for g in day['games']:venue[g['gamePk']]=g['venue']['id']
p['venue']=p.game_pk.map(venue)
p['base_state']=sum((p[f'on_{b}b'].notna().astype(int)*(2**(b-1))) for b in (1,2,3))
p['score_bin']=pd.cut(p.bat_score_diff,[-np.inf,-4,-1,0,3,np.inf],labels=['trailing4+','trailing1-3','tie','leading1-3','leading4+']).astype(str)
p['matchup']=p.stand.fillna('?')+p.p_throws.fillna('?')
p['batter_year']=p.batter.astype(str)+'_'+p.game_year.astype(str)
p['pitcher_year']=p.pitcher.astype(str)+'_'+p.game_year.astype(str)
p['venue_year']=p.venue.astype(str)+'_'+p.game_year.astype(str)
p['inning_bin']=p.inning.clip(upper=10)
features=['batter_year','pitcher_year','matchup','venue_year','score_bin','base_state','outs_when_up','inning_bin','game_year']
codes=[pd.factorize(p[f].fillna('missing').astype(str))[0] for f in features]
sizes=[int(x.max())+1 for x in codes]
games=p.game_pk.unique().copy();rng.shuffle(games)
foldmap={g:i%5 for i,g in enumerate(games)};fold=p.game_pk.map(foldmap).to_numpy()
y=p.z.to_numpy()
def oof_ridge(alpha):
    prediction=np.zeros(len(p)); diagnostics=[]
    for f in range(5):
        tr=fold!=f;te=~tr;yt=y[tr];intercept=yt.mean();fitted=np.full(len(yt),intercept)
        coef=[np.zeros(s) for s in sizes];tc=[c[tr] for c in codes]
        ns=[np.bincount(c,minlength=s) for c,s in zip(tc,sizes)]
        for iteration in range(150):
            old=fitted.copy();shift=(yt-fitted).mean();intercept+=shift;fitted+=shift
            for j,(c,s) in enumerate(zip(tc,sizes)):
                fitted-=coef[j][c]
                coef[j]=np.bincount(c,weights=yt-fitted,minlength=s)/(ns[j]+alpha)
                fitted+=coef[j][c]
            if np.max(np.abs(fitted-old))<1e-7:break
        prediction[te]=intercept+sum(co[c[te]] for co,c in zip(coef,codes))
        diagnostics.append({'fold':f,'iterations':iteration+1,'max_last_change':float(np.max(np.abs(fitted-old)))})
    return prediction,diagnostics
model_log={}
for alpha in (20.,100.,500.):
    pred,diag=oof_ridge(alpha)
    p['pred']=pred;p['resid']=y-pred
    rr=reached[['pa_id','count','game_year']].merge(p[['pred','resid']],left_on='pa_id',right_index=True)
    rmean=rr.groupby(['game_year','count']).resid.mean()
    # Center within each season at all-eligible-PA residual mean, exactly anchoring 0-0.
    adjusted=np.array([100+100*sum(q[yr]*(rmean.loc[yr,c]-rmean.loc[yr,'0-0']) for yr in (2024,2025)) for c in COUNTS])
    result[f'adjusted_index_alpha{int(alpha)}']=adjusted
    model_log[str(alpha)]={'OOF_MSE':float(np.mean((y-pred)**2)),'constant_MSE':float(np.mean((y-1)**2)),'diagnostics':diag}
    print('Adjustment alpha',alpha,'max shift',float(np.max(np.abs(adjusted-point))),flush=True)
save(result,'advantage_count_results.csv')
# Compare major covariate strata to their own 0-0 baseline as a heterogeneity diagnostic.
strata=[]
for feature in ['matchup','base_state','outs_when_up','score_bin','venue_year']:
    rr=reached.merge(p[[feature]],left_on='pa_id',right_index=True)
    for (yr,g),r in rr.groupby(['game_year',feature]):
        b=r.loc[r['count'].eq('0-0'),'value'].mean()
        for c,z in r.groupby('count'):
            strata.append(dict(feature=feature,group=g,year=yr,count=c,N=len(z),index=100*z.value.mean()/b))
save(pd.DataFrame(strata),'advantage_context_strata.csv')
# Reference-denominator sensitivity: omit sacrifice bunts as official wOBA does.
sens=[]
for label,subset in [('omit_sac_bunt',reached[~reached.event.isin(['sac_bunt','sac_bunt_double_play'])]),('omit_OTHER',reached[reached.result.ne('OTHER')])]:
    val=np.zeros(12)
    for yr in (2024,2025):
        r=subset[subset.game_year.eq(yr)];m=r.groupby('count').value.mean().reindex(COUNTS)
        val+=q[yr]*100*m.to_numpy()/m.loc['0-0']
    sens.extend(dict(sensitivity=label,count=c,index=x) for c,x in zip(COUNTS,val))
save(pd.DataFrame(sens),'advantage_denominator_sensitivity.csv')
manifest=[]
for f in sorted((ROOT/'data').rglob('*')):
    if f.is_file() and (f.suffix=='.csv' or f.name.startswith('schedule_')) and 'feasibility' not in f.name:
        manifest.append({'path':str(f.relative_to(ROOT)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
audit={'raw_rows':len(d),'all_PA':len(pa),'eligible_PA':len(p),'games':int(p.game_pk.nunique()),'batter_count':int(p.batter.nunique()),'pitcher_count':int(p.pitcher.nunique()),
       'exclusions':pa.exclusion.value_counts().to_dict(),'unmapped_events':pa.loc[pa.result.isna(),'event'].value_counts(dropna=False).astype(int).to_dict(),
       'repeated_count_rows_removed':int(len(d)-len(d.drop_duplicates(['pa_id','count']))),'PA_with_multiple_nonnull_events':int((d.groupby('pa_id').events.count()>1).sum()),
       'first_count_distribution':first['count'].value_counts().to_dict() if 'count' in first else {},
       'weights':WEIGHTS,'scale':SCALE,'league_R_PA':RPA,'baseline_value':base.to_dict(),'season_mix':q.to_dict(),
       'bootstrap_replicates':B,'seed':20260907,'simultaneous_critical':float(critical),'venue_missing':int(p.venue.isna().sum()),
       'model':model_log,'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'inputs':manifest}
(OUT/'advantage_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
# Store bootstrap draws to allow paired count comparisons without assuming independence.
np.savez_compressed(OUT/'advantage_bootstrap.npz',index=boots,runs=bootruns,counts=np.array(COUNTS))
assert (events[['1B','2B','3B','HR','BB','HBP','K','OUT','OTHER']].sum(axis=1)==events.N_PA).all()
assert events.loc['0-0','N_PA']==len(p)
assert abs(point[0]-100)<1e-9
print(result[['count','N_PA','index','CI95_low','CI95_high','grade','grade_certainty','adjusted_index_alpha100']].to_string(index=False),flush=True)
