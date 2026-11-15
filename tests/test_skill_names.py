"""Canonical exposure migration preserves source payloads and reversible profiles."""
import argparse
import copy
import json
from pathlib import Path
import sys
import subprocess
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
        builds, receipts, payloads, addons = {}, {}, {}, {}
        addon_flags = self.addon_flags()
        for source_name, exposed in names.RENAMES.items():
            root = self.base / 'sources' / source_name
            entry = Path('skills') / source_name
            if source_name == 'product-marketing':
                entry = Path('.')
            elif source_name == 'synthesize-research':
                entry = Path('product-management/skills/synthesize-research')
            skill = root / entry / 'SKILL.md'
            skill.parent.mkdir(parents=True)
            skill.write_text('---\nname: ' + source_name + '\ndescription: Original method\n---\n'
                             '# Original ' + source_name + '\n')
            if source_name == 'product-marketing':
                skill.write_text(skill.read_text() + 'Run `/product-marketing` anytime to update.\nData: `.agents/product-marketing.md`.\n')
            elif source_name == 'synthesize-research':
                skill.write_text(skill.read_text() + '```\n/synthesize-research $ARGUMENTS\n```\n')
            (root / 'support.md').write_text('Original method and source coordinates: ' + source_name + '\n')
            (root / 'LICENSE').write_text('Original rights notice for ' + source_name + '\n')
            (skill.parent / 'references').mkdir()
            (skill.parent / 'references/api.md').write_text('Original API and command syntax.\n')
            (skill.parent / 'assets').mkdir()
            (skill.parent / 'assets/sample.bin').write_bytes(b'\x00\xffretained resource')
            if source_name == 'unslop':
                (root / 'README.md').write_text('In Claude Code, type `/unslop`. In Codex, type `$unslop`.\n'
                                               '```\n/unslop this dashboard\n```\n'
                                               'Copy `skills/unslop` to `~/.claude/skills/unslop`.\n')
            files = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            payloads[source_name] = (entry, files)
            if source_name in addon_flags:
                addons[source_name] = {'source': root, 'entry': entry, 'overrides': {},
                         'provenance': {'repository': 'fixture/' + source_name, 'revision': 'pinned-fixture',
                                        'source_path': str(entry), 'license': 'fixture'},
                         'frozen_files': {rel: (data, 0o444) for rel, data in files.items()}}
                continue
            spec = selected[exposed]
            receipt = {'content_sha256': source_name, 'builder_sha256': 'fixture', 'entry_dir': str(entry),
                       'files': {rel: native.sha(data) for rel, data in files.items()}}
            (root / '.nstack-release.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
            builds[(spec['candidate_id'], spec['source_path'])] = root
            receipts[root] = (receipt, {}, spec)
        return builds, receipts, payloads, addons

    def addon_flags(self):
        return {name: flag.replace('-', '_') for flag, entries in claude.ADDONS.items()
                for name in entries if name in names.RENAMES}

    def args(self, home, state, legacy=False):
        addon_flags = self.addon_flags()
        return argparse.Namespace(home=str(home), state=str(state),
                                  only=[source if legacy else exposed for source, exposed in names.RENAMES.items()
                                        if source not in addon_flags],
                                  agent_reach=False, repository_docs=False, replace=True, vault=None,
                                  **{flag: True for flag in addon_flags.values()})

    def assert_payloads(self, index, payloads, claude_host=False):
        self.assertEqual(len(index), len(names.RENAMES))
        by_name = {row['name']: row for row in index}
        self.assertEqual(set(by_name), set(names.RENAMES.values()))
        for source, exposed in names.RENAMES.items():
            row = by_name[exposed]
            self.assertEqual(row['source_name'], source)
            self.assertEqual(row['aliases'], [source])
            self.assertEqual(row['source_path'], str(payloads[source][0]) if source in self.addon_flags()
                             else dict(native.selection())[exposed]['source_path'])
            active = Path(row['skill_path'])
            entry, files = payloads[source]
            bundle = active.parents[len(entry.parts)]
            for relative, original in files.items():
                installed = (bundle / relative).read_bytes()
                if relative in names.HOST_INVOCATIONS.get(source, {}):
                    receipt = json.loads((bundle / names.PORT_RECEIPT).read_text())['files'][relative]
                    self.assertEqual(receipt['before_sha256'], native.sha(original))
                    self.assertEqual(receipt['after_sha256'], native.sha(installed) if not claude_host or relative != str(entry / 'SKILL.md')
                                     else native.sha(names.entry_name(installed, exposed)))
                    self.assertEqual((bundle / receipt['original']).read_bytes(), original)
                    if source == 'unslop':
                        self.assertIn(b'nstack profile:', installed)
                        self.assertIn(b'`/ui-polish`', installed)
                        self.assertIn(b'`$ui-polish`', installed)
                        self.assertIn(b'Copy `skills/unslop` to `~/.claude/skills/unslop`.', installed)
                    elif source == 'product-marketing':
                        self.assertIn(b'`/product-marketing-context`', installed)
                        self.assertIn(b'`.agents/product-marketing.md`', installed)
                    else:
                        self.assertIn(b'/user-research-synthesis $ARGUMENTS', installed)
                    continue
                if relative == str(entry / 'SKILL.md'):
                    self.assertEqual(names.entry_name(installed, source), names.entry_name(original, source))
                    self.assertIn(('name: ' + (json.dumps(exposed) if claude_host else exposed) + '\n').encode(), installed)
                else:
                    self.assertEqual(installed, original)

    def roundtrip(self, adapter):
        builds, receipts, payloads, addons = self.sources()
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
            return copy.deepcopy(addons[name]) if name in addons else real_addon(name)
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

    def test_reviewed_host_invocations_leave_cli_catalogs_paths_archives_and_unreviewed_files_exact(self):
        path = 'skills/hyperframes-cli/references/init-and-scaffold.md'
        original = (b'For assets, see the `media-use` skill.\n'
                    b'`hyperframes skills` installs (/hyperframes, /media-use).\n'
                    b'CLI: `hyperframes media-use --local-only`.\n'
                    b'Source: `skills/media-use/SKILL.md`.\n')
        files = {path: (original, 0o444), 'upstream/' + path: (original, 0o444),
                 'LICENSE': (b'Original rights notice.\n', 0o444),
                 'scripts/example.sh': (b'agent-browser skills get core\n', 0o555)}
        rendered = names.expose_files('hyperframes-cli', files)
        self.assertEqual(rendered[path][0], original.replace(b'see the `media-use` skill', b'see the `hyperframes-media` skill'))
        for relative in set(files) - {path}:
            self.assertEqual(rendered[relative], files[relative])
        self.assertEqual(rendered[names.ORIGINALS + '/' + path + '.original'][0], original)
        self.assertFalse(any(Path(relative).name == 'SKILL.md' for relative in set(rendered) - set(files)))
        self.assertEqual(names.expose_files('codex-skill', {'references/commands/cli-anything.md': (b'agent-harness/cli_anything/<software>/core', 0o444)})['references/commands/cli-anything.md'][0], b'agent-harness/cli_anything/<software>/core')
        with self.assertRaisesRegex(ValueError, 'anchor missing'):
            names.expose_files('hyperframes-cli', {path: (b'Changed upstream instructions.\n', 0o444)})

    def test_gstack_function_descriptions_are_freshly_discoverable_without_changing_source_bodies(self):
        selected = dict(native.selection())
        sources, receipts = {}, {}
        for name, override in names.DESCRIPTIONS.items():
            root = self.base / name
            root.mkdir()
            original = ('---\nname: ' + name + '\ndescription: ' + override['source'] + '\n---\n'
                        'Original method body, including flags and incremental rollouts.\n').encode()
            (root / 'SKILL.md').write_bytes(original)
            (root / 'LICENSE').write_text('Original source rights.\n')
            receipt = {'content_sha256': name, 'builder_sha256': 'fixture', 'entry_dir': '.',
                       'files': {p.name: native.sha(p.read_bytes()) for p in root.iterdir()}}
            (root / '.nstack-release.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
            spec = selected[name]
            sources[(spec['candidate_id'], spec['source_path'])] = root
            receipts[root] = (receipt, {}, spec)
        state = self.base / 'state'
        with patch.object(native.nstack, 'build', side_effect=lambda candidate, path: sources[(candidate, path)]), \
                patch.object(native.nstack, 'registered_release', side_effect=lambda root: receipts[root]):
            release, index = native.prepare(state, [(name, selected[name]) for name in names.DESCRIPTIONS], [])
        for row in index:
            active = Path(row['skill_path'])
            original = (self.base / row['name'] / 'SKILL.md').read_bytes()
            self.assertEqual(active.read_bytes().split(b'---', 2)[2], original.split(b'---', 2)[2])
            port = json.loads((active.parent / names.PORT_RECEIPT).read_text())['files']['SKILL.md']
            self.assertEqual((active.parent / port['original']).read_bytes(), original)
            self.assertEqual(port['after_sha256'], native.sha(active.read_bytes()))
        (state / 'native-skill-index.json').write_text(json.dumps(index))
        helper = ROOT / 'addons/01/scripts/capabilities.py'
        found = json.loads(subprocess.check_output([sys.executable, str(helper), '--state', str(state), 'problem framing'], text=True))
        self.assertEqual([row['name'] for row in found['matches']], ['gstack-office-hours'])
        self.assertIn('design partner', found['matches'][0]['description'])


if __name__ == '__main__':
    unittest.main()
