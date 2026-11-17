"""Offline source/package fidelity only, not tests of model routing intelligence."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import native_setup as native
from closure import validate

ADDON = ROOT / 'addons/agent-orchestration'


class OrchestrationTierFidelity(unittest.TestCase):
    def test_empty_profile_contains_no_model_or_budget_authority(self):
        profile = json.loads((ADDON / 'examples/tier-profile.json').read_text())
        self.assertEqual(profile['schema_version'], 1)
        self.assertEqual(set(profile['tiers']), {'Y', 'Z'})
        for tier in profile['tiers'].values():
            self.assertEqual(set(tier), {'requested_selector', 'requested_effort_or_variant',
                                         'user_authority', 'availability_evidence',
                                         'tool_context_limits', 'observed_task_results'})
            self.assertEqual(tier['observed_task_results'], [])
            self.assertTrue(all(value is None for key, value in tier.items()
                                if key != 'observed_task_results'))
        self.assertIsNone(profile['task_scope'])
        self.assertTrue(all(value is None for value in profile['task_caps'].values()))
        self.assertFalse(any(p.suffix in {'.py', '.sh', '.toml', '.yaml', '.yml'}
                             for p in ADDON.rglob('*') if p.is_file()))

    def test_native_exposure_preserves_complete_support_and_inert_profile(self):
        name = native.skill_names.canonical('agent-orchestration')
        self.assertEqual(name, 'multi-model-agent-orchestration')
        spec = native.addon_definition('agent-orchestration')
        spec['exposure_name'] = name
        files = native.addon_files(spec)
        self.assertTrue({'references/tiers-and-quality.md', 'examples/tier-profile.json',
                         'references/hosts.md', 'references/dispatch-and-review.md',
                         'SOURCE.json', 'LICENSE'} <= set(files))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            for rel, (data, _) in files.items():
                target = out / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            validate(out)
            for rel in ('references/tiers-and-quality.md', 'examples/tier-profile.json',
                        'references/hosts.md', 'references/dispatch-and-review.md',
                        'SOURCE.json', 'LICENSE'):
                self.assertEqual((out / rel).read_bytes(), (ADDON / rel).read_bytes())
            # Frontmatter naming is the intended adaptation; method body is intact.
            source_body = (ADDON / 'SKILL.md').read_text().split('\n---\n', 1)[1]
            adapted = (out / 'SKILL.md').read_text()
            self.assertIn('name: multi-model-agent-orchestration\n', adapted)
            self.assertEqual(adapted.split('\n---\n', 1)[1], source_body)

    def test_missing_tier_support_is_detected_by_actual_closure_validator(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'addon'
            shutil.copytree(ADDON, out)
            (out / 'references/tiers-and-quality.md').unlink()
            with self.assertRaisesRegex(ValueError, 'Unresolved closure link'):
                validate(out)

    def test_linked_profile_cannot_enter_native_source_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            out = base / 'addons/agent-orchestration'
            shutil.copytree(ADDON, out)
            profile = out / 'examples/tier-profile.json'
            outside = base / 'outside.json'
            outside.write_bytes(profile.read_bytes())
            profile.unlink()
            profile.symlink_to(outside)
            with patch.object(native, 'ROOT', base):
                with self.assertRaisesRegex(ValueError, 'Linked addon source'):
                    native.addon_definition('agent-orchestration')


if __name__ == '__main__':
    unittest.main()
