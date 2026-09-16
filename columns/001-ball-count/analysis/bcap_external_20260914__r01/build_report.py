"""Build the prespecified Korean external comparison from completed saved tables.

No estimation, model changes, fitting, new multiplicity selection or data fetching.
Run only after the sealed external analyses finish. Withheld rows remain empty.
"""
from pathlib import Path
import csv
import datetime
import hashlib
import html
import json
import math
import os
import sys

B = Path(__file__).resolve().parent
ROOT = B.parents[3]
AN = B.parent
COUNTS = [f'{b}-{s}' for b in range(4) for s in range(3)]
REGIONS = ['HIGH', 'LOW', 'INSIDE', 'OUTSIDE', 'CENTER']
RN = {'HIGH': '상', 'LOW': '하', 'INSIDE': '좌(몸쪽)', 'OUTSIDE': '우(바깥쪽)', 'CENTER': '가운데(존 안 전체)', 'ALL': '전체'}
MN = {'pitch_sb': '투수 실제 S/B', 'swing': '타자 스윙/테이크', 'pitch': 'FB/NFB', 'pitch_ff': '포심/비포심'}
JN = {'REPRODUCED': '같은 방향 재현', 'OPPOSITE_DIRECTION': '반대 방향', 'UNCERTAIN': '불명확',
      'NO_SUPPORT': '비교 자료 부족', 'WITHHELD_MEASUREMENT': '측정 정합성 미확보로 보류'}
