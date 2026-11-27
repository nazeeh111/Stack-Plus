import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from lib import selected_catalog as catalog


class SelectedCatalogTests(unittest.TestCase):
    def test_scoped_entries_are_source_bound(self):
        data = json.loads(catalog.CATALOG.read_text())
        names = [r["name"] for r in data["methods"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertNotIn(data["explicit_lead"], names)
        for row in data["methods"]:
            self.assertTrue(row["scope"])
            self.assertEqual(sum(bool(row.get(k)) for k in ("checkout_bundle","native_base","leaf")), 1, row["name"])
            if "source" in row:
                self.assertRegex(row["source"]["revision"], r"^[a-f0-9]{40}$")
            if "checkout_bundle" in row:
                self.assertTrue((catalog.ROOT/row["checkout_bundle"]/"SKILL.md").is_file())

    def test_pinned_method_includes_shared_file_and_preserves_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary).resolve()
            repo = work/"publisher"
            subprocess.run(["git","init","-q",repo],check=True)
            for relative, text in {
                "plugins/sample/skills/original/SKILL.md": "---\nname: original\ndescription: Read a signal.\n---\nRead ../../references/rule.md\n",
                "plugins/sample/references/rule.md": "Read the packet time first.\n",
                "plugins/sample/skills/other/SKILL.md": "Unselected sibling.\n",
                "LICENSE": "Synthetic test publisher notice.\n",
            }.items():
                path = repo/relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            subprocess.run(["git","-C",repo,"add","."],check=True)
            subprocess.run(["git","-C",repo,"-c","user.name=Fixture","-c","user.email=fixture@example.invalid",
                            "-c","commit.gpgsign=false","commit","-qm","fixture"],check=True)
            pin=subprocess.check_output(["git","-C",repo,"rev-parse","HEAD"],text=True).strip()
            leaf="plugins/sample/skills/original"
            row={"name":"signal-read","scope":"Project-scoped","source":{"repository":"example/publisher","revision":pin,"path":leaf},
                 "leaf":leaf,"shared":"sample"}
            data={"shared_support":{"sample":["plugins/sample/references/rule.md"]}}
            location=work/"result"
            entry=catalog.stage(row,data,location,repo)
            self.assertIn('name: "signal-read"', (entry/"SKILL.md").read_text())
            self.assertEqual((entry.resolve()/"../../references/rule.md").read_text(),"Read the packet time first.\n")
            self.assertFalse((entry.resolve().parent/"other").exists())
            receipt=json.loads((location/"bundle/bundle.json").read_text())
            for name,digest in receipt["document_sha256"].items():
                self.assertEqual(hashlib.sha256((location/"bundle/package"/name).read_bytes()).hexdigest(),digest)
            (location/"mine").write_text("untouched")
            with self.assertRaises(ValueError):
                catalog.stage(row,data,location,repo)
            self.assertEqual((location/"mine").read_text(),"untouched")


if __name__ == "__main__":
    unittest.main()
