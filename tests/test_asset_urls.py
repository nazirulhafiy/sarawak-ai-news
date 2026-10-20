#!/usr/bin/env python3
"""Content-hash asset URLs and the hand-typed query-stamp ban."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kit.python.asset_urls import (  # noqa: E402
    assert_no_hand_typed_v,
    content_hash,
    versioned_href,
)


class ContentHashTests(unittest.TestCase):
    def test_hash_is_sha256_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon.bin"
            path.write_bytes(b"abc")
            full = hashlib.sha256(b"abc").hexdigest()
            self.assertEqual(content_hash(path), full[:12])
            self.assertEqual(content_hash(path, n=8), full[:8])
            self.assertEqual(len(content_hash(path)), 12)

    def test_versioned_href_appends_and_replaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "social-card.png"
            path.write_bytes(b"png-bytes")
            digest = hashlib.sha256(b"png-bytes").hexdigest()[:12]
            stamped = versioned_href("https://ai.sarawak.news/social-card.png", path)
            self.assertEqual(
                stamped, f"https://ai.sarawak.news/social-card.png?v={digest}"
            )
            replaced = versioned_href(
                "https://ai.sarawak.news/social-card.png?v=old&x=1", path
            )
            self.assertEqual(
                replaced,
                f"https://ai.sarawak.news/social-card.png?v={digest}&x=1",
            )
            relative = versioned_href("social-card.png", path)
            self.assertEqual(relative, f"social-card.png?v={digest}")

    def test_repo_has_no_hand_typed_asset_query(self):
        assert_no_hand_typed_v(ROOT)

    def test_hand_typed_query_in_scripts_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            scripts = root / "scripts"
            scripts.mkdir()
            (scripts / "build.py").write_text(
                'href = "favicon.svg?v=20260908"\n',
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError) as caught:
                assert_no_hand_typed_v(root)
            self.assertIn("scripts/build.py", str(caught.exception))

    def test_generated_block_may_mention_the_stamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "design.md").write_text(
                "<!-- BEGIN GENERATED: hosting -->\n"
                "content hash query ?v=stamp\n"
                "<!-- END GENERATED: hosting -->\n"
                "Icons use a content hash query string.\n",
                encoding="utf-8",
            )
            assert_no_hand_typed_v(root)

    def test_stamp_outside_generated_block_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "design.md").write_text(
                "<!-- BEGIN GENERATED: hosting -->\n"
                "ok\n"
                "<!-- END GENERATED: hosting -->\n"
                'href="favicon.svg?v=solid3"\n',
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError):
                assert_no_hand_typed_v(root)


if __name__ == "__main__":
    unittest.main()
