"""Create plan and SHA256 seal before any new external V2 row processing."""
from pathlib import Path
import datetime,hashlib,json,shutil
import pandas as pd
B=Path(__file__).resolve().parent;ROOT=B.parents[3];AN=B.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def meta(p):
    with Path(p).open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=Path(p).relative_to(ROOT).as_posix(),sha256=h,bytes=Path(p).stat().st_size)
def write(p,d):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)

def main():
    assert not (B/'plan.json').exists() and not (B/'plan_seal.json').exists()
    specs={m:ROOT/f'models/bcap/{m}/v{v}/specification.yaml' for m,v in [('pitch','0.2.0'),('swing','0.2.0'),('pitch_sb','0.1.0'),('pitch_ff','0.1.0')]}
    cc={m:read(p) for m,p in specs.items()}
    engine=ROOT/'models/bcap/development_v2/v0.2.0/engine.py'
    assert not (B/'engine.py').exists();shutil.copy2(engine,B/'engine.py')
    dev=ROOT/'columns/001-ball-count/data/processed/bcap_dev_v2_20260912__r01.pkl'
    d=pd.read_pickle(dev)
    roster={k:sorted(map(int,d.loc[d.eligible_pitch|d.eligible_swing,k].unique())) for k in ['pitcher','batter']};del d
    inputs={2023:ROOT/'columns/001-ball-count/data/processed/bcap_2023_v010_bcap_pitch__mlb_2023__20260909__r01.pkl',2026:ROOT/'columns/001-ball-count/data/processed/bcap_2026_v010_bcap_pitch__mlb_2026_ytd_20260907__20260909__r01.pkl'}
    runs={};fitlogs=[]
    for year in [2023,2026]:
        runs[str(year)]={};period='2023' if year==2023 else '2026_ytd_20260907'
        for model in specs:
            log=AN/f'runs/bcap_{model}__mlb_2024_2025__20260912__r01/artifacts/fit_diagnostics.csv';fitlogs.append(log)
            logs=pd.read_csv(log);alphas={}
            for target,label in [('p','prop'),('m0','m0'),('m1','m1')]:
                values=logs.loc[logs.fit_id.str.fullmatch('fold[012]/'+label),'alpha'].unique()
                assert len(values)==1;alphas[target]=int(values[0])
            runs[str(year)][model]=dict(run_id=f'bcap_{model}__mlb_{period}__20260914__r01',definition=specs[model].relative_to(ROOT).as_posix(),fixed_alpha=alphas,measurement_hold=year==2026 and model in ['pitch_sb','swing'])
    weights=read(ROOT/'models/bcai/ridge/v0.2.0/specification.yaml')['weights'];weights={str(y):weights[str(2025 if y==2026 else y)] for y in [2023,2024,2025,2026]}
    plan=dict(plan_id='bcap_external_20260914__r01',created_at_utc=now(),status='FROZEN_BEFORE_NEW_V2_EXTERNAL_RESULTS',
        purpose='External pattern replication and final column conclusions; no algorithm improvement, policy learning or chasing significance',
        prior_exposure='2023/2026 already used in BCAI/Ridge and BCAP V1. Latest development/light-review/metadata and historical summaries read before plan. No new V2 external contrasts viewed. Not virgin test sets or independent external preregistration.',
        inputs={str(y):meta(p) for y,p in inputs.items()},date_ranges={'2023':['2023-03-30','2023-10-01'],'2026':['2026-03-25','2026-09-07']},
        measurement={'2023':'same official pre-2026 definition as development; no transformation','2026_pitch_sb':'MEASUREMENT_HOLD','2026_swing':'MEASUREMENT_HOLD','2026_pitch_and_FF':'allowed; no coordinate/zone predictors'},
        actions=cc['pitch']['actions'],weights=weights,weight_scale='Season-specific final PA W. 2026 fixed 2025. Same construction but coefficients differ; compare direction and ranges, not exact like-for-like magnitudes or percentages/runs. No BCAI/transition reward or sum across PA pitches.',
        population='Existing completed/eligible PA rows and original exclusions preserved. PITCH/FF eligible_pitch, 2023 SB eligible_pitch plus finite geometry and top>bot, SWING existing eligible_swing then existing physical support. Selected observational current-decision target, not a one-pitch causal intervention or sequential PA policy.',
        exclusions=cc['pitch']['pa_exclusions'],features={m:c['features'] for m,c in cc.items()},
        estimation='External year separately, same fixed V2 ridge nuisance algorithm, same 3 outer game folds. AIPW on same supported rows per action. Fixed development selected alphas (identical across all 3 development folds); no external alpha selection. Internal 5-way outer-training game partition fold0 for Platt, propensity fits folds1-4, arm outcomes all outer-training rows. Dictionaries/centering only corresponding fit data.',
        predictor_test='NOT_RUN: no full-development final fit exists; no unnecessary final refit or ensemble prediction test. Reported MSE/Brier concern external OOF auxiliary models, never frozen development predictions.',
        policy='No policy learned or evaluated; only adjusted group contrasts.',seed=20260909,outer_folds=3,nuisance_seed='20260909+2000+outer_fold; same fixed deterministic convention in each year',
        support={k:cc['pitch'][k] for k in ['trim','numerical_epsilon','min_entity_arm_training','min_rows','min_ess','min_arm_games','min_coverage','max_game_share']},
        unknown='Train-only categorical dictionaries; unknown blocks have zero centered effect. Same entity-arm support >=30 in external nuisance training; unseen support entity cannot be imputed supported. Report known/unseen vs development roster separately from external nuisance known/unseen. No outcome-based new exclusions.',
        development_rosters=roster,runs=runs,comparison_runs={str(y):f'bcap_pitch_compare__mlb_{"2023" if y==2023 else "2026_ytd_20260907"}__20260914__r01' for y in [2023,2026]},
        primary={'contrasts':['pitch_sb:0-2:2023','pitch_sb:1-2:2023','pitch_sb:0-2:2026','pitch_sb:1-2:2026'],'family':4,'expected_delta_sign':1,'delta':'S minus B','margin_W':.01,'interval':'two-sided fixed-score game-cluster t(G-1), alpha=.05/4 Bonferroni; retain 4 even with 2026 measurement hold'},
        secondary={'family':236,'scope':'2 years x (10 other SB counts + 60 SWING count-region cells + 2 pitch definitions x 12 counts x 2 own/common populations)=236. Missing measurement comparisons retained in family denominator. No fine pitch SWING cells or new pitch families. Development original219/255 intervals preserved separately; external236 is a different prespecified family, not selected post-results.'},
        descriptive='Nominal95 intervals and raw/gcomp/AIPW on same support; pitch fold3 direction and support, no formal extra subgroup tests. Propensity/calibration, extreme weights, known/unseen, composition, denominators. No extra trims/clips or bootstrap.',
        judgment={'priority':['MEASUREMENT_HOLD if measurement not comparable, without numeric estimate','NO_SUPPORT if existing group gates fail','REPRODUCED if reference direction matches and adjusted interval excludes0','OPPOSITE_DIRECTION if opposite direction and adjusted interval excludes0','UNCERTAIN otherwise'],
            'reference':'SB main positive; other SB and pitch use stored development point direction per own/common; SWING CENTER positive, outside negative. Development unconfirmed cells explicitly tagged and same-direction external result is exploratory, not reproduction of an established effect.',
            'separate_flags':'point sign same/opposite; interval excludes0; sign-oriented lower bound>=.01; entire adjusted interval inside±.01; raw/gcomp/AIPW sign reversals. These flags do not turn uncertainty into equality or causal recommendation.',
            'opposite_weak':'Opposite point but interval contains0 => UNCERTAIN, with opposite point direction explicitly shown'},
        uncertainty='Conditional fixed-score game cluster intervals reflect within-game repeated PA/pitches. Nuisance re-learning and cross-game player/series dependence not included, actual coverage unverified. No claim full-learning95.',
        stopping='Complete possible modules and report, retain measurement holds and contrary/uncertain findings. No refitting algorithm changes, new data, KBO, new seeds, bootstrap, joint/sequential policy, external publication.')
    write(B/'plan.json',plan)
    files=[B/'plan.json',B/'plan.md',Path(__file__),B/'prepare_external.py',B/'run_external.py',B/'engine.py',B/'verify_primary.py',B/'measurement_review.md',B/'measurement_review.json',engine,dev,*inputs.values(),*specs.values(),*set(fitlogs),ROOT/'models/bcai/observed/v1.0.0/specification.yaml',ROOT/'models/bcai/ridge/v0.2.0/specification.yaml',AN/'bcap_independent_review_20260909__r01/lineage/all_strict_count_exceptions.csv']
    for name in ['pitch','pitch_sb','swing']:
        files.append(AN/f'runs/bcap_{name}__mlb_2024_2025__20260912__r01/artifacts/count_values.csv')
    files.extend([AN/'bcap_v2_development_20260912__r01/batter_five_regions.csv',AN/'runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/primary_values.csv'])
    write(B/'plan_seal.json',dict(sealed_at_utc=now(),scope='Local auditable before-new-V2-external-results seal, not externally witnessed preregistration',files=[meta(p) for p in sorted(set(files))]))
    print('SEALED',read(B/'plan_seal.json')['sealed_at_utc'],len(files),flush=True)

if __name__=='__main__':main()
