"""Offline transaction/privacy controls. Not evidence of native model delivery."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "integrations/knowledge-continuity"
# macOS SDK sys/stat.h defines UF_TRACKED=0x40 for document-ID handling.
# This allowance is only for observations after capture has returned, never guards.
UF_TRACKED_LATER_OBSERVATION = 0x00000040
spec = importlib.util.spec_from_file_location("knowledge_continuity", SOURCE / "knowledge.py")
k = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k)


class KnowledgeContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="nstack-knowledge-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "Knowledge"
        self.vault.mkdir()
        self.state = self.root / "state"
        self.state.mkdir()
        self.git = str(Path(shutil.which("git")).resolve())
        self.g("init", "-q")
        self.g("config", "user.name", "Fixture Owner")
        self.g("config", "user.email", "fixture@example.invalid")
        (self.vault / "existing.md").write_text("unchanged\n")
        self.g("add", "existing.md")
        self.g("commit", "-qm", "Initial fixture")
        self.obsidian = self.root / "obsidian"
        self.obsidian.write_text(f"#!{sys.executable}\nimport pathlib,sys\np=next(x[5:] for x in sys.argv if x.startswith('path='))\nsys.stdout.buffer.write(pathlib.Path(p).read_bytes())\n")
        self.obsidian.chmod(0o700)
        self.cfg = {"version": 1, "enabled": True, "owner": "Fixture Owner", "vault": str(self.vault), "vault_name": "Knowledge", "state": str(self.state), "obsidian": str(self.obsidian), "git": self.git}
        self.source = self.root / "source.md"
        self.source.write_text("Observed fixture decision supported by source.\n")
        self.candidate = {"version": 1, "note": "Projects/Fixture.md", "note_id": "project-fixture", "scope": "fixture project", "source_kind": "file", "source": str(self.source), "source_sha256": k.digest(self.source.read_bytes()), "source_revision": "fixture-v1", "event_date": "2026-11-15", "expected_sha256": None, "expected_generation": 0, "body": "# Fixture\n\nKeep supported decisions with their source.\n", "reason": "Record a verified reusable fixture decision."}

    def g(self, *args):
        return subprocess.run([self.git, *args], cwd=self.vault, capture_output=True, check=True).stdout

    def test_standalone_writer_saves_and_replays_outside_project(self):
        settings = self.root / "settings.json"
        settings.write_text(json.dumps(self.cfg))
        candidate = self.root / "candidate.json"
        candidate.write_text(json.dumps(self.candidate))
        (self.vault / "existing.md").write_text("keep staged bytes\n")
        self.g("add", "existing.md")
        (self.vault / "existing.md").write_text("keep working bytes\n")
        before = self.g("diff", "--cached", "--binary")
        command = [sys.executable, "-I", "-B", str(SOURCE / "knowledge.py"),
                   "--settings", str(settings), "capture", "--candidate", str(candidate),
                   "--host", "codex", "--session", "fixture-session", "--event", "fixture-event"]

        def invoke():
            result = subprocess.run(command, cwd=self.root, capture_output=True, timeout=30,
                                    env={"PATH": os.defpath, "GIT_CONFIG_NOSYSTEM": "1",
                                         "GIT_CONFIG_GLOBAL": os.devnull})
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            return json.loads(result.stdout)

        saved = invoke()
        note = (self.vault / self.candidate["note"]).read_bytes()
        meta, body = k.metadata(note)
        key = k.identity("codex", "fixture-session", "fixture-event")
        self.assertEqual((saved["status"], saved["key"], saved["note_sha256"]),
                         ("saved", key, k.digest(note)))
        self.assertEqual((meta["capture_event"], meta["source_sha256"], meta["generation"]),
                         (key, self.candidate["source_sha256"], "1"))
        self.assertEqual(body.strip(), self.candidate["body"].strip())
        self.assertEqual(self.g("show", "HEAD:" + self.candidate["note"]), note)
        self.assertEqual(invoke(), saved)
        self.assertEqual(self.g("rev-parse", "HEAD").decode().strip(), saved["checkpoint"])
        self.assertEqual(self.g("diff", "--cached", "--binary"), before)
        self.assertEqual((self.vault / "existing.md").read_text(), "keep working bytes\n")

    def test_writer_uses_own_dependency_without_touching_other_imports(self):
        before = list(sys.path)
        other = SimpleNamespace()
        with patch.dict(sys.modules, {"transaction_paths": other}):
            fs = k.filesystem_tools()
            self.assertEqual(fs.parent_identity.__globals__["__file__"], str(ROOT / "lib/transaction_paths.py"))
            self.assertIs(sys.modules["transaction_paths"], other)
            self.assertEqual(before, sys.path)

    def test_redirected_writer_dependency_rejects_before_creating_event_journal(self):
        library = self.root / "release/lib"
        library.mkdir(parents=True)
        (library / "transaction_paths.py").symlink_to(ROOT / "lib/transaction_paths.py")
        writer = library.parent / "integrations/knowledge-continuity/knowledge.py"
        with patch.object(k, "__file__", str(writer)), self.assertRaisesRegex(k.Rejected, "symlink/noncanonical"):
            self.save()
        self.assertFalse((self.state / "transactions" / k.identity("codex", "session1", "turn1")).exists())
        self.assertFalse((self.vault / self.candidate["note"]).exists())

    def test_reuse_private_empty_interrupted_journal(self):
        transactions = k.transaction_root(self.state)
        journal = transactions / k.identity("codex", "session1", "turn1")
        journal.mkdir(mode=0o700)
        self.assertEqual(self.save()["status"], "saved")
        self.assertTrue((self.vault / self.candidate["note"]).is_file())

    def test_preserve_partial_interrupted_journal(self):
        transactions = k.transaction_root(self.state)
        journal = transactions / k.identity("codex", "session1", "turn1")
        journal.mkdir(mode=0o700)
        (journal / "before.md").write_text("preexisting recovery evidence")
        with self.assertRaisesRegex(k.Rejected, "requires reviewed recovery"):
            self.save()
        self.assertEqual((journal / "before.md").read_text(), "preexisting recovery evidence")
        self.assertFalse((self.vault / self.candidate["note"]).exists())

    def save(self, candidate=None, *, host="codex", event="turn1", verify=False):
        return k.capture(self.cfg, candidate or self.candidate, host, "session1", event, verify_obsidian=verify)

    def current(self, body=None):
        candidate = copy.deepcopy(self.candidate)
        raw = (self.vault / candidate["note"]).read_bytes()
        meta, _ = k.metadata(raw)
        candidate.update(expected_sha256=k.digest(raw), expected_generation=int(meta["generation"]))
        if body:
            candidate["body"] = body
        return candidate

    def assert_post_capture_snapshot(self, actual, expected):
        observed = copy.deepcopy(actual)
        flags = expected["metadata"]["flags"]
        self.assertIn(observed["metadata"]["flags"], (flags, flags | UF_TRACKED_LATER_OBSERVATION))
        observed["metadata"]["flags"] = flags
        self.assertEqual(observed, expected)

    def test_later_snapshot_allowance_is_additive_tracked_bit_only(self):
        expected = {"kind": "file", "sha256": "a" * 64, "metadata": {"flags": 1, "mode": 0o640, "uid": 1000, "gid": 1000, "acl_sha256": "b" * 64, "xattrs": {"user.fixture": "c" * 64}}}
        additive = copy.deepcopy(expected)
        additive["metadata"]["flags"] |= UF_TRACKED_LATER_OBSERVATION
        self.assert_post_capture_snapshot(additive, expected)
        for changed_flags in (0, 128, 129, 193):
            bad = copy.deepcopy(expected); bad["metadata"]["flags"] = changed_flags
            with self.subTest(flags=changed_flags), self.assertRaises(AssertionError):
                self.assert_post_capture_snapshot(bad, expected)
        with self.assertRaises(AssertionError):
            self.assert_post_capture_snapshot(expected, additive)  # A removed tracked bit is forbidden.
        for field, value in (("mode", 0o600), ("uid", 1001), ("gid", 1001), ("acl_sha256", "d" * 64), ("xattrs", {})):
            bad = copy.deepcopy(additive); bad["metadata"][field] = value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                self.assert_post_capture_snapshot(bad, expected)
        bad = copy.deepcopy(additive); bad["sha256"] = "e" * 64
        with self.assertRaises(AssertionError): self.assert_post_capture_snapshot(bad, expected)

    def test_late_checkpoint_observation_is_one_read_with_private_evidence(self):
        expected = {"kind": "file", "sha256": "a" * 64, "metadata": {"flags": 1, "mode": 0o640, "uid": 1000, "gid": 1000, "acl_sha256": "b" * 64, "xattrs": {"user.fixture": "c" * 64}}}
        observed = copy.deepcopy(expected); observed["metadata"]["flags"] |= 0x40
        fake = SimpleNamespace(fingerprint=Mock(return_value=observed))
        journal = self.state / "one-observation"; journal.mkdir()
        with patch.object(k.sys, "platform", "darwin"), patch.object(k.stat, "UF_TRACKED", 0x40, create=True):
            result, classification = k.verify_late_checkpoint(fake, self.root / "fixture.md", expected, journal)
        self.assertIs(result, observed)
        self.assertEqual(classification, "darwin-uf-tracked-added")
        self.assertEqual(fake.fingerprint.call_count, 1)
        proof = k.load_json(journal / "late-verification.json")
        self.assertEqual((proof["expected"], proof["observed"]), (expected, observed))
        self.assertEqual(proof["phase"], "post-checkpoint")

    def test_late_checkpoint_allowance_rejects_all_other_changes_and_unknown_platform(self):
        expected = {"kind": "file", "sha256": "a" * 64, "metadata": {"flags": 1, "mode": 0o640, "uid": 1000, "gid": 1000, "acl_sha256": "b" * 64, "xattrs": {"user.fixture": "c" * 64}}}
        observed = copy.deepcopy(expected); observed["metadata"]["flags"] |= 0x40
        with patch.object(k.sys, "platform", "darwin"), patch.object(k.stat, "UF_TRACKED", 0x40, create=True):
            self.assertEqual(k.late_checkpoint_result(expected, expected), "exact")
            self.assertEqual(k.late_checkpoint_result(expected, observed), "darwin-uf-tracked-added")
            self.assertEqual(k.late_checkpoint_result(observed, expected), "rejected")
            for flags in (0, 0x40, 0x81, 0xC1):
                bad = copy.deepcopy(observed); bad["metadata"]["flags"] = flags
                self.assertEqual(k.late_checkpoint_result(expected, bad), "rejected")
            for key, value in (("mode", 0o600), ("uid", 1001), ("gid", 1001), ("acl_sha256", "d" * 64), ("xattrs", {})):
                bad = copy.deepcopy(observed); bad["metadata"][key] = value
                self.assertEqual(k.late_checkpoint_result(expected, bad), "rejected")
            bad = copy.deepcopy(observed); bad["sha256"] = "e" * 64
            self.assertEqual(k.late_checkpoint_result(expected, bad), "rejected")
            journal = self.state / "rejected-observation"; journal.mkdir()
            with self.assertRaises(k.Rejected):
                k.verify_late_checkpoint(SimpleNamespace(fingerprint=lambda _: bad), self.root / "fixture.md", expected, journal)
            self.assertEqual(k.load_json(journal / "late-verification.json")["result"], "rejected")
        with patch.object(k.sys, "platform", "linux"):
            self.assertEqual(k.late_checkpoint_result(expected, observed), "rejected")
        with patch.object(k.sys, "platform", "darwin"), patch.object(k.stat, "UF_TRACKED", 0x80, create=True):
            self.assertEqual(k.late_checkpoint_result(expected, observed), "rejected")

    @unittest.skipUnless(sys.platform == "darwin", "Darwin checkpoint tracking seam")
    def test_checkpoint_tracking_addition_seam_preserves_bytes_and_saves_honest_receipt(self):
        fs = k.filesystem_tools(); original_fp = fs.fingerprint; original_run = k.run
        target = self.vault / self.candidate["note"]; phase = {"checkpointed": False}
        def observation(path):
            value = original_fp(path)
            if path == target and value.get("kind") == "file":
                value = copy.deepcopy(value); value["metadata"]["flags"] &= ~0x40
                if phase["checkpointed"]: value["metadata"]["flags"] |= 0x40
            return value
        def command(argv, **kwargs):
            result = original_run(argv, **kwargs)
            if "commit" in argv: phase["checkpointed"] = True
            return result
        fs.fingerprint = observation
        with patch.object(k, "filesystem_tools", return_value=fs), patch.object(k, "run", side_effect=command):
            result = self.save()
        proof = k.load_json(self.state / "transactions" / result["key"] / "late-verification.json")
        self.assertEqual(result["late_verification"], "darwin-uf-tracked-added")
        self.assertEqual((proof["expected"]["metadata"]["flags"], proof["observed"]["metadata"]["flags"]), (0, 0x40))
        self.assertEqual(self.g("show", "HEAD:" + self.candidate["note"]), target.read_bytes())
        # The old unchanged exact comparator rejects this deterministic final seam.
        old_fs = k.filesystem_tools(); old_fs.fingerprint = lambda _: proof["observed"]
        with self.assertRaises(ValueError): old_fs.same(target, proof["expected"])

    def test_prewrite_tracked_bit_change_is_still_rejected_before_replacement(self):
        self.save()
        candidate = self.current("# Fixture\n\nPrewrite concurrent-flag control.\n")
        target = self.vault / candidate["note"]; before = target.read_bytes(); head = self.g("rev-parse", "HEAD")
        fs = k.filesystem_tools(); original_fp = fs.fingerprint; original_json = k.atomic_json; phase = {"prepared": False}
        def observation(path):
            value = original_fp(path)
            if value.get("kind") == "file":
                value = copy.deepcopy(value); value["metadata"]["flags"] &= ~0x40
                if path == target and phase["prepared"]: value["metadata"]["flags"] |= 0x40
            return value
        def transaction_written(path, data):
            original_json(path, data)
            if path.name == "transaction.json": phase["prepared"] = True
        fs.fingerprint = observation
        with patch.object(k, "filesystem_tools", return_value=fs), patch.object(k, "atomic_json", side_effect=transaction_written), patch.object(k, "verify_late_checkpoint", wraps=k.verify_late_checkpoint) as final_check:
            with self.assertRaisesRegex(ValueError, "Concurrent change"):
                self.save(candidate, event="prewrite-flag")
            self.assertEqual(final_check.call_count, 0)
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(self.g("rev-parse", "HEAD"), head)
        self.assertIsNone(k.read_receipt(self.cfg, k.identity("codex", "session1", "prewrite-flag")))

    def test_save_requires_matching_file_and_private_path_checkpoint(self):
        result = self.save()
        raw = (self.vault / self.candidate["note"]).read_bytes()
        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["obsidian_index"], "deferred")
        self.assertEqual(result["note_sha256"], k.digest(raw))
        self.assertEqual(self.g("show", "HEAD:" + self.candidate["note"]), raw)
        journal = self.state / "transactions" / result["key"]
        self.assertEqual((journal / "before.md").read_bytes(), (journal / "restore-rehearsal.md").read_bytes())
        self.assertEqual(self.g("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").decode().strip(), self.candidate["note"])
        self.assertNotIn("co-authored", self.g("log", "-1", "--format=%B").decode().lower())

    def test_closed_app_route_never_calls_obsidian(self):
        self.cfg["obsidian"] = str(self.root / "absent-app-command")
        self.assertEqual(self.save()["obsidian_index"], "deferred")

    def test_explicit_native_readback_success_and_failure_separate_from_persistence(self):
        self.assertEqual(self.save(verify=True)["obsidian_index"], "verified")
        self.obsidian.write_text("#!/bin/sh\nexit 17\n")
        result = self.save(self.current("# Fixture\n\nCorrection.\n"), event="turn2", verify=True)
        self.assertEqual((result["status"], result["obsidian_index"]), ("saved", "failed"))

    def test_replayed_event_and_both_host_duplicate_do_not_increment(self):
        first = self.save()
        self.assertEqual(self.save(), first)
        checkpoint = self.g("rev-parse", "HEAD")
        duplicate = self.save(self.current(), host="opencode", event="message2")
        self.assertEqual((duplicate["status"], duplicate["reason"]), ("skip", "duplicate"))
        self.assertEqual(self.g("rev-parse", "HEAD"), checkpoint)
        altered = copy.deepcopy(self.candidate)
        altered["body"] = "# Different body"
        with self.assertRaises(k.Rejected): self.save(altered)

    def test_optional_skip_does_not_prevent_later_useful_same_event_capture(self):
        k.receipt(self.cfg, "codex", "session1", "turn1", "skip", reason="no-useful-knowledge")
        saved = self.save()
        self.assertEqual(saved["status"], "saved")
        self.assertEqual(self.save(), saved)
        changed = {**self.candidate, "body": "# Different later input\n"}
        with self.assertRaises(k.Rejected): self.save(changed)
        self.assertEqual(k.read_receipt(self.cfg, saved["key"]), saved)

    def test_optional_duplicate_skip_can_be_followed_by_same_event_correction(self):
        self.save(event="initial")
        duplicate = self.save(self.current(), event="later")
        self.assertEqual((duplicate["status"], duplicate["reason"]), ("skip", "duplicate"))
        correction = self.current("# Fixture\n\nA useful later correction.\n")
        saved = self.save(correction, event="later")
        self.assertEqual((saved["status"], saved["generation"]), ("saved", 2))

    def test_correction_preserves_stable_id_aliases_and_preimage(self):
        self.save()
        note = self.vault / self.candidate["note"]
        note.write_text(note.read_text().replace("\n---\n# Fixture", '\naliases:\n- Fixture alias\n---\n# Fixture'))
        before = note.read_bytes()
        result = self.save(self.current("# Fixture\n\nCorrected conclusion.\n"), host="opencode", event="message2")
        meta, body = k.metadata(note.read_bytes())
        self.assertEqual(meta["note_id"], "project-fixture")
        self.assertEqual(meta["generation"], "2")
        self.assertIn("Fixture alias", note.read_text())
        self.assertIn("generation 1", meta["supersedes"])
        self.assertEqual((self.state / "transactions" / result["key"] / "before.md").read_bytes(), before)

    def test_unrelated_staged_and_dirty_bytes_preserved(self):
        (self.vault / "staged.md").write_text("staged private work\n")
        self.g("add", "staged.md")
        (self.vault / "existing.md").write_text("dirty private work\n")
        staged = self.g("diff", "--cached", "--binary")
        self.save()
        self.assertEqual(self.g("diff", "--cached", "--binary"), staged)
        self.assertEqual((self.vault / "existing.md").read_bytes(), b"dirty private work\n")

    def test_stale_generation_scope_source_and_hash_reject_without_writes(self):
        self.save()
        good = self.current("# Correction\n")
        before = (self.vault / good["note"]).read_bytes()
        for field, value in [("expected_generation", 99), ("scope", "other scope"), ("expected_sha256", "0"*64), ("source_sha256", "0"*64), ("note_id", "wrong-note")]:
            with self.subTest(field=field):
                bad = {**good, field: value}
                with self.assertRaises(k.Rejected): self.save(bad, event="bad" + field)
                self.assertEqual((self.vault / good["note"]).read_bytes(), before)

    def test_conflict_appearing_during_preparation_is_preserved(self):
        self.save()
        candidate = self.current("# Correction\n")
        note = self.vault / candidate["note"]
        original = k.atomic_json
        def racing(path, data):
            original(path, data)
            if path.name == "transaction.json": note.write_text("user's newer independent bytes\n")
        with patch.object(k, "atomic_json", side_effect=racing):
            with self.assertRaisesRegex(k.Rejected, "changed during preparation"):
                self.save(candidate, event="race")
        self.assertEqual(note.read_bytes(), b"user's newer independent bytes\n")

    def test_native_git_hook_denial_is_not_bypassed_or_reported_saved(self):
        hook = self.vault / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nexit 17\n"); hook.chmod(0o700)
        with self.assertRaises(k.Rejected): self.save()
        self.assertIsNone(k.read_receipt(self.cfg, k.identity("codex", "session1", "turn1")))
        self.assertTrue((self.state / "transactions" / k.identity("codex", "session1", "turn1") / "candidate.md").exists())
        self.assertNotIn("Fixture.md", self.g("ls-tree", "-r", "--name-only", "HEAD").decode())

    def test_checkpoint_wrong_bytes_never_get_saved_receipt(self):
        real_run = k.run
        def wrong(argv, **kwargs):
            if "show" in argv: return b"wrong checkpoint"
            return real_run(argv, **kwargs)
        with patch.object(k, "run", side_effect=wrong):
            with self.assertRaisesRegex(k.Rejected, "checkpoint bytes mismatch"): self.save()
        self.assertIsNone(k.read_receipt(self.cfg, k.identity("codex", "session1", "turn1")))

    def test_writer_lock_conflict_does_not_touch_note(self):
        import fcntl
        with (self.state / "writer.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError): self.save()
        self.assertFalse((self.vault / self.candidate["note"]).exists())

    def test_duplicate_stable_id_at_another_path_and_unknown_state_rejected(self):
        self.save()
        bad = {**self.candidate, "note": "Projects/Duplicate.md"}
        with self.assertRaisesRegex(k.Rejected, "stable note ID"):
            k.prepare(self.cfg, bad, "opencode", "session2", "event2")
        note = self.vault / self.candidate["note"]
        note.write_text(note.read_text().replace('state: "current"', 'state: "unrecognized"'))
        with self.assertRaises(k.Rejected): self.save(self.current("# Correction\n"), event="wrong-state")

    def test_receipt_ledger_bounded_and_saved_receipt_cannot_be_overwritten(self):
        for n in range(513):
            key = k.identity("codex", "session1", f"turn{n}")
            k.atomic_json(self.state / "receipts" / (key + ".json"), {"version": 1, "key": key, "host": "codex", "status": "skip"})
        k.receipt(self.cfg, "codex", "session1", "latest", "skip", reason="no-useful-knowledge")
        self.assertEqual(len(list((self.state / "receipts").glob("*.json"))), 512)
        self.save()
        with self.assertRaisesRegex(k.Rejected, "immutable"):
            k.receipt(self.cfg, "codex", "session1", "turn1", "skip", reason="duplicate")

    def test_remote_or_staged_target_denies_before_mutation(self):
        self.g("remote", "add", "fixture", "https://example.invalid/private")
        with self.assertRaises(k.Rejected): self.save()
        self.assertFalse((self.vault / self.candidate["note"]).exists())
        self.g("remote", "remove", "fixture")
        self.save()
        candidate = self.current("# Changed\n")
        self.g("add", "-f", "--", self.candidate["note"])
        note = self.vault / self.candidate["note"]
        note.write_bytes(note.read_bytes() + b"user staged change\n")
        self.g("add", "--", self.candidate["note"])
        with self.assertRaises(k.Rejected): self.save(self.current("# Another\n"), event="staged")

    def test_current_context_is_attribution_without_invented_file_verification(self):
        candidate = {**self.candidate, "source_kind": "current-context", "source": "codex:session1:turn1", "source_sha256": None, "source_revision": "current-context"}
        self.save(candidate)
        note = (self.vault / candidate["note"]).read_text()
        self.assertIn("no independent file verification", note)
        self.assertIn('source_sha256: null', note)
        bad = {**candidate, "source": "codex:other:other"}
        with self.assertRaises(k.Rejected): k.prepare(self.cfg, bad, "codex", "session1", "new")

    def test_symlink_traversal_fifo_credential_and_false_booleans_rejected(self):
        other = self.root / "outside.md"; other.write_text("protected\n")
        (self.vault / "linked.md").symlink_to(other)
        fifo = self.root / "fifo"; os.mkfifo(fifo)
        variants = [{"note": "../outside.md"}, {"note": "linked.md"}, {"source": str(fifo)}, {"source": str(self.root / "auth.json")}, {"expected_generation": False}, {"version": True}, {"body": "token sk-proj-" + "a"*30}]
        for changed in variants:
            with self.subTest(changed=list(changed)):
                with self.assertRaises((k.Rejected, OSError)):
                    k.prepare(self.cfg, {**self.candidate, **changed}, "codex", "session1", "turn1")
        self.assertEqual(other.read_text(), "protected\n")

    def test_codex_passive_identity_has_no_state_lookup_or_routine_work(self):
        class Payload(dict):
            def get(self, key, default=None):
                if key in {"prompt", "transcript_path", "last_assistant_message", "model"}:
                    raise AssertionError("content-bearing field accessed")
                return super().get(key, default)
        payload = Payload(hook_event_name="UserPromptSubmit", cwd=str(self.root), session_id="session1", turn_id="turn1", prompt="NEVER_COPY", transcript_path="/not/readable")
        with patch.object(k, "read_receipt", side_effect=AssertionError("receipt lookup")), patch.object(k, "receipt", side_effect=AssertionError("routine receipt")), patch.object(k, "regular_bytes", side_effect=AssertionError("file read")):
            result = k.event(self.cfg, payload)
        output = result["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(output.splitlines()[0], "Knowledge event: host=codex session=session1 event=turn1.")
        self.assertEqual(output.splitlines()[1], k.CUE)
        self.assertLessEqual(len(k.CUE.split()), 18)
        for unwanted in ("receipt_key", "skip", "Read ", "before finishing", "nstack-knowledge", "NEVER_COPY"):
            self.assertNotIn(unwanted, output)
        self.assertEqual(list(self.state.iterdir()), [])
        self.assertFalse((self.vault / self.candidate["note"]).exists())

    def test_stop_is_inert_even_without_identity_or_available_state(self):
        with patch.object(k, "read_receipt", side_effect=AssertionError("receipt lookup")), patch.object(k, "safe_absolute", side_effect=AssertionError("path lookup")), patch.object(k, "receipt", side_effect=AssertionError("routine receipt")):
            for fields in ({}, {"stop_hook_active": False}, {"stop_hook_active": True}, {"cwd": "/unavailable", "session_id": "unknown"}):
                self.assertEqual(k.event(self.cfg, {"hook_event_name": "Stop", **fields}), {})

    def test_optional_skip_does_not_block_later_useful_capture_in_same_event(self):
        k.receipt(self.cfg, "codex", "session1", "turn1", "skip", reason="no-useful-knowledge")
        result = self.save()
        self.assertEqual(result["status"], "saved")
        self.assertEqual(k.read_receipt(self.cfg, result["key"])["status"], "saved")
        self.assertEqual(self.save(), result)
        with self.assertRaises(k.Rejected): self.save({**self.candidate, "body": "# Changed after saved\n"})

    def test_optional_duplicate_skip_can_become_same_event_correction(self):
        self.save()
        skipped = self.save(self.current(), event="followup")
        self.assertEqual(skipped["status"], "skip")
        saved = self.save(self.current("# Fixture\n\nLater useful correction.\n"), event="followup")
        self.assertEqual((saved["status"], saved["generation"]), ("saved", 2))

    def test_codex_subagent_or_unknown_agent_prompt_is_inert(self):
        root = {"hook_event_name": "UserPromptSubmit", "cwd": str(self.root), "session_id": "session1", "turn_id": "turn1"}
        self.assertIn("hookSpecificOutput", k.event(self.cfg, root))
        for fields in ({"agent_id": "child", "agent_type": "worker"}, {"agent_id": None}, {"agent_type": None}, {"agent_id": {}}, {"agent_type": ""}):
            with self.subTest(fields=list(fields)):
                self.assertEqual(k.event(self.cfg, {**root, **fields}), {})

    def test_git_magic_path_is_literal_and_unrelated_work_stays_out_of_commit(self):
        candidate = {**self.candidate, "note": ":(glob)**/*.md"}
        (self.vault / "existing.md").write_text("unrelated dirty bytes\n")
        (self.vault / "staged.md").write_text("unrelated staged bytes\n")
        self.g("add", "staged.md")
        staged_before = self.g("diff", "--cached", "--binary")
        result = self.save(candidate)
        changed = self.g("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", "HEAD").split(b"\0")
        self.assertEqual([x for x in changed if x], [os.fsencode(candidate["note"])])
        self.assertEqual(result["status"], "saved")
        self.assertEqual(self.g("show", "HEAD:existing.md"), b"unchanged\n")
        self.assertEqual(self.g("diff", "--cached", "--binary"), staged_before)

    def test_interrupted_uncheckpointed_note_requires_reviewed_recovery(self):
        original = k.atomic_json
        def interrupt(path, data):
            original(path, data)
            if path.name == "stage.json" and data.get("stage") == "written":
                raise OSError("simulated interruption after file write")
        with patch.object(k, "atomic_json", side_effect=interrupt):
            with self.assertRaises(OSError): self.save()
        self.assertTrue((self.vault / self.candidate["note"]).exists())
        with self.assertRaises(k.Rejected): self.save(self.current(), event="reconcile")
        self.assertIsNone(k.read_receipt(self.cfg, k.identity("codex", "session1", "reconcile")))

    def test_matching_head_does_not_hide_an_unresolved_transaction(self):
        self.save()
        event = k.identity("codex", "session1", "turn1")
        (self.state / "transactions" / event / "stage.json").unlink()
        with self.assertRaisesRegex(k.Rejected, "unresolved transaction"):
            self.save(self.current(), event="reconcile")

    def test_disabled_environment_blocks_every_mutation_and_keeps_status_read_only(self):
        with patch.dict(os.environ, {"NSTACK_KNOWLEDGE_DISABLED": "1"}):
            with self.assertRaisesRegex(k.Rejected, "disabled"): self.save()
            for status in ("skip", "blocked", "missing"):
                with self.assertRaisesRegex(k.Rejected, "disabled"):
                    k.receipt(self.cfg, "codex", "session1", "turn1", status)
            self.assertIsNone(k.read_receipt(self.cfg, k.identity("codex", "session1", "turn1")))
        self.assertFalse((self.vault / self.candidate["note"]).exists())

    def test_known_and_configured_transcript_memory_sources_are_never_opened(self):
        shapes = (".codex/sessions/fixture.jsonl", ".codex/archived_sessions/fixture.jsonl", ".codex/memories/current.md", ".codex/memories_v2/current.md", ".opencode/sessions/current.json")
        for n, rel in enumerate(shapes):
            source = self.root / rel
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("Synthetic forbidden source, not real host data.\n")
            candidate = {**self.candidate, "source": str(source), "source_sha256": k.digest(source.read_bytes())}
            real_read = k.regular_bytes
            def reject_source_read(path, bound):
                if path == source: raise AssertionError("forbidden source opened")
                return real_read(path, bound)
            with self.subTest(shape=rel), patch.object(k, "regular_bytes", side_effect=reject_source_read):
                with self.assertRaises(k.Rejected): self.save(candidate, event=f"excluded{n}")
        custom = self.root / "custom-host"
        source = custom / "sessions/example.jsonl"
        source.parent.mkdir(parents=True); source.write_text("Synthetic custom host source.\n")
        candidate = {**self.candidate, "source": str(source), "source_sha256": k.digest(source.read_bytes())}
        with patch.dict(os.environ, {"CODEX_HOME": str(custom)}):
            with self.assertRaises(k.Rejected): self.save(candidate, event="custom-codex")
        self.cfg["excluded_source_roots"] = [str(custom)]
        with self.assertRaises(k.Rejected): self.save(candidate, event="custom-explicit")

    def test_transaction_parent_symlink_is_rejected_without_outside_effects(self):
        outside = self.root / "unrelated-directory"; outside.mkdir()
        (self.state / "transactions").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(k.Rejected, "transaction parent"): self.save()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.vault / self.candidate["note"]).exists())

    @unittest.skipUnless(sys.platform == "darwin", "macOS metadata preservation control")
    def test_correction_and_separate_restore_preserve_xattr_acl_flags_owner_mode(self):
        import stat
        import pwd
        self.save()
        note = self.vault / self.candidate["note"]
        subprocess.run(["/usr/bin/xattr", "-w", "com.nstack.review", "preserve-fixture-metadata", str(note)], capture_output=True, check=True)
        subprocess.run(["/bin/chmod", "+a", f"user:{pwd.getpwuid(os.getuid()).pw_name} allow read,write", str(note)], capture_output=True, check=True)
        note.chmod(0o640)
        os.chflags(note, note.stat().st_flags | stat.UF_NODUMP)
        fs = k.filesystem_tools()
        before = fs.fingerprint(note)
        correction = self.current("# Fixture\n\nCorrected with metadata preserved.\n")
        result = self.save(correction, event="metadata-correction")
        self.assertEqual(k.metadata(note.read_bytes())[1], correction["body"].rstrip() + "\n")
        expected_target = copy.deepcopy(before)
        expected_target["sha256"] = result["note_sha256"]
        # Runtime comparisons were exact before/during mutation and after checkpoint.
        # Later native document-ID tracking may add bit64, never remove/change others.
        self.assert_post_capture_snapshot(fs.fingerprint(note), expected_target)
        journal = self.state / "transactions" / result["key"]
        self.assert_post_capture_snapshot(fs.fingerprint(journal / "before.md"), before)
        self.assert_post_capture_snapshot(fs.fingerprint(journal / "restore-rehearsal.md"), before)

    def test_disabled_or_nonlocal_event_has_no_effect(self):
        payload = {"hook_event_name": "UserPromptSubmit", "cwd": str(self.root), "session_id": "session1", "turn_id": "turn1"}
        self.assertIn("hookSpecificOutput", k.event(self.cfg, payload))
        self.assertEqual(k.event({**self.cfg, "enabled": False}, payload), {})
        self.assertEqual(k.event(self.cfg, {**payload, "hook_event_name": "SubagentStop"}), {})
        with patch.dict(os.environ, {"NSTACK_KNOWLEDGE_DISABLED": "1"}): self.assertEqual(k.event(self.cfg, payload), {})

    def test_oversized_hook_input_and_unknown_fields_do_not_leak(self):
        settings = self.root / "settings.json"; settings.write_text(json.dumps(self.cfg))
        result = subprocess.run([sys.executable, str(SOURCE / "knowledge.py"), "--settings", str(settings), "event"], input=b"sensitive" * 10000, capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b"{}\n")
        self.assertEqual(result.stderr, b"")

    def test_scientific_isolated_transport_still_disables_hooks(self):
        transport = ROOT / "integrations/research/codex-transport/transport.py"
        text = transport.read_text()
        self.assertIn('"apps", "plugins", "plugin_hooks", "hooks"', text)
        self.assertIn("DISABLED_FEATURES", text)
        transport_spec = importlib.util.spec_from_file_location("knowledge_transport_check", transport)
        transport_module = importlib.util.module_from_spec(transport_spec)
        transport_spec.loader.exec_module(transport_module)
        with patch.object(transport_module, "policy", return_value={}), patch.object(transport_module, "clean_environment", return_value={}):
            args = transport_module.config_arguments({"web_search": "disabled", "workspace": self.root}, read_only=True, context={"effort": "high"})
        self.assertIn("features.hooks=false", args)
        self.assertIn("plugins._default.enabled=false", args)
        self.assertIn("features.memories=false", args)

    def test_writer_rejects_receipt_parent_link_but_passive_prompt_never_reads_it(self):
        outside = self.root / "outside-receipts"; outside.mkdir()
        (self.state / "receipts").symlink_to(outside, target_is_directory=True)
        payload = {"hook_event_name": "UserPromptSubmit", "cwd": str(self.root), "session_id": "session1", "turn_id": "turn1"}
        self.assertIn("hookSpecificOutput", k.event(self.cfg, payload))
        with self.assertRaises(k.Rejected): self.save()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.vault / self.candidate["note"]).exists())

    @unittest.skipUnless(shutil.which("node"), "Node required for OpenCode plugin contract controls")
    def test_opencode_passive_identity_privacy_scope_disable_and_bounded_memory(self):
        script = r'''
import assert from "node:assert/strict";
import {writeFile} from "node:fs/promises";
import {setup} from PLUGIN;
const cfg = CFG, hooks = new Map();
let parent = false, forbidden = 0, metadataReads = 0;
const fail = () => { forbidden++; throw Error("forbidden adapter work") };
const ctx = {app:{version:"2.3.0"},options:{settings:SETTINGS},location:{directory:ROOT},get storage(){return fail()},get model(){return fail()},get credential(){return fail()},session:{hook:async(n,f)=>{hooks.set(n,f);return{dispose:async()=>hooks.delete(n)}},get:async({sessionID})=>{metadataReads++;return{data:parent?{id:sessionID,parentID:"parent"}:{id:sessionID}}},get synthetic(){return fail()},get generate(){return fail()},get switchModel(){return fail()}}};
const dispose = await setup(ctx);
assert.deepEqual([...hooks.keys()],["prompt","context"]);
assert(!hooks.has("experimental.idle"));
await hooks.get("prompt")({sessionID:"session1",messageID:"msg_user1",get prompt(){return fail()}});
const context = {sessionID:"session1",system:[{type:"text",text:"original"}],get messages(){return fail()},get model(){return fail()},get tools(){return fail()}};
await hooks.get("context")(context);
assert.equal(context.system.length,2);assert.equal(context.system[0].text,"original");
assert.equal(context.system[1].text.split("\n")[0],"Knowledge event: host=opencode session=session1 event=msg_user1.");
for(const word of ["receipt_key","skip","Read ","before finishing","nstack-knowledge"]) assert(!context.system[1].text.includes(word));
parent=true;await hooks.get("prompt")({sessionID:"child",messageID:"msg_child"});const child={sessionID:"child",system:[]};await hooks.get("context")(child);assert.equal(child.system.length,0);parent=false;
await hooks.get("prompt")({sessionID:"bad/id",messageID:"msg_bad"});
for(let i=0;i<129;i++) await hooks.get("prompt")({sessionID:"session_"+i,messageID:"msg_"+i});
const evicted={sessionID:"session1",system:[]};await hooks.get("context")(evicted);assert.equal(evicted.system.length,0);
const newest={sessionID:"session_128",system:[]};await hooks.get("context")(newest);assert(newest.system[0].text.includes("event=msg_128."));
const oldPrompt=hooks.get("prompt"),before=metadataReads;await dispose();assert.equal(hooks.size,0);await oldPrompt({sessionID:"disposed",messageID:"msg_disposed"});assert.equal(metadataReads,before);
await setup(Object.assign(Object.create(ctx),{location:{directory:ROOT,workspaceID:"remote"}}));assert.equal(hooks.size,0);
await setup(Object.assign(Object.create(ctx),{app:{version:"2.4.0"}}));assert.equal(hooks.size,0);
await writeFile(SETTINGS,JSON.stringify({...cfg,enabled:false}));const disabled=Object.create(ctx);Object.defineProperty(disabled,"app",{get:fail});await setup(disabled);assert.equal(hooks.size,0);
assert.equal(forbidden,0);
console.log(JSON.stringify({status:"passed",native_delivery:false,forbidden_calls:forbidden,registered_hooks:["prompt","context"]}));
'''
        settings = self.root / "settings.json"
        # A missing state/vault proves the passive adapter does not read either.
        config = {**self.cfg, "state": str(self.root / "absent-state"), "vault": str(self.root / "absent-vault")}
        settings.write_text(json.dumps(config))
        script = script.replace("PLUGIN", json.dumps((SOURCE / "opencode.js").as_uri())).replace("CFG", json.dumps(config)).replace("SETTINGS", json.dumps(str(settings))).replace("ROOT", json.dumps(str(self.root)))
        result = subprocess.run([shutil.which("node"), "--input-type=module", "-e", script], capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertFalse(json.loads(result.stdout)["native_delivery"])


if __name__ == "__main__":
    unittest.main()
