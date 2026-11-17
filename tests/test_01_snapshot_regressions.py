"""Invocation-lifetime, eligible-scope and bounded-identity behavior regressions."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(os.environ.get('NSTACK_01_TEST_SCRIPT', Path(__file__).resolve().parents[1] / 'addons/01/scripts/capabilities.py'))
spec = importlib.util.spec_from_file_location('snapshot_regression_target', SCRIPT)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SHA = lambda text: hashlib.sha256(text.encode()).hexdigest()


class SnapshotRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name).resolve()
        self.rows = []

    def skill(self, name, description='Generic procedure', body='ordinary body', **fields):
        entry = self.state / 'native-releases/frozen/bundles' / name / 'SKILL.md'
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text(f'---\nname: {name}\ndescription: {description}\n---\n{body}')
        self.rows.append({'name':name,'skill_path':str(entry),**fields})
        self.save()
        return entry

    def save(self):
        (self.state/'native-skill-index.json').write_text(json.dumps(self.rows))

    def cli(self, *args):
        stream = io.StringIO()
        with patch.object(sys,'argv',[str(SCRIPT),'--state',str(self.state),*args]), contextlib.redirect_stdout(stream):
            m.main()
        return json.loads(stream.getvalue())

    def test_batch_reads_each_admitted_body_once_and_preserves_independent_results(self):
        self.skill('one',body='correlation transformation')
        self.skill('two',body='asynchronous race repair')
        with patch.object(m,'inventory',wraps=m.inventory)as inventory,patch.object(m,'functional_catalog',wraps=m.functional_catalog)as catalog,patch.object(m,'body_prefix',wraps=m.body_prefix)as bodies:
            result=self.cli('--body','--need','correlation','--need','asynchronous race')
        self.assertEqual([r['matches'][0]['name']for r in result['needs']],['one','two'])
        self.assertEqual(inventory.call_count,1)
        self.assertEqual(catalog.call_count,1)
        self.assertEqual(bodies.call_count,2)
        self.assertEqual(result['needs'][0]['body_discovery'],result['needs'][1]['body_discovery'])

    def test_batch_observes_body_and_metadata_changes_on_later_invocations(self):
        entry=self.skill('one',body='aurora transformation')
        before=self.cli('--body','--need','aurora','--need','one')
        entry.write_text(entry.read_text().replace('aurora transformation','beacon transformation').replace('Generic procedure','New procedure'))
        after=self.cli('--body','--need','aurora','--need','beacon')
        self.assertTrue(before['needs'][0]['matches'])
        self.assertEqual(after['needs'][0]['matches'],[])
        new=after['needs'][1]['matches'][0];old=before['needs'][0]['matches'][0]
        self.assertNotEqual(new['body_source']['sha256'],old['body_source']['sha256'])
        self.assertNotEqual(new['metadata_sha256'],old['metadata_sha256'])

    def test_excluded_bodies_cannot_starve_later_eligible_body(self):
        cards={};facets={'work':{'validate':'Validate'},'domains':{'other':'Other','target':'Target'},'artifacts':{'reports':'Reports'}}
        for i in range(35):
            name=f'junk-{i:02d}' if i<34 else 'target'
            self.skill(name,body='x'*m.MAX_BODY_BYTES if i<34 else 'needle technique')
            cards[name]={'description_sha256':SHA('Generic procedure'),'function':'Generic procedure','distinguish':'','work':['validate'],'domains':['other'if i<34 else'target'],'artifacts':['reports']}
        with patch.object(m,'functional_catalog',return_value=(cards,facets,{'status':'read'})),patch.object(m,'body_prefix',wraps=m.body_prefix)as bodies:
            result=m.search(self.state,['needle'],body=True,facet_filters={'domains':['target']})
        self.assertEqual([r['name']for r in result['matches']],['target'])
        self.assertEqual(bodies.call_count,1)
        self.assertEqual(result['body_discovery']['records']['budget_exhausted'],0)

    def test_eligible_filter_never_opens_excluded_body(self):
        self.skill('excluded',body='unused')
        self.skill('target',body='needle')
        cards={name:{'description_sha256':SHA('Generic procedure'),'function':'Generic procedure','distinguish':'','work':['validate'],'domains':[name],'artifacts':['reports']}for name in ['excluded','target']}
        original=m.body_prefix
        def only_target(path,*args):
            self.assertEqual(path.parent.name,'target')
            return original(path,*args)
        with patch.object(m,'functional_catalog',return_value=(cards,{},{})),patch.object(m,'body_prefix',only_target):
            self.assertEqual(m.search(self.state,['needle'],body=True,facet_filters={'domains':['target']})['matches'][0]['name'],'target')

    def test_oversized_alias_list_is_omitted_without_losing_valid_records(self):
        self.skill('large',body='needle',aliases=['x'*(m.MAX_RUNTIME_FIELD_CHARS+1)])
        self.skill('valid',aliases=['legacy'])
        result=m.search(self.state,['large']);row=result['matches'][0]
        self.assertNotIn('aliases',row)
        self.assertIn('aliases',row['oversized_fields_omitted'])
        self.assertLess(len(json.dumps(result)),10000)
        self.assertEqual(m.search(self.state,['legacy'])['matches'][0]['name'],'valid')
        self.assertEqual(m.search(self.state,['needle'],body=True)['matches'][0]['name'],'large')

    def test_alias_item_count_and_aggregate_character_bounds(self):
        self.skill('many',aliases=['a']*(m.MAX_RUNTIME_LIST_ITEMS+1))
        self.skill('sum',aliases=['a'*2048,'b'*2049])
        self.skill('boundary',aliases=['z'*m.MAX_RUNTIME_FIELD_CHARS])
        for name in ['many','sum']:
            row=m.search(self.state,[name])['matches'][0]
            self.assertNotIn('aliases',row)
            self.assertIn('aliases',row['oversized_fields_omitted'])
        self.assertEqual(len(m.search(self.state,['boundary'])['matches'][0]['aliases'][0]),m.MAX_RUNTIME_FIELD_CHARS)

    def test_description_source_and_deployment_bounds_keep_body_discoverable(self):
        long='x'*(m.MAX_RUNTIME_FIELD_CHARS+1)
        self.skill('large',description=long,body='needle',source_name=long,deployment=long)
        row=m.search(self.state,['needle'],body=True)['matches'][0]
        self.assertEqual(row['name'],'large')
        self.assertEqual(set(row['oversized_fields_omitted']),{'description','source_name','deployment'})
        for key in ['description','source_name','deployment']:self.assertNotIn(key,row)

    def test_oversized_required_names_are_explicitly_rejected_without_hiding_valid(self):
        self.skill('valid',body='needle')
        self.rows.insert(0,{'name':'x'*(m.MAX_RUNTIME_FIELD_CHARS+1),'skill_path':self.rows[0]['skill_path']})
        self.save();result=m.search(self.state,['needle'],body=True)
        self.assertEqual([r['name']for r in result['matches']],['valid'])
        self.assertEqual(result['sources'][0]['oversized_skill_records_omitted'],1)

    def test_user_root_frontmatter_identity_and_description_are_bounded(self):
        root=self.state/'user-skills';entry=root/'invalid/SKILL.md';entry.parent.mkdir(parents=True)
        entry.write_text('---\nname: '+'x'*(m.MAX_RUNTIME_FIELD_CHARS+1)+'\ndescription: needle\n---\nneedle')
        good=root/'valid/SKILL.md';good.parent.mkdir();good.write_text('---\nname: valid\ndescription: '+'x'*(m.MAX_RUNTIME_FIELD_CHARS+1)+'\n---\nneedle')
        result=m.search(self.state,['needle'],body=True,skill_roots=[root])
        self.assertEqual([r['name']for r in result['matches']],['valid'])
        self.assertNotIn('description',result['matches'][0])
        self.assertEqual(result['sources'][0]['oversized_skill_records_omitted'],1)

    def test_batched_runtime_limits_and_alias_identity_remain_inert_and_present(self):
        tools=self.state/'native-tools';tools.mkdir()
        (tools/'index.json').write_text(json.dumps([{'name':'engine','aliases':['legacy'],'description':'beacon renderer','callable':False,'state':'denied','limits':['No execution authorized'],'readiness':'Prior fixture only','command':['python3','/fixture/script.py']}]))
        result=self.cli('--need','legacy','--need','beacon')
        for need in result['needs']:
            row=need['matches'][0]
            self.assertFalse(row['callable']);self.assertEqual(row['state'],'denied');self.assertEqual(row['limits'],['No execution authorized']);self.assertEqual(row['command'],['python3','/fixture/script.py'])
        self.assertEqual(result['needs'][0]['matches'][0]['match']['exact_identity'],['legacy'])


if __name__=='__main__':unittest.main(verbosity=2)
