"""Freeze the bounded FF/non-FF extension before inspecting its outcome contrasts."""
from pathlib import Path
import datetime,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[2]
DAY=datetime.datetime.now().strftime('%Y%m%d')
CODE=ROOT/'models/bcap/pitch_ff/v0.1.0'
AN=ROOT/'columns/001-ball-count/analysis'
B=AN/f'bcap_pitch_classification_{DAY}__r01'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def meta(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}
def js(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
assert not B.exists() and not (CODE/'specification.yaml').exists()
B.mkdir(parents=True);CODE.mkdir(parents=True,exist_ok=True)
old=ROOT/'models/bcap/pitch/v0.2.0/specification.yaml'
c=json.loads(old.read_text(encoding='utf-8-sig'))
valid=c['actions']['FB']+c['actions']['NFB']
c.update(model_id='BCAP-PITCH-FF-v0.1.0',version='0.1.0',status_at_definition='DRAFT',generation='V2 FF extension',variant='pitch',action1='FF',action0='non-FF',comparison_family=255)
c['action_codes']={'FF':['FF'],'non-FF':[x for x in valid if x!='FF']}
c['eligibility']='Reuse exactly eligible_pitch rows in bcap_dev_v2_20260912__r01.pkl; all eligible codes must be in the closed valid list. Missing/UN/PO/other exclusions are never assigned non-FF.'
c['lag_mapping']='Retain original prev_pitch_group=FB/NFB; only current action definition changes. This is not a previous-FF feature experiment.'
c['tuning']='No new tuning. Fixed alpha p100/m0=m1=1000; new propensity, Platt, and action outcome fits for new A, once per original game fold.'
c['family_scope']='Union of original219 contrasts and36 additions (FF own12, FF common12, FB common12)=255. All48 main report contrasts use Bonferroni255; legacy FB own219 intervals remain separately identified. No reduction of multiplicity after seeing outcomes.'
c['uncertainty']='Existing fixed-score game-cluster sandwich with t(G-1); individual nominal95 and primary Bonferroni255. Whole-game repeated pitches handled; full nuisance-learning and across-game player dependence remain unassessed.'
c['evidence_labels']='Primary gates plus explicit analysis_plan.json rules: insufficient support; material method/year/fold instability; interval-contained small difference; consistent development direction; remaining uncertainty. No causal recommendation.'
for k in ['s_b_definition','s_b_eligibility','region','region_model_inputs']:c.pop(k,None)
js(CODE/'specification.yaml',c)
shutil.copy2(ROOT/'models/bcap/development_v2/v0.2.0/engine.py',CODE/'engine.py')
plan={
 'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'model_id':c['model_id'],'definition':meta(CODE/'specification.yaml'),'engine':meta(CODE/'engine.py'),
 'existing_result_exposure':'Original V2 results have already been viewed, including3-0 and3-1 concerns; this is a development extension after exposure, not independent preregistration.',
 'FF_outcome_exposure':'No FF/non-FF action-specific Y means, fitted contrasts or results inspected yet. Only source schema and pitch code/eligibility frequencies were inspected.',
 'source':'columns/001-ball-count/data/processed/bcap_dev_v2_20260912__r01.pkl',
 'old_run':'bcap_pitch__mlb_2024_2025__20260912__r01',
 'new_run':f'bcap_pitch_ff__mlb_2024_2025__{DAY}__r01',
 'comparison_run':f'bcap_pitch_compare__mlb_2024_2025__{DAY}__r01',
 'closed_codes':c['action_codes'],'excluded_codes':['PO','UN','missing','any code outside closed list'],
 'population':'Same existing eligible_pitch rows, completed selected PAs; PA exclusions and seasonal W exactly inherited. Retain known development count exceptions without changes.',
 'estimand':'Current single-pitch family comparison in observed selected decision rows, final PA W. Same real evaluation rows per contrast; not intention, sequential policy, or identified causal intervention.',
 'nuisance':'Exact original engine bytes, original pre-pitch14features, both player shrinkage, original game3fold assignments checked by row_id+pitch keys, seed20260909, fixedalpha100/1000/1000, training-game Platt, no tuning/full refit.',
 'support':'Each scheme: train pitcher at least30 occurrences of each NEW action and .05<=OOF p<=.95. Common mask is intersection. No outcome Y/residual/sign threshold in mask; p is trained on action only. Common mask is model-dependent estimated support, not a preselected population.',
 'denominators':'Coverage always support rows divided by all eligible rows in same count/year/fold. Common rows exactly identical for both schemes; each scheme retains its own action, p and ESS. Retention common/own also shown. Naive means use observed arms within those same supported rows, so arm composition differs; gcomp/AIPW standardize both arms to identical rows.',
 'group_gates':{k:c[k] for k in ['min_rows','min_ess','min_arm_games','min_coverage','max_game_share']},
 'practical_delta_W':.01,
 'primary':'48count contrasts: 12counts x2schemes x2populations(own/common). No primary overall contrast, no statistical difference-of-contrasts because actions differ.',
 'multiplicity':{'legacy_family':219,'new_contrasts':36,'union_family':255,'primary_intervals':'Bonferroni255 for all48; retain nominal95 and old own219 for attribution, no promotion based on unadjusted intervals','auxiliary':'year2/fold3 x12 x2schemes x2populations, nominal95 descriptive only; no independent validation or new significance decisions'},
 'secondary':'Counts/action rates/propensity bins and quantiles/IPW ESS and game concentration; naive vs gcomp vs AIPW; all2years and3original folds; pitch composition including FF,SI,FC,existing NFB aggregate and actual code frequencies. These are saved-score aggregates, not new subtype models.',
 'instability_rule':'Record any sign flip separately. Material instability if gcomp and AIPW have opposite signs and bothabs>=.01, or supported year/fold estimates include both <=-.01 and >=+.01. Naive-vs-adjusted flips indicate confounding sensitivity, not alone a gate failure.',
 'decision_priority':[
  'NO_SUPPORT if any primary sample/overlap gate fails; no favorable action assigned.',
  'UNSTABLE if material instability rule holds; display point and intervals but withhold consistent-direction label.',
  'SMALL_RANGE if full Bonferroni255 interval is within[-.01,.01]; conditional small-range evidence only, not universal equivalence.',
  'CONSISTENT_DEVELOPMENT if corrected interval excludes0, abs(point)>=.01, both year and all3fold subgroups pass gates and share AIPW sign; gcomp no material opposing sign. Report separately whether interval lies beyond practical margin.',
  'UNCERTAIN otherwise; distinguish tiny point/wide range, directional nominal-only, supported direction with practical-size uncertainty, and missing subgroup support.'
 ],
 'basic_checks':'Keys, labels, W and count link inherited and checked; same original game split; no current/post-action predictors; calibration and dictionaries inside training; solver convergence; finite scores; independent rowwise AIPW arithmetic check in production; same action denominator; count totals; old saved results reproduced from scores without fitting.',
 'not_run':['swing/SB modifications or fitting','old FB refit','external years2023/2026','new data/KBO','bootstrap/repeatedseeds','broad search','learned policy','independent full audit','Drive/publication'],
 'stopping_rule':'Complete these two definitions, diagnostics and report; insufficient evidence is valid. No further definition/model search or automatic external verification.'
}
js(B/'analysis_plan.json',plan)
(B/'analysis_plan.md').write_text('''# FB/NFB 및 포심/비포심 비교 — 추가 결과 전 기준

2024·2025 개발 확장이다. 기존 FB/NFB의 3-0·3-1 결과를 이미 알고 있으며 최초 독립 사전등록이라고 부르지 않는다. 새 FF/non-FF의 행동별 결과를 열람하기 전에 본 기준을 고정한다.

현재 한 구의 행동 분류만 FF 대 non-FF로 바꾼다. 기존 적격 행·최종 PA 시즌 W·14개 투구 전 입력·투타 축소·3fold 경기 분리·고정 규제·훈련 내 Platt를 유지한다. 직전 구종 입력은 기존 FB/NFB 그대로다. 미상·피치아웃·결측 및 기존 PA 제외를 비포심에 채우지 않는다. 자체 지지 표본과 두 지지의 교집합 표본을 모두 제시하며, 교집합도 두 모델의 행동 자체를 같게 만들지는 않는다.

주요 표는 12카운트×2분류×자체/공통=48개 차이다. 기존219개에 신규36개(FF 자체12+두 분류 공통24)를 더한255를 Bonferroni 가족으로 사용한다. 과거 FB 자체219 구간과 판정은 원 결과로 따로 보존한다. 이번 비교표에서는 양 분류 모두255를 적용해 기준을 완화하지 않는다. 연도2개·기존fold3개는 저장 점수의 내부 탐색으로, 개별 명목95% 구간만 표시하고 독립 검증이나 추가 유의성 판정으로 쓰지 않는다.

실질 차이 기준은 기존0.01 W다. 보정 구간 전체가±0.01 W 안에 있어야 ‘설정 범위 안 작은 차이’로 표시한다. 지원 미달, 실질적인 방법/연도/fold 반전, 작은 범위, 개발 내 일관된 방향, 나머지 불확실을 구분한다. 세부 배타적 판정 순서와 부호 반전 임계값은 analysis_plan.json이 실행 기준이다. 불명확을 동등함으로 바꾸거나 방향을 만들기 위해 기준을 재선택하지 않는다.

고정 점수의 경기 변동을 반영한 구간은 전체 재학습 불확실성·경기 간 선수 의존성·실제95% 포함률을 보장하지 않는다. 표본 선택과 의도·구종 품질·컨디션의 남은 교란을 명시한다. 더 복잡한 모델이나 분류 탐색으로 확장하지 않고 두 분류 비교와 보고서에서 종료한다.
''',encoding='utf-8')
js(B/'plan_seal.json',{'sealed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'phase':'Before new FF action outcome summaries or fitting','files':[meta(B/'analysis_plan.json'),meta(B/'analysis_plan.md'),meta(CODE/'specification.yaml'),meta(CODE/'engine.py')],'source_old_spec':meta(old),'notice':'Local timestamp/hash record only; no independent or external seal.'})
(CODE/'model_card.md').write_text('# BCAP-PITCH-FF-v0.1.0\n\nDRAFT. 2024·2025 기존 PITCH와 행동 분류만 다른 포심/비포심 개발 비교. 추가 결과 전 명세 고정; 실행 전.\n',encoding='utf-8')
(CODE/'validation.md').write_text('# 기본 확인 상태\n\n실행 전. 외부 검증 미실시.\n',encoding='utf-8')
print(json.dumps({'bundle':str(B),'code':str(CODE),'at_utc':plan['created_at_utc']},ensure_ascii=True))
