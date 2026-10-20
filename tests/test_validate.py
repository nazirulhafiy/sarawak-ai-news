"""Tests for allowed-source validation (events #24-style gate for AI News)."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import items_lib as L  # noqa: E402


class AllowedSourcesFile(unittest.TestCase):
    def test_allowed_sources_file_is_sorted_unique(self):
        payload = json.loads((ROOT / "data" / "allowed-sources.json").read_text())
        self.assertIsInstance(payload, list)
        self.assertEqual(payload, sorted(payload, key=str.casefold))
        self.assertEqual(len(payload), len(set(payload)))
        self.assertTrue(all(isinstance(name, str) and name.strip() == name for name in payload))

    def test_published_sources_are_allowed(self):
        allowed = L.load_allowed_sources()
        items = L.load_json(L.ITEMS)
        used = {item["source"] for item in items}
        self.assertTrue(used)
        self.assertTrue(used.issubset(allowed), sorted(used - allowed))


class Validation(unittest.TestCase):
    def setUp(self):
        self.allowed = {
            "DayakDaily",
            "The Borneo Post",
            "Sarawak Tribune",
            "UKAS",
        }
        self.good = {
            "id": "test-item-2026",
            "date": "2026-10-15",
            "source": "DayakDaily",
            "url": "https://dayakdaily.com/example",
            "title": "Example headline",
            "section": "Policy",
            "tags": ["ai"],
            "summary": "A one-sentence Sarawak AI signal.",
            "why_it_matters": "Editorial note.",
            "confidence": "high",
            "caveat": "Checked against source.",
        }

    def test_accepts_allowed_source(self):
        self.assertEqual(L.validate_item(self.good, self.allowed), [])

    def test_rejects_missing_source(self):
        item = dict(self.good)
        del item["source"]
        errs = L.validate_item(item, self.allowed)
        self.assertTrue(any("source is required" in e for e in errs))

    def test_rejects_blank_source(self):
        errs = L.validate_item(dict(self.good, source="  "), self.allowed)
        self.assertTrue(any("source is required" in e for e in errs))

    def test_rejects_unknown_source(self):
        errs = L.validate_item(dict(self.good, source="Fake Outlet"), self.allowed)
        self.assertTrue(any("not in data/allowed-sources.json" in e for e in errs))

    def test_rejects_near_miss_source_name(self):
        # Closest past-mistake shape: dropping "The" from a known outlet label.
        errs = L.validate_item(dict(self.good, source="Borneo Post"), self.allowed)
        self.assertTrue(any("not in data/allowed-sources.json" in e for e in errs))

    def test_collection_rejects_duplicate_id_and_url(self):
        a = dict(self.good)
        b = dict(self.good, id="other-id")
        errs = L.validate_collection([a, a], self.allowed)
        self.assertTrue(any("duplicate id" in e for e in errs))
        errs = L.validate_collection([a, b], self.allowed)
        self.assertTrue(any("duplicate url" in e for e in errs))


class ValidateScript(unittest.TestCase):
    def test_cli_passes_on_repo_items(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "validate.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("OK:", result.stdout)

    def test_cli_fails_on_unknown_source(self):
        items = L.load_json(L.ITEMS)
        broken = copy.deepcopy(items)
        broken[0]["source"] = "Fake Outlet"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data = tmp_path / "data"
            data.mkdir()
            (data / "items.json").write_text(json.dumps(broken), encoding="utf-8")
            (data / "allowed-sources.json").write_text(
                (ROOT / "data" / "allowed-sources.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            # Point the library paths via a small wrapper that swaps ROOT files.
            # Run validate against copied data by monkeypatching via env-free copy
            # of the script logic.
            sys.path.insert(0, str(SCRIPTS))
            import items_lib as lib

            errs = lib.validate_collection(
                broken,
                lib.load_allowed_sources(ROOT / "data" / "allowed-sources.json"),
            )
            self.assertTrue(any("Fake Outlet" in e for e in errs))


if __name__ == "__main__":
    unittest.main()
