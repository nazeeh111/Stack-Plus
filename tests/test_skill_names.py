"""Canonical exposure migration preserves source payloads and reversible profiles."""
import argparse
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import native_setup as native
import claude_setup as claude
import skill_names as names
from transaction import fingerprint


class SkillNames(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        previous = native.nstack.STATE
        self.addCleanup(setattr, native.nstack, 'STATE', previous)

    def sources(self):
        """Synthetic complete sources at the real selection/build boundary, offline."""
        selected = dict(native.selection())
        builds, receipts, payloads = {}, {}, {}
        addon = None
        for source_name, exposed in names.RENAMES.items():
            root = self.base / 'sources' / source_name
            entry = Path('skills') / source_name
            skill = root / entry / 'SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text('---\nname: ' + source_name + '\ndescription: Original method\n---\n'
                             '# Original ' + source_name + '\nRead [support](../../support.md).\n')
            (root / 'support.md').write_text('Original method and source coordinates: ' + source_name + '\n')
            (root / 'LICENSE').write_text('Original rights notice for ' + source_name + '\n')
            (skill.parent / 'references').mkdir()
            (skill.parent / 'references/api.md').write_text('Original API and command syntax.\n')
            (skill.parent / 'assets').mkdir()
            (skill.parent / 'assets/sample.bin').write_bytes(b'\x00\xffretained resource')
            files = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            payloads[source_name] = (entry, files)
            if source_name == 'unslop':
                addon = {'source': root, 'entry': entry, 'overrides': {},
                         'provenance': {'repository': 'fixture/unslop', 'revision': 'pinned-fixture',
                                        'source_path': str(entry), 'license': 'fixture'},
                         'frozen_files': {rel: (data, 0o444) for rel, data in files.items()}}
                continue
            spec = selected[exposed]
            receipt = {'content_sha256': source_name, 'builder_sha256': 'fixture', 'entry_dir': str(entry),
                       'files': {rel: native.sha(data) for rel, data in files.items()}}
            (root / '.nstack-release.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
            builds[(spec['candidate_id'], spec['source_path'])] = root
            receipts[root] = (receipt, {}, spec)
        return builds, receipts, payloads, addon

    def args(self, home, state, legacy=False):
        return argparse.Namespace(home=str(home), state=str(state),
                                  only=[source if legacy else exposed for source, exposed in names.RENAMES.items()
                                        if source != 'unslop'],
                                  unslop=True, agent_reach=False, repository_docs=False, replace=True, vault=None)

    def assert_payloads(self, index, payloads, claude_host=False):
        self.assertEqual(len(index), 6)
        by_name = {row['name']: row for row in index}
        self.assertEqual(set(by_name), set(names.RENAMES.values()))
        for source, exposed in names.RENAMES.items():
            row = by_name[exposed]
            self.assertEqual(row['source_name'], source)
            self.assertEqual(row['aliases'], [source])
            self.assertEqual(row['source_path'], str(payloads[source][0]) if source == 'unslop'
                             else dict(native.selection())[exposed]['source_path'])
            active = Path(row['skill_path'])
            entry, files = payloads[source]
            bundle = active.parents[len(entry.parts)]
            for relative, original in files.items():
                installed = (bundle / relative).read_bytes()
                if relative == str(entry / 'SKILL.md'):
                    self.assertEqual(names.entry_name(installed, source), names.entry_name(original, source))
                    self.assertIn(('name: ' + (json.dumps(exposed) if claude_host else exposed) + '\n').encode(), installed)
                else:
                    self.assertEqual(installed, original)

    def roundtrip(self, adapter):
        builds, receipts, payloads, addon = self.sources()
        home, state = self.base / 'home', self.base / 'state'
        home.mkdir()
        is_claude = adapter is claude
        discovery = home / ('.claude/skills' if is_claude else '.agents/skills')
        own = discovery / 'personal'
        own.mkdir(parents=True)
        (own / 'SKILL.md').write_text('Unrelated exact user bytes.\n')
        original_root = fingerprint(discovery)
        config = home / ('.claude/settings.json' if is_claude else '.codex/config.toml')
        config.parent.mkdir(exist_ok=True)
        config.write_text('{"model":"keep-model"}\n' if is_claude else 'model = "keep-model"\n')
        config_before = fingerprint(config)
        real_addon = native.addon_definition
        def definition(name):
            return copy.deepcopy(addon) if name == 'unslop' else real_addon(name)
        with patch.object(native.nstack, 'build', side_effect=lambda candidate, path: builds[(candidate, path)]), \
                patch.object(native.nstack, 'registered_release', side_effect=lambda root: receipts[root]), \
                patch.object(native, 'addon_definition', side_effect=definition):
            args = self.args(home, state, legacy=True)
            with patch.dict(names.RENAMES, {}, clear=True):
                first = adapter.apply(args)
            previous_root = fingerprint(discovery)
            previous_index = fingerprint(state / ('claude-skill-index.json' if is_claude else 'native-skill-index.json'))
            self.assertTrue(set(names.RENAMES).issubset({p.name for p in discovery.iterdir()}))
            second = adapter.apply(args)  # Legacy --only still selects canonical exposures.
            self.assertNotEqual(first['release'], second['release'])
            self.assertTrue(set(names.RENAMES).isdisjoint({p.name for p in discovery.iterdir()}))
            self.assertTrue(set(names.RENAMES.values()).issubset({p.name for p in discovery.iterdir()}))
            index_path = state / ('claude-skill-index.json' if is_claude else 'native-skill-index.json')
            self.assert_payloads(json.loads(index_path.read_text()), payloads, is_claude)
            self.assertEqual(fingerprint(config), config_before)
            for legacy in (False, True):
                self.assertFalse(adapter.apply(self.args(home, state, legacy))['changed'])
            self.assertFalse((state / 'native-tools').exists())
            self.assertFalse((state / 'runtimes').exists())
            adapter.rollback(second['run'], False)
            self.assertEqual(fingerprint(discovery), previous_root)
            self.assertEqual(fingerprint(index_path), previous_index)
            adapter.rollback(first['run'], False)
            self.assertEqual(fingerprint(discovery), original_root)
            self.assertEqual(fingerprint(config), config_before)

    def test_native_renames_migrate_once_preserve_payloads_and_restore_legacy_generation(self):
        self.roundtrip(native)

    def test_claude_renames_retire_only_owned_legacy_links_and_restore_previous_generation(self):
        self.roundtrip(claude)

    def test_claude_fresh_unowned_legacy_entries_block_duplicate_exposure_without_mutation(self):
        for source, exposed in names.RENAMES.items():
            for kind in ('directory', 'file', 'broken-link'):
                with self.subTest(source=source, kind=kind):
                    base = self.base / (source + '-' + kind)
                    home, state = base / 'home', base / 'state'
                    legacy = home / '.claude/skills' / source
                    legacy.parent.mkdir(parents=True)
                    if kind == 'directory':
                        legacy.mkdir()
                        (legacy / 'SKILL.md').write_text('Unowned dirty legacy method.\n')
                    elif kind == 'file':
                        legacy.write_text('Unowned legacy file bytes.\n')
                    else:
                        legacy.symlink_to(base / 'missing-source')
                    settings = home / '.claude/settings.json'
                    settings.write_text('{"model":"keep-model","permissions":{"deny":["Bash(rm:*)"]}}\n')
                    instructions = home / '.claude/CLAUDE.md'
                    instructions.write_text('Unowned user instructions.\n')
                    journal = state / 'runs/unrelated/journal.json'
                    journal.parent.mkdir(parents=True)
                    journal.write_text('["existing unrelated journal bytes"]\n')
                    before = {path: fingerprint(path) for path in (home, state)}
                    release = state / 'claude-releases/fixture'
                    row = {'name': exposed, 'source_name': source, 'aliases': [source],
                           'skill_path': str(release / 'bundles' / exposed / 'SKILL.md')}
                    with patch.object(claude, 'prepare', return_value=(release, [row])), \
                            patch.object(claude.profile_install, 'stage', side_effect=AssertionError('must not stage')):
                        with self.assertRaisesRegex(ValueError, 'Unowned legacy Claude skill collision'):
                            claude.apply(self.args(home, state))
                    for path, saved in before.items():
                        self.assertEqual(fingerprint(path), saved)
                    self.assertFalse((legacy.parent / exposed).exists())
                    self.assertFalse((state / 'claude-profile.json').exists())
                    self.assertFalse((state / 'rollback.sh').exists())

    def test_naming_policy_is_part_of_release_identity_and_collisions_fail_before_build(self):
        state = self.base / 'state'
        before, _ = native.prepare(state, [], [])
        with patch.dict(names.RENAMES, {'future-source': 'future-exposure'}):
            after, _ = native.prepare(state, [], [])
        self.assertNotEqual(before, after)
        with patch.object(native.nstack, 'build', side_effect=AssertionError('must not build')):
            with self.assertRaisesRegex(ValueError, 'Canonical skill names collide'):
                native.prepare(state, [('frontend-design', {}), ('web-ui-design', {})], [])


if __name__ == '__main__':
    unittest.main()
