"""Sequence authorized BCAP history runs; all data preparation and statistics use R.

This driver never downloads data or overwrites an existing analysis run. It waits
for completed BCAI input audits, then fits the four frozen BCAP definitions.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
COL = ROOT / 'columns/001-ball-count'
RUNS = COL / 'analysis/runs'
MODELS = ('pitch', 'pitch_sb', 'swing', 'pitch_ff')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(info):
    path = ROOT / info['path']
    if not path.is_file() or sha(path) != info['sha256']:
        raise RuntimeError(f'Input hash mismatch: {path}')
    return path


def completed(pattern):
    matches = []
    for path in RUNS.glob(pattern + '/manifest.json'):
        manifest = read(path)
        if manifest.get('status') == 'COMPLETE':
            matches.append((path.parent, manifest))
    return sorted(matches, key=lambda x: x[0].name)


def prerequisite():
    """Require actual numerical reproduction of every development module."""
    evidence = {}
    for model in MODELS:
        candidates = completed(f'bcap_{model}_r__mlb_2024_2025__20260928__r*')
        if not candidates:
            raise RuntimeError(f'2024/25 R reproduction incomplete: {model}')
        run, manifest = candidates[-1]
        check_path = run / 'artifacts/checks.json'
        checks = read(check_path)
        if checks.get('status') != 'PASS':
            raise RuntimeError(f'Numerical checks not passed: {model}')
        required = {'python_nuisance_tolerance', 'python_AIPW_tolerance',
                    'python_support_exact', 'python_summary_tolerance'}
        passed = {x['check'] for x in checks['checks'] if x['status'] == 'PASS'}
        if not required <= passed:
            raise RuntimeError(f'Incomplete reproduction checks: {model}')
        expected = next(x for x in manifest['outputs'] if Path(x['path']).name == 'checks.json')
        verify(expected)
        evidence[model] = dict(run=run.name, checks_sha256=sha(check_path))
    return evidence


def historical_input(year):
    candidates = completed(f'bcai_history__mlb_{year}__*__r*')
    if not candidates:
        return None
    run, manifest = candidates[-1]
    config_record = next((x for x in manifest['input']
                          if (ROOT / x['path']).resolve() == (run / 'config.json').resolve()), None)
    if config_record is None:
        raise RuntimeError('BCAI config missing from input manifest')
    verify(config_record)
    cfg = read(run / 'config.json')
    if cfg['years'] != [year]:
        raise RuntimeError('Historical BCAI config year mismatch')
    for numerical_source in [cfg['weights_source']] + [s['schedule'] for s in cfg['seasons']]:
        record = next((x for x in manifest['input']
                       if (ROOT / x['path']).resolve() == (ROOT / numerical_source).resolve()), None)
        if record is None:
            raise RuntimeError('BCAI numerical source absent from input manifest')
        verify(record)
    paths = []
    for provenance in cfg['input_provenance']:
        provpath = ROOT / provenance
        record = next((x for x in manifest['input']
                       if (ROOT / x['path']).resolve() == provpath.resolve()), None)
        if record is None:
            raise RuntimeError('BCAI provenance missing from manifest')
        verify(record)
        for info in read(provpath)['source_files']:
            paths.append(rel(verify(info)))
    if len(paths) != len(set(paths)):
        raise RuntimeError('Repeated source files')
    return run, cfg, paths


def check_wait_state(year):
    progress = COL / 'analysis/r_history_20260928/progress.json'
    if progress.exists():
        for record in read(progress):
            if record.get('stop_reason') or (record['year'] == year and record['status'] == 'FAILED'):
                raise RuntimeError(f'BCAI acquisition/calculation stopped: {record}')


def run_r(rscript, script, config, logpath):
    env = os.environ.copy()
    for key in ('LANG', 'LC_ALL', 'LC_CTYPE'):
        env.pop(key, None)
    with Path(logpath).open('x', encoding='utf-8') as log:
        subprocess.run([rscript, '--vanilla', script, str(config)], cwd=ROOT,
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)


def acquire_lock(path):
    """OS-released advisory lock, including after an interrupted process."""
    stream = path.open('a+b')
    stream.seek(0)
    if not stream.read(1):
        stream.write(b'0')
        stream.flush()
    stream.seek(0)
    if os.name == 'nt':
        import msvcrt
        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    return stream


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--years', nargs='+', type=int, required=True)
    parser.add_argument('--rscript', required=True)
    parser.add_argument('--date', default=dt.date.today().strftime('%Y%m%d'))
    parser.add_argument('--wait-for-inputs', action='store_true')
    parser.add_argument('--check-only', action='store_true')
    parser.add_argument('--preparation-attempt', type=int, default=1)
    args = parser.parse_args()
    if len(set(args.years)) != len(args.years) or any(y < 2015 or y > 2023 for y in args.years):
        parser.error('Explicit unique historical years 2015..2023 required')
    if not args.date.isdigit() or len(args.date) != 8:
        parser.error('Date must be YYYYMMDD')
    if args.preparation_attempt < 1:
        parser.error('Preparation attempt must be positive')
    prerequisites = prerequisite()
    bundle = COL / f'analysis/r_bcap_history_{args.date}'
    bundle.mkdir(parents=True, exist_ok=True)
    if args.check_only:
        print(json.dumps(dict(prerequisites=prerequisites,
                             available_years=[y for y in args.years if historical_input(y)]),
                         ensure_ascii=False, indent=2))
        return
    lock = acquire_lock(bundle / 'driver.lock')
    state = dict(status='RUNNING', pid=os.getpid(), years=args.years,
                 preparation_attempt=args.preparation_attempt,
                 prerequisites=prerequisites, records=[], started_at=dt.datetime.now().isoformat())
    progress = bundle / 'progress.json'
    if progress.exists():
        archive = bundle / 'progress_attempts'
        archive.mkdir(exist_ok=True)
        shutil.copy2(progress, archive / (dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.json'))
    save(progress, state)
    try:
        for year in args.years:
            record = dict(year=year, status='WAITING_FOR_BCAI_INPUT', models={})
            state['records'].append(record)
            save(progress, state)
            source = historical_input(year)
            while source is None and args.wait_for_inputs:
                check_wait_state(year)
                time.sleep(30)
                source = historical_input(year)
            if source is None:
                raise RuntimeError(f'BCAI source audit not complete for {year}')
            source_run, cfg, rawfiles = source
            prep = COL / f'data/processed/r_bcap_history_{args.date}/{year}/r{args.preparation_attempt:02d}'
            prep.mkdir(parents=True, exist_ok=True)
            prepared = prep / 'prepared.rds'
            audit = prep / 'audit/preparation_audit.json'
            record.update(status='PREPARING_R', source_run=source_run.name)
            save(progress, state)
            if prepared.exists() or audit.exists():
                if not prepared.exists() or not audit.exists():
                    raise RuntimeError(f'Partial preparation requires new path: {year}')
                saved_audit = read(audit)
                if saved_audit['status'] != 'PASS':
                    raise RuntimeError('Preparation audit not passed')
                if saved_audit['weights'] != cfg['weights']:
                    raise RuntimeError('Prepared weights differ from audited BCAI weights')
                for info in saved_audit['outputs']:
                    verify(info)
                for info in saved_audit['inputs']:
                    # Source notes are editorial provenance, not numerical data.
                    if info['path'] != cfg.get('source_notes'):
                        verify(info)
            else:
                prep_config = dict(input_csv=rawfiles, years=[year], seasons=cfg['seasons'],
                                   weights=cfg['weights'], weights_source=cfg['weights_source'],
                                   source_notes=cfg['source_notes'], output_rds=rel(prepared),
                                   schedule_venue_policy='legacy_last_schedule_record',
                                   audit_dir=rel(prep / 'audit'))
                config_path = prep / 'config.json'
                if config_path.exists():
                    raise RuntimeError('Partial preparation exists; preserve and inspect it')
                save(config_path, prep_config)
                run_r(args.rscript, 'models/bcap/r/prepare_raw.R', config_path, prep / 'execution.log')
            for model in MODELS:
                alias = f'bcap_{model}_r_history__mlb_{year}__{args.date}'
                done = completed(alias + '__r*')
                if done:
                    run, saved = done[-1]
                    record['models'][model] = dict(status='COMPLETE_EXISTING', run=run.name)
                    save(progress, state)
                    continue
                run = RUNS / (alias + '__r01')
                config_path = bundle / (run.name + '.config.json')
                if run.exists() or config_path.exists():
                    raise RuntimeError(f'Non-complete previous attempt requires review/new run ID: {run.name}')
                model_config = dict(model=model, years=[year], input_rds=rel(prepared),
                                    output_dir=rel(run), seed=20260928 + year,
                                    comparison_family=255,
                                    role='Exploratory within-year refit; not untouched external validation',
                                    comparison_scope='Predeclared conservative family upper bound 255 for 232 reported groups across four modules within this year; not across years',
                                    source_bcai_run=source_run.name)
                save(config_path, model_config)
                frozen = bundle / 'execution_code' / run.name
                frozen.mkdir(parents=True, exist_ok=False)
                for filename in ('run.R', 'engine.R'):
                    shutil.copy2(ROOT / 'models/bcap/r' / filename, frozen / filename)
                record.update(status='FITTING_R', active_model=model)
                record['models'][model] = dict(status='RUNNING', run=run.name)
                save(progress, state)
                print(year, model, 'START', flush=True)
                run_r(args.rscript, str(frozen / 'run.R'), config_path, bundle / (run.name + '.log'))
                manifest = read(run / 'manifest.json')
                if manifest['status'] != 'COMPLETE':
                    raise RuntimeError(f'R did not complete: {run.name}')
                record['models'][model] = dict(status='COMPLETE', run=run.name)
                save(progress, state)
                print(year, model, 'COMPLETE', flush=True)
            record.update(status='COMPLETE', active_model=None)
            save(progress, state)
            renderer = ROOT / 'tools/render_bcap_history.R'
            if renderer.exists():
                env = os.environ.copy()
                for key in ('LANG', 'LC_ALL', 'LC_CTYPE'):
                    env.pop(key, None)
                report = subprocess.run([args.rscript, '--vanilla', str(renderer)], cwd=ROOT,
                                        env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if report.returncode:
                    record['report_warning'] = report.stdout[-2000:] + report.stderr[-2000:]
            save(progress, state)
        state['status'] = 'COMPLETE'
    except BaseException as exc:
        state.update(status='INTERRUPTED' if isinstance(exc, KeyboardInterrupt) else 'FAILED', error=str(exc))
        if state['records']:
            state['records'][-1]['status'] = state['status']
        raise
    finally:
        state['updated_at'] = dt.datetime.now().isoformat()
        save(progress, state)
        lock.close()


if __name__ == '__main__':
    main()
