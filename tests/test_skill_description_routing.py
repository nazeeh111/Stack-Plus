"""Exercise actual metadata adaptation and discovery over the existing catalog."""
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lib'))
import skill_names
spec=importlib.util.spec_from_file_location('description_discovery',ROOT/'addons/01/scripts/capabilities.py')
discovery=importlib.util.module_from_spec(spec);spec.loader.exec_module(discovery)


class DescriptionRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native=Path.home()/'Library/Application Support/nstack'
        if not (native/'native-skill-index.json').is_file():
            raise unittest.SkipTest('Actual installed catalog unavailable')
        cls.live=json.loads((native/'native-skill-index.json').read_text())
        cls.tmp=tempfile.TemporaryDirectory(prefix='nstack-description-routing-',dir='/private/tmp')
        cls.state=Path(cls.tmp.name);rows=[];cls.originals={};cls.adapted={}
        for row in cls.live:
            name=row['name'];raw=Path(row['skill_path']).read_bytes()
            # Apply the same entry transformation as native exposure, not a fake
            # index with guessed descriptions or hand-authored method contents.
            rendered=skill_names.entry_name(raw,name)
            cls.originals[name]=raw;cls.adapted[name]=rendered
            target=cls.state/'native-releases/fixture/bundles'/name/'SKILL.md'
            target.parent.mkdir(parents=True);target.write_bytes(rendered)
            rows.append({**row,'skill_path':str(target)})
        (cls.state/'native-skill-index.json').write_text(json.dumps(rows))
        (cls.state/'native-tools').mkdir()
        (cls.state/'native-tools/index.json').write_bytes((native/'native-tools/index.json').read_bytes())

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def names(self,*terms):
        return [r['name'] for r in discovery.search(self.state,list(terms),limit=12)['matches']]

    def test_real_operation_queries_select_the_defined_contribution(self):
        cases=[
            (('instability','batch size','throughput','learning rate'),'deep-learning-training-diagnostics'),
            (('TypeScript','audio','cues','animation'),'motion-canvas-vector-animation'),
            (('Remotion','crop','trim','composition'),'remotion-animation-markup'),
            (('Remotion','Studio','editable','keyframes'),'remotion-editable-video-markup'),
            (('experiment','hypothesis'),'experimental-design'),
        ]
        for terms,expected in cases:
            with self.subTest(terms=terms):self.assertEqual(self.names(*terms)[0],expected)

    def test_growth_route_and_existing_canonical_and_alias_lookups_remain(self):
        self.assertIn('ab-testing',self.names('conversion','growth'))
        names={r['name'] for r in self.live}
        self.assertEqual(len(names),len(self.live))
        for row in self.live:
            self.assertEqual(self.names(row['name'])[0],row['name'])
            for alias in row.get('aliases',[]):
                self.assertEqual(self.names(alias)[0],row['name'],alias)

    def test_metadata_changes_preserve_the_complete_method_body(self):
        for name,raw in self.originals.items():
            with self.subTest(name=name):
                self.assertEqual(raw.split(b'---',2)[2],self.adapted[name].split(b'---',2)[2])
        for name in ('ab-testing','sitewide-seo-audit','lean-formalize'):
            description=discovery.frontmatter(self.state/'native-releases/fixture/bundles'/name/'SKILL.md')[0]['description']
            self.assertNotIn('seo-page',description)
            self.assertNotIn('proof-writer',description)

    def test_changed_source_description_is_not_silently_adapted(self):
        raw=self.originals['ab-testing']
        drift=re.sub(rb'(?m)^description:.*$', b'description: Unreviewed source purpose', raw, count=1)
        self.assertNotEqual(drift,raw)
        with self.assertRaisesRegex(ValueError,'description changed'):
            skill_names.entry_name(drift,'ab-testing')


if __name__=='__main__':unittest.main()
