"""Transport an existing, trusted local pickle to R-readable CSV; no analysis."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd

FIELDS = ['game_pk', 'at_bat_number', 'pitch_number', 'game_year',
          'game_date', 'balls', 'strikes', 'events']

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source, target = Path(args.input), Path(args.output)
    meta = target.with_suffix('.provenance.json')
    if target.exists() or meta.exists():
        raise FileExistsError('Transport outputs already exist; use a new path')
    before = sha(source)
    frame = pd.read_pickle(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    frame[FIELDS].to_csv(target, index=False, encoding='utf-8-sig')
    after = sha(source)
    assert before == after, 'Source changed during transport'
    record = dict(role='format transport only; no filtering, sorting, or statistics',
                  input=str(source), input_sha256=before, rows=len(frame),
                  fields=FIELDS, output=str(target), output_sha256=sha(target),
                  python_pandas=pd.__version__)
    meta.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(rows=len(frame), fields=len(FIELDS), source_unchanged=True)))

if __name__ == '__main__':
    main()
