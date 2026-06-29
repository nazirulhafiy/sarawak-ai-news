import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BuildTest(unittest.TestCase):
    def test_seed_data_has_required_fields(self):
        items = json.loads((ROOT / "data" / "items.json").read_text())
        required = {"id", "date", "source", "url", "title", "section", "tags", "summary", "why_it_matters", "confidence", "caveat"}
        self.assertGreaterEqual(len(items), 4)
        for item in items:
            self.assertTrue(required.issubset(item), item.get("id"))
            self.assertTrue(item["url"].startswith("https://"))
            self.assertLess(len(item["summary"]), 700)

    def test_build_outputs_aligned_style_static_site(self):
        result = subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertIn("Built", result.stdout)
        html = (ROOT / "dist" / "index.html").read_text()
        self.assertIn("Sarawak.News", html)
        self.assertIn("LAST UPDATED — SUNDAY, JUNE 28, 2026, 11:05 AM", html)
        self.assertIn("Tracking Sarawak’s AI, news, policy, and future economy.", html)
        self.assertIn("An independent news aggregator collecting important AI updates from Sarawak’s government, universities, businesses, and tech ecosystem.", html)
        self.assertIn("Latest intelligence signals", html)
        self.assertIn("Sarawak.News is an independent publication", html)
        self.assertNotIn("How This Is Built", html)
        self.assertNotIn("Sponsor This Brief", html)
        self.assertNotIn("Make This Brief Shorter", html)
        self.assertNotIn("Get this delivered to your inbox weekly", html)
        self.assertNotIn("Signal categories", html)
        self.assertNotIn("<nav", html)
        self.assertNotIn("Matched signal terms", html)
        self.assertIn('target="_blank"', html)
        for label in [">AI<", ">Tech<", ">PCDS 2030<", ">Policy<", ">Startups<", ">Energy<", ">Events<"]:
            self.assertNotIn(label, html)
        public_items = json.loads((ROOT / "dist" / "items.json").read_text())
        self.assertEqual(len(public_items), 15)
        self.assertTrue(all(item["date"] for item in public_items))
        public_titles = {item["title"] for item in public_items}
        self.assertIn("AI to transform Sarawak's economy, services, workforce productivity", public_titles)
        self.assertIn("Digital State: Sarawak adopts AI to address citizen needs", public_titles)
        self.assertIn("Sarawak Eyes Sovereign AI Infrastructure", public_titles)
        self.assertIn("Sarawak's AI future takes shape", public_titles)
        self.assertIn("Sarawak expands early intervention with AI screening", public_titles)
        self.assertNotIn("Sarawak Digital Economy Research Grant", public_titles)
        self.assertNotIn("Sarawak Digital Economy Research Grant", html)

    def test_build_outputs_compact_alternative_without_replacing_main(self):
        subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        alternative = (ROOT / "dist" / "alternative" / "index.html").read_text()
        css = (ROOT / "dist" / "alternative" / "alternative.css").read_text()
        items = json.loads((ROOT / "dist" / "alternative" / "items.json").read_text())

        self.assertIn("AI.Sarawak.News — Compact brief", alternative)
        self.assertEqual(alternative.count('class="story-card"'), 15)
        self.assertIn("LAST UPDATED — SUNDAY, JUNE 28, 2026, 11:05 AM", alternative)
        self.assertIn("Tracking Sarawak’s AI, news, policy, and future economy.", alternative)
        self.assertIn("Sarawak.News is an independent publication", alternative)
        self.assertNotIn("<nav", alternative)
        self.assertNotIn("Current version", alternative)
        self.assertNotIn("Signal categories", alternative)
        self.assertNotIn("reviewed signals", alternative)
        self.assertNotIn("source-notes", alternative)
        self.assertNotIn("confidence-", alternative)
        self.assertIn("max-width: 680px", css)
        self.assertIn("grid-template-columns: 40px minmax(0, 1fr)", css)
        self.assertIn("font-size: 48px", css)
        self.assertIn("--canvas: #ffffff", css)
        self.assertIn("--card: #ffffff", css)
        self.assertIn("background: var(--card)", css)
        self.assertTrue(all(item.get("url") for item in items))
        self.assertTrue(all(item.get("why_it_matters") for item in items))
        self.assertTrue(all(item.get("confidence") for item in items))
        self.assertTrue(all(item.get("caveat") for item in items))


if __name__ == "__main__":
    unittest.main()
