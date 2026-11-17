"""Provenance and review-fixture integrity, not simulated model application."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT/'addons/game-systems-review'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class GameSystemsReview(unittest.TestCase):
    def test_full_original_closure_and_mit_notice(self):
        receipt = json.loads((ADDON/'SOURCE.json').read_text())
        self.assertEqual(receipt['repository'], 'Donchitos/Claude-Code-Game-Studios')
        self.assertEqual(receipt['revision'], 'abc0de79d6ceb0b5d7aa693945849b3937afbe6a')
        self.assertEqual(len(receipt['upstream_files']), 16)
        recorded = set(receipt['upstream_files'])
        actual = {str(p.relative_to(ADDON)) for p in (ADDON/'upstream').rglob('*') if p.is_file()}
        self.assertEqual(actual, recorded)
        for path, row in receipt['upstream_files'].items():
            original = ADDON/path
            self.assertFalse(original.is_symlink())
            self.assertEqual(sha(original), row['sha256'], path)
            self.assertEqual(original.stat().st_size, row['bytes'], path)
        self.assertEqual((ADDON/'LICENSE').read_bytes(), (ADDON/'upstream/LICENSE').read_bytes())
        self.assertIn('Copyright (c) 2026 Donchitos', (ADDON/'LICENSE').read_text())

    def test_all_adaptations_replay_from_full_originals(self):
        receipt = json.loads((ADDON/'SOURCE.json').read_text())
        self.assertEqual(len(receipt['adapted_files']), 10)
        for destination, row in receipt['adapted_files'].items():
            original = ADDON/'upstream'/row['source_path']
            self.assertEqual(sha(original), row['source_sha256'])
            self.assertEqual(sha(ADDON/destination), row['active_sha256'])
            self.assertEqual(sha(ADDON/row['diff']), row['diff_sha256'])
            with tempfile.TemporaryDirectory(prefix='game-review-replay-', dir='/private/tmp') as tmp:
                target = Path(tmp)/destination
                target.parent.mkdir(parents=True)
                target.write_bytes(original.read_bytes())
                subprocess.run(['git', 'apply', '--check', str(ADDON/row['diff'])], cwd=tmp,
                               check=True, capture_output=True)
                subprocess.run(['git', 'apply', str(ADDON/row['diff'])], cwd=tmp,
                               check=True, capture_output=True)
                self.assertEqual(target.read_bytes(), (ADDON/destination).read_bytes(), destination)

    def test_declared_native_files_are_closed_and_linked(self):
        receipt = json.loads((ADDON/'SOURCE.json').read_text())
        declared = set(receipt['upstream_files']) | set(receipt['adapted_files'])
        declared |= {row['diff'] for row in receipt['adapted_files'].values()}
        declared |= set(receipt['authored_native_files']) | {'SOURCE.json', 'LICENSE'}
        actual = {str(p.relative_to(ADDON)) for p in ADDON.rglob('*') if p.is_file()}
        self.assertEqual(actual, declared)
        for relative, row in receipt['authored_native_files'].items():
            self.assertEqual(sha(ADDON/relative), row['sha256'], relative)
        for path in [ADDON/'SKILL.md', ADDON/'NATIVE-BINDINGS.md', *list((ADDON/'references').rglob('*.md'))]:
            text = path.read_text()
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((path.parent/link.split('#')[0]).is_file(), (path, link))
            self.assertNotRegex(text, r'(?m)^(model:|allowed-tools:|tools:|memory:|!`bash)')
        self.assertFalse(any(p.is_symlink() for p in ADDON.rglob('*')))

    def test_domain_checklists_and_report_contract_are_retained(self):
        original = ADDON/'upstream/.claude/skills/review-all-gdds/references'
        active = ADDON/'references/cross-gdd'
        # These checklists are the contribution being retained. Adaptations may
        # change native callbacks and qualify theory, never remove a checklist.
        for name in ['2-consistency', '3-design-holism', '4-scenarios']:
            headings = lambda text: re.findall(r'^### [234][a-z]:.+$', text, re.M)
            self.assertEqual(headings((original/(name+'.md')).read_text()),
                             headings((active/(name+'.md')).read_text()))
        old = (original/'5-report.md').read_text().split('## Phase 5:', 1)[1]
        new = (active/'5-report.md').read_text().split('## Phase 5:', 1)[1]
        self.assertEqual(old, new)
        for name in ['balance-check.md', 'cross-gdd-review.md']:
            source = 'balance-check' if name.startswith('balance') else 'review-all-gdds'
            old = (ADDON/f'upstream/.claude/skills/{source}/SKILL.md').read_text()
            new = (ADDON/'references'/name).read_text()
            self.assertEqual(re.findall(r'^## Phase \d+:.*$', old, re.M),
                             re.findall(r'^## Phase \d+:.*$', new, re.M))

    def test_review_fixture_has_reproducible_numeric_controls(self):
        case = ADDON/'fixtures/review-case'
        combat = json.loads((case/'data/combat.json').read_text())
        self.assertGreater(combat['weapon_damage'], 110)
        self.assertLess(combat['weapon_damage'], 200)
        self.assertGreater(combat['kill_gold'], 12)
        self.assertEqual(combat['kill_gold'] * combat['shared_reward_multiplier']**2, 400)
        self.assertEqual(10*combat['kill_gold']-50, 950)
        # The old-heading/no-summary input must remain in the review denominator.
        gdds = [p for p in (case/'design/gdd').glob('*.md')
                if p.stem not in ('systems-index', 'game-pillars', 'game-concept')]
        self.assertEqual(sorted(p.name for p in gdds), ['combat.md', 'economy.md'])
        self.assertNotIn('## Summary', (case/'design/gdd/combat.md').read_text())
        self.assertIn('## Detailed Design', (case/'design/gdd/economy.md').read_text())
        clean = json.loads((ADDON/'fixtures/consistent-case/data/config.json').read_text())
        self.assertEqual(clean, {'weapon_damage': 100, 'kill_gold': 10, 'death_loss': 5, 'shield_cost': 15})

    def test_expertise_exclusions_preserve_the_source_boundary(self):
        original = (ADDON/'upstream/.claude/agents/game-designer.md').read_text()
        source_exclusions = original.split('### What This Agent Must NOT Do', 1)[1].split('### Delegation Map', 1)[0]
        active = (ADDON/'references/game-designer.md').read_text()
        exclusions = active.split('### Outside this expertise scope', 1)[1].split('### Expertise boundaries', 1)[0]
        self.assertIn('These are exclusions, not assignments:', exclusions)
        # Each prohibited responsibility remains an exclusion, despite removal
        # of foreign department/dispatch assumptions from its explanation.
        for action in re.findall(r'^- (Write implementation code|Make art or audio direction decisions|Write final narrative content|Make architecture or technology choices|Approve scope changes)', source_exclusions, re.M):
            self.assertIn('- '+action, exclusions)
        self.assertNotIn('### Expertise scope\n', active)

    def test_edge_only_fixture_cannot_be_covered_by_the_old_section_whitelist(self):
        case = ADDON/'fixtures/edge-only-case/design/gdd'
        combat = (case/'combat.md').read_text()
        economy = (case/'economy.md').read_text()
        ordinary, edge_rules = economy.split('## Edge Cases\n', 1)
        # The contradictory overrides are raw rules only in the formerly
        # omitted section, with no reference that could trigger old escalation.
        self.assertNotIn('Null Seal', ordinary)
        self.assertNotIn('Edge Cases', ordinary)
        self.assertIn('zero final damage', edge_rules)
        self.assertIn('suppresses all requested gold loss', edge_rules)
        self.assertIn('final_damage = max(10, modified_damage)', combat)
        self.assertIn('death_loss = min(current_gold, 25)', combat)
        for document in [combat, ordinary]:
            self.assertIn('## Dependencies', document)
            self.assertIn('## Acceptance Criteria', document)
            self.assertRegex(document, r'## Detailed (Rules|Design)')
        loader = (ADDON/'references/cross-gdd/1-load.md').read_text()
        self.assertIn('|Edge Cases|', loader)
        self.assertNotIn('Edge Cases feeds no', loader)


if __name__ == '__main__':
    unittest.main()
