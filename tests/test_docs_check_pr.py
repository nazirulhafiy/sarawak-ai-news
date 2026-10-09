import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.docs_check_pr import (
    FAILURE_MESSAGE,
    is_docs_change,
    is_watched,
)


class DocsCheckPrTests(unittest.TestCase):
    def test_watched_css_and_js(self) -> None:
        self.assertTrue(is_watched("site/style.css"))
        self.assertTrue(is_watched("site/app.js"))
        self.assertFalse(is_watched("site/brief-net.svg"))

    def test_watched_fonts_and_build(self) -> None:
        self.assertTrue(is_watched("site/fonts/OFL.txt"))
        self.assertTrue(is_watched("scripts/build.py"))

    def test_ignores_data_and_dist(self) -> None:
        self.assertFalse(is_watched("data/items.json"))
        self.assertFalse(is_watched("dist/index.html"))
        self.assertFalse(is_watched("site/style.css.bak"))

    def test_docs_prefix(self) -> None:
        self.assertTrue(is_docs_change("docs/design.md"))
        self.assertFalse(is_docs_change("README.md"))

    def test_failure_message(self) -> None:
        self.assertIn("no-docs-needed", FAILURE_MESSAGE)


if __name__ == "__main__":
    unittest.main()
