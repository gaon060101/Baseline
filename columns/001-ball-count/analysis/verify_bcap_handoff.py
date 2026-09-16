"""Audit handoff files only; never train models or fetch data."""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EVIDENCE = HERE / 'handoff_bcap_review_evidence.json'
DOC = HERE / 'handoff_bcap_review.md'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def links():
    found = []
    for target in re.findall(r'\]\(([^)]+)\)', DOC.read_text(encoding='utf-8')):
        if '://' in target:
            continue
        path = (HERE / target.split('#')[0]).resolve()
        if not path.is_file() and path != EVIDENCE:
            raise AssertionError(f'Missing link: {target}')
        if path != EVIDENCE:
            found.append(path)
    return found


def current_summary():
    runs = []
    for path in sorted((HERE / 'runs').glob('*/manifest.json')):
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        runs.append({'run_id': data['run_id'], 'model_id': data['model_id'],
                     'status': data.get('status', 'legacy_no_execution_status'),
                     'model_status': data.get('model_status')})
    diag = HERE / 'runs/bcai_ridge__mlb_2024_2025__20260908__r02/artifacts/all_fit_diagnostics.csv'
    with diag.open(encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    obs = HERE / 'runs/bcai_obs__mlb_2024_2025__20260907__r01/artifacts/advantage_count_results.csv'
    with obs.open(encoding='utf-8-sig', newline='') as f:
        counts = list(csv.DictReader(f))
    assert len(rows) == 207 and all(r['converged'] == 'True' for r in rows)
    assert len(counts) == 12 and len({r['count'] for r in counts}) == 12
    return {'runs': runs, 'bcap_run_count': sum(r['model_id'].startswith('BCAP-') for r in runs),
            'bcap_model_directory_exists': (ROOT / 'models/bcap').exists(),
            'existing_ridge_fit_rows': len(rows), 'existing_ridge_all_converged': True,
            'existing_obs_count_rows': len(counts),
            'existing_obs_baseline_PA': int(next(r['N_PA'] for r in counts if r['count'] == '0-0')),
            'bcap_statistical_checks': 'NOT_RUN'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--create-evidence', action='store_true')
    args = parser.parse_args()
    targets = links()
    if args.create_evidence:
        if EVIDENCE.exists():
            raise FileExistsError('Evidence snapshot already exists; preserve it.')
        paths = set(targets + [DOC, Path(__file__).resolve()])
        paths.update((HERE / 'runs').glob('*/manifest.json'))
        paths.update((ROOT / 'models/bcai/ridge/v0.2.0').glob('*.md'))
        paths.add(ROOT / 'models/bcai/ridge/v0.2.0/structure_validation.json')
        paths.update(HERE / p for p in ['analyze_count_advantage.py', 'verify_count_advantage.py'])
        paths.update(ROOT / 'models/bcai/ridge/v0.2.0' / p for p in
                     ['ridge_v02.py', 'external_validation.py', 'specification.yaml'])
        record = {'created_at_utc': datetime.now(timezone.utc).isoformat(),
                  'scope': 'Handoff integrity and existing artifact summaries; not BCAP model seal, training, causal validation, or full raw-data rehash.',
                  'prompt_original_location': 'C:/Users/백창현/.codex/attachments/1d087f12-54e9-4f25-8892-d703090d8a54/pasted-text.txt',
                  'summary': current_summary(),
                  'files': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': p.stat().st_size,
                             'sha256': sha(p)} for p in sorted(paths)]}
        with EVIDENCE.open('x', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
            f.write('\n')
    saved = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    for entry in saved['files']:
        path = ROOT / entry['path']
        assert path.is_file(), entry['path']
        assert sha(path) == entry['sha256'], f"Hash changed: {entry['path']}"
    assert current_summary() == saved['summary'], 'Inventory/summary changed since handoff'
    result = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'status': 'PASS',
              'evidence_sha256': sha(EVIDENCE), 'checked_files': len(saved['files']),
              'local_document_links': len(targets) + 1, 'summary': saved['summary']}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
