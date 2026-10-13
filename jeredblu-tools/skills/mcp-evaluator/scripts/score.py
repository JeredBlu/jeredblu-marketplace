#!/usr/bin/env python3
"""Validate MCP review judgments and calculate points locally; never contacts a server.
Exit 0 means valid ledger, not a safe target. Exit 2 means invalid input.
"""
import argparse
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
import re
import sys

RUBRIC = Path(__file__).resolve().parent.parent / 'references' / 'rubric-v1.json'
SEVERITIES = ('none', 'low', 'medium', 'high', 'critical')
STATES = ('pass', 'concern', 'fail', 'unknown', 'not_applicable')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def template(rubric):
    return {'rubric_version': rubric['rubric_version'],
            'target': {'identity': 'OWNER/REPO or service URL', 'transport': 'stdio',
                       'review_basis': 'source', 'revision': 'REPLACE_WITH_COMMIT_OR_SNAPSHOT_SHA',
                       'deployment': 'Describe exact launch/package/service version and data scope'},
            'checks': [{'id': c['id'], 'status': 'unknown', 'severity': 'none',
                        'reason': 'Not reviewed yet', 'evidence': []} for c in rubric['checks']]}


def evaluate(ledger, rubric):
    require(isinstance(ledger, dict), 'ledger must be an object')
    require(set(ledger) == {'rubric_version', 'target', 'checks'}, 'unexpected or missing ledger fields')
    require(ledger['rubric_version'] == rubric['rubric_version'], 'rubric version mismatch')
    target = ledger['target']
    require(isinstance(target, dict), 'target must be an object')
    require(set(target) == {'identity', 'transport', 'review_basis', 'revision', 'deployment'}, 'invalid target fields')
    require(nonempty(target['identity']) and nonempty(target['deployment']), 'target identity and deployment required')
    require(target['transport'] in ('stdio', 'local_http', 'remote_http'), 'invalid transport')
    require(target['review_basis'] in ('source', 'hosted_docs'), 'invalid review_basis')
    if target['review_basis'] == 'source':
        require(isinstance(target['revision'], str) and re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', target['revision']),
                'source revision must be a full commit or supplied snapshot SHA')
    else:
        require(target['transport'] == 'remote_http' and nonempty(target['revision']),
                'hosted_docs requires remote_http and dated/versioned documentation snapshot label')
    require(isinstance(ledger['checks'], list), 'checks must be an array')
    specs = {c['id']: c for c in rubric['checks']}
    submitted = {}
    for item in ledger['checks']:
        require(isinstance(item, dict), 'check must be an object')
        require(set(item) == {'id', 'status', 'severity', 'reason', 'evidence'}, 'invalid check fields; weights cannot be overridden')
        ident, status, severity = item['id'], item['status'], item['severity']
        require(isinstance(ident, str) and ident in specs, 'unrecognized check id')
        require(ident not in submitted, 'duplicate check: ' + ident)
        require(status in STATES and severity in SEVERITIES, ident + ': invalid status/severity')
        require(nonempty(item['reason']), ident + ': reason required')
        require(isinstance(item['evidence'], list), ident + ': evidence must be array')
        require(status == 'unknown' or item['evidence'], ident + ': resolved check requires evidence')
        for ev in item['evidence']:
            require(isinstance(ev, dict) and nonempty(ev.get('source')) and nonempty(ev.get('detail')), ident + ': source/detail required')
            if 'line_start' in ev or 'line_end' in ev:
                start, end = ev.get('line_start'), ev.get('line_end', ev.get('line_start'))
                require(type(start) is int and type(end) is int and 1 <= start <= end, ident + ': invalid evidence line range')
        if status in ('pass', 'unknown', 'not_applicable'):
            require(severity == 'none', ident + ': status requires severity none')
        elif status == 'concern':
            require(severity in ('low', 'medium'), ident + ': concern must be low/medium')
        else:
            require(SEVERITIES.index(severity) >= SEVERITIES.index(specs[ident]['fail_min_severity']), ident + ': fail below severity floor')
        if status == 'not_applicable':
            require(ident == 'privacy.hosted' and target['transport'] != 'remote_http',
                    'only hosted-deployment check can be N/A for a local server')
        if target['review_basis'] == 'hosted_docs' and ident in rubric['implementation_checks']:
            require(status in ('unknown', 'fail'), ident + ': docs alone cannot resolve implementation as pass/concern')
        submitted[ident] = item
    rows = []
    for spec in rubric['checks']:
        item = submitted.get(spec['id'], {'id': spec['id'], 'status': 'unknown', 'severity': 'none',
                                         'reason': 'Missing from submitted ledger', 'evidence': []})
        weight = 0 if item['status'] == 'not_applicable' else spec['weight']
        earned = Decimal(weight) * Decimal(str(rubric['status_credit'].get(item['status'], 0)))
        rows.append({**item, 'dimension': spec['dimension'], 'weight': weight, 'earned_points': float(earned)})
    applicable = sum(c['weight'] for c in rows)
    unknown = sum(c['weight'] for c in rows if c['status'] == 'unknown')
    assessed = applicable - unknown
    earned = sum(Decimal(str(c['earned_points'])) for c in rows)
    worst = max((c['severity'] for c in rows), key=SEVERITIES.index)
    cap = rubric['severity_caps'][worst]
    raw = earned * 100 / assessed if assessed else None
    score = min(raw, Decimal(cap)) if assessed else None
    missing_core = [c['id'] for c in rows if c['id'] in rubric['core_checks'] and c['status'] == 'unknown']
    if worst == 'critical': verdict = 'DO NOT USE'
    elif worst == 'high': verdict = 'NOT RECOMMENDED'
    elif not assessed or missing_core: verdict = 'INCOMPLETE'
    elif score < 30: verdict = 'DO NOT USE'
    elif score < 50: verdict = 'NOT RECOMMENDED'
    elif score < 85: verdict = 'USE WITH CAUTION'
    elif unknown: verdict = 'REVIEWED WITH LIMITATIONS'
    else: verdict = 'NO MAJOR RISKS IDENTIFIED'
    def rounded(value):
        return float(value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if value is not None else None
    dimensions = {}
    for dim, label in rubric['dimensions'].items():
        subset = [c for c in rows if c['dimension'] == dim]
        dimensions[dim] = {'label': label, 'earned_points': sum(c['earned_points'] for c in subset),
                           'applicable_points': sum(c['weight'] for c in subset),
                           'assessed_points': sum(c['weight'] for c in subset if c['status'] != 'unknown')}
    return {'rubric_version': rubric['rubric_version'], 'target': target, 'verdict': verdict,
            'score': rounded(score), 'raw_reviewed_score': rounded(raw), 'score_is_provisional': bool(unknown),
            'earned_points': float(earned), 'assessed_points': assessed, 'applicable_points': applicable,
            'unknown_points': unknown, 'coverage_percent': rounded(Decimal(assessed) * 100 / applicable),
            'unresolved_core_checks': missing_core, 'severity_cap': {'severity': worst, 'maximum': cap},
            'status_counts': dict(Counter(c['status'] for c in rows)), 'dimensions': dimensions, 'checks': rows,
            'limitations': ['Heuristic reviewed-evidence score; not probability, certification or runtime test.',
                            'Coverage is weighted checks assessed, not source-code coverage.',
                            'Evidence authenticity and classifications require judgment; calculator only validates structure and arithmetic.',
                            'Reviewed source does not establish deployed service behavior or package equivalence.']}


def markdown(result):
    def cell(value): return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')
    score = 'unavailable' if result['score'] is None else str(result['score']) + '/100'
    lines = ['# ' + result['verdict'], '', 'Reviewed-evidence score: **' + score + '**' +
             (' (provisional; assessed checks only).' if result['score_is_provisional'] else ' (assessed checks).'),
             'Weighted check coverage: ' + str(result['coverage_percent']) + '%; not source-code coverage.',
             'Scope: ' + cell(result['target']),
             f"Calculation: {result['earned_points']} / {result['assessed_points']} assessed points × 100; {result['unknown_points']} unknown points.",
             'Severity cap: ' + cell(result['severity_cap']) + '.',
             'Unresolved core checks: ' + (', '.join(result['unresolved_core_checks']) or 'none') + '.', '',
             '| Dimension | Earned | Assessed | Applicable |', '|---|---:|---:|---:|']
    for d in result['dimensions'].values():
        lines.append('| ' + ' | '.join(cell(d[k]) for k in ('label', 'earned_points', 'assessed_points', 'applicable_points')) + ' |')
    lines += ['', '| Check | Result | Severity | Points | Reason and evidence |', '|---|---|---|---:|---|']
    for c in result['checks']:
        ev = '; '.join(e['source'] + (':' + str(e['line_start']) if 'line_start' in e else '') + ': ' + e['detail'] for e in c['evidence'])
        pts = 'unknown' if c['status'] == 'unknown' else str(c['earned_points']) + '/' + str(c['weight'])
        lines.append('| ' + ' | '.join(map(cell, [c['id'], c['status'], c['severity'], pts, c['reason'] + ' — ' + ev])) + ' |')
    return '\n'.join(lines + ['', *['- ' + s for s in result['limitations']], ''])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', nargs='?')
    parser.add_argument('--template', action='store_true')
    parser.add_argument('--markdown', action='store_true')
    args = parser.parse_args()
    try:
        rubric = load_json(RUBRIC)
        if args.template:
            print(json.dumps(template(rubric), indent=2))
        else:
            require(bool(args.ledger), 'provide ledger or --template')
            result = evaluate(load_json(args.ledger), rubric)
            print(markdown(result) if args.markdown else json.dumps(result, indent=2))
        return 0
    except (ValueError, TypeError, OSError) as exc:
        print('Invalid evaluation: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
