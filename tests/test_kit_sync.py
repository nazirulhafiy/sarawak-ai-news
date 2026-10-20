#!/usr/bin/env python3
"""Sister kit pin checks against the hub clone at SN_HUB_PATH / .hub-kit-ref."""

from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = (ROOT / "kit" / "PIN").read_text(encoding="utf-8").strip()


def _hub_path() -> Path | None:
    for candidate in (
        os.environ.get("SN_HUB_PATH", ""),
        str(ROOT / ".hub-kit-ref"),
        "/agent/repos/sarawak-news-hub",
    ):
        if not candidate:
            continue
        path = Path(candidate)
        if not path.is_dir():
            continue
        if not ((path / ".git").exists() or (path / "kit").is_dir()):
            continue
        try:
            subprocess.check_output(
                ["git", "-C", str(path), "cat-file", "-e", f"{PIN}^{{commit}}"],
                stderr=subprocess.STDOUT,
            )
            return path
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    return None


class KitSyncTests(unittest.TestCase):
    def test_sister_check_passes(self):
        hub = _hub_path()
        if hub is None:
            self.skipTest("hub clone with kit PIN commit not available")
        result = subprocess.run(
            ["python3", "kit/sync.py", "--check", "--hub-path", str(hub)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OK kit sync", result.stdout)

    def test_hand_edited_kit_file_fails(self):
        hub = _hub_path()
        if hub is None:
            self.skipTest("hub clone with kit PIN commit not available")
        target = ROOT / "kit" / "js" / "back-to-top.js"
        original = target.read_text(encoding="utf-8")
        try:
            target.write_text(original + "\n/* drift */\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", "kit/sync.py", "--check", "--hub-path", str(hub)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FAIL kit sync", result.stderr)
            self.assertIn("local edit or stale vendor", result.stderr)
        finally:
            target.write_text(original, encoding="utf-8")

    def test_contact_invariant_fails(self):
        hub = _hub_path()
        if hub is None:
            self.skipTest("hub clone with kit PIN commit not available")
        target = ROOT / "kit" / "shell.py"
        original = target.read_text(encoding="utf-8")
        try:
            target.write_text(
                original.replace(
                    "mailto:contact@sarawak.news", "mailto:nobody@example.com"
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", "kit/sync.py", "--check", "--hub-path", str(hub)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("footer-contact", result.stderr)
        finally:
            target.write_text(original, encoding="utf-8")

    def test_stale_pin_fails(self):
        hub = _hub_path()
        if hub is None:
            self.skipTest("hub clone with kit PIN commit not available")
        pin_path = ROOT / "kit" / "PIN"
        original = pin_path.read_text(encoding="utf-8")
        try:
            pin_path.write_text("0" * 40 + "\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", "kit/sync.py", "--check", "--hub-path", str(hub)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FAIL kit sync", result.stderr)
        finally:
            pin_path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
