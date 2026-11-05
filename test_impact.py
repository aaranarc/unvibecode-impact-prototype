"""Run: python -m unittest -v   (standard library only)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile

from impact_prototype import analyse, load, module_name

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "tiny_resolved_graph.json")


class ImpactTest(unittest.TestCase):
    def setUp(self):
        self.edges, self.unresolved, _ = load(FIXTURE)

    def test_direct_and_two_hop_dependents(self):
        a = analyse(self.edges, self.unresolved, "src/pkg/core.py")
        self.assertEqual(a["direct"], ["src/pkg/api.py", "src/pkg/cli.py"])
        self.assertEqual(a["indirect"], ["tests/test_api.py"])  # imports api.py, which imports core.py

    def test_flags_stem_fallback_link(self):
        a = analyse(self.edges, self.unresolved, "src/pkg/core.py")
        self.assertEqual([(e["source"], e["strategy"]) for e in a["weak"]], [("src/pkg/cli.py", "stem_fallback")])

    def test_warns_when_package_import_is_misrouted(self):
        # `import pkg` resolved to a same-named test fixture instead of src/pkg/__init__.py (src/ layout, issue #308).
        a = analyse(self.edges, self.unresolved, "src/pkg/__init__.py")
        self.assertEqual(a["direct"], [])
        self.assertEqual(len(a["misrouted"]), 1)  # file-level edge only; the symbol-level copy is not double counted
        self.assertEqual(len(a["missed"]), 1)

    def test_stdlib_unresolved_is_not_reported(self):
        a = analyse(self.edges, self.unresolved, "src/pkg/api.py")
        self.assertEqual(a["own_unresolved"], ["requests"])

    def test_module_name(self):
        self.assertEqual(module_name("src/flask/__init__.py"), "flask")
        self.assertEqual(module_name("src/flask/app.py"), "flask.app")
        self.assertEqual(module_name("pkg/mod.py"), "pkg.mod")

    def test_zip_input_gives_same_dependents(self):
        rows = [dict(source_file=e["source"], target_file=e["target"], relationship=e["type"], confidence=e["confidence"])
                for e in self.edges if e["level"] == "file"]
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tiny-repository-context.zip")
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("connections.jsonl", "\n".join(json.dumps(r) for r in rows))
                z.writestr("unresolved_relationships.jsonl", "")
                z.writestr("manifest.json", json.dumps({"repository": "tiny"}))
            edges, unresolved, _ = load(path)
        self.assertEqual(analyse(edges, unresolved, "src/pkg/core.py")["direct"], ["src/pkg/api.py", "src/pkg/cli.py"])

    def test_cli_prints_pr_block(self):
        out = subprocess.run([sys.executable, os.path.join(HERE, "impact_prototype.py"), FIXTURE, "src/pkg/core.py"],
                             capture_output=True, text=True, check=True).stdout
        self.assertIn("Direct dependents: 2", out)
        self.assertIn("### Impact checked with UnvibeCode", out)

    def test_cli_prints_zip_selection_tokens_when_available(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tiny-repository-context.zip")
            selections = [
                dict(file="src/pkg/core.py", source_tokens=700, scopes={"1": dict(
                    estimated_tokens=1200, included_files=["src/pkg/core.py", "src/pkg/api.py"])}),
                dict(file="src/pkg/api.py", source_tokens=500),
                dict(file="tests/test_api.py", source_tokens=300),
            ]
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("connections.jsonl", "")
                z.writestr("unresolved_relationships.jsonl", "")
                z.writestr("manifest.json", json.dumps({"repository": "tiny"}))
                z.writestr("selections.jsonl", "\n".join(json.dumps(r) for r in selections))
            command = [sys.executable, os.path.join(HERE, "impact_prototype.py"), path, "src/pkg/core.py"]
            out = subprocess.run(command, capture_output=True, text=True, check=True).stdout
            self.assertIn("AI context: radius 1 = 1,200 est. tokens (2 files) vs 1,500 for the whole repo "
                          "(UnvibeCode's estimates)", out)
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("connections.jsonl", "")
                z.writestr("unresolved_relationships.jsonl", "")
                z.writestr("manifest.json", json.dumps({"repository": "tiny"}))
            out = subprocess.run(command, capture_output=True, text=True, check=True).stdout
            self.assertNotIn("AI context:", out)


if __name__ == "__main__":
    unittest.main()
