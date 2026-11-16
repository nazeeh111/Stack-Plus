"""A matching leaf is not authority to change a different containing directory."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))
import transaction
from transaction import Transaction, copy, fingerprint


class TargetOwnership(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.profile = self.root / "profile"
        self.profile.mkdir()
        self.target = self.profile / "config"
        self.target.write_text("original")
        self.run = self.root / "runs/install"

    def install(self, *, absent=False, config=False):
        if absent:
            self.target.unlink()
        tx = Transaction(self.run)
        with tx.lock():
            if config:
                self.target.write_text("owned=1\nother=1\n")
                tx.replace_file(
                    self.target, b"owned=2\nother=1\n",
                    config={"updates": [[["owned"], 2]], "retire": []},
                )
            else:
                tx.replace_file(self.target, b"installed")
        return tx

    def replace_parent(self, kind="directory"):
        self.moved = self.root / "moved-profile"
        self.profile.rename(self.moved)
        self.foreign = self.root / "foreign" if kind == "symlink" else self.profile
        self.foreign.mkdir()
        for child in self.moved.iterdir():
            copy(child, self.foreign / child.name)
        if kind == "symlink":
            self.profile.symlink_to(self.foreign, target_is_directory=True)

    def restore_parent(self):
        if self.profile.is_symlink():
            self.profile.unlink()
        else:
            self.profile.rename(self.root / "retained-foreign")
        self.moved.rename(self.profile)

    def rollback(self):
        tx = Transaction(self.run)
        with tx.lock():
            tx.rollback()

    def test_symlink_parent_rejected_without_touching_foreign_or_journal(self):
        self.install()
        self.replace_parent("symlink")
        before = fingerprint(self.foreign)
        journal = (self.run / "journal.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertEqual(fingerprint(self.foreign), before)
        self.assertEqual((self.run / "journal.json").read_bytes(), journal)
        self.assertEqual((self.moved / "config").read_text(), "installed")
        self.restore_parent()
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")

    def test_identical_leaf_in_new_directory_does_not_confer_ownership(self):
        self.install()
        self.replace_parent()
        before = fingerprint(self.foreign)
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertEqual(fingerprint(self.foreign), before)
        self.restore_parent()
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")

    def test_restore_to_absent_cannot_delete_foreign_matching_leaf(self):
        self.install(absent=True)
        self.replace_parent()
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertEqual(self.target.read_text(), "installed")
        self.restore_parent()
        self.rollback()
        self.assertFalse(self.target.exists())

    def test_retired_target_not_restored_into_replacement_directory(self):
        self.target.unlink()
        skill = self.profile / "skill"
        skill.mkdir()
        (skill / "private-work").write_text("retain this original")
        tx = Transaction(self.run)
        with tx.lock():
            tx.retire(skill)
        self.replace_parent()
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertEqual(list(self.foreign.iterdir()), [])
        self.restore_parent()
        self.rollback()
        self.assertEqual((skill / "private-work").read_text(), "retain this original")

    def test_config_inverse_never_merges_foreign_settings(self):
        self.install(config=True)
        self.replace_parent()
        self.target.write_text("owned=2\nother=99\n")
        before = fingerprint(self.target)
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertEqual(fingerprint(self.target), before)
        self.restore_parent()
        self.target.write_text("owned=2\nother=3\n")
        self.rollback()
        self.assertEqual(self.target.read_text(), "owned=1\nother=3\n")

    def test_all_pending_parents_checked_before_first_restoration(self):
        tx = self.install()
        other = self.root / "other/config"
        other.parent.mkdir()
        other.write_text("original other")
        with tx.lock():
            tx.replace_file(other, b"installed other")
        self.replace_parent()
        journal = (self.run / "journal.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertEqual(other.read_text(), "installed other")
        self.assertEqual((self.run / "journal.json").read_bytes(), journal)

    def test_staged_file_carries_original_directory_identity(self):
        tx = Transaction(self.run)
        with tx.lock():
            staged = tx.stage_file(self.target, b"installed")
            self.replace_parent()
            before = fingerprint(self.target)
            with self.assertRaisesRegex(ValueError, "parent"):
                tx.replace_file(self.target, b"installed", prepared=staged)
            self.assertEqual(fingerprint(self.target), before)
        self.assertFalse((self.run / "journal.json").exists())

    def test_prepared_restore_rechecks_parent_after_restart(self):
        tx = self.install()
        with tx.lock(), patch.object(tx, "_finish_rollback", side_effect=RuntimeError("stop before restore")):
            with self.assertRaisesRegex(RuntimeError, "stop before"):
                tx.rollback()
        self.assertEqual(json.loads((self.run / "journal.json").read_text())[0]["phase"], "rollback-prepared")
        self.replace_parent()
        stage = self.run / "rollback-stage/0"
        before = fingerprint(stage)
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertEqual(fingerprint(stage), before)
        self.assertEqual(self.target.read_text(), "installed")
        self.restore_parent()
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")

    def test_backup_preparing_retry_does_not_adopt_new_parent(self):
        original_copy = transaction.copy

        def interrupted(source, destination):
            if str(destination).endswith("/before/0"):
                raise RuntimeError("stop before backup")
            return original_copy(source, destination)

        tx = Transaction(self.run)
        with tx.lock(), patch.object(transaction, "copy", side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError, "before backup"):
                tx.replace_file(self.target, b"installed")
        self.replace_parent()
        retry = Transaction(self.run)
        with retry.lock():
            with self.assertRaisesRegex(ValueError, "parent"):
                retry.replace_file(self.target, b"installed")
        self.assertEqual(self.target.read_text(), "original")
        self.assertFalse((self.run / "before/0").exists())

    def test_missing_original_parent_blocks_recovery_until_restored(self):
        self.install()
        self.profile.rename(self.root / "moved-profile")
        with self.assertRaisesRegex(ValueError, "parent"):
            self.rollback()
        self.assertFalse(self.profile.exists())
        (self.root / "moved-profile").rename(self.profile)
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")

    def test_linked_ancestor_refused_before_staging_or_journaling(self):
        nested = self.profile / "nested"
        nested.mkdir()
        target = nested / "config"
        target.write_text("original nested")
        self.replace_parent("symlink")
        tx = Transaction(self.run)
        with tx.lock():
            with self.assertRaisesRegex(ValueError, "parent"):
                tx.replace_file(target, b"installed")
        self.assertEqual(target.read_text(), "original nested")
        self.assertFalse((self.run / "journal.json").exists())

    def test_missing_parents_valid_repeat_and_rollback(self):
        target = self.root / "fresh/nested/config"
        tx = Transaction(self.run)
        with tx.lock():
            tx.replace_file(target, b"installed")
        journal = (self.run / "journal.json").read_bytes()
        retry = Transaction(self.run)
        with retry.lock():
            retry.replace_file(target, b"installed")
        self.assertEqual((self.run / "journal.json").read_bytes(), journal)
        self.rollback()
        self.assertFalse(target.exists())

    def test_nested_targets_refused_before_retiring_an_owned_parent(self):
        tx = self.install()
        before = fingerprint(self.profile)
        with tx.lock():
            with self.assertRaisesRegex(ValueError, "Overlapping"):
                tx.retire(self.profile)
        self.assertEqual(fingerprint(self.profile), before)
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")

    def test_nested_targets_refused_without_recreating_retired_parent(self):
        tx = Transaction(self.run)
        with tx.lock():
            tx.retire(self.profile)
            with self.assertRaisesRegex(ValueError, "Overlapping"):
                tx.replace_file(self.target, b"new nested file")
        self.assertFalse(self.profile.exists())
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")

    def test_leaf_link_and_directory_exchange_preserve_originals(self):
        skill = self.profile / "skill"
        skill.mkdir()
        (skill / "work").write_text("retained")
        before = fingerprint(skill)
        link = self.profile / "leaf"
        link.symlink_to("old-target")
        link_before = fingerprint(link)
        tx = Transaction(self.run)
        with tx.lock():
            tx.link(skill, self.root / "new-target")
            tx.link(link, "new-leaf-target")
        self.assertTrue(skill.is_symlink())
        self.rollback()
        self.assertEqual(fingerprint(skill), before)
        self.assertEqual(fingerprint(link), link_before)

    def test_legacy_journal_still_restores_but_does_not_invent_historical_identity(self):
        self.install()
        journal = self.run / "journal.json"
        rows = json.loads(journal.read_text())
        for row in rows:
            row.pop("parent", None)
        journal.write_text(json.dumps(rows))
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")
        self.assertNotIn("parent", json.loads(journal.read_text())[0])

    def test_final_restore_uses_open_directory_not_redirected_path(self):
        self.install()
        original_replace = transaction.os.replace
        interrupted = False

        def moved_after_check(source, destination, *args, **kwargs):
            nonlocal interrupted
            if not interrupted and "/rollback-stage/" in str(source):
                interrupted = True
                self.replace_parent()
            return original_replace(source, destination, *args, **kwargs)

        with patch.object(transaction.os, "replace", side_effect=moved_after_check):
            with self.assertRaisesRegex(ValueError, "parent|conflict"):
                self.rollback()
        self.assertTrue(interrupted)
        self.assertEqual((self.foreign / "config").read_text(), "installed")
        self.assertEqual((self.moved / "config").read_text(), "original")
        self.restore_parent()
        self.rollback()
        self.assertEqual(self.target.read_text(), "original")

    def check_prepare_rebinding(self, kind):
        original = fingerprint(self.target)
        original_parent = self.profile.stat().st_ino
        tx = Transaction(self.run)
        real_prepare = tx.prepare

        def change_after_open(*args, **kwargs):
            self.replace_parent()
            return real_prepare(*args, **kwargs)

        def operation(current):
            if kind == "file":
                current.replace_file(self.target, b"installed")
            else:
                current.link(self.target, self.root / "desired-link")

        with tx.lock(), patch.object(tx, "prepare", side_effect=change_after_open):
            with self.assertRaises(ValueError):
                operation(tx)
        rows = json.loads((self.run / "journal.json").read_text())
        self.assertEqual(rows[0]["parent"]["inode"], original_parent)
        self.assertEqual(rows[0]["phase"], "backup-preparing")
        self.assertEqual(fingerprint(self.moved / "config"), original)
        self.assertEqual(fingerprint(self.target), original)
        retry = Transaction(self.run)
        with retry.lock():
            with self.assertRaisesRegex(ValueError, "parent"):
                operation(retry)
        self.assertEqual(fingerprint(self.target), original)
        self.assertEqual(fingerprint(self.moved / "config"), original)
        # No target-entry mutation can precede a saved prepared row. Canceling this
        # backup-only intent must not restore into either directory.
        self.rollback()
        self.assertEqual(fingerprint(self.target), original)
        self.assertEqual(fingerprint(self.moved / "config"), original)
        self.assertEqual(json.loads((self.run / "journal.json").read_text())[0]["phase"],
                         "rolled-back")

    def test_file_preparation_keeps_opened_parent_authority_on_retry(self):
        self.check_prepare_rebinding("file")

    def test_link_preparation_keeps_opened_parent_authority_on_retry(self):
        self.check_prepare_rebinding("link")

    def test_caller_prepared_file_resumes_after_original_parent_is_renamed_back(self):
        original = fingerprint(self.target)
        original_parent = self.profile.stat().st_ino
        tx = Transaction(self.run)
        real_prepare = tx.prepare

        def change_after_open(*args, **kwargs):
            self.replace_parent()
            return real_prepare(*args, **kwargs)

        with tx.lock():
            staged = tx.stage_file(self.target, b"installed")
            with patch.object(tx, "prepare", side_effect=change_after_open):
                with self.assertRaises(ValueError):
                    tx.replace_file(self.target, b"unused caller bytes", prepared=staged)
        rows = json.loads((self.run / "journal.json").read_text())
        self.assertEqual(rows[0]["parent"]["inode"], original_parent)
        self.assertEqual(rows[0]["before"], original)
        self.restore_parent()
        retry = Transaction(self.run)
        with retry.lock():
            retry.replace_file(self.target, b"installed")
            self.assertEqual(len(retry.rows), 1)
            self.assertEqual(retry.rows[0]["parent"]["inode"], original_parent)
        self.assertEqual(self.target.read_text(), "installed")
        self.rollback()
        self.assertEqual(fingerprint(self.target), original)
        self.assertEqual((self.root / "retained-foreign/config").read_text(), "original")


if __name__ == "__main__":
    unittest.main()
