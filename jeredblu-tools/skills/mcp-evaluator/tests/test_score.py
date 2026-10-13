"""Local behavior tests; no network, package install, MCP calls or target execution."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('mcp_score', ROOT / 'scripts/score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)
RUBRIC = score.load_json(score.RUBRIC)


def ledger(transport='stdio'):
    obj = score.template(RUBRIC)
    obj['target'].update(identity='fixture/local-reader', revision='a'*40, transport=transport,
                         deployment='Static source fixture, user-selected data directory')
    return obj


def resolve(obj, ident, status='pass', severity='none'):
    item = next(c for c in obj['checks'] if c['id'] == ident)
    item.update(status=status, severity=severity, reason='Fixture reviewed boundary',
                evidence=[{'source': 'fixture.py', 'line_start': 1, 'line_end': 5,
                           'detail': 'Controlled fixture evidence, not a real security finding'}])
    return item


def complete(transport='stdio'):
    obj = ledger(transport)
    for check in obj['checks']:
        resolve(obj, check['id'])
    if transport != 'remote_http': resolve(obj, 'privacy.hosted', 'not_applicable')
    return obj


class ScoreTests(unittest.TestCase):
    def evaluate(self, obj): return score.evaluate(obj, RUBRIC)

    def test_weights_total_100(self):
        self.assertEqual(sum(c['weight'] for c in RUBRIC['checks']), 100)
        self.assertEqual(len({c['id'] for c in RUBRIC['checks']}), 14)

    def test_all_unknown(self):
        r = self.evaluate(ledger())
        self.assertIsNone(r['score'])
        self.assertEqual(r['coverage_percent'], 0)
        self.assertEqual(r['verdict'], 'INCOMPLETE')

    def test_all_pass_local(self):
        r = self.evaluate(complete())
        self.assertEqual((r['score'], r['coverage_percent'], r['applicable_points']), (100, 100, 94))
        self.assertEqual(r['verdict'], 'NO MAJOR RISKS IDENTIFIED')

    def test_all_pass_remote(self):
        r = self.evaluate(complete('remote_http'))
        self.assertEqual(r['applicable_points'], 100)

    def test_low_concern_half_credit(self):
        obj = complete()
        resolve(obj, 'security.authorization', 'concern', 'low')
        r = self.evaluate(obj)
        self.assertEqual(r['earned_points'], 89)
        self.assertEqual(r['score'], 94.7)
        self.assertEqual(r['dimensions']['security']['earned_points'], 40)

    def test_medium_cap(self):
        obj = complete()
        resolve(obj, 'privacy.logging', 'concern', 'medium')
        r = self.evaluate(obj)
        self.assertEqual(r['score'], 69)
        self.assertEqual(r['verdict'], 'USE WITH CAUTION')

    def test_high_overrides_good_average(self):
        obj = complete()
        resolve(obj, 'security.authorization', 'fail', 'high')
        r = self.evaluate(obj)
        self.assertGreater(r['raw_reviewed_score'], 85)
        self.assertEqual((r['score'], r['verdict']), (49, 'NOT RECOMMENDED'))

    def test_critical_overrides_unknowns(self):
        obj = ledger()
        resolve(obj, 'security.credentials', 'fail', 'critical')
        r = self.evaluate(obj)
        self.assertEqual(r['verdict'], 'DO NOT USE')
        self.assertTrue(r['score_is_provisional'])

    def test_core_missing_keeps_high_partial_score_incomplete(self):
        obj = complete()
        obj['checks'] = [c for c in obj['checks'] if c['id'] != 'security.inputs']
        r = self.evaluate(obj)
        self.assertEqual(r['score'], 100)
        self.assertEqual(r['verdict'], 'INCOMPLETE')
        self.assertIn('security.inputs', r['unresolved_core_checks'])
        self.assertEqual(r['assessed_points'], 84)

    def test_noncore_missing_limits_verdict(self):
        obj = complete()
        obj['checks'] = [c for c in obj['checks'] if c['id'] != 'reliability.maintenance']
        r = self.evaluate(obj)
        self.assertEqual(r['verdict'], 'REVIEWED WITH LIMITATIONS')
        self.assertEqual(r['coverage_percent'], 94.7)

    def test_thin_docs_do_not_approve_opaque_service(self):
        obj = ledger('remote_http')
        obj['target'].update(review_basis='hosted_docs', revision='docs captured 2026-10-13')
        resolve(obj, 'transparency.disclosure')
        r = self.evaluate(obj)
        self.assertEqual((r['score'], r['coverage_percent'], r['verdict']), (100, 5, 'INCOMPLETE'))

    def test_docs_cannot_pass_implementation(self):
        for ident in RUBRIC['implementation_checks']:
            for state in ('pass', 'concern'):
                with self.subTest(ident=ident, state=state):
                    obj = ledger('remote_http')
                    obj['target'].update(review_basis='hosted_docs', revision='docs snapshot')
                    resolve(obj, ident, state, 'low' if state == 'concern' else 'none')
                    with self.assertRaises(ValueError): self.evaluate(obj)

    def test_docs_can_establish_concrete_unsafe_launch_failure(self):
        obj = ledger('remote_http')
        obj['target'].update(review_basis='hosted_docs', revision='docs snapshot')
        resolve(obj, 'supply.launch', 'fail', 'high')
        self.assertEqual(self.evaluate(obj)['verdict'], 'NOT RECOMMENDED')

    def test_remote_cannot_exclude_hosted_unknown(self):
        obj = complete('remote_http')
        resolve(obj, 'privacy.hosted', 'not_applicable')
        with self.assertRaises(ValueError): self.evaluate(obj)

    def test_transport_cannot_be_excluded_for_stdio(self):
        obj = complete()
        resolve(obj, 'security.transport', 'not_applicable')
        with self.assertRaises(ValueError): self.evaluate(obj)

    def test_local_http_allows_hosted_na_but_still_reviews_transport(self):
        r = self.evaluate(complete('local_http'))
        self.assertEqual(r['assessed_points'], 94)
        self.assertEqual(next(c['status'] for c in r['checks'] if c['id']=='security.transport'), 'pass')

    def test_resolved_needs_evidence(self):
        for status, severity in [('pass','none'), ('concern','low'), ('fail','high'), ('not_applicable','none')]:
            obj = complete()
            c = resolve(obj, 'privacy.hosted' if status=='not_applicable' else 'security.transport', status, severity)
            c['evidence'] = []
            with self.subTest(status=status), self.assertRaises(ValueError): self.evaluate(obj)

    def test_invalid_severity_pairs(self):
        for status, severity in [('pass','low'),('unknown','high'),('concern','critical'),('fail','none'),('fail','medium')]:
            obj = ledger()
            resolve(obj, 'security.transport', status, severity)
            with self.subTest(status=status,severity=severity), self.assertRaises(ValueError): self.evaluate(obj)

    def test_duplicate_check(self):
        obj = ledger(); obj['checks'].append(copy.deepcopy(obj['checks'][0]))
        with self.assertRaises(ValueError): self.evaluate(obj)

    def test_unknown_id(self):
        obj = ledger(); obj['checks'][0]['id'] = 'security.magic'
        with self.assertRaises(ValueError): self.evaluate(obj)

    def test_no_weight_override(self):
        obj = ledger(); obj['checks'][0]['weight'] = 0
        with self.assertRaises(ValueError): self.evaluate(obj)

    def test_no_score_override(self):
        obj = ledger(); obj['score'] = 100
        with self.assertRaises(ValueError): self.evaluate(obj)

    def test_source_revision_required(self):
        for revision in ('main', '', None, 'a'*39):
            obj = ledger(); obj['target']['revision'] = revision
            with self.subTest(revision=revision), self.assertRaises(ValueError): self.evaluate(obj)

    def test_snapshot_hash_accepted(self):
        obj = ledger(); obj['target']['revision'] = 'b'*64
        self.assertEqual(self.evaluate(obj)['target']['revision'], 'b'*64)

    def test_invalid_lines(self):
        for evidence in ({'line_start':0}, {'line_start':True}, {'line_start':5,'line_end':1}, {'line_end':5}):
            obj = complete(); obj['checks'][0]['evidence'] = [{'source':'fixture.py','detail':'Fixture', **evidence}]
            with self.subTest(evidence=evidence), self.assertRaises(ValueError): self.evaluate(obj)

    def test_markdown_includes_scope_calculation_and_escapes_pipes(self):
        obj = complete(); obj['target']['deployment'] = 'local | restricted\naccount'
        rendered = score.markdown(self.evaluate(obj))
        self.assertIn('94.0 / 94', rendered)
        self.assertIn('local \\| restricted', rendered)
        self.assertIn('not source-code coverage', rendered)

    def test_input_is_not_mutated(self):
        obj = complete(); before = copy.deepcopy(obj)
        self.evaluate(obj)
        self.assertEqual(obj, before)

    def test_duplicate_json_key_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'bad.json'; p.write_text('{"checks":[],"checks":[]}')
            with self.assertRaises(ValueError): score.load_json(p)

    def test_cli_success_and_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'ledger.json'; p.write_text(json.dumps(complete()))
            result = subprocess.run([sys.executable,str(ROOT/'scripts/score.py'),str(p)],capture_output=True,text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['score'],100)
            p.write_text('{}')
            bad = subprocess.run([sys.executable,str(ROOT/'scripts/score.py'),str(p)],capture_output=True,text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertEqual(bad.stdout, '')

    def test_cli_template_is_unknown_and_requires_real_revision(self):
        result = subprocess.run([sys.executable,str(ROOT/'scripts/score.py'),'--template'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        obj = json.loads(result.stdout)
        self.assertTrue(all(c['status']=='unknown' for c in obj['checks']))
        with self.assertRaises(ValueError): self.evaluate(obj)


if __name__ == '__main__': unittest.main()
