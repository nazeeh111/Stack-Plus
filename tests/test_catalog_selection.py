"""Catalog operations use one current snapshot, not persistent cached state."""
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "lib")]
import native_setup as native

nstack = native.nstack


def reference_name(candidate, path, repository, catalog):
    selected = next((row for row in catalog["skills"] if (
        row["candidate_id"], row["source_path"], row["source_repository"]
    ) == (candidate, path, repository)), {})
    raw = selected.get("native_name") or Path(path).parent.name or repository.split("/")[-1]
    return candidate.lower() + "-" + re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")


def reference_selection(catalog):
    modes = {row["id"]: row["deployment"] for row in catalog["components"]}
    rows = []
    for row in catalog["skills"]:
        if modes[row["candidate_id"]] != "on demand" or row["delivery"] not in (
            "intact upstream leaf", "narrow-patched leaf", "native runtime/method adapter",
        ):
            continue
        name = reference_name(row["candidate_id"], row["source_path"],
                              row["source_repository"], catalog)
        prefix = row["candidate_id"].lower() + "-"
        if not name.startswith(prefix):
            raise ValueError("Unexpected source skill name")
        rows.append((native.skill_names.canonical(name[len(prefix):]), row))
    if len({name for name, _ in rows}) != len(rows):
        raise ValueError("Natural skill names collide")
    return rows


