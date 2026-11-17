"""Exact native ports, source preservation and contribution-discovery contracts."""
from pathlib import Path
import hashlib,importlib.util,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'))
import skill_names,patch_host_skills,skill_build
spec=importlib.util.spec_from_file_location('trigger_discovery',ROOT/'addons/01/scripts/capabilities.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
FIX=Path(__file__).parent/'trigger-fixtures'

class TriggerBoundaryPorts(unittest.TestCase):
 def test_inline_ports_preserve_complete_body_and_refuse_unreviewed_description(self):
  for name in ['test-driven-development','google-workspace-cli','product-marketing-context']:
   with self.subTest(name=name):
    raw=(FIX/(name+'.original.md')).read_bytes();rendered=skill_names.entry_name(raw,name)
    self.assertEqual(raw.split(b'---',2)[2],rendered.split(b'---',2)[2])
    changed=raw.replace(b'description:',b'description: unreviewed ',1)
    with self.assertRaises(ValueError):skill_names.entry_name(changed,name)
    self.assertEqual(skill_names.entry_name(rendered,name),rendered)
 def test_bigquery_native_port_retains_original_and_rejects_drift(self):
  raw=(FIX/'bigquery-optimization.original.md').read_bytes()
  with tempfile.TemporaryDirectory()as td:
   out=Path(td).resolve();p=out/'SKILL.md';p.write_bytes(raw);patch_host_skills.patch('L020','bigquery-optimization',out)
   self.assertEqual((out/'NATIVE-ORIGINALS/bigquery-SKILL.md.original').read_bytes(),raw)
   values,_=m.frontmatter(p);self.assertIn('capacity',values['description']);self.assertNotIn('bigquery-troubleshooting',values['description'])
   drift=raw.replace(b'Provides workflows',b'Unreviewed workflows',1);p.write_bytes(drift)
   with self.assertRaises(ValueError):patch_host_skills.patch('L020','bigquery-optimization',out)
   self.assertEqual(p.read_bytes(),drift)
 def test_tdd_native_port_keeps_original_and_changes_only_reviewed_seams_and_handoff(self):
  raw=(FIX/'test-driven-development.original.md').read_bytes()
  with tempfile.TemporaryDirectory()as td:
   out=Path(td).resolve();p=out/'SKILL.md';p.write_bytes(raw);skill_build.patch_p001(out,'tdd')
   self.assertEqual((out/'NATIVE-ORIGINALS/tdd-SKILL.md.original').read_bytes(),raw)
   self.assertIn('## Anti-patterns',p.read_text());self.assertIn('**Red before green.**',p.read_text())
   self.assertNotIn('No test is written at an unconfirmed seam',p.read_text());self.assertIn('already supplied interface choices',p.read_text())
   drift=raw.replace(b'**Test only at pre-agreed seams.**',b'**Unreviewed seam process.**',1);p.write_bytes(drift)
   with self.assertRaises(ValueError):skill_build.patch_p001(out,'tdd')
   self.assertEqual(p.read_bytes(),drift);self.assertEqual((out/'NATIVE-ORIGINALS/tdd-SKILL.md.original').read_bytes(),raw)
 def test_four_ported_descriptions_bind_cards_without_changing_any_facet(self):
  cards,_,_=m.functional_catalog();old=json.loads((FIX/'FACETS-BEFORE.json').read_text())
  for key in cards:
   for facet in ['work','domains','artifacts']:self.assertEqual(cards[key][facet],old[key][facet])
  with tempfile.TemporaryDirectory()as td:
   state=Path(td);rows=[]
   for name in ['test-driven-development','google-workspace-cli','product-marketing-context','bigquery-optimization']:
    p=state/'native-releases/trial'/name/'SKILL.md';p.parent.mkdir(parents=True)
    if name=='bigquery-optimization':p.write_bytes((FIX/'bigquery-optimization.original.md').read_bytes());patch_host_skills.patch('L020',name,p.parent)
    else:p.write_bytes(skill_names.entry_name((FIX/(name+'.original.md')).read_bytes(),name))
    rows.append({'name':name,**skill_names.metadata(name),'skill_path':str(p)})
   (state/'native-skill-index.json').write_text(json.dumps(rows))
   for terms,expected in [(['marketing','positioning'],'product-marketing-context'),(['BigQuery','capacity','partitioning'],'bigquery-optimization'),(['gws','authentication'],'google-workspace-cli'),(['test-first','behavioral'],'test-driven-development')]:
    result=m.search(state,terms);self.assertEqual(result['matches'][0]['name'],expected);self.assertIn('function',result['matches'][0])
   self.assertNotIn('product-marketing-context',[r['name']for r in m.search(state,['new','scientific','project'])['matches']])
   for r in rows:
    self.assertEqual(m.search(state,[r['name']])['matches'][0]['name'],r['name'])
    for alias in r['aliases']:self.assertEqual(m.search(state,[alias])['matches'][0]['name'],r['name'])
 def test_catalogue_rows_represent_actual_card_contributions(self):
  text=(ROOT/'docs/CAPABILITY_CATALOG.md').read_text();cards,_,_=m.functional_catalog()
  for name,key in [('test-driven-development','tdd'),('google-workspace-cli','gws-shared'),('product-marketing-context','product-marketing'),('bigquery-optimization','bigquery-optimization')]:
   row=next(line for line in text.splitlines()if line.startswith('| '+name+' |'));self.assertIn(cards[key]['function'],row);self.assertIn(cards[key]['distinguish'],row)

if __name__=='__main__':unittest.main(verbosity=2)
