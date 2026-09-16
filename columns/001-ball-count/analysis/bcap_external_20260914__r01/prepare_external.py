"""Sealed, minimal V2 transformation of existing V1 external input pickles.

This prepares selected-row labels/features, never nuisance fits or action values.
The source and all existing artifacts remain untouched. 2026 location-dependent
analyses are withheld; retained V1 measurement columns are historical metadata.
"""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import traceback

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
BUNDLE = Path(__file__).resolve().parent
COL = ROOT / 'columns/001-ball-count'
KEY = ['game_pk', 'at_bat_number', 'pitch_number']
SOURCES = {
    2023: COL / 'data/processed/bcap_2023_v010_bcap_pitch__mlb_2023__20260909__r01.pkl',
    2026: COL / 'data/processed/bcap_2026_v010_bcap_pitch__mlb_2026_ytd_20260907__20260909__r01.pkl',
}
EXPECTED = {
    2023: dict(rows=720684, games=2430, PA=184478, eligible_PA=183534,
               pitch=716113, swing=716385, first='2023-03-30', last='2023-10-01', exceptions=3),
    2026: dict(rows=639042, games=2165, PA=164281, eligible_PA=163327,
               pitch=635095, swing=635451, first='2026-03-25', last='2026-09-07', exceptions=1),
}
SPEC_PATH = ROOT / 'models/bcap/pitch/v0.2.0/specification.yaml'
OBS_PATH = ROOT / 'models/bcai/observed/v1.0.0/specification.yaml'
WEIGHTS_PATH = ROOT / 'models/bcai/ridge/v0.2.0/specification.yaml'
EXCEPTIONS_PATH = COL / 'analysis/bcap_independent_review_20260909__r01/lineage/all_strict_count_exceptions.csv'


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2,
        default=lambda x: x.item() if hasattr(x, 'item') else str(x)), encoding='utf-8')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def meta(path):
    path = Path(path).resolve()
    return dict(path=path.relative_to(ROOT).as_posix(), sha256=sha(path), bytes=path.stat().st_size)


def seal_check(source):
    """Require code, plan, source and semantic definitions to be in the seal."""
    plan = BUNDLE / 'plan.json'
    seal_path = BUNDLE / 'plan_seal.json'
    read(plan)
    seal = read(seal_path)
    records = {str(x['path']).replace('\\', '/'): x for x in seal['files']}
    required = [plan, Path(__file__), source, SPEC_PATH, OBS_PATH, WEIGHTS_PATH, EXCEPTIONS_PATH]
    for path in required:
        relative = path.resolve().relative_to(ROOT).as_posix()
        if relative not in records:
            raise AssertionError('Required pre-access sealed file absent: ' + relative)
    for relative, item in records.items():
        path = ROOT / relative
        if sha(path) != item['sha256']:
            raise AssertionError('Sealed hash changed: ' + relative)
    return meta(plan), meta(seal_path)


