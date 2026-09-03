import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build


class BuildTest(unittest.TestCase):
    @staticmethod
    def reviewed_items():
        return json.loads((ROOT / "data" / "items.json").read_text())

    @classmethod
    def updated_labels(cls):
        return build.last_updated(cls.reviewed_items())

    def test_last_updated_follows_newest_reviewed_item(self):
        items = [
            {"date": "2026-01-15"},
            {"date": "2026-08-20"},
            {"date": "2026-07-04"},
        ]
        value, _, compact = build.last_updated(items)
        self.assertEqual(value, "2026-08-20")
        self.assertEqual(compact, "THURSDAY, 20 AUG 2026")

    def test_last_updated_ignores_stale_site_metadata(self):
        site_value = json.loads((ROOT / "data" / "site.json").read_text())["last_updated"]
        newer_than_site = "2026-12-01"
        older_than_site = "2026-01-02"
        self.assertLess(older_than_site, site_value[:10])
        self.assertGreater(newer_than_site, site_value[:10])

        newer_value, _, newer_compact = build.last_updated(
            [{"date": older_than_site}, {"date": newer_than_site}]
        )
        self.assertEqual(newer_value, newer_than_site)
        self.assertEqual(newer_compact, "TUESDAY, 1 DEC 2026")

        older_value, _, older_compact = build.last_updated([{"date": older_than_site}])
        self.assertEqual(older_value, older_than_site)
        self.assertEqual(older_compact, "FRIDAY, 2 JAN 2026")
        self.assertNotEqual(older_value, site_value[:10])

    def test_last_updated_requires_dated_items(self):
        with self.assertRaises(ValueError):
            build.last_updated([])
        with self.assertRaises(ValueError):
            build.last_updated([{"title": "undated"}])

    def test_build_last_updated_tracks_newest_item_not_site_json(self):
        newest = max(item["date"] for item in self.reviewed_items())
        site_day = json.loads((ROOT / "data" / "site.json").read_text())["last_updated"][:10]
        value, _, compact = self.updated_labels()
        self.assertEqual(value, newest)

        subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        html = (ROOT / "dist" / "index.html").read_text()
        sitemap = (ROOT / "dist" / "sitemap.xml").read_text()
        self.assertIn(
            f'<span class="updated-label">Last updated</span><time datetime="{newest}">{compact}</time>',
            html,
        )
        self.assertIn(f"<lastmod>{newest}</lastmod>", sitemap)
        if site_day != newest:
            self.assertNotIn(f'<time datetime="{site_day}"', html)
            self.assertNotIn(f"<lastmod>{site_day}</lastmod>", sitemap)

    def test_seed_data_has_required_fields(self):
        items = json.loads((ROOT / "data" / "items.json").read_text())
        required = {"id", "date", "source", "url", "title", "section", "tags", "summary", "why_it_matters", "confidence", "caveat"}
        categories = {"Policy", "Public Services", "Education", "Workforce", "Research", "Infrastructure", "Business"}
        self.assertGreaterEqual(len(items), 4)
        for item in items:
            self.assertTrue(required.issubset(item), item.get("id"))
            self.assertTrue(item["url"].startswith("https://"))
            self.assertLess(len(item["summary"]), 700)
            self.assertIn(item["section"], categories)

    def test_build_outputs_aligned_style_static_site(self):
        result = subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertIn("Built", result.stdout)
        html = (ROOT / "dist" / "index.html").read_text()
        css = (ROOT / "dist" / "style.css").read_text()
        js = (ROOT / "dist" / "app.js").read_text()
        expected_items = len(json.loads((ROOT / "data" / "items.json").read_text()))
        self.assertIn('<span class="brand-lockup"><a class="brand" href="/">AI.Sarawak.News</a></span>', html)
        self.assertIn('<nav class="site-nav" id="primary-navigation" aria-label="Primary">', html)
        self.assertIn('<a class="site-nav-link is-active" aria-current="page" href="/">Home</a>', html)
        self.assertIn('<a class="site-nav-link" href="about.html">About</a>', html)
        self.assertIn('<span class="bar-rule-tail" aria-hidden="true"></span>', html)
        updated_iso, _, compact_updated = self.updated_labels()
        self.assertIn(f'<span class="updated-label">Last updated</span><time datetime="{updated_iso}">{compact_updated}</time>', html)
        self.assertIn(compact_updated, html)
        self.assertLess(html.index('class="brief-deck"'), html.index('class="updated"'))
        self.assertIn("Sarawak AI news, in one place.", html)
        self.assertIn("AI.Sarawak.News tracks artificial intelligence developments across Sarawak", html)
        self.assertIn("bringing Sarawak AI policy, projects, research and adoption", html)
        self.assertIn("Latest intelligence signals", html)
        self.assertIn('Built by <a class="site-footer-link site-footer-credit-link" href="https://hafiy.my" target="_blank" rel="noopener noreferrer">hafiy.my</a>, an independent publication. Not affiliated with the Sarawak Government.', html)
        self.assertIn('class="site-footer"', html)
        self.assertIn('<div class="site-footer-main">', html)
        self.assertIn('<nav aria-label="Explore" class="site-footer-nav">', html)
        self.assertIn('<p class="site-footer-brand">AI.Sarawak.News</p>', html)
        self.assertIn('<p class="site-footer-note">', html)
        self.assertIn('<h2>Explore</h2>', html)
        self.assertIn('<a class="site-footer-link" href="/" aria-current="page">Home</a>', html)
        self.assertIn('<a class="site-footer-link" href="about.html">About</a>', html)
        self.assertIn('AI news updates are sourced from public reports, news outlets, and official announcements.', html)
        self.assertIn('Each item links to its source and includes a concise editorial summary.', html)
        self.assertIn('class="back-to-top" type="button" data-back-to-top aria-label="Back to top" hidden', html)
        self.assertIn('class="back-to-top-label">Back to top</span>', html)
        self.assertIn('class="back-to-top-arrow" aria-hidden="true">↑</span>', html)
        self.assertEqual(html.count('class="story-card"'), expected_items)
        self.assertEqual(html.count('class="story-section"'), expected_items)
        self.assertEqual(html.count('class="story-source-label"'), expected_items)
        self.assertEqual(html.count('class="category-filter-button'), 8)
        self.assertIn('data-category-filter hidden', html)
        self.assertIn('data-section="infrastructure"', html)
        self.assertIn('data-section-filter="all"', html)
        self.assertIn('data-section-filter="policy"', html)
        for category in ["Policy", "Public Services", "Education", "Workforce", "Research", "Infrastructure", "Business"]:
            self.assertIn(f'data-filter-label="{category}"', html)
            self.assertIn(f'class="story-section">{category}</span>', html)
        self.assertIn('<script src="app.js" defer></script>', html)
        self.assertIn('class="story-rank" aria-label="Chronological item 1">1</div>', html)
        self.assertIn('<time datetime="2026-06-24">24 Jun 2026</time>', html)
        description = "Follow Sarawak AI news across policy, public services, education, workforce, research, infrastructure and business."
        self.assertIn(f'<meta name="description" content="{description}" />', html)
        self.assertIn('<meta name="google-site-verification" content="5Ro7_ZjEKgT00hwHzOx0paD1Cme1tLYEGdttr_CwHvo" />', html)
        self.assertIn('<meta name="robots" content="index,follow" />', html)
        self.assertIn('<meta property="og:title" content="Sarawak AI News | AI.Sarawak.News" />', html)
        self.assertIn('<meta property="og:site_name" content="AI.Sarawak.News" />', html)
        self.assertIn('<meta property="og:url" content="https://ai.sarawak.news/" />', html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image" />', html)
        self.assertIn('<link rel="canonical" href="https://ai.sarawak.news/" />', html)
        self.assertIn('<meta name="twitter:title" content="Sarawak AI News | AI.Sarawak.News" />', html)
        self.assertIn('<title>Sarawak AI News | AI.Sarawak.News</title>', html)
        self.assertIn('<script type="application/ld+json">', html)
        self.assertIn('"@type":"WebSite"', html)
        self.assertIn('"@type":"CollectionPage"', html)
        structured_data = html.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
        schema = json.loads(structured_data)
        self.assertEqual([node["@type"] for node in schema["@graph"]], ["WebSite", "CollectionPage"])
        sitemap = (ROOT / "dist" / "sitemap.xml").read_text()
        self.assertIn(f"<lastmod>{updated_iso[:10]}</lastmod>", sitemap)
        self.assertIn("<loc>https://ai.sarawak.news/about.html</loc>", sitemap)
        for category in ["policy", "public-services", "education", "workforce", "research", "infrastructure", "business"]:
            category_path = ROOT / "dist" / f"{category}.html"
            self.assertTrue(category_path.exists())
            category_html = category_path.read_text()
            self.assertIn(f'<link rel="canonical" href="https://ai.sarawak.news/{category}.html" />', category_html)
            self.assertIn(f"<loc>https://ai.sarawak.news/{category}.html</loc>", sitemap)
            self.assertIn('<script type="application/ld+json">', category_html)
            self.assertIn('href="/">View all Sarawak AI news</a>', category_html)
        self.assertEqual(sitemap.count("<url>"), 9)
        self.assertIn('<a class="site-footer-link" href="/policy.html">Policy</a>', html)
        self.assertIn('<a class="site-footer-link" href="/public-services.html">Public Services</a>', html)
        self.assertIn('<h2 class="site-footer-categories-title">Categories</h2>', html)
        self.assertNotIn('>Topics</h2>', html)
        ET.fromstring(sitemap)
        self.assertNotIn("How This Is Built", html)
        self.assertNotIn("Sponsor This Brief", html)
        self.assertNotIn("Make This Brief Shorter", html)
        self.assertNotIn("Get this delivered to your inbox weekly", html)
        self.assertNotIn("Signal categories", html)
        self.assertNotIn("Independent AI brief", html)
        self.assertNotIn("Matched signal terms", html)
        self.assertNotIn('class="story-caveat"', html)
        self.assertNotIn("Source note:", html)
        self.assertIn('target="_blank"', html)
        self.assertIn('data-theme-toggle', html)
        self.assertIn('data-nav-toggle', html)
        self.assertIn('theme-icon-morph', html)
        self.assertIn('localStorage.getItem("sarawak-theme")', html)
        self.assertIn("max-width: 840px", css)
        self.assertIn("max-width: 760px", css)
        self.assertIn(".site-footer", css)
        self.assertIn(".category-page", css)
        self.assertIn(".category-story-list", css)
        self.assertIn("grid-template-columns: 40px minmax(0, 1fr)", css)
        self.assertIn('font-family: "Geist"', css)
        self.assertIn('Geist_Variable-s.p.0mrjj4bg00-he.woff2', css)
        self.assertIn("button { font: inherit; }", css)
        self.assertIn(".site-footer-nav .site-footer-link:hover", css)
        self.assertIn("color: var(--sarawak-red);", css)
        self.assertIn("font-weight: 700", css)
        self.assertIn("text-decoration-color: var(--sarawak-red)", css)
        self.assertIn(".site-nav-link.is-active", css)
        self.assertIn("border-color: transparent", css)
        self.assertIn("background: var(--sarawak-black)", css)
        self.assertIn("font-size: clamp(40px, 6vw, 48px)", css)
        self.assertIn("font-weight: 700", css)
        self.assertIn("animation: story-reveal .7s cubic-bezier(.22, 1, .36, 1) both", css)
        self.assertIn("animation-delay: calc(.65s + var(--story-delay, 0) * 75ms)", css)
        self.assertIn("--story-delay", html)
        self.assertIn("@keyframes story-reveal", css)
        self.assertIn("@keyframes hero-reveal", css)
        self.assertIn("@keyframes hero-content-reveal", css)
        self.assertIn("background: var(--card)", css)
        self.assertIn('html[data-theme="dark"]', css)
        self.assertIn('html[data-theme="dark"] .brief { background: var(--page); }', css)
        self.assertIn("--canvas: #0f1115", css)
        self.assertIn(".theme-toggle", css)
        self.assertIn("setTheme", js)
        self.assertIn("font-size: 16px", css)
        self.assertIn("--canvas: #ffffff", css)
        self.assertIn("--card: #ffffff", css)
        self.assertIn("background: var(--card)", css)
        self.assertIn("background: var(--sarawak-black)", css)
        self.assertIn(".back-to-top:hover", css)
        self.assertIn(".back-to-top:hover .back-to-top-arrow", css)
        self.assertIn(".back-to-top .back-to-top-arrow", css)
        self.assertIn("rotate(-.25deg)", css)
        self.assertIn(".story-card:hover", css)
        self.assertIn(".story-card:hover h2 a", css)
        self.assertIn("color: var(--ink);", css)
        self.assertIn('tabindex="0"', html)
        self.assertIn('story.addEventListener("click"', js)
        self.assertIn(".back-to-top-label { display: none; }", css)
        self.assertIn("color: var(--sarawak-yellow)", css)
        self.assertNotIn("-webkit-line-clamp", css)
        self.assertIn("--sarawak-red: #d22630", css)
        self.assertIn("--sarawak-yellow: #f7c948", css)
        self.assertIn("--sarawak-black: #111111", css)
        self.assertNotIn(".story-rank::after", css)
        self.assertIn(".category-filter-button.is-active", css)
        self.assertIn(".category-filter-options:has(.category-filter-button:hover)", css)
        self.assertIn(".category-filter-button.is-active:not(:hover)", css)
        self.assertIn(".updated-label", css)
        self.assertIn(".updated time", css)
        self.assertIn("padding: 0 0 14px", css)
        self.assertIn("flex-wrap: nowrap", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn(".story-section", css)
        self.assertIn(".story-source", css)
        self.assertIn(".story-source-label", css)
        self.assertIn("background: var(--sarawak-yellow)", css)
        self.assertIn("color: var(--sarawak-black)", css)
        self.assertIn('applyFilter("all")', js)
        self.assertIn("story.hidden = !isVisible", js)
        self.assertIn('button.dataset.sectionFilter !== "all"', js)
        self.assertIn('applyFilter(resetToAll ? "all"', js)
        self.assertIn('history.scrollRestoration = "manual"', js)
        self.assertIn('navigation?.type === "reload"', js)
        self.assertIn('window.scrollY < 600', js)
        self.assertIn('window.scrollTo({ top: 0', js)
        for label in [">AI<", ">Tech<", ">PCDS 2030<", ">Startups<", ">Energy<", ">Events<"]:
            self.assertNotIn(label, html)
        public_items = json.loads((ROOT / "dist" / "items.json").read_text())
        self.assertEqual(len(public_items), expected_items)
        self.assertTrue(all(item["date"] for item in public_items))
        public_titles = {item["title"] for item in public_items}
        self.assertIn("AI to transform Sarawak's economy, services, workforce productivity", public_titles)
        self.assertIn("Digital State: Sarawak adopts AI to address citizen needs", public_titles)
        self.assertIn("Sarawak Eyes Sovereign AI Infrastructure", public_titles)
        self.assertIn("Sarawak's AI future takes shape", public_titles)
        self.assertIn("Sarawak expands early intervention with AI screening", public_titles)
        self.assertIn("Managing transition to AI-native economy", public_titles)
        self.assertNotIn("Sarawak Digital Economy Research Grant", public_titles)
        self.assertNotIn("Sarawak Digital Economy Research Grant", html)
        self.assertTrue(all(item.get("url") for item in public_items))
        self.assertTrue(all(item.get("why_it_matters") for item in public_items))
        self.assertTrue(all(item.get("confidence") for item in public_items))
        self.assertTrue(all(item.get("caveat") for item in public_items))

        about = (ROOT / "dist" / "about.html").read_text()
        self.assertIn('<title>About | AI.Sarawak.News</title>', about)
        self.assertIn('<meta name="description" content="Learn how AI.Sarawak.News reviews and links Sarawak AI news, policy, projects, research and adoption." />', about)
        self.assertIn('<a class="site-nav-link" href="/">Home</a>', about)
        self.assertIn('<a class="site-nav-link is-active" aria-current="page" href="about.html">About</a>', about)
        self.assertIn("What this site does", about)
        self.assertIn("How stories are selected", about)
        self.assertIn("Full article bodies are not republished.", about)
        self.assertNotIn('class="about-facts"', about)
        self.assertNotIn('class="about-topics"', about)
        self.assertIn('class="theme-toggle"', about)
        self.assertIn('class="site-footer"', about)
        self.assertIn('<nav aria-label="Explore" class="site-footer-nav">', about)
        self.assertIn('<a class="site-footer-link" href="/">Home</a>', about)
        self.assertIn('<a class="site-footer-link" href="about.html" aria-current="page">About</a>', about)
        self.assertIn('class="about-page"', about)

    def test_build_preserves_only_supported_routes(self):
        alternative_dir = ROOT / "dist" / "alternative"
        alternative_dir.mkdir(parents=True, exist_ok=True)
        (alternative_dir / "legacy.html").write_text("stale alternative")
        deferred_about = ROOT / "dist" / "about.html"
        deferred_about.write_text("future about page")

        subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertFalse(alternative_dir.exists())
        self.assertTrue(deferred_about.exists())
        self.assertIn("About AI.Sarawak.News", deferred_about.read_text())


if __name__ == "__main__":
    unittest.main()
