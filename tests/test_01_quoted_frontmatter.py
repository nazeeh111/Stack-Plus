"""Supported YAML flow-string metadata, retrieval and admission regressions."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

SCRIPT=Path(os.environ.get('NSTACK_01_TEST_SCRIPT',Path(__file__).resolve().parents[1]/'addons/01/scripts/capabilities.py'))
spec=importlib.util.spec_from_file_location('quoted_target',SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

CASES=[
    ("'First line\n  second line\n  final line'",'First line second line final line'),
    ('"First line\n  second line\n  final line"','First line second line final line'),
    ("'A ''quoted'' author\n  and C:\\data'","A 'quoted' author and C:\\data"),
    ('"A \\"quoted\\" value\n  and \\u03bb"','A "quoted" value and λ'),
    ('"a\\\n  b"','ab'),
    ('"a \\\n  b"','a b'),
    ("'first\n\n  paragraph'",'first\nparagraph'),
    ('"first\n\n  paragraph"','first\nparagraph'),
    ("'literal # content\n  next' # outside comment",'literal # content next'),
    ('"hex \\x41, unicode \\u03bb, codepoint \\U0001f680"','hex A, unicode λ, codepoint 🚀'),
    ('"escaped\\ space and slash \\/"','escaped space and slash /'),
]


class QuotedFrontmatter(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name).resolve()

    def entry(self,value,body='Body sentinel must not decode: \xff'):
        path=self.root/'skills/opaque/SKILL.md';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(('---\nname: opaque\ndescription: '+value+'\n---\n').encode()+body.encode('latin-1'))
        return path

    def test_quoted_multiline_and_escape_values_are_not_truncated(self):
        for value,expected in CASES:
            with self.subTest(value=value):self.assertEqual(m.frontmatter(self.entry(value))[0]['description'],expected)

    def test_existing_block_scalar_and_plain_multiline_metadata_stay_compatible(self):
        for value,expected in [('>-\n  first line\n  second line','first line second line'),('|-\n  first line\n  second line','first line\nsecond line'),('\n  first line\n  second line','first line second line')]:
            with self.subTest(value=value):self.assertEqual(m.frontmatter(self.entry(value))[0]['description'],expected)

    def test_complete_omnigraph_contract_is_retrievable_without_body_search(self):
        value="'Design Omnigraph .pg schemas, parameterized\n  .gq queries, validated loads and schema migration plans. Use for\n  an explicitly chosen Omnigraph project.'"
        entry=self.entry(value);state=self.root/'state';state.mkdir()
        for terms in [['gq'],['validated','loads'],['schema','migration'],['explicitly','chosen']]:
            with self.subTest(terms=terms):
                result=m.search(state,terms,skill_roots=[entry.parents[1]])
                self.assertEqual(result['matches'][0]['name'],'opaque')
                self.assertNotIn('body_source',result['matches'][0])
                self.assertIn('explicitly chosen Omnigraph project',result['matches'][0]['description'])

    def test_modified_continuation_is_fresh_and_fingerprint_changes(self):
        entry=self.entry("'Ordinary method\n  for aurora conversion.'");state=self.root/'state';state.mkdir()
        before=m.search(state,['aurora'],skill_roots=[entry.parents[1]])
        entry.write_bytes(entry.read_bytes().replace(b'aurora conversion',b'beacon validation'))
        self.assertEqual(m.search(state,['aurora'],skill_roots=[entry.parents[1]])['matches'],[])
        after=m.search(state,['beacon'],skill_roots=[entry.parents[1]])
        self.assertNotEqual(before['matches'][0]['metadata_sha256'],after['matches'][0]['metadata_sha256'])

    def test_unclosed_quoted_value_cannot_absorb_the_next_top_level_field(self):
        path=self.entry("'unfinished\nmetadata:\n  marker: unknown")
        with self.assertRaises(ValueError):m.frontmatter(path)

    def test_unknown_or_incomplete_escapes_fail_closed(self):
        for value in ['"invalid \\q"','"invalid \\u12"','"invalid \\Uffffffff"']:
            with self.subTest(value=value),self.assertRaises(ValueError):m.frontmatter(self.entry(value))

    def test_quoted_header_still_obeys_existing_byte_bound(self):
        with self.assertRaises(ValueError):m.frontmatter(self.entry("'"+'x'*(m.MAX_FRONTMATTER+1)+"'"))

    def test_command_looking_text_is_only_metadata(self):
        effect=self.root/'must-not-exist';value="'Use the literal command\n  touch "+str(effect)+" and do not execute it.'"
        parsed=m.frontmatter(self.entry(value))[0]['description']
        self.assertIn(str(effect),parsed);self.assertFalse(effect.exists())


if __name__=='__main__':unittest.main(verbosity=2)