def prepare(year):
    source = SOURCES[year]
    expected = EXPECTED[year]
    destination = COL / f'data/processed/bcap_external_v2_{year}_20260914__r01.pkl'
    audit = BUNDLE / f'preparation_{year}'
    access_path = BUNDLE / f'preparation_access_{year}.json'
    if destination.exists() or audit.exists() or access_path.exists():
        raise FileExistsError('Preparation has existing evidence/output; choose a new run rather than overwrite.')
    plan, seal = seal_check(source)
    audit.mkdir(parents=True)
    access = dict(at_utc=now(), year=year, event='first_reused_external_input_row_load_for_V2_preparation',
                  purpose='Post-seal labels and key/W checks; no action-value estimation or fitting',
                  source=meta(source), plan=plan, seal=seal,
                  prior_exposure='Existing BCAI/Ridge and BCAP V1 input; not a never-seen dataset.')
    write(access_path, access)
    checks = []

    def check(name, okay, detail=None):
        checks.append(dict(check=name, status='PASS' if bool(okay) else 'FAIL', detail=detail))
        if not okay:
            raise AssertionError(name)

    try:
        d = pd.read_pickle(source)
        check('specified_year_only', set(d.game_year.unique()) == {year})
        check('existing_input_rows_games_PA', len(d) == expected['rows'] and
              d.game_pk.nunique() == expected['games'] and d.pa_id.nunique() == expected['PA'])
        check('complete_unique_pitch_keys', not d[KEY].isna().any().any() and not d.duplicated(KEY).any())
        check('unique_row_id', d.row_id.is_unique and not d.row_id.isna().any())
        check('pitch_order_unchanged_sorted', d[KEY].reset_index(drop=True).equals(
              d[KEY].sort_values(KEY).reset_index(drop=True)))
        dates = d.official_date.astype(str)
        check('official_date_existing_bounds', dates.min() == expected['first'] and dates.max() == expected['last'],
              dict(first=dates.min(), last=dates.max()))
        check('valid_pre_pitch_counts', d.balls.between(0, 3).all() and d.strikes.between(0, 2).all())
        check('count_string_matches_pre_pitch_counts', d['count'].astype(str).eq(
              d.balls.astype(str) + '-' + d.strikes.astype(str)).all())
        check('PA_key_mapping', d.groupby('pa_id', observed=True)[KEY[:2]].nunique().le(1).all().all())
        check('PA_Y_constant', d.groupby('pa_id', observed=True).Y.nunique().le(1).all())
        check('eligible_PA_existing_count', d.loc[d.eligible_pa, 'pa_id'].nunique() == expected['eligible_PA'])
        for variant in ['pitch', 'swing']:
            check(variant + '_eligibility_existing_count', int(d['eligible_' + variant].sum()) == expected[variant])
            check(variant + '_eligibility_reason', d['eligible_' + variant].eq(d['reason_' + variant].eq('included')).all())
            a = d.loc[d['eligible_' + variant], 'A_' + variant]
            check(variant + '_binary_complete_action', a.notna().all() and a.isin([0, 1]).all())
        obs = read(OBS_PATH)
        event_map = {event: result for result, events in obs['result_classification'].items() for event in events}
        last = d.drop_duplicates('pa_id', keep='last').set_index('pa_id')
        final = d.pa_id.map(last.events.astype('string'))
        check('terminal_event_link', final.fillna('MISSING').eq(d.final_event.astype('string').fillna('MISSING')).all())
        results = final.map(event_map)
        check('OBS_result_classification', results.astype('string').fillna('MISSING').eq(
              d.result.astype('string').fillna('MISSING')).all())
        weight_year = 2025 if year == 2026 else year
        weights = read(WEIGHTS_PATH)['weights'][str(weight_year)]
        wanted_Y = np.array([weights.get(str(result), 0.) if eligible else np.nan
                            for result, eligible in zip(d.result, d.eligible_pa)])
        check('season_W_no_extra_reward', np.allclose(d.Y, wanted_Y, rtol=0, atol=0, equal_nan=True))
        spec = read(SPEC_PATH)
        fb, nfb = spec['actions']['FB'], spec['actions']['NFB']
        coarse = {**{x: 'FB' for x in fb}, **{x: 'NFB' for x in nfb}}
        group = d.pitch_type.astype('string').map(coarse).fillna('UNCLASSIFIED')
        check('current_closed_FB_NFB_mapping', group.astype(str).eq(d.pitch_group.astype(str)).all())
        check('eligible_pitch_closed_codes', d.loc[d.eligible_pitch, 'pitch_type'].isin(fb + nfb).all())
        check('FB_action_labels', d.loc[d.eligible_pitch, 'A_pitch'].eq(
              d.loc[d.eligible_pitch, 'pitch_group'].eq('FB').astype(int)).all())
        swing_map = {**{x: 1 for x in spec['actions']['Swing']}, **{x: 0 for x in spec['actions']['Take']}}
        check('Swing_action_labels', d.loc[d.eligible_swing, 'A_swing'].eq(
              d.loc[d.eligible_swing, 'description'].astype('string').map(swing_map)).all())
        d['prev_pitch_group'] = d.prev_pitch_type.astype('string').map(
            {**coarse, 'START': 'START', 'MISSING_PREVIOUS': 'MISSING_PREVIOUS'}).fillna('UNCLASSIFIED').astype('category')
        check('coarse_previous_pitch_categories', set(d.prev_pitch_group.astype(str)) <=
              {'FB', 'NFB', 'START', 'MISSING_PREVIOUS', 'UNCLASSIFIED'})
        # Original fine lag was computed before any eligibility filtering; preserve it.
        check('first_PA_lag_START_preserved', d.drop_duplicates('pa_id').prev_pitch_group.eq('START').all())
        ff = d.pitch_type.astype('string').map({x: int(x == 'FF') for x in fb + nfb}).astype('Int8')
        d['A_pitch_ff'] = ff.mask(~d.eligible_pitch)
        d['eligible_pitch_ff'] = d.eligible_pitch.copy()
        d['reason_pitch_ff'] = d.reason_pitch.astype(str)
        check('FF_action_and_eligibility', d.loc[d.eligible_pitch_ff, 'A_pitch_ff'].eq(
              d.loc[d.eligible_pitch_ff, 'pitch_type'].eq('FF').astype(int)).all())
        if year == 2023:
            geometry = d[['plate_x', 'plate_z', 'sz_top', 'sz_bot']].to_numpy(dtype=float)
            valid = np.isfinite(geometry).all(axis=1) & d.sz_top.gt(d.sz_bot).to_numpy()
            inside = d.plate_x.abs().le(17 / 24) & d.plate_z.ge(d.sz_bot) & d.plate_z.le(d.sz_top)
            d['A_pitch_sb'] = pd.array(np.where(valid, inside.astype(int), np.nan), dtype='Int8')
            d['eligible_pitch_sb'] = d.eligible_pitch & valid
            d['reason_pitch_sb'] = np.where(~d.eligible_pitch, d.reason_pitch.astype(str),
                                          np.where(~valid, 'invalid_geometry', 'included'))
            check('SB_binary_complete_action', d.loc[d.eligible_pitch_sb, 'A_pitch_sb'].notna().all())
            measurement = '2023 pre-2026 ball-center geometry; 2024/2025 concept retained'
        else:
            d['A_pitch_sb'] = pd.array([pd.NA] * len(d), dtype='Int8')
            d['eligible_pitch_sb'] = False
            d['reason_pitch_sb'] = 'measurement_withheld_2026'
            check('2026_SB_no_geometric_action_computed', d.A_pitch_sb.isna().all() and not d.eligible_pitch_sb.any())
            measurement = '2026 S/B and SWING execution withheld for incompatible plane/zone; retained V1 location columns not used'
        exceptions = pd.read_csv(EXCEPTIONS_PATH, usecols=KEY + ['game_year'])
        known_keys = pd.MultiIndex.from_frame(exceptions.loc[exceptions.game_year.eq(year), KEY])
        d['known_count_exception'] = pd.MultiIndex.from_frame(d[KEY]).isin(known_keys)
        check('known_exceptions_flagged_and_retained', int(d.known_count_exception.sum()) == expected['exceptions'])
        d.loc[d.known_count_exception, KEY + ['game_year', 'count', 'description']].to_csv(
            audit / 'known_exceptions_retained.csv', index=False)
        flow = []
        for variant in ['pitch', 'pitch_ff', 'pitch_sb', 'swing']:
            for reason, rows in d.groupby('reason_' + variant, observed=True, dropna=False):
                flow.append(dict(model=variant, year=year, reason=str(reason), rows=len(rows),
                                 PA=rows.pa_id.nunique(), games=rows.game_pk.nunique(),
                                 execution_allowed=not (year == 2026 and variant in ['pitch_sb', 'swing'])))
        pd.DataFrame(flow).to_csv(audit / 'selection_counts.csv', index=False)
        d.to_pickle(destination)
        result = dict(status='PASS', started_at_utc=access['at_utc'], finished_at_utc=now(), year=year,
                      rows=len(d), games=d.game_pk.nunique(), PA=d.pa_id.nunique(), weights=weights,
                      weight_reference_year=weight_year,
                      eligible={v: int(d['eligible_' + v].sum()) for v in ['pitch', 'pitch_ff', 'pitch_sb', 'swing']},
                      measurement_status=measurement, checks=checks, input=access['source'], output=meta(destination),
                      code=meta(__file__), plan=plan, seal=seal,
                      known_count_exceptions='Existing unresolved exceptions flagged only; no correction or new audit',
                      scope='Minimal reuse checks. No raw re-audit, nuisance fits, action-value estimates or new data.',
                      definitions=[meta(x) for x in [SPEC_PATH, OBS_PATH, WEIGHTS_PATH, EXCEPTIONS_PATH]])
        write(audit / 'preparation.json', result)
        print(json.dumps({k: result[k] for k in ['status', 'year', 'rows', 'games', 'eligible', 'measurement_status']},
                         ensure_ascii=False), flush=True)
    except Exception:
        write(audit / 'preparation.json', dict(status='FAILED', year=year, at_utc=now(), checks=checks,
                                              error=traceback.format_exc(), source=access['source']))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--year', type=int, choices=[2023, 2026], required=True)
    prepare(parser.parse_args().year)