DEFAULT_DEV = {
    'pitch_sb': 'columns/001-ball-count/analysis/runs/bcap_pitch_sb__mlb_2024_2025__20260912__r01/artifacts/count_values.csv',
    'swing': 'columns/001-ball-count/analysis/bcap_v2_development_20260912__r01/batter_five_regions.csv',
    'pitch_compare': 'columns/001-ball-count/analysis/runs/bcap_pitch_compare__mlb_2024_2025__20260912__r01/artifacts/primary_values.csv',
}
INPUTS = {}


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def metadata(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': digest, 'bytes': path.stat().st_size}


def remember(path):
    path = Path(path).resolve()
    INPUTS[str(path)] = metadata(path)
    return path


def read_json(path):
    return json.loads(remember(path).read_text(encoding='utf-8-sig'))


def read_csv(path):
    with remember(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def write_csv(path, rows):
    fields = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def number(value):
    try:
        out = float(value)
        return out if math.isfinite(out) else None
    except (TypeError, ValueError):
        return None


def truth(value):
    return value is True or str(value).lower() == 'true'


def fmt(value, digits=3, signed=False):
    value = number(value)
    return '—' if value is None else format(value, ('+' if signed else '') + f'.{digits}f')


def integer(value):
    value = number(value)
    return '—' if value is None else f'{value:,.0f}'


def percent(value):
    value = number(value)
    return '—' if value is None else f'{100 * value:.1f}%'


def sign(value):
    value = number(value)
    return 0 if value is None or value == 0 else 1 if value > 0 else -1


def interval(row, prefix=''):
    low = row.get(prefix + 'adjusted95_low')
    high = row.get(prefix + 'adjusted95_high')
    return f'[{fmt(low, signed=True)}, {fmt(high, signed=True)}]'


def excludes_zero(low, high):
    low, high = number(low), number(high)
    return low is not None and high is not None and (low > 0 or high < 0)


def same_target_interval(row):
    low, high, direction = number(row.get('adjusted95_low')), number(row.get('adjusted95_high')), row['target_sign']
    return low is not None and high is not None and (low > 0 if direction > 0 else high < 0)


def key(row):
    return row['model'], row['count'], row['region'], row['population']


def normalize_dev(row, model):
    result = dict(row)
    result.update(model=model, region=row.get('region', 'ALL'), population=row.get('population', 'own'))
    result['adjusted95_low'] = row.get('adjusted95_low', row.get('family95_low'))
    result['adjusted95_high'] = row.get('adjusted95_high', row.get('family95_high'))
    result['family'] = 255 if model in ['pitch', 'pitch_ff'] else 219
    if 'gcomp_delta' not in result:
        result['gcomp_delta'] = number(row['gcomp1']) - number(row['gcomp0'])
    result['established'] = truth(result.get('support_gate')) and excludes_zero(
        result['adjusted95_low'], result['adjusted95_high'])
    if model in ['pitch', 'pitch_ff']:
        result['established'] = row.get('category') == 'CONSISTENT_DEVELOPMENT'
    return result


def classify(row):
    if row['measurement_hold']:
        return 'WITHHELD_MEASUREMENT'
    if not truth(row.get('support_gate')):
        return 'NO_SUPPORT'
    direction = row['target_sign']
    if same_target_interval(row) and sign(row['delta']) == direction:
        return 'REPRODUCED'
    if excludes_zero(row.get('adjusted95_low'), row.get('adjusted95_high')) and sign(row['delta']) == -direction:
        return 'OPPOSITE_DIRECTION'
    return 'UNCERTAIN'


def build_comparison(plan):
    paths = dict(DEFAULT_DEV)
    paths.update(plan.get('development_tables', {}))
    devrows = []
    devrows += [normalize_dev(x, 'pitch_sb') for x in read_csv(ROOT / paths['pitch_sb'])]
    devrows += [normalize_dev(x, 'swing') for x in read_csv(ROOT / paths['swing'])]
    for row in read_csv(ROOT / paths['pitch_compare']):
        devrows.append(normalize_dev(row, 'pitch' if row['scheme'] == 'FB' else 'pitch_ff'))
    assert len(devrows) == 120 and len({key(x) for x in devrows}) == 120
    output = []
    manifests = []
    for year in [2023, 2026]:
        external = {}
        hold_models = set()
        for model in ['pitch_sb', 'swing', 'pitch', 'pitch_ff']:
            task = plan['runs'][str(year)][model]
            run = AN / 'runs' / task['run_id']
            manifest = read_json(run / 'manifest.json')
            manifests.append((year, model, run, manifest))
            assert manifest['status'] in ['COMPLETE', 'WITHHELD_MEASUREMENT'], str(run)
            if manifest['status'] == 'WITHHELD_MEASUREMENT':
                hold_models.add(model)
                continue
            if model in ['pitch_sb', 'swing']:
                rows = read_csv(run / 'artifacts/values.csv')
                assert len(rows) == (12 if model == 'pitch_sb' else 60)
                for row in rows:
                    external[key(row)] = row
        run = AN / 'runs' / plan['comparison_runs'][str(year)]
        manifest = read_json(run / 'manifest.json')
        assert manifest['status'] == 'COMPLETE'
        manifests.append((year, 'pitch_compare', run, manifest))
        rows = read_csv(run / 'artifacts/values.csv')
        assert len(rows) == 48
        external.update({key(x): x for x in rows})
        for dev in devrows:
            model = dev['model']
            held = model in hold_models
            row = dict(year=year, model=model, count=dev['count'], region=dev['region'], population=dev['population'],
                       measurement_hold=held, is_primary=model == 'pitch_sb' and dev['count'] in ['0-2', '1-2'])
            if not held:
                row.update(external[key(dev)])
                row['year'] = year
            row['family'] = 4 if row['is_primary'] else 236
            row['target_sign'] = 1 if model == 'pitch_sb' and row['is_primary'] else (
                (1 if row['region'] == 'CENTER' else -1) if model == 'swing' else sign(dev['delta']))
            for name, value in dev.items():
                row['dev_' + name] = value
            row['development_established'] = bool(dev['established'])
            row['development_status'] = ('개발에서 방향 근거 있음' if dev['established'] else
                                         '개발에서 확정하지 못한 비교; 외부 방향을 탐색적으로 대조')
            row['judgment'] = classify(row)
            row['judgment_ko'] = JN[row['judgment']]
            row['same_point_direction'] = '' if held else sign(row.get('delta')) == row['target_sign']
            row['adjusted_interval_excludes_zero'] = '' if held else excludes_zero(row.get('adjusted95_low'), row.get('adjusted95_high'))
            row['interval_supports_001_in_target_direction'] = ''
            if not held:
                lo, hi = number(row.get('adjusted95_low')), number(row.get('adjusted95_high'))
                if lo is not None and hi is not None:
                    row['interval_supports_001_in_target_direction'] = truth(row.get('support_gate')) and (
                        lo >= .01 if row['target_sign'] > 0 else hi <= -.01)
            output.append(row)
    assert len(output) == 240 and sum(x['is_primary'] for x in output) == 4
    assert len({(x['year'], key(x)) for x in output}) == 240
    for row in output:
        if row['measurement_hold']:
            assert all(row.get(x) in [None, ''] for x in ['delta', 'Q0', 'Q1', 'n', 'ESS0', 'ESS1', 'adjusted95_low', 'adjusted95_high'])
    return output, manifests


def display_status(row):
    text = row['judgment_ko']
    if row['judgment'] == 'REPRODUCED' and not row['development_established']:
        text = '외부 같은 방향 · 개발 미확정'
    return text


def result_text(row, compact=False):
    if row['measurement_hold']:
        return '측정 정합성 미확보로 보류 — 재현 실패·자료 부족 판정 아님'
    support = f"n {integer(row.get('n'))}/{integer(row.get('n_all'))} · 포함률 {percent(row.get('coverage'))} · 행동 수 {integer(row.get('rows0'))}/{integer(row.get('rows1'))} · ESS {integer(row.get('ESS0'))}/{integer(row.get('ESS1'))}"
    if row['judgment'] == 'NO_SUPPORT':
        return f"비교 자료 부족 · Δ/구간 판정 보류; {support}; {row.get('support_reasons', '')}"
    value = f"Δ {fmt(row['delta'], signed=True)} W {interval(row)} · {display_status(row)}"
    return value + ('; ' + support if not compact else '')


def dev_text(row):
    support = f"n {integer(row.get('dev_n'))}/{integer(row.get('dev_n_all'))} · 포함률 {percent(row.get('dev_coverage'))} · 행동 수 {integer(row.get('dev_rows0'))}/{integer(row.get('dev_rows1'))} · ESS {integer(row.get('dev_ESS0'))}/{integer(row.get('dev_ESS1'))}"
    if not truth(row.get('dev_support_gate')):
        return '비교 자료 부족 · Δ/구간 판정 보류; ' + support
    status = row.get('dev_judgment', row.get('dev_evidence', ''))
    return f"Δ {fmt(row['dev_delta'], signed=True)} W {interval(row, 'dev_')} · {status}; {support}"


def lookup(rows, year, model, count, region='ALL', population='own'):
    return next(x for x in rows if x['year'] == year and key(x) == (model, count, region, population))


def main_sentences(rows):
    sb_parts = []
    for count in ['0-2', '1-2']:
        r = lookup(rows, 2023, 'pitch_sb', count)
        if r['judgment'] == 'REPRODUCED':
            practical = ('구간 전체가 0.01 W 이상이었다' if r['interval_supports_001_in_target_direction'] else
                         '구간 전체가 0.01 W 이상인 차이까지 뒷받침하지는 못했다')
            sb_parts.append(f"{count}는 2023에서도 존 밖 B 쪽의 보정 평균 공격가치가 낮았다"
                            f"(S−B {fmt(r['delta'])} W, 주요 4개 비교 보정 구간 {interval(r)} W). {practical}.")
        elif r['judgment'] == 'OPPOSITE_DIRECTION':
            sb_parts.append(f"{count}는 2023에서 개발과 반대인 존 안 S 쪽으로 나타났다"
                            f"(S−B {fmt(r['delta'], signed=True)} W, 보정 구간 {interval(r)} W).")
        elif r['judgment'] == 'NO_SUPPORT':
            sb_parts.append(f"{count}는 2023 비교 표본이 지원 기준에 미달해 재현 여부를 판단하지 않았다.")
        else:
            same = '같은 방향의 점추정이었지만' if r.get('same_point_direction') else '개발의 방향을 유지하지 못했고'
            sb_parts.append(f"{count}는 2023에서 {same} 차이를 충분히 구분하지 못했다"
                            f"(S−B {fmt(r.get('delta'), signed=True)} W, 보정 구간 {interval(r)} W).")
    sb = '2024–2025 개발자료의 투수 위치 패턴을 기존 2023 자료에서 점검했다. ' + ' '.join(sb_parts)
    sb += ' 2026 S/B는 좌표 기준면·존 정의의 정합성을 확보하지 못해 측정 보류했다.'
    inside = [x for x in rows if x['year'] == 2023 and x['model'] == 'swing' and x['region'] == 'CENTER']
    outside = [x for x in rows if x['year'] == 2023 and x['model'] == 'swing' and x['region'] != 'CENTER']
    def tally(group, predicate):
        return sum(predicate(x) for x in group)
    inside_supported = [x for x in inside if x['judgment'] != 'NO_SUPPORT']
    outside_supported = [x for x in outside if x['judgment'] != 'NO_SUPPORT']
    inside_uncertain = [x['count'] for x in inside_supported if x['judgment'] == 'UNCERTAIN']
    sw = (f"타자의 2023 위치별 비교에서는 존 안 12카운트 중 {len(inside_supported)}개가 지원 기준을 통과했고, "
          f"그중 {tally(inside_supported, lambda x: number(x['delta']) > 0)}개가 스윙 쪽 점추정이었다"
          f"(보정 구간도 같은 방향인 셀 {tally(inside_supported, lambda x: x['judgment'] == 'REPRODUCED')}개). "
          f"존 밖 48개 보고 셀 중 {len(outside_supported)}개가 지원 기준을 통과했고, "
          f"그중 {tally(outside_supported, lambda x: number(x['delta']) < 0)}개가 테이크 쪽 점추정이었다"
          f"(보정 구간도 같은 방향인 셀 {tally(outside_supported, lambda x: x['judgment'] == 'REPRODUCED')}개). " +
          ('존 안에서 차이가 불명확한 카운트는 ' + '·'.join(inside_uncertain) + '이다. ' if inside_uncertain else '') +
          '3-0은 개발에서도 불명확·자료 부족이 있던 비교이므로 확정 가설의 성공 여부로 세지 않는다. '
          '모서리는 두 보고 구역에 겹치며, 카운트 평균을 모든 위치의 행동 지시로 적용할 수 없다. 2026 타자 분석은 측정 보류다.')
    special = []
    for year in [2023, 2026]:
        r = lookup(rows, year, 'pitch_ff', '3-2', population='common')
        special.append(f"{year}의 3-2 포심/비포심 공통 표본 비교는 {display_status(r)}"
                       + (f"(FF−비포심 {fmt(r.get('delta'), signed=True)} W)" if r['judgment'] != 'NO_SUPPORT' else ''))
    all_pitch = [x for x in rows if x['model'] in ['pitch', 'pitch_ff']]
    uncertain = sum(x['judgment'] == 'UNCERTAIN' for x in all_pitch)
    unsupported = sum(x['judgment'] == 'NO_SUPPORT' for x in all_pitch)
    pitch = (f"두 구종 분류의 외부 자체·공통 표본 비교 총 96개 중 {uncertain}개는 차이가 불명확했고 "
             f"{unsupported}개는 비교 자료가 부족했다. " + '; '.join(special) + '. '
             'FB/NFB 3-0의 남은 차이와 표본·보정 의존성, 3-1의 추정 방식 민감성은 별도 표에 보존했다. '
             '이 결과로 모든 타석의 구종 우열이나 구종 간 동등성을 단정하지 않는다.')
    caveat = ('이 결론은 기존 자료에 고정 학습 절차를 적용한 관찰 패턴의 재현이다. W는 최종 타석 결과의 시즌별 가중 공격가치로, '
              '확률·득점·한 타석의 투구별 차이 합계가 아니다. 경기 군집 구간은 고정 점수의 불확실성만 반영하며 '
              '전체 재학습과 경기 간 선수 의존성, 선수 보정 후 남은 미측정 차이를 해결한 것은 아니다.')
    return sb, sw, pitch, caveat


def markdown_table(headers, rows):
    escape = lambda v: str(v).replace('|', '/').replace('\n', ' ')
    return '| ' + ' | '.join(headers) + ' |\n|' + '|'.join([' --- '] * len(headers)) + '|\n' + '\n'.join(
        '| ' + ' | '.join(escape(v) for v in row) + ' |' for row in rows)


def html_table(headers, rows, table_id=''):
    return (f'<div class="table-wrap" id="{html.escape(table_id)}"><table><thead><tr>' +
            ''.join('<th>' + html.escape(str(x)) + '</th>' for x in headers) + '</tr></thead><tbody>' +
            ''.join('<tr>' + ''.join('<td>' + html.escape(str(cell)).replace('; ', '<br>') + '</td>' for cell in row) + '</tr>' for row in rows) +
            '</tbody></table></div>')


def main():
    outputs = ['comparison.csv', 'primary_SB.csv', 'report.html', 'report.md', 'column_conclusion.md',
               'reproduction.md', 'report_manifest.json', 'report_access_log.json']
    assert all(not (B / x).exists() for x in outputs), 'Report outputs already exist; preserve the completed report.'
    plan = read_json(B / 'plan.json')
    seal = read_json(B / 'plan_seal.json')
    for record in seal['files']:
        assert metadata(ROOT / record['path'])['sha256'] == record['sha256'], record['path']
    write_json(B / 'report_access_log.json', dict(at_utc=now(), event='first_report_aggregate_read',
               plan_sealed_at_utc=seal['sealed_at_utc'], scope='Completed external aggregate tables; no fitting'))
    rows, manifests = build_comparison(plan)
    write_csv(B / 'comparison.csv', rows)
    primary = [x for x in rows if x['is_primary']]
    write_csv(B / 'primary_SB.csv', primary)
    sb, sw, pitch, caveat = main_sentences(rows)
    paragraphs = [sb, sw, pitch, caveat]
    md = ['# BCAP 외부 패턴 재현: 개발 / 2023 / 2026',
          '2024–2025에서 발견한 패턴을 기존 2023·2026 자료로 점검했다. 모델 상태는 EXPERIMENTAL이다. '
          '2023은 과거 연도 재현이며, 2026은 9월 7일까지의 개발 이후 자료다. 두 자료는 과거 BCAI/Ridge와 BCAP V1에 사용했다.',
          '## 핵심 결론'] + paragraphs[:3]
    body = ['<header><p class="eyebrow">BASELINE · 001 BALL COUNT</p><h1>BCAP, 다른 연도에서도 같은 패턴인가</h1>'
            '<p>2024–2025 개발 / 2023 과거 연도 재현 / 2026-09-07까지 개발 이후 자료</p>'
            '<span class="badge">EXPERIMENTAL · 관찰 패턴 재현</span></header>',
            '<nav><a href="#summary">핵심 결론</a><a href="#sb">투수 S/B</a><a href="#swing">타자 5구역</a>'
            '<a href="#pitch">구종 계열</a><a href="#method">범위와 확인</a></nav>',
            '<section id="summary"><h2>칼럼에 남길 결론</h2>' + ''.join('<p>' + html.escape(x) + '</p>' for x in paragraphs[:3]) + '</section>']
    notes = ('Δ는 항상 행동1−행동0이다. S/B는 S−B이므로 양수일 때 B 쪽의 공격가치가 낮다. '
             '타자는 Swing−Take이므로 양수는 Swing 쪽, 음수는 Take 쪽이다. '
             '구종은 FB−NFB 또는 FF−비포심이며 양수는 두 번째 계열 쪽 공격가치가 낮다는 뜻이다. '
             '모든 가치 비교의 단위는 선택된 현재 의사결정 행당 W이며, 각 표의 ESS와 행동 수는 행동0/행동1 순서다.')
    md += ['## 표를 읽는 방법', notes,
           '개발 구간은 기존 219개(S/B·타자), 255개(구종 분류) 보정을 유지한다. '
           '외부 주요 S/B는 0-2·1-2×두 연도=4개, 보조 결과는 나머지 236개를 고정한 Bonferroni 보정이다. '
           '2026 측정 보류가 생겨도 비교 가족을 줄이지 않는다. 같은 방향 재현은 지원 기준 통과와 보정 구간의 해당 방향 0 배제를 뜻한다. '
           '작은 차이·동등성을 자동으로 뜻하지 않으며 0.01 W 참고선은 별도로 확인한다.']
    body.append('<section><h2>표를 읽는 방법</h2><p>' + html.escape(notes) + '</p><p>' + html.escape(md[-1]) + '</p></section>')
    primary_rows = []
    for r in primary:
        primary_rows.append([str(r['year']), r['count'], result_text(r),
            '—' if r['measurement_hold'] or r['judgment'] == 'NO_SUPPORT' else ('예' if r['same_point_direction'] else '아니오'),
            '—' if r['measurement_hold'] or r['judgment'] == 'NO_SUPPORT' else ('예' if r['adjusted_interval_excludes_zero'] else '아니오'),
            '—' if r['measurement_hold'] or r['judgment'] == 'NO_SUPPORT' else ('예' if r['interval_supports_001_in_target_direction'] else '확보하지 못함')])
    phead = ['연도', '카운트', '외부 보정 차이·지원 표본', '같은 점방향', '구간 0 배제', '구간 전체 ≥0.01 W']
    md += ['## 주 검증: 0-2·1-2의 존 밖 투구', markdown_table(phead, primary_rows)]
    body.append('<section id="sb"><h2>주 검증 · 0-2와 1-2의 존 밖 투구</h2>' + html_table(phead, primary_rows) + '</section>')

    def three_year_table(model, region='ALL', population='own'):
        table = []
        for count in COUNTS:
            a = lookup(rows, 2023, model, count, region, population)
            z = lookup(rows, 2026, model, count, region, population)
            table.append([count, dev_text(a), result_text(a), result_text(z)])
        return table

    head = ['카운트', '2024–2025 개발 · Δ [기존 보정 구간]', '2023 · Δ [외부 보정 구간]', '2026 · Δ [외부 보정 구간]']
    table = three_year_table('pitch_sb')
    md += ['## S/B 전체 12카운트', '0-2·1-2만 주 가설이다. 나머지 10카운트는 보조 비교이며, 0-1의 불명확을 재현해야 한다고 요구하지 않았다.', markdown_table(head, table)]
    body.append('<section><h2>S/B · 전체 12카운트</h2><p>0-2·1-2만 주 가설이며 나머지는 보조 비교다. S는 실제 공 중심의 존 안, B는 존 밖이다. 심판 판정·투수 의도가 아니다.</p>' + html_table(head, table) + '</section>')
    region_note = ('가운데는 존 안 전체다. 상·하·좌(몸쪽)·우(바깥쪽)의 모서리는 두 보고 구역에 포함되지만 학습은 공당 한 행이다. '
                   '투구 위치 비율의 분모는 해당 카운트의 적격 투구, 실제 스윙률의 분모는 해당 구역 적격 투구, '
                   '가치·ESS의 분모는 해당 구역의 비교 가능 표본이다. 위치·움직임은 타자의 실시간 지각을 보장하지 않는 사후 측정값이다.')
    md += ['## 타자 12카운트×5구역', region_note]
    body.append('<section id="swing"><h2>타자 · 5구역</h2><p>' + html.escape(region_note) + '</p></section>')
    for region in REGIONS:
        table = three_year_table('swing', region)
        for cells, count in zip(table, COUNTS):
            r = lookup(rows, 2023, 'swing', count, region)
            cells[1] += f"; 위치 비율 {percent(r.get('dev_fraction_of_count_all'))} / 스윙률 {percent(r.get('dev_action1_rate_all'))}"
            cells[2] += f"; 위치 비율 {percent(r.get('fraction_of_count_all'))} / 스윙률 {percent(r.get('action1_rate_all'))}"
        md += ['### ' + RN[region], markdown_table(head, table)]
        body.append('<section><h3>' + RN[region] + '</h3>' + html_table(head, table, 'region-' + region) + '</section>')
    pitch_note = ('FB=FF·SI·FC이며 NFB는 기존 닫힌 나머지 유효 구종이다. FF/비포심은 포심 FF만 첫 행동이며 '
                  'SI·FC와 나머지 유효 구종이 비포심이다. 두 분류를 같은 행동 비교로 읽거나 FF/비포심을 패스트볼/변화구로 부르지 않는다. '
                  '자체 표본은 각 모형의 지원 표본, 공통 표본은 같은 연도에서 두 분류가 모두 지원되는 행이다. '
                  '공통 표본도 행동 정의의 차이를 없애지는 않는다.')
    md += ['## 구종 계열: 자체·공통 표본', pitch_note]
    body.append('<section id="pitch"><h2>구종 계열 · 자체와 공통 표본</h2><p>' + html.escape(pitch_note) + '</p></section>')
    for population in ['own', 'common']:
        for model in ['pitch', 'pitch_ff']:
            title = MN[model] + ' · ' + ('자체 지원 표본' if population == 'own' else '공통 지원 표본')
            table = three_year_table(model, population=population)
            md += ['### ' + title, markdown_table(head, table)]
            body.append('<section><h3>' + title + '</h3>' + html_table(head, table) + '</section>')
    sensitivity = []
    for year in [2023, 2026]:
        for count in ['3-0', '3-1']:
            for population in ['own', 'common']:
                r = lookup(rows, year, 'pitch', count, population=population)
                sensitivity.append([year, count, '자체' if population == 'own' else '공통', fmt(r.get('naive_delta'), signed=True),
                    fmt(r.get('gcomp_delta'), signed=True), fmt(r.get('delta'), signed=True),
                    f"{integer(r.get('rows0'))}/{integer(r.get('rows1'))}",
                    f"{integer(r.get('ESS0'))}/{integer(r.get('ESS1'))}", display_status(r)])
    sh = ['연도', '카운트', '표본', '단순 평균 Δ', '결과모형 Δ', 'AIPW Δ', '행동 수 NFB/FB', 'ESS NFB/FB', '판정']
    sensitive_note = ('위 세 추정치는 같은 비교 표본을 사용한다. 표본 부족인 행의 수치는 검토용 계산값이며 행동 방향의 근거로 사용하지 않는다. '
                      '개발 FB/NFB 3-0의 통합 차이는 남았지만 일부 분할의 NFB ESS가 부족했고, 단순 평균과 보정 후 방향이 달랐다. '
                      '3-1은 개발 결과모형과 AIPW의 부호가 달랐다. 외부 분할별 값은 각 비교 실행의 fold_values.csv에 보존하며 '
                      '명목 구간을 추가 주요 검정으로 사용하지 않는다.')
    md += ['## FB/NFB의 표본·보정 민감성', sensitive_note, markdown_table(sh, sensitivity)]
    body.append('<section><h2>FB/NFB · 표본과 보정 민감성</h2><p>' + html.escape(sensitive_note) + '</p>' + html_table(sh, sensitivity) + '</section>')
    method = ('개발에는 최종 전체 재적합 모델이나 학습된 정책이 없다. 이번에는 개발에서 고정한 알고리즘과 규제값으로 '
              '외부 각 연도 안의 경기를 세 분할해 결과·선택확률 보정 모형을 한 번씩 적합했다. '
              '따라서 고정 학습 절차를 통한 외부 패턴 재현이며 완전히 고정된 단일 예측 모델의 시험이나 정책가치 평가가 아니다. '
              '훈련 내부 범주 사전·Platt 보정·선수 축소를 유지했고, 외부 결과에 맞춘 튜닝은 하지 않았다. '
              'SB 규제는 p/m0/m1=1000, 나머지 세 모델은 100/1000/1000이다. '
              '2023 W는 2023 상수, 2026 W는 2025 상수를 고정했다. 2024·2025도 각 시즌 상수를 사용하므로 '
              '같은 정의의 W라도 완전히 같은 가중 척도는 아니며 연도별 차이 크기의 직접 비교에는 한계가 있다.')
    support_note = ('행 지원은 선택확률 0.05~0.95, 훈련 안 해당 선수의 양 행동 각 30행 이상이며 타자는 측정 지원도 필요하다. '
                    '집단 지원은 비교 행 500 이상, 양 행동 ESS 200 이상·경기 100 이상, 포함률 50% 이상, '
                    '각 행동 역확률 가중치의 최대 한 경기 집중도 5% 이하다. '
                    '외부 훈련에서 미관측인 범주 효과는 중심화 블록의 0 기여이며, 미관측 선수를 임의로 지원 처리하지 않는다. '
                    '개발에서 본 선수인지 여부와 해당 외부 훈련 분할에서 본 선수인지 여부는 서로 다른 진단이다.')
    completed = [x for x in manifests if x[3]['status'] == 'COMPLETE' and x[1] != 'pitch_compare']
    diagnostic_rows = []
    for year, model, run, manifest in completed:
        checks = read_json(run / 'artifacts/basic_checks.json')
        metrics = read_json(run / 'artifacts/metrics.json')
        known = read_csv(run / 'artifacts/known_unseen.csv')
        for record in known:
            diagnostic_rows.append([year, MN[model], record['group'], integer(record['n']), integer(record['support']),
                                    fmt(record['MSE'], 6), fmt(record['Brier'], 6)])
        assert checks['status'] == 'PASS' and metrics['all_fit_converged'] is True
    kh = ['연도', '모델', '집단', '평가 행', '지원 행', '결과 MSE', '선택확률 Brier']
    known_note = ('아래 값은 외부 자체 OOF 보정 모형의 진단이며 저장된 개발 모형의 외부 예측 성능이 아니다. '
                  'known_dev_both는 두 선수 모두 개발에 등장, unseen_dev_any는 둘 중 하나 이상 개발에 미등장, '
                  'unknown_external_nuisance_any는 현재 외부 훈련 분할에서 하나 이상 미관측이다. 집단은 서로 겹칠 수 있다. '
                  '완전히 고정된 개발 단일 예측 모델의 시험은 이번에 수행하지 않았다.')
    md += ['## 수행 범위와 기본 확인', method, support_note, caveat, known_note, markdown_table(kh, diagnostic_rows)]
    body.append('<section id="method"><h2>수행 범위와 기본 확인</h2>' + ''.join('<p>' + html.escape(x) + '</p>' for x in [method, support_note, caveat, known_note]) + html_table(kh, diagnostic_rows) + '</section>')
    paths = [('plan.json', '결과 전 검증 계획'), ('plan_seal.json', '시각·해시 봉인'), ('comparison.csv', '240개 개발/외부 비교'),
             ('primary_SB.csv', '주요 S/B 4개 비교'), ('column_conclusion.md', '칼럼용 결론'), ('reproduction.md', '재현 안내'),
             ('measurement_review.json', '2026 측정 판단')]
    md += ['## 근거 파일', '\n'.join(f'- [{label}]({path})' for path, label in paths)]
    links = '<ul>' + ''.join(f'<li><a href="{html.escape(path)}">{html.escape(label)}</a></li>' for path, label in paths) + '</ul>'
    for year, model, run, manifest in manifests:
        relative = Path(os.path.relpath(run / 'manifest.json', B)).as_posix()
        md.append(f'- [{year} {MN.get(model, "구종 자체·공통 집계")} 실행]({relative}) — {manifest["status"]}')
        links += f'<p><a href="{html.escape(relative)}">{year} {html.escape(MN.get(model, "구종 자체·공통 집계"))} 실행</a> · {html.escape(manifest["status"])}</p>'
    body.append('<section><h2>실행과 근거 파일</h2>' + links + '<p>각 실행의 propensity.csv·calibration.csv·support_exclusions.csv·fold_records.json·fit_diagnostics.csv와 저장 예측·점수를 함께 보존했다. 재학습 불확실성·새 seed·신규 수집·KBO·순차 정책은 수행하지 않았다.</p></section>')
    css = '''body{margin:0;background:#f4f6f8;color:#243445;font:16px/1.75 "Malgun Gothic",sans-serif}main{max-width:1440px;margin:auto;padding:36px 28px 70px}header{background:#142d40;color:white;padding:38px;border-radius:16px}h1{font-size:34px;line-height:1.35;margin:8px 0 14px}h2{font-size:25px;color:#123a4b}h3{font-size:21px}.eyebrow{font-size:12px;letter-spacing:2px;color:#b6d5dc}.badge{display:inline-block;border:1px solid #8cc8cb;border-radius:20px;padding:4px 14px;font-size:13px}nav{display:flex;gap:22px;flex-wrap:wrap;padding:18px 0}a{color:#006774;text-decoration-thickness:1px;text-underline-offset:3px}section{background:white;border:1px solid #e0e6eb;border-radius:12px;padding:25px;margin:20px 0}p{max-width:1180px}.table-wrap{overflow:auto}table{border-collapse:collapse;min-width:100%;font-size:13px;line-height:1.65}th,td{text-align:left;vertical-align:top;padding:13px;border-bottom:1px solid #dfe7ec}th{background:#edf3f5;color:#163846;position:sticky;top:0}td:first-child{font-weight:700;white-space:nowrap}tr:nth-child(even){background:#f8fafb}td:not(:first-child){min-width:170px}footer{color:#637382;font-size:13px}@media(max-width:700px){main{padding:15px}header{padding:23px}h1{font-size:27px}section{padding:17px}}'''
    document = '<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Baseline BCAP 외부 패턴 재현</title><style>' + css + '</style><body><main>' + ''.join(body) + '<footer>기존 결과와 원본은 보존했다. 이 보고서는 외부 결과에 맞춰 모델을 바꾸는 후속 탐색 없이 요청한 비교를 마무리한다.</footer></main></body></html>'
    (B / 'report.html').write_text(document, encoding='utf-8')
    (B / 'report.md').write_text('\n\n'.join(md) + '\n', encoding='utf-8')
    (B / 'column_conclusion.md').write_text('# 칼럼에 사용할 최종 결론\n\n' + '\n\n'.join(paragraphs) + '\n', encoding='utf-8')
    reproduce = ('# 재현 안내\n\n기존 실행 ID·완료 결과를 덮어쓰지 않는다. 아래는 이번 실제 실행의 명령 구조이며, '
                 '다시 계산하려면 새 bundle·새 출력 경로·새 실행 ID와 새 봉인이 필요하다.\n\n'
                 f'프로젝트: `{ROOT.as_posix()}`\n\n'
                 '1. `plan.json`과 `plan_seal.json`의 입력·설정·코드 SHA256을 확인한다.\n'
                 '2. `prepare_external.py --year 2023`, `--year 2026`으로 기존 V1 정제본을 새 경로에 준비한다.\n'
                 '3. 각 연도에 `run_external.py --year YEAR --model MODEL`을 실행한다. MODEL은 pitch_sb, swing, pitch, pitch_ff이다. '
                 '2026 pitch_sb·swing은 적합 없이 측정 보류 manifest를 남긴다.\n'
                 '4. `run_external.py --year YEAR --model compare`로 구종 자체·공통 표본을 재집계한다.\n'
                 '5. `build_report.py`는 완료 CSV·manifest만 읽어 이 보고서를 만든다. 기존 산출물이 있으면 중단한다.\n\n'
                 '실제 Python 경로·명령·시각·환경은 각 실행 manifest의 command/environment에 있다. '
                 '보고서 비교표는 comparison.csv 240행, 주요 S/B는 primary_SB.csv 4행이다. '
                 '값·표본·구간·지원 판정은 원 CSV와 연결되며, 측정 보류 행의 외부 값은 비워 둔다.\n')
    (B / 'reproduction.md').write_text(reproduce, encoding='utf-8')
    write_json(B / 'report_manifest.json', dict(status='COMPLETE', at_utc=now(), purpose='Prespecified saved-table external pattern comparison; no estimation',
               inputs=list(INPUTS.values()), code=metadata(__file__), rows=dict(comparison=240, primary_SB=4),
               measurement_rows_blank=sum(x['measurement_hold'] for x in rows),
               outputs=[metadata(B / name) for name in outputs if name != 'report_manifest.json']))
    print(json.dumps(dict(status='COMPLETE', comparison_rows=240, primary_rows=4, report=str(B / 'report.html')), ensure_ascii=False))


if __name__ == '__main__':
    main()
