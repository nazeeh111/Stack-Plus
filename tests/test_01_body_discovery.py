"""Progressive discovery from admitted instruction bytes, not runtime execution."""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'addons/01/scripts/capabilities.py'
SPEC = importlib.util.spec_from_file_location('body_discovery', SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
SHA = lambda raw: hashlib.sha256(raw).hexdigest()


class BodyDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='nstack-body-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.state = self.base / 'state'; self.state.mkdir()
        self.rows = []

    def skill(self, name, body, description='General local procedure', aliases=()):
        entry = self.state / 'native-releases/fixture/bundles' / name / 'SKILL.md'
        entry.parent.mkdir(parents=True)
        header = f'---\nname: {name}\ndescription: {description}\n---\n'.encode()
        entry.write_bytes(header + (body.encode() if isinstance(body, str) else body))
        self.rows.append({'name': name, 'skill_path': str(entry), 'aliases': list(aliases)})
        (self.state / 'native-skill-index.json').write_text(json.dumps(self.rows))
        return entry, header

    def search(self, *terms, **options):
        return module.search(self.state, list(terms), **options)

    def test_unknown_names_expose_body_only_contributions_and_field_evidence(self):
        self.skill('amber', 'Identify correlations before combining estimates.')
        self.skill('cobalt', 'Inspect coupling and co-change before extracting a module.')
        self.skill('cinder', 'A terminal state must not masquerade as a deadlock.')
        self.skill('violet', 'Apply inversion to expose an untested assumption.')
        terms = ['correlation', 'coupling', 'deadlock', 'inversion']
        self.assertEqual(self.search(*terms)['matches'], [])
        found = self.search(*terms, body=True)
        self.assertEqual(found['total_matches'], 4)
        self.assertEqual({term for row in found['matches'] for term in row['match']['body']}, set(terms))
        for row in found['matches']:
            self.assertEqual(row['match']['function'], [])
            self.assertEqual(row['match']['fields'], {'description': [], 'activation': [], 'functional_summary': []})
            self.assertEqual(row['body_source']['hash_scope'], 'SKILL.md complete body bytes read')
            self.assertTrue(all(item['field'] == 'body' for item in row['match']['evidence']))

    def test_expanded_ranking_counts_distinct_function_plus_body_concepts(self):
        self.skill('early', 'No other terms.', 'Inspect correlation')
        self.skill('later', 'Inspect coupling and correlations.', 'Inspect correlation')
        self.skill('body-only', 'Inspect coupling and correlation.')
        self.skill('coupling', 'Unrelated body.', 'Unrelated description')
        found = self.search('correlation', 'coupling', body=True)
        self.assertEqual([row['name'] for row in found['matches']],
                         ['later', 'body-only', 'early', 'coupling'])
        first, second = found['matches'][:2]
        self.assertEqual(first['match']['concept_coverage'], ['correlation', 'coupling'])
        self.assertEqual(first['match']['rank'], second['match']['rank'])
        # A term repeated in header/body is one concept, and name overlap cannot
        # outrank equal contribution evidence. Exact whole-query lookup can.
        self.assertEqual(self.search('coupling', body=True)['matches'][0]['name'], 'coupling')

    def test_explicit_alias_lookup_stays_first_in_body_mode(self):
        self.skill('first', 'Use the legacy beacon in comparisons.')
        self.skill('other', 'Ordinary method.', aliases=['beacon'])
        result = self.search('beacon', body=True)
        self.assertEqual(result['matches'][0]['name'], 'other')
        self.assertEqual(result['matches'][0]['match']['exact_identity'], ['beacon'])

    def test_default_never_calls_body_reader_or_emits_its_content(self):
        self.skill('unknown', b'Body sentinel must not decode: \xff', 'Inspect beacon')
        with patch.object(module, 'body_prefix', side_effect=AssertionError('Unexpected body read')):
            found = self.search('beacon')
        self.assertNotIn('body_discovery', found)
        self.assertNotIn('body_source', found['matches'][0])
        self.assertNotIn('Body sentinel', json.dumps(found))
        self.assertEqual(found['matches'][0]['hash_scope'], 'SKILL.md frontmatter only')

    def test_negation_and_executable_looking_text_are_inert_leads(self):
        effect = self.base / 'must-not-exist'
        body = f'Do NOT use this method for deadlock analysis.\n```sh\ntouch {effect}\n```\n'
        self.skill('unknown', body)
        found = self.search('deadlock', body=True)
        row = found['matches'][0]
        self.assertIn('Do NOT use', row['match']['evidence'][0]['excerpt'])
        self.assertIn('negative or misleading text', found['scope'])
        self.assertIn('do not establish suitability', found['scope'])
        self.assertFalse(effect.exists())

    def test_body_drift_is_fresh_even_with_identical_metadata(self):
        entry, header = self.skill('unknown', 'Find coupling now.\n')
        first = self.search('coupling', body=True)
        entry.write_bytes(header + b'Find inversion now.\n')
        self.assertEqual(self.search('coupling', body=True)['matches'], [])
        changed = self.search('inversion', body=True)
        before, after = first['matches'][0], changed['matches'][0]
        self.assertEqual(before['metadata_sha256'], after['metadata_sha256'])
        self.assertEqual(first['sources'], changed['sources'])
        self.assertNotEqual(before['body_source']['sha256'], after['body_source']['sha256'])
        self.assertNotEqual(first['body_discovery']['sources_sha256'], changed['body_discovery']['sources_sha256'])

    def test_query_snippets_hash_only_body_and_keep_actual_skill_line(self):
        body = '# Method\n' + 'Unrelated line.\n' * 30 + 'Measure correlation in both samples.\n' + 'Tail.\n' * 30
        _, header = self.skill('unknown', body)
        row = self.search('correlation', body=True)['matches'][0]
        source = row['body_source']; snippet = row['match']['evidence'][0]
        self.assertEqual(source['sha256'], SHA(body.encode()))
        self.assertEqual(source['header_sha256'], SHA(header))
        self.assertEqual(source['body_bytes'], len(body.encode()))
        self.assertFalse(source['truncated'])
        self.assertEqual(snippet['line'], header.count(b'\n') + 32)
        self.assertIn('correlation', snippet['excerpt'])
        self.assertLessEqual(len(snippet['excerpt']), module.MAX_SNIPPET_CHARS)
        self.assertTrue(snippet['excerpt_truncated'])

    def test_per_file_and_aggregate_byte_bounds_and_prefix_provenance(self):
        body = b'coupling ' + b'x' * 200 + b' inversion'
        entry, header = self.skill('one', body)
        self.skill('two', body)
        with patch.object(module, 'MAX_BODY_BYTES', 20), patch.object(module, 'MAX_BODY_TOTAL_BYTES', len(header) + 20):
            found = self.search('coupling', 'inversion', body=True)
        self.assertEqual(found['total_matches'], 1)
        row = found['matches'][0]
        self.assertEqual(row['match']['body'], ['coupling'])
        self.assertEqual(row['body_source']['body_bytes'], 20)
        self.assertEqual(row['body_source']['sha256'], SHA(body[:20]))
        self.assertEqual(row['body_source']['hash_scope'], 'SKILL.md body prefix bytes read')
        self.assertTrue(row['body_source']['truncated'])
        self.assertEqual(found['body_discovery']['read_bytes'], len(header) + 20)
        self.assertEqual(found['body_discovery']['records']['budget_exhausted'], 1)
        # A limit inside the header must not spill into body or exceed budget.
        text, source = module.body_prefix(entry, SHA(header), 7)
        self.assertEqual(text, '')
        self.assertLessEqual(source['read_bytes'], 7)
        self.assertNotEqual(source['status'], 'read')

    def test_evidence_count_and_excerpt_length_stay_bounded(self):
        terms = ['alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta']
        self.skill('unknown', '\n'.join('x' * 500 + ' ' + term + ' ' + 'y' * 500 for term in terms))
        found = self.search(*terms, body=True)['matches'][0]
        self.assertEqual(len(found['match']['body']), len(terms))
        self.assertEqual(len(found['match']['evidence']), module.MAX_BODY_SNIPPETS)
        self.assertTrue(all(len(item['excerpt']) <= module.MAX_SNIPPET_CHARS for item in found['match']['evidence']))

    def test_readiness_limits_and_other_files_never_create_function_matches(self):
        entry, _ = self.skill('unknown', 'Read [support](references/extra.md), not other files.')
        support = entry.parent / 'references/extra.md'; support.parent.mkdir()
        support.write_text('hidden correlation sentinel')
        (entry.parent / 'references/SKILL.md').write_text('---\nname: hidden\ndescription: sentinel\n---\ninversion')
        tools = self.state / 'native-tools'; tools.mkdir()
        (tools / 'index.json').write_text(json.dumps([{'name': 'engine', 'description': 'Other purpose',
            'readiness': 'Deadlock checks untested', 'limits': 'Coupling unsupported',
            'recipe': str(support), 'instructions': str(support)}]))
        original = module.regular_file
        opened = []
        @contextmanager
        def tracked(path):
            opened.append(path)
            with original(path) as stream:
                yield stream
        with patch.object(module, 'regular_file', tracked):
            found = self.search('correlation', 'deadlock', 'coupling', 'inversion', body=True)
        self.assertEqual(found['matches'], [])
        self.assertNotIn(support, opened)
        self.assertNotIn(support.with_name('SKILL.md'), opened)

    def test_runtime_list_constraints_and_blocked_state_survive_without_false_matches(self):
        tools = self.state / 'native-tools'; tools.mkdir()
        rows = [
            {'name': 'engine', 'description': 'Computational studies',
             'limits': ['No campaign retry authorized', 'Deadlock analysis unsupported'],
             'readiness': ['Source inspected', 'Runtime blocked'],
             'checks': ['static-evidence.json'], 'callable': False, 'state': 'admission_rejected'},
            {'name': 'malformed', 'description': 'Computational studies',
             'limits': ['valid', {'private': 'not inert prose'}], 'callable': 'false',
             'checks': ['valid', 7]},
        ]
        (tools / 'index.json').write_text(json.dumps(rows))
        found = self.search('engine')
        row = found['matches'][0]
        self.assertEqual(row['limits'], rows[0]['limits'])
        self.assertEqual(row['readiness'], rows[0]['readiness'])
        self.assertEqual(row['recorded_checks'], ['static-evidence.json'])
        self.assertIs(row['callable'], False)
        self.assertEqual(row['state'], 'admission_rejected')
        self.assertEqual(self.search('deadlock')['matches'], [])
        self.assertEqual(self.search('deadlock', body=True)['matches'], [])
        invalid = self.search('malformed')['matches'][0]
        self.assertNotIn('limits', invalid)
        self.assertNotIn('callable', invalid)
        self.assertNotIn('recorded_checks', invalid)

    def test_metadata_drift_between_admission_and_body_does_not_mix_generations(self):
        entry, _ = self.skill('unknown', 'coupling')
        original = module.body_prefix
        def mutate(path, expected, budget):
            path.write_text(path.read_text().replace('General local procedure', 'New description'))
            return original(path, expected, budget)
        with patch.object(module, 'body_prefix', mutate):
            found = self.search('unknown', 'coupling', body=True)
        self.assertEqual(found['matches'][0]['body_source']['status'], 'metadata_changed')
        self.assertEqual(found['matches'][0]['match']['body'], [])

    def test_sensitive_roots_and_outside_symlinks_never_reach_content_reader(self):
        entry, _ = self.skill('ordinary', 'ordinary body')
        secret = self.base / '.aws/synthetic/SKILL.md'; secret.parent.mkdir(parents=True)
        secret.write_text('---\nname: secret\ndescription: sentinel\n---\ninversion sentinel')
        link = entry.parent.parent / 'redirect/SKILL.md'; link.parent.mkdir(); link.symlink_to(secret)
        self.rows.extend([{'name': 'private', 'skill_path': str(secret)}, {'name': 'redirect', 'skill_path': str(link)}])
        (self.state / 'native-skill-index.json').write_text(json.dumps(self.rows))
        original = module.os.fdopen; info = secret.stat()
        def checked(descriptor, *args, **kwargs):
            actual = os.fstat(descriptor)
            self.assertNotEqual((actual.st_dev, actual.st_ino), (info.st_dev, info.st_ino))
            return original(descriptor, *args, **kwargs)
        with patch.object(module.os, 'fdopen', checked):
            result = module.search(self.state, ['sentinel'], body=True, skill_roots=[self.base / '.aws'])
        self.assertEqual(result['matches'], [])

    def test_post_admission_file_and_parent_symlink_swaps_fail_closed(self):
        for parent_swap in (False, True):
            with self.subTest(parent_swap=parent_swap):
                name = 'parent-swap' if parent_swap else 'file-swap'
                entry, _ = self.skill(name, 'ordinary body')
                secret = self.base / '.aws' / name / 'SKILL.md'; secret.parent.mkdir(parents=True)
                secret.write_text('---\nname: secret\ndescription: sentinel\n---\ninversion sentinel')
                original = module.body_prefix; info = secret.stat(); fdopen = module.os.fdopen
                def checked(descriptor, *args, **kwargs):
                    actual = os.fstat(descriptor)
                    self.assertNotEqual((actual.st_dev, actual.st_ino), (info.st_dev, info.st_ino))
                    return fdopen(descriptor, *args, **kwargs)
                def swap(path, expected, budget):
                    if path == entry:
                        if parent_swap:
                            path.parent.rename(path.parent.with_name(name + '-retained'))
                            path.parent.symlink_to(secret.parent)
                        else:
                            path.unlink(); path.symlink_to(secret)
                    return original(path, expected, budget)
                with patch.object(module, 'body_prefix', swap), patch.object(module.os, 'fdopen', checked):
                    found = self.search('sentinel', body=True)
                self.assertEqual(found['matches'], [])

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO requires POSIX')
    def test_fifo_body_mode_is_nonblocking_and_never_read_as_text(self):
        root = self.base / 'skills'; entry = root / 'queued/SKILL.md'; entry.parent.mkdir(parents=True)
        os.mkfifo(entry)
        completed = subprocess.run([sys.executable, '-B', str(SCRIPT), '--state', str(self.state),
            '--skills-root', str(root), '--body', 'coupling'], text=True, capture_output=True, timeout=2, check=True)
        self.assertEqual(json.loads(completed.stdout)['matches'], [])
        with self.assertRaises(ValueError):
            module.body_prefix(entry, SHA(b''), 100)

    def test_cli_requires_explicit_body_flag(self):
        self.skill('unknown', 'coupling')
        command = [sys.executable, '-B', str(SCRIPT), '--state', str(self.state), 'coupling']
        self.assertEqual(json.loads(subprocess.check_output(command, text=True))['matches'], [])
        expanded = json.loads(subprocess.check_output(command + ['--body'], text=True))
        self.assertEqual(expanded['matches'][0]['match']['body'], ['coupling'])

    def test_body_reader_fails_closed_without_descriptor_support(self):
        entry, header = self.skill('unknown', 'coupling')
        with patch.object(module.os, 'supports_dir_fd', set()):
            with self.assertRaisesRegex(ValueError, 'unavailable'):
                module.body_prefix(entry, SHA(header), 1000)

    def test_casefolded_literal_match_keeps_original_excerpt(self):
        self.skill('unknown', '# Context\nStraße is the original source spelling.\n')
        row = self.search('strasse', body=True)['matches'][0]
        self.assertEqual(row['match']['body'], ['strasse'])
        self.assertIn('Straße', row['match']['evidence'][0]['excerpt'])


class RealInstructionCoverage(unittest.TestCase):
    def test_real_installed_body_only_terms_without_method_name_queries(self):
        state = Path.home() / 'Library/Application Support/nstack'
        index = state / 'native-skill-index.json'
        if not index.is_file():
            self.skipTest('Installed nstack source is unavailable; synthetic unknown-name coverage still runs')
        for term, expected in [('correlation', 'uncertainty-and-units'), ('coupling', 'module-interface-design'),
                               ('deadlock', 'tla-state-machine-checking'), ('inversion', 'creative-reframing')]:
            with self.subTest(term=term):
                found = module.search(state, [term], limit=30, body=True)
                selected = next(row for row in found['matches'] if row['name'] == expected)
                self.assertEqual(selected['match']['function'], [])
                self.assertIn(term, selected['match']['body'])
                self.assertTrue(selected['body_source']['sha256'])


if __name__ == '__main__':
    unittest.main()
