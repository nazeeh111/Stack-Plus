"""Regression checks for wrapped upstream sibling-resolution instructions."""
import pathlib
import ast
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "lib"))
import patch_dcc

class NativeSiblingBinding(unittest.TestCase):
    def test_single_line_and_wrapped_policies_have_one_identical_native_binding(self):
        policy = ("If a sibling skill named here is missing from your available skills, "
                  "load it with `skill_get` (Scenario MCP) or ask the user to install it "
                  "(https://github.com/scenario-labs/skills#install); unattended, "
                  "proceed from tool schemas and flag the gap.")
        prefix = "Source path: `scenario-unreal-expert/scripts`.\n"
        suffix = "\nKeep method data, examples, identifiers and source notices exact.\n"
        outputs = []
        for fragment in (policy, policy.replace("sibling skill", "sibling\nskill"),
                         policy.replace("sibling skill", "sibling\n  skill").replace("flag the", "flag\nthe")):
            with self.subTest(fragment=fragment):
                result = patch_dcc.native_siblings(prefix + fragment + suffix, required=True)
                self.assertTrue(result.startswith(prefix))
                self.assertTrue(result.endswith(suffix))
                self.assertNotIn("`skill_get`", result)
                self.assertEqual(result.count("Resolve only the siblings selected for this task"), 1)
                outputs.append(result)
        self.assertEqual(outputs, [outputs[0]] * len(outputs))

    def test_animation_patch_removes_the_actual_wrapped_foreign_loader(self):
        with tempfile.TemporaryDirectory(prefix="nstack-dcc-binding-", dir="/private/tmp") as temp:
            out = pathlib.Path(temp)
            (out / "scripts").mkdir()
            raw = ("---\nname: scenario-unreal-animation\ndescription: Source animation method\n---\n"
                   "If a sibling\nskill named here is missing from your available skills, load it with "
                   "`skill_get` (Scenario MCP) or ask the user to install it; unattended, "
                   "proceed from tool schemas and flag the gap.\n"
                   "Keep `ue_anim.py`, original method and source paths.\n")
            (out / "SKILL.md").write_text(raw)
            patch_dcc.patch("X-CREATIVE-UNREAL", "scenario-unreal-animation", out)
            result = (out / "SKILL.md").read_text()
            self.assertNotIn("`skill_get`", result)
            self.assertIn("Resolve only the siblings selected for this task", result)
            self.assertIn("Keep `ue_anim.py`, original method and source paths.", result)

    def test_source_sibling_roots_resolve_discovery_symlinks_without_renaming_source_paths(self):
        with tempfile.TemporaryDirectory(prefix="nstack-dcc-roots-", dir="/private/tmp") as temp:
            base = pathlib.Path(temp)
            for number, (relative, variable) in enumerate(patch_dcc.SIBLING_ROOTS.items()):
                with self.subTest(relative=relative):
                    source = base / str(number) / "source" / "original-leaf"
                    helper = source / relative
                    helper.parent.mkdir(parents=True)
                    expert = source.parent / "scenario-blender-expert" / "scripts"
                    expert.mkdir(parents=True)
                    sibling = expert / "bx_audit.py"
                    sibling.write_bytes(b"# Original sibling helper bytes.\n")
                    raw = (variable + " = os.path.dirname(os.path.abspath(__file__))\n"
                           "EXPERT = os.path.join(os.path.dirname(os.path.dirname(" + variable + ")), "
                           "'scenario-blender-expert', 'scripts')\n")
                    helper.write_text(raw)
                    unrelated = source / "scripts/unreviewed.py"
                    unrelated.write_text(raw)
                    discovery = base / str(number) / "skills" / "canonical-exposure"
                    discovery.parent.mkdir()
                    discovery.symlink_to(source, target_is_directory=True)
                    logical = discovery / relative
                    before = {"os": os, "__file__": str(logical)}
                    exec(compile(ast.parse(raw), str(logical), "exec"), before)
                    self.assertFalse(pathlib.Path(before["EXPERT"]).exists())
                    patch_dcc.resolve_sibling_roots(source)
                    after = {"os": os, "__file__": str(logical)}
                    adapted = helper.read_text()
                    exec(compile(ast.parse(adapted), str(logical), "exec"), after)
                    self.assertEqual(pathlib.Path(after["EXPERT"]), expert)
                    self.assertTrue(pathlib.Path(after["EXPERT"]).is_dir())
                    direct = {"os": os, "__file__": str(helper)}
                    exec(compile(ast.parse(adapted), str(helper), "exec"), direct)
                    for context in (after, direct):
                        found = pathlib.Path(context["EXPERT"]) / "bx_audit.py"
                        self.assertEqual(found.resolve(), sibling.resolve())
                        self.assertEqual(found.read_bytes(), b"# Original sibling helper bytes.\n")
                    self.assertEqual(adapted, raw.replace("os.path.abspath(__file__)", "os.path.realpath(__file__)", 1))
                    self.assertEqual(unrelated.read_text(), raw)
                    self.assertIn("'scenario-blender-expert'", adapted)
                    helper.write_text("# Changed source anchor\n")
                    with self.assertRaisesRegex(ValueError, "sibling root changed"):
                        patch_dcc.resolve_sibling_roots(source)

    def test_selected_unreal_policy_fails_closed_if_missing_or_duplicated(self):
        self.assertEqual(patch_dcc.native_siblings("Unrelated Blender method."), "Unrelated Blender method.")
        policy = "If a sibling skill flag the gap."
        result = patch_dcc.native_siblings(policy + "\n" + policy)
        self.assertEqual(result.count("Resolve only the siblings selected for this task"), 1)
        self.assertTrue(result.endswith("\n" + policy))
        for text in ("Policy changed.", "If a sibling skill flag the gap.\nIf a sibling skill flag the gap."):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "sibling policy"):
                    patch_dcc.native_siblings(text, required=True)

if __name__ == "__main__":
    unittest.main()
