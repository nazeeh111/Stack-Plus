"""Functional views preserve coverage, freshness and name-independent retrieval."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'addons/01/scripts/capabilities.py'
spec = importlib.util.spec_from_file_location('functional_capabilities', SCRIPT)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SHA = lambda text: hashlib.sha256(text.encode()).hexdigest()


class FunctionalCatalog(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.rows = []
        self.facets = {'work': {'validate': 'Validate', 'create': 'Create'},
                       'domains': {'data': 'Data', 'web': 'Web'},
                       'artifacts': {'reports': 'Reports', 'interfaces': 'Interfaces'}}
        self.cards = {}

    def skill(self, name, description, source=None, function='Propagate correlated uncertainty'):
        entry = self.root / 'native-releases/fixture/bundles' / name / 'SKILL.md'
        entry.parent.mkdir(parents=True)
        entry.write_text('---\nname: '+name+'\ndescription: '+description+'\n---\nLocal body.\n')
        source = source or name
        self.rows.append({'name': name, 'source_name': source, 'skill_path': str(entry)})
        (self.root / 'native-skill-index.json').write_text(json.dumps(self.rows))
        self.cards[source] = {'description_sha256': SHA(description), 'function': function,
                              'distinguish': 'Correlated measurement errors, not UI state.',
                              'work': ['validate'], 'domains': ['data', 'web'],
                              'artifacts': ['reports', 'interfaces']}
        return entry

    def catalog(self):
        return patch.object(m, 'functional_catalog', return_value=(self.cards, self.facets, {'status': 'read'}))

    def test_same_contribution_is_reachable_through_multiple_views(self):
        self.skill('opaque', 'Analyze measurements')
        with self.catalog():
            view = m.browse(self.root, 'domains')
            self.assertEqual(set(view['groups']), {'data', 'web'})
            self.assertEqual(view['groups']['data']['examples'][0]['name'], 'opaque')
            self.assertEqual(view['groups']['web']['examples'][0]['name'], 'opaque')
            self.assertEqual(m.search(self.root, ['correlated'], facet_filters={'work': ['validate']})['total_matches'], 1)

    def test_stale_or_unknown_card_never_hides_current_metadata(self):
        entry = self.skill('opaque', 'Analyze measurements')
        entry.write_text(entry.read_text().replace('Analyze measurements', 'New conversion method'))
        with self.catalog():
            self.assertEqual(m.search(self.root, ['correlated'])['matches'], [])
            row = m.search(self.root, ['conversion'])['matches'][0]
            self.assertIn('stale', row['functional_status']); self.assertNotIn('function', row)
            self.assertEqual(m.search(self.root, ['conversion'], facet_filters={'work': ['validate']})['matches'], [])
            self.assertEqual(len(m.browse(self.root, 'work')['unclassified']), 1)

    def test_facet_and_negative_boundary_text_add_no_rank_weight(self):
        self.skill('opaque', 'Analyze measurements', function='Analyze measurements')
        with self.catalog():
            for term in ('data', 'validate', 'UI state'):
                self.assertEqual(m.search(self.root, [term])['matches'], [])

    def test_runtime_identity_collision_does_not_inherit_a_skill_card(self):
        self.skill('opaque', 'Analyze measurements')
        tools = self.root / 'native-tools'; tools.mkdir()
        (tools / 'index.json').write_text(json.dumps([
            {'name': 'opaque', 'description': 'Analyze measurements', 'callable': False}]))
        with self.catalog():
            rows = m.search(self.root, ['measurements'])['matches']
            runtime = next(r for r in rows if r['kind'] == 'runtime')
            self.assertNotIn('function', runtime); self.assertFalse(runtime['callable'])
            view = m.browse(self.root, 'work')
            self.assertEqual(view['groups']['validate']['count'], 1)

    def test_summary_only_body_mode_match_has_actual_evidence(self):
        self.skill('opaque', 'Analyze measurements')
        with self.catalog():
            row = m.search(self.root, ['correlated'], body=True)['matches'][0]
            self.assertEqual(row['match']['fields']['functional_summary'], ['correlated'])
            self.assertIn('functional_summary', [e['field'] for e in row['match']['evidence']])

    def test_identifier_and_order_changes_preserve_dominant_function_match(self):
        self.skill('popular-council', 'Review interface colors', source='color-source', function='Review interface colors')
        self.skill('unfamiliar', 'Analyze measurements', source='measurement-source')
        with self.catalog():
            before = m.search(self.root, ['correlated', 'uncertainty'], limit=1)['matches'][0]
            self.rows.reverse(); self.rows[0]['name'] = 'method-47'
            (self.root / 'native-skill-index.json').write_text(json.dumps(self.rows))
            after = m.search(self.root, ['correlated', 'uncertainty'], limit=1)['matches'][0]
        self.assertEqual(before['source_name'], after['source_name'])
        self.assertEqual(before['match']['rank'], after['match']['rank'])

    def test_loader_rejects_oversize_and_invalid_facets_without_executing_content(self):
        self.skill('opaque', 'Analyze measurements')
        fake = self.root / 'skill/scripts/capabilities.py'; fake.parent.mkdir(parents=True)
        data = self.root / 'skill/references/capability-cards.json'; data.parent.mkdir()
        data.write_text(json.dumps({'version': 1, 'facets': self.facets, 'cards': self.cards}))
        with patch.object(m, '__file__', str(fake)):
            cards, _, source = m.functional_catalog()
            self.assertEqual(set(cards), {'opaque'}); self.assertEqual(source['status'], 'read')
            with patch.object(m, 'MAX_CATALOG_BYTES', 10):
                self.assertEqual(m.functional_catalog()[2]['status'], 'unavailable')
            invalid = {'version': 1, 'facets': {'work': []}, 'cards': self.cards}
            data.write_text(json.dumps(invalid))
            self.assertEqual(m.functional_catalog()[2]['status'], 'unavailable')

    def test_cli_keeps_distinct_needs_separate(self):
        self.skill('one', 'Analyze correlation')
        self.skill('two', 'Repair asynchronous races')
        result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--state', str(self.root),
            '--need', 'correlation', '--need', 'asynchronous races'], capture_output=True, text=True, check=True)
        needs = json.loads(result.stdout)['needs']
        self.assertEqual([r['matches'][0]['name'] for r in needs], ['one', 'two'])


if __name__ == '__main__': unittest.main()