class CatalogSelection(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "registry/manifest.json").read_text())
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()

    def registry(self, root, catalog):
        path = root / "registry/manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(catalog))
        return path

    def test_selection_reads_actual_manifest_once_per_call(self):
        path = nstack.ROOT / "registry/manifest.json"
        actual_load = nstack.load
        reads = []

        def counted(source):
            result = actual_load(source)
            if Path(source) == path:
                reads.append(Path(source))
            return result

        with patch.object(nstack, "load", side_effect=counted):
            first = native.selection()
            self.assertEqual(len(reads), 1)
            second = native.selection()
            self.assertEqual(len(reads), 2)
        self.assertEqual(first, second)
        self.assertEqual(first, reference_selection(self.catalog))

    def test_all_registered_method_sets_canonical_legacy_and_changed_aliases(self):
        original_aliases = dict(native.skill_names.RENAMES)
        changed_aliases = dict(original_aliases)
        selected_names = {name for name, _ in reference_selection(self.catalog)}
        source = next(source for source, exposed in changed_aliases.items()
                      if exposed in selected_names)
        changed_aliases[source] = "catalog-fresh-alias"
        for aliases in ({}, original_aliases, changed_aliases):
            with self.subTest(aliases=len(aliases)), patch.dict(
                native.skill_names.RENAMES, aliases, clear=True
            ):
                actual = native.selection()
                self.assertEqual(actual, reference_selection(self.catalog))
                self.assertEqual(len(actual), 170)
                self.assertEqual(len({name for name, _ in actual}), 170)
                if aliases is changed_aliases:
                    self.assertIn("catalog-fresh-alias", {name for name, _ in actual})

    def test_all_registered_shelf_names_match_prior_rules_and_snapshot_is_not_mutated(self):
        before = copy.deepcopy(self.catalog)
        for row in self.catalog["skills"]:
            arguments = (row["candidate_id"], row["source_path"], row["source_repository"])
            self.assertEqual(nstack.shelf_name(*arguments, catalog=self.catalog),
                             reference_name(*arguments, self.catalog))
        for arguments in (
            ("UNKNOWN", "SKILL.md", "owner/Fallback.Name"),
            ("UNKNOWN", "folder/Readable_Name/SKILL.md", "owner/repository"),
        ):
            self.assertEqual(nstack.shelf_name(*arguments, catalog=self.catalog),
                             reference_name(*arguments, self.catalog))
        self.assertEqual(self.catalog, before)

    def test_same_size_mtime_preserved_registry_edit_is_seen_on_next_call(self):
        catalog = copy.deepcopy(self.catalog)
        selected = reference_selection(catalog)[0][1]
        selected["native_name"] = "fresh-a"
        root = self.base / "source"
        path = self.registry(root, catalog)
        before_stat = path.stat()
        with patch.object(nstack, "ROOT", root):
            first = native.selection()
            selected["native_name"] = "fresh-b"
            path.write_text(json.dumps(catalog))
            os.utime(path, ns=(before_stat.st_atime_ns, before_stat.st_mtime_ns))
            self.assertEqual(path.stat().st_size, before_stat.st_size)
            self.assertEqual(path.stat().st_mtime_ns, before_stat.st_mtime_ns)
            second = native.selection()
        self.assertNotEqual(first[0][0], second[0][0])
        self.assertEqual(second, reference_selection(catalog))

    def test_root_changes_and_removed_manifest_are_never_hidden_by_a_cache(self):
        first_catalog = copy.deepcopy(self.catalog)
        second_catalog = copy.deepcopy(self.catalog)
        reference_selection(first_catalog)[0][1]["native_name"] = "root-one"
        reference_selection(second_catalog)[0][1]["native_name"] = "root-two"
        one, two = self.base / "one", self.base / "two"
        self.registry(one, first_catalog)
        second_path = self.registry(two, second_catalog)
        with patch.object(nstack, "ROOT", one):
            first = native.selection()
        with patch.object(nstack, "ROOT", two):
            second = native.selection()
            second_path.unlink()
            with self.assertRaises(FileNotFoundError):
                native.selection()
        self.assertEqual(first, reference_selection(first_catalog))
        self.assertEqual(second, reference_selection(second_catalog))
        self.assertNotEqual(first[0][0], second[0][0])

    def test_registry_replacement_during_read_does_not_mix_catalog_generations(self):
        original = copy.deepcopy(self.catalog)
        replacement = copy.deepcopy(self.catalog)
        chosen = reference_selection(replacement)[0][1]
        chosen["native_name"] = "replacement-name"
        root = self.base / "source"
        path = self.registry(root, original)
        actual_load = nstack.load
        reads = []

        def replace_after_read(source):
            result = actual_load(source)
            if Path(source) == path:
                reads.append(Path(source))
                if len(reads) == 1:
                    next_path = path.with_suffix(".next")
                    next_path.write_text(json.dumps(replacement))
                    os.replace(next_path, path)
            return result

        with patch.object(nstack, "ROOT", root), patch.object(
            nstack, "load", side_effect=replace_after_read
        ):
            first = native.selection()
            second = native.selection()
        self.assertEqual(first, reference_selection(original))
        self.assertEqual(second, reference_selection(replacement))
        self.assertEqual(len(reads), 2)

    def test_standalone_lookup_reloads_by_default_and_explicit_context_is_local(self):
        first = copy.deepcopy(self.catalog)
        second = copy.deepcopy(self.catalog)
        selected = reference_selection(first)[0][1]
        arguments = (selected["candidate_id"], selected["source_path"],
                     selected["source_repository"])
        selected["native_name"] = "snapshot-one"
        reference_selection(second)[0][1]["native_name"] = "snapshot-two"
        root = self.base / "source"
        path = self.registry(root, first)
        with patch.object(nstack, "ROOT", root):
            original = nstack.shelf_name(*arguments)
            path.write_text(json.dumps(second))
            self.assertNotEqual(nstack.shelf_name(*arguments), original)
            self.assertEqual(nstack.shelf_name(*arguments, catalog=first), original)
            self.assertEqual(nstack.shelf_name(*arguments),
                             reference_name(*arguments, second))

    def test_eligibility_filter_order_and_duplicate_first_match_collision(self):
        components, skills = [], []
        for i, (deployment, delivery) in enumerate((
            ("on demand", "intact upstream leaf"),
            ("on demand", "narrow-patched leaf"),
            ("on demand", "native runtime/method adapter"),
            ("on demand", "selective-merge reference"),
            ("consult", "intact upstream leaf"),
            ("trial", "intact upstream leaf"),
            ("substitute", "intact upstream leaf"),
        )):
            candidate = "P" + str(i)
            components.append({"id": candidate, "deployment": deployment})
            skills.append({
                "candidate_id": candidate, "delivery": delivery,
                "source_repository": "fixture/repository",
                "source_path": "skills/fixture-" + str(i) + "/SKILL.md",
            })
        catalog = {"components": components, "skills": skills}
        root = self.base / "source"
        path = self.registry(root, catalog)
        with patch.object(nstack, "ROOT", root):
            selected = native.selection()
            self.assertEqual(selected, reference_selection(catalog))
            self.assertEqual([name for name, _ in selected],
                             ["fixture-0", "fixture-1", "fixture-2"])
            duplicate = dict(skills[0], native_name="would-hide-duplicate")
            catalog["skills"].append(duplicate)
            path.write_text(json.dumps(catalog))
            with self.assertRaisesRegex(ValueError, "Natural skill names collide"):
                native.selection()


if __name__ == "__main__":
    unittest.main()
