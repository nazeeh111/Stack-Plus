"""Native removed-link repair respects the original journal parent binding."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_native_setup as fixtures

native = fixtures.native
from transaction import Transaction, fingerprint


class RepairOwnership(unittest.TestCase):
    def setUp(self):
        saved = native.nstack.STATE
        self.addCleanup(setattr, native.nstack, 'STATE', saved)

    def exercise(self, substitute):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            home = base / 'home'
            home.mkdir()
            state = base / 'state'
            fixture = fixtures.NativeSetup()
            source, leaf, receipt = fixture.fixture(base)
            parent = home / '.agents'
            original = parent / 'skills' / 'old'
            original.mkdir(parents=True)
            (original / 'dirty.txt').write_text('original dirty bytes\n')
            (parent / 'unrelated.txt').write_text('preserve sibling\n')
            agents = home / '.codex/AGENTS.md'
            agents.parent.mkdir()
            agents.write_text('original instructions\n')
            args = fixture.args(home, state)
            with patch.object(native.nstack, 'build', return_value=source), patch.object(
                native.nstack, 'registered_release', return_value=(receipt, {}, leaf)
            ):
                result = native.apply(args)
                target = parent / 'skills'
                target.unlink()
                moved = home / 'original-agents'
                parent.rename(moved)
                foreign = base / 'foreign-agents'
                foreign.mkdir()
                (foreign / 'unrelated.txt').write_text('preserve sibling\n')
                if substitute == 'directory':
                    foreign.rename(parent)
                    foreign = parent
                else:
                    parent.symlink_to(foreign, target_is_directory=True)
                foreign_before = fingerprint(foreign)
                moved_before = fingerprint(moved)
                instruction_before = agents.read_bytes()
                journal = Path(result['run']) / 'journal.json'
                journal_before = journal.read_bytes()
                with self.assertRaisesRegex(ValueError, 'parent|Linked'):
                    native.apply(args)
                self.assertEqual(fingerprint(foreign), foreign_before)
                self.assertEqual(fingerprint(moved), moved_before)
                self.assertEqual(agents.read_bytes(), instruction_before)
                self.assertEqual(journal.read_bytes(), journal_before)
                if substitute == 'directory':
                    parent.rename(base / 'preserved-foreign')
                else:
                    parent.unlink()
                moved.rename(parent)
                repaired = native.apply(args)
                self.assertTrue(repaired['repaired_removed_entry'])
                self.assertTrue(target.is_symlink())
                self.assertEqual(journal.read_bytes(), journal_before)
                self.assertEqual((parent / 'unrelated.txt').read_text(), 'preserve sibling\n')
                self.assertEqual(agents.read_bytes(), instruction_before)
                tx = Transaction(result['run'])
                with tx.lock():
                    tx.rollback()
                self.assertEqual((target / 'old/dirty.txt').read_text(), 'original dirty bytes\n')
                self.assertEqual((parent / 'unrelated.txt').read_text(), 'preserve sibling\n')
                self.assertEqual(agents.read_text(), 'original instructions\n')

    def test_identical_replacement_directory_refuses_then_repairs_original(self):
        self.exercise('directory')

    def test_linked_replacement_refuses_then_repairs_original(self):
        self.exercise('symlink')

    def test_legacy_unbound_row_refuses_automatic_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            home = base / 'home'
            home.mkdir()
            state = base / 'state'
            fixture = fixtures.NativeSetup()
            source, leaf, receipt = fixture.fixture(base)
            args = fixture.args(home, state)
            with patch.object(native.nstack, 'build', return_value=source), patch.object(
                native.nstack, 'registered_release', return_value=(receipt, {}, leaf)
            ):
                result = native.apply(args)
                target = home / '.agents/skills'
                target.unlink()
                journal = Path(result['run']) / 'journal.json'
                rows = json.loads(journal.read_text())
                row = next(row for row in rows if row['path'] == str(target))
                del row['parent']
                journal.write_text(json.dumps(rows))
                before = journal.read_bytes()
                with self.assertRaisesRegex(ValueError, 'legacy run'):
                    native.apply(args)
                self.assertFalse(target.exists())
                self.assertFalse(target.is_symlink())
                self.assertEqual(journal.read_bytes(), before)

    def test_swap_after_open_cannot_redirect_link_to_substitute(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            home = base / 'home'
            home.mkdir()
            state = base / 'state'
            fixture = fixtures.NativeSetup()
            source, leaf, receipt = fixture.fixture(base)
            args = fixture.args(home, state)
            with patch.object(native.nstack, 'build', return_value=source), patch.object(
                native.nstack, 'registered_release', return_value=(receipt, {}, leaf)
            ):
                native.apply(args)
                parent = home / '.agents'
                target = parent / 'skills'
                target.unlink()
                moved = home / 'moved-original'
                original_link = os.link
                def swap(source, destination, *args, **kwargs):
                    if destination == 'skills' and kwargs.get('dst_dir_fd') is not None:
                        parent.rename(moved)
                        parent.mkdir()
                        (parent / 'foreign.txt').write_text('foreign bytes')
                    return original_link(source, destination, *args, **kwargs)
                with patch.object(native.os, 'link', side_effect=swap):
                    with self.assertRaisesRegex(ValueError, 'parent'):
                        native.apply(args)
                self.assertFalse((parent / 'skills').exists())
                self.assertFalse((parent / 'skills').is_symlink())
                self.assertEqual((parent / 'foreign.txt').read_text(), 'foreign bytes')
                self.assertTrue((moved / 'skills').is_symlink())

    def test_occupied_leaf_is_not_overwritten_during_repair(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            home = base / 'home'
            home.mkdir()
            state = base / 'state'
            fixture = fixtures.NativeSetup()
            source, leaf, receipt = fixture.fixture(base)
            args = fixture.args(home, state)
            with patch.object(native.nstack, 'build', return_value=source), patch.object(
                native.nstack, 'registered_release', return_value=(receipt, {}, leaf)
            ):
                result = native.apply(args)
                target = home / '.agents/skills'
                target.unlink()
                journal = Path(result['run']) / 'journal.json'
                before = journal.read_bytes()
                original_link = os.link
                def occupy(source, destination, *args, **kwargs):
                    if destination == 'skills' and kwargs.get('dst_dir_fd') is not None:
                        target.write_text('concurrent foreign file')
                    return original_link(source, destination, *args, **kwargs)
                with patch.object(native.os, 'link', side_effect=occupy):
                    with self.assertRaises(FileExistsError):
                        native.apply(args)
                self.assertEqual(target.read_text(), 'concurrent foreign file')
                self.assertEqual(journal.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
