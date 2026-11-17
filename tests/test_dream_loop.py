"""Offline provenance and method-fidelity checks for the native Dream Loop port.

No image generation, target scripts, provider calls, accounts or Blender runs.
"""
import difflib
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "addons" / "dream-loop"
PIN = "9bddb901f7d071cfefdd21e264267c757177a9df"
# Independent reviewed source hashes, not computed from the receipt under test.
EXPECTED = {'.gitignore': '7150ac9987659039892027707e578e0ac0695c60aae8a17bb8aa13c52b9fdf99', 'LICENSE': '1607e9149a254c619d0ceb4119ed9346e13048c28c1d437d80ff2837e40159da', 'README.md': '3db72b0ce7bff56e78785f4d93c9c6f48b3cf89f91615208c76bd000e71a9bdd', 'SKILL.md': '6f736c4d663e5b394fb322035a2d28f197f02372e4479762b127d2c954738054', 'assets/vesper-preview.gif': '7edf3bab79603683ec0167a5d0997e48cf8677b07207159d0dac05ef64fd7597', 'references/fal.md': 'db2a4d1af4a6a0bcc88bd325d56e7ea23ffa5bd56ef5f968e7507c527a75213c', 'references/plus-mode/assets-3d.md': 'f7ad8d7b63c305371192fa9671ce98cc049fd5fa6bd4d2c794db16897191fa80', 'references/plus-mode/workflow.md': '6736c2207142bfaa8b6219b55b95e08f242632c6b1d962f0bf6cf444c91ab9ee', 'references/pro-mode/assets-3d.md': '8a402cd3aebf97d058252a92325b9299f7f4a191c19e256f0bcdbac12bdc9231', 'references/pro-mode/workflow.md': '6b3636a2a33bacb507098ca1f766485521469191418a9d56ce956fad4fba566e', 'scripts/fal-batch.mjs': '4c8eb9029dd055cd54a7400110388c9840bfa14867d9e11491430ba1a389209d', 'scripts/fal-batch.test.mjs': '08e6dbf118e5270af7db4901164145ca4a084909c8b31a3ced80cc7ef6582781', 'scripts/preview-server.py': '5652e4179fb2571739eab759f24cace434d3ec2c61aa715101c4c1b5b5ee9ebb'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive_path(root, source_path):
    archived = {"SKILL.md": "ORIGINAL-SKILL.md", ".gitignore": "ORIGINAL-GITIGNORE"}.get(source_path, source_path)
    return root / "upstream" / archived


def verify_source(root):
    meta = json.loads((root / "SOURCE.json").read_text())
    assert (meta["repository"], meta["revision"], meta["license"]) == ("achimala/dream-loop", PIN, "MIT")
    assert meta["source_file_count"] == len(EXPECTED) == 13
    recorded = meta["upstream_files"]
    actual = {str(p.relative_to(root)) for p in (root / "upstream").rglob("*") if p.is_file()}
    assert set(recorded) == actual, "unrecorded or missing archived source"
    assert {row["source_path"] for row in recorded.values()} == set(EXPECTED)
    for rel, row in recorded.items():
        assert root / rel == archive_path(root, row["source_path"])
        assert digest(root / rel) == row["sha256"] == EXPECTED[row["source_path"]], rel
    return meta


def verify_active(root):
    meta = verify_source(root)
    for rel in meta["unchanged_active_files"]:
        assert (root / rel).read_bytes() == archive_path(root, rel).read_bytes(), rel
    for row in meta["adapted_files"]:
        source = archive_path(root, row["source_path"])
        active = root / row["active_path"]
        assert digest(source) == row["source_sha256"]
        assert digest(active) == row["active_sha256"], row["active_path"]
        expected = "".join(difflib.unified_diff(source.read_text().splitlines(True), active.read_text().splitlines(True), fromfile="upstream/" + row["source_path"], tofile=row["active_path"]))
        assert (root / row["diff"]).read_text() == expected, row["diff"]
    # Original Pro prompt and exit criteria are runtime instructions, not archival decoration.
    pro = root / "references/pro-mode/workflow.md"
    assert pro.read_bytes() == archive_path(root, "references/pro-mode/workflow.md").read_bytes()
    entry = (root / "SKILL.md").read_text()
    for mode in ("pro", "plus"):
        assert f"](references/{mode}-mode/workflow.md)" in entry
    assert "](references/native-operation.md)" in entry
    native = (root / "references/native-operation.md").read_text()
    assert "](pro-mode/workflow.md)" in native
    return meta


def verify_links(root):
    # Archives intentionally retain upstream's two broken Fal links. Active files must resolve.
    for file in root.rglob("*.md"):
        if "upstream" in file.relative_to(root).parts:
            continue
        for target in re.findall(r"(?<!!)\[[^\]\n]*\]\(([^)]+)\)", file.read_text()):
            if re.match(r"(?:[a-zA-Z][a-zA-Z0-9+.-]*:|#)", target):
                continue
            path = target.split("#", 1)[0]
            if path:
                resolved = (file.parent / path).resolve()
                assert resolved.is_relative_to(root.resolve()), (file, target, "outside installed bundle")
                assert resolved.is_file(), (file, target, "missing active reference")


class DreamLoopPort(unittest.TestCase):
    def test_exact_complete_source_and_mit_notice(self):
        verify_source(ADDON)
        license_text = (ADDON / "LICENSE").read_text()
        self.assertEqual(digest(ADDON / "LICENSE"), EXPECTED["LICENSE"])
        self.assertIn("Copyright (c) 2026 Anshu Chimala", license_text)
        self.assertEqual(len(list(ADDON.rglob("SKILL.md"))), 1)

    def test_portable_release_preserves_complete_archived_source(self):
        # The durable code installer intentionally excludes hidden paths. Check
        # its actual selection, not just a copy of the checkout's addon tree.
        import importlib.util
        spec = importlib.util.spec_from_file_location("dream_portable_installer", ROOT / "install.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        portable = dict((str(rel), source) for source, rel in installer.portable_files())
        meta = verify_source(ADDON)
        for rel in meta["upstream_files"]:
            retained = "addons/dream-loop/" + rel
            self.assertIn(retained, portable)
            self.assertEqual(digest(portable[retained]), digest(ADDON / rel))

    def test_active_port_provenance_diffs_and_local_links(self):
        verify_active(ADDON)
        verify_links(ADDON)

    def test_pro_full_loop_rubric_stall_and_performance_contract_survive(self):
        source = archive_path(ADDON, "references/pro-mode/workflow.md").read_text()
        active = (ADDON / "references/pro-mode/workflow.md").read_text()
        self.assertEqual(active, source)
        # Validate actual source method landmarks in addition to byte identity.
        for phrase in ("Take a first pass at implementing the target", "independent judge subagent with a fresh context", "Address all of the judge’s feedback carefully", "**Composition (0-3):**", "**Lighting (0-3):**", "**Materials (0-3):**", "**Details (0-1):**", "**score >= 8 and target FPS acceptable**", "**score >= 8 but target FPS unacceptable**", "**Stall approaching**", "**Stalled**", "best score hasn't improved by a full point in 2 rounds"):
            self.assertIn(phrase.replace("judge’s", "judge's"), active)

    def test_plus_workers_and_three_round_handoff_survive(self):
        rel = "references/plus-mode/workflow.md"
        source = archive_path(ADDON, rel).read_text()
        active = (ADDON / rel).read_text()
        self.assertEqual(active.split("The loop:", 1)[1], source.split("The loop:", 1)[1])
        self.assertEqual(active.split("- Always give subagents a fresh, empty context; do not fork", 1)[1], source.split("- Always give subagents a fresh, empty context; do not fork", 1)[1])
        self.assertIn("inheriting the current model and effort", active)

    def test_asset_decision_order_and_material_requirements_preserved(self):
        for mode, steps in (("pro", ["### 1. Can you download an external asset?", "### 2. Use an image-to-3D model", "### 3. Model it in Blender", "### 4. Procedural assets"]), ("plus", ["### 1. Can you download an external asset?", "### 2. Use an image-to-3D model", "### 3. Procedural assets"])):
            rel = f"references/{mode}-mode/assets-3d.md"
            active = (ADDON / rel).read_text()
            source = archive_path(ADDON, rel).read_text()
            positions = [active.index(step) for step in steps]
            self.assertEqual(positions, sorted(positions))
            # Preserve the complete Blender/procedural/material method after provider selection.
            self.assertEqual(active.split("### 3.", 1)[1], source.split("### 3.", 1)[1])
            self.assertIn("explicit user authorization", active)
            self.assertIn("](../fal.md)", active)
        self.assertIn("DO NOT use Blender for modeling", (ADDON / "references/plus-mode/assets-3d.md").read_text())

    def test_negative_source_drift_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "addon"
            shutil.copytree(ADDON, fixture)
            archive_path(fixture, "scripts/fal-batch.mjs").write_text("unreviewed replacement")
            with self.assertRaises(AssertionError):
                verify_source(fixture)

    def test_negative_missing_active_reference_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "addon"
            shutil.copytree(ADDON, fixture)
            native = fixture / "references/native-operation.md"
            native.write_text(native.read_text() + "\n[required asset](missing-required-asset.md)\n")
            with self.assertRaises(AssertionError):
                verify_links(fixture)

    def test_negative_critic_threshold_change_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = Path(temp) / "addon"
            shutil.copytree(ADDON, fixture)
            pro = fixture / "references/pro-mode/workflow.md"
            original = pro.read_text()
            altered = original.replace("score >= 8", "score >= 2")
            self.assertNotEqual(original, altered)
            pro.write_text(altered)
            with self.assertRaises(AssertionError):
                verify_active(fixture)


if __name__ == "__main__":
    unittest.main()
