import hashlib
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import build


def social_card_url() -> str:
    digest = hashlib.sha256(
        (ROOT / "site" / "social-card.png").read_bytes()
    ).hexdigest()[:12]
    return f"https://ai.sarawak.news/social-card.png?v={digest}"


def site_copy() -> dict[str, str]:
    return build.load_site()


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
        self.assertIn('<header class="bar">', html)
        self.assertIn('<div class="bar-inner">', html)
        copy = site_copy()
        self.assertIn(
            '<span class="brand-lockup"><a class="brand" href="/">'
            '<img class="brand-mark brand-mark-light" src="icons/nav-mark-transparent.svg" alt="" width="220" height="220" decoding="async" aria-hidden="true" />'
            '<img class="brand-mark brand-mark-dark" src="icons/nav-mark-transparent-dark.svg" alt="" width="220" height="220" decoding="async" aria-hidden="true" />'
            f'<span class="brand-text">{copy["title"]}</span></a></span>',
            html,
        )
        self.assertTrue((ROOT / "dist" / "icons" / "nav-mark-transparent.svg").is_file())
        self.assertTrue((ROOT / "dist" / "icons" / "nav-mark-transparent-dark.svg").is_file())
        self.assertIn(".brand-mark", css)
        self.assertIn("white-space: nowrap", css)
        self.assertIn('<nav class="site-nav" id="primary-navigation" aria-label="Primary">', html)
        self.assertIn('<a class="site-nav-link is-active" href="/" aria-current="page">Home</a>', html)
        self.assertIn('<a class="site-nav-link" href="tracker.html">Tracker</a>', html)
        self.assertIn('<a class="site-nav-link" href="about.html">About</a>', html)
        self.assertIn('<span class="bar-rule-tail" aria-hidden="true"></span>', html)
        updated_iso, _, compact_updated = self.updated_labels()
        self.assertIn(f'<span class="updated-label">Last updated</span><time datetime="{updated_iso}">{compact_updated}</time>', html)
        self.assertIn(compact_updated, html)
        self.assertLess(html.index('class="brief-deck"'), html.index('class="updated"'))
        self.assertEqual(html.count('class="brief-net"'), 1)
        self.assertLess(html.index('class="brief-net"'), html.index('id="brief-title"'))
        self.assertIn('<svg class="brief-net" role="presentation" viewBox="0 0 520 480"', html)
        self.assertIn('cx="260" cy="220" r="9"', html)
        self.assertIn('x1="80" y1="90" x2="180" y2="60"', html)
        self.assertIn(copy["tagline"], html)
        self.assertIn(f'<h1 id="brief-title">{copy["tagline"]}</h1>', html)
        self.assertIn("Each card links to its source.", html)
        self.assertIn("Latest intelligence signals", html)
        self.assertIn('Built by <a class="site-footer-link site-footer-credit-link" href="https://hafiy.my" target="_blank" rel="noopener noreferrer">hafiy.my</a>, an independent publication. Not affiliated with the Sarawak Government.', html)
        self.assertIn('class="site-footer"', html)
        self.assertIn('site-footer-main site-footer-main--column-stacks', html)
        self.assertIn('site-footer-grid-brand-cell', html)
        self.assertIn('site-footer-grid-stack-left', html)
        self.assertIn('site-footer-grid-stack-right', html)
        self.assertIn(
            '<nav aria-label="Explore" class="site-footer-nav site-footer-grid-explore">',
            html,
        )
        self.assertIn(f'<p class="site-footer-brand">{copy["title"]}</p>', html)
        self.assertIn('<p class="site-footer-note">', html)
        self.assertIn('<br class="site-footer-note-break" />', html)
        self.assertIn(
            'AI news updates are sourced from public reports, news outlets, and official '
            'announcements.<br class="site-footer-note-break" />Each item links to its '
            'source and includes a concise editorial summary.',
            html,
        )
        self.assertIn('<h2>Explore</h2>', html)
        self.assertIn('<a class="site-footer-link" href="/" aria-current="page">Home</a>', html)
        self.assertIn('<a class="site-footer-link" href="tracker.html">Tracker</a>', html)
        self.assertIn('<a class="site-footer-link" href="about.html">About</a>', html)
        self.assertIn('<a class="site-footer-link" href="mailto:contact@sarawak.news">Contact</a>', html)
        explore_nav, _ = html.split(
            '<nav aria-label="Explore" class="site-footer-nav site-footer-grid-explore">',
            1,
        )[1].split("</nav>", 1)
        self.assertNotIn('href="https://sarawak.news/"', explore_nav)
        self.assertNotIn('href="https://events.sarawak.news/"', explore_nav)
        self.assertNotIn('href="https://bantuan.sarawak.news/"', explore_nav)
        self.assertIn('<nav aria-label="Hub" class="site-footer-fleet-nav">', html)
        self.assertIn('site-footer-grid-fleet', html)
        self.assertIn("<h2>Hub</h2>", html)
        self.assertNotIn('class="site-footer-grid-explore-divider"', html)
        self.assertIn('<a class="site-footer-link" href="https://sarawak.news/">Sarawak</a>', html)
        self.assertIn(
            '<a class="site-footer-link" href="https://events.sarawak.news/">Events</a>',
            html,
        )
        self.assertIn(
            '<a class="site-footer-link" href="https://bantuan.sarawak.news/">Bantuan</a>',
            html,
        )
        fleet_block = html.split('class="site-footer-fleet-nav"', 1)[1].split("</nav>", 1)[0]
        self.assertLess(
            fleet_block.index(">Sarawak</a>"),
            fleet_block.index(">Events</a>"),
        )
        self.assertLess(
            fleet_block.index(">Events</a>"),
            fleet_block.index(">Bantuan</a>"),
        )
        self.assertNotIn('rel="nofollow"', html.split("site-footer", 1)[1])
        self.assertNotIn("https://ai.sarawak.news/", html.split('class="site-footer-fleet-nav"', 1)[1])
        self.assertNotIn(">AI</a>", fleet_block)
        self.assertIn('class="back-to-top" type="button" data-back-to-top aria-label="Back to top" hidden', html)
        self.assertIn('class="back-to-top-label">Back to top</span>', html)
        self.assertIn('class="back-to-top-arrow" aria-hidden="true">↑</span>', html)
        self.assertEqual(html.count('class="story-card"'), expected_items)
        self.assertEqual(html.count('class="story-section"'), expected_items)
        self.assertEqual(html.count('class="story-source-label"'), expected_items)
        self.assertNotIn('class="story-source-prefix"', html)
        self.assertNotIn("Read on", html)
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
        description = copy["description"]
        page_title = build.seo_document_title(copy)
        self.assertEqual(len(description), 153)
        self.assertIn(f'<meta name="description" content="{description}" />', html)
        self.assertIn(f'<meta property="og:description" content="{description}" />', html)
        self.assertIn(f'<meta name="twitter:description" content="{description}" />', html)
        self.assertIn('<meta name="google-site-verification" content="5Ro7_ZjEKgT00hwHzOx0paD1Cme1tLYEGdttr_CwHvo" />', html)
        self.assertIn('<meta name="robots" content="index,follow" />', html)
        self.assertIn(f'<meta property="og:title" content="{copy["title"]}" />', html)
        self.assertIn(f'<meta property="og:site_name" content="{copy["title"]}" />', html)
        self.assertIn('<meta property="og:url" content="https://ai.sarawak.news/" />', html)
        card = social_card_url()
        self.assertIn(f'<meta property="og:image" content="{card}" />', html)
        self.assertIn('<meta property="og:image:width" content="1200" />', html)
        self.assertIn('<meta property="og:image:height" content="630" />', html)
        self.assertIn('<meta name="twitter:card" content="summary_large_image" />', html)
        self.assertIn(f'<meta name="twitter:image" content="{card}" />', html)
        self.assertIn('<link rel="canonical" href="https://ai.sarawak.news/" />', html)
        self.assertIn(
            f'<link rel="alternate" type="application/rss+xml" title="{copy["title"]}" '
            'href="https://ai.sarawak.news/feed.xml" />',
            html,
        )
        self.assertIn(f'<meta name="twitter:title" content="{copy["title"]}" />', html)
        self.assertIn(f'<title>{page_title}</title>', html)
        self.assertIn('<script type="application/ld+json">', html)
        social_card = ROOT / "dist" / "social-card.png"
        self.assertTrue(social_card.exists())
        self.assertGreater(social_card.stat().st_size, 1000)
        self.assertIn('"@type":"Organization"', html)
        self.assertIn('"@type":"WebSite"', html)
        self.assertIn('"@type":"CollectionPage"', html)
        self.assertIn('"@type":"ItemList"', html)
        structured_data = html.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0]
        schema = json.loads(structured_data)
        self.assertEqual(
            [node["@type"] for node in schema["@graph"]],
            ["Organization", "WebSite", "CollectionPage", "ItemList"],
        )
        organization, website, collection, item_list = schema["@graph"]
        self.assertEqual(organization["name"], copy["title"])
        self.assertIn("logo", organization)
        self.assertTrue(organization["logo"]["url"].startswith("https://ai.sarawak.news/icons/nav-mark-transparent.svg?v="))
        self.assertEqual(website["name"], copy["title"])
        self.assertEqual(website["description"], description)
        self.assertEqual(website["publisher"], {"@id": "https://ai.sarawak.news/#organization"})
        self.assertEqual(collection["name"], page_title)
        self.assertEqual(collection["description"], description)
        self.assertEqual(item_list["numberOfItems"], expected_items)
        self.assertEqual(len(item_list["itemListElement"]), expected_items)
        self.assertEqual(item_list["itemListElement"][0]["position"], 1)
        self.assertTrue(item_list["itemListElement"][0]["url"].startswith("https://"))
        sitemap = (ROOT / "dist" / "sitemap.xml").read_text()
        self.assertIn(f"<lastmod>{updated_iso[:10]}</lastmod>", sitemap)
        self.assertIn("<loc>https://ai.sarawak.news/about.html</loc>", sitemap)
        section_names = {
            "policy": "Policy",
            "public-services": "Public Services",
            "education": "Education",
            "workforce": "Workforce",
            "research": "Research",
            "infrastructure": "Infrastructure",
            "business": "Business",
        }
        for category, section_name in section_names.items():
            category_path = ROOT / "dist" / f"{category}.html"
            self.assertTrue(category_path.exists())
            category_html = category_path.read_text()
            self.assertNotIn(f"<loc>https://ai.sarawak.news/{category}.html</loc>", sitemap)
            self.assertIn('<meta name="robots" content="noindex,follow" />', category_html)
            self.assertIn('<meta http-equiv="refresh" content="0;url=https://ai.sarawak.news/" />', category_html)
            self.assertIn('<link rel="canonical" href="https://ai.sarawak.news/" />', category_html)
            self.assertIn('location.replace("https://ai.sarawak.news/");', category_html)
            self.assertIn(f'href="https://ai.sarawak.news/">Continue to {copy["title"]}</a>', category_html)
            self.assertIn(f'<title>{section_name} stories moved | {copy["title"]}</title>', category_html)
            self.assertNotIn('class="story-card"', category_html)
        self.assertEqual(sitemap.count("<url>"), 4)
        self.assertIn("<loc>https://ai.sarawak.news/</loc>", sitemap)
        self.assertIn("<loc>https://ai.sarawak.news/tracker.html</loc>", sitemap)
        self.assertIn("<loc>https://ai.sarawak.news/about.html</loc>", sitemap)
        self.assertIn("<loc>https://ai.sarawak.news/feed.xml</loc>", sitemap)
        self.assertNotIn("brief-about", html)
        self.assertNotIn("About this brief", html)
        about_html = (ROOT / "dist" / "about.html").read_text()
        self.assertIn('id="about-network"', about_html)
        network = about_html.split('id="about-network"', 1)[1].split("</ul>", 1)[0]
        self.assertIn('href="https://sarawak.news/"', network)
        self.assertIn('href="https://events.sarawak.news/"', network)
        self.assertIn('href="https://bantuan.sarawak.news/"', network)
        self.assertNotIn("about.html", network)
        self.assertNotIn(" · <a href=", network)
        self.assertNotIn("pcds2030", about_html.lower())
        self.assertNotIn('href="https://ai.sarawak.news/"', network)
        feed_xml = (ROOT / "dist" / "feed.xml").read_text()
        ET.fromstring(feed_xml)
        self.assertIn(f"<title>{copy['title']}</title>", feed_xml)
        self.assertIn("<link>https://ai.sarawak.news/</link>", feed_xml)
        self.assertEqual(feed_xml.count("<item>"), expected_items)
        self.assertNotIn('<a class="site-footer-link" href="/policy.html">Policy</a>', html)
        self.assertNotIn('<h2 class="site-footer-categories-title">Categories</h2>', html)
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
        self.assertIn("grid-template-columns: 28px minmax(0, 1fr)", css)
        self.assertIn('font-family: "Geist"', css)
        self.assertIn('url("fonts/Geist-Variable.woff2")', css)
        self.assertIn("font-display: swap", css)
        self.assertIn("ui-sans-serif, system-ui", css)
        self.assertNotIn("shadcn.io", css)
        geist = ROOT / "dist" / "fonts" / "Geist-Variable.woff2"
        self.assertEqual(geist.read_bytes()[:4], b"wOF2")
        self.assertGreater(geist.stat().st_size, 1000)
        self.assertEqual(geist.read_bytes(), (ROOT / "site" / "fonts" / "Geist-Variable.woff2").read_bytes())
        self.assertIn("SIL OPEN FONT LICENSE", (ROOT / "dist" / "fonts" / "OFL.txt").read_text(encoding="utf-8"))
        self.assertIn('rel="preload" href="fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin', html)
        self.assertIn('data-category-scroll', html)
        self.assertIn("can-scroll-end", js)
        self.assertIn("can-scroll-start", js)
        self.assertIn("border-color: var(--sarawak-yellow);", css)
        self.assertIn("button { font: inherit; }", css)
        self.assertIn("/* sn-kit:footer-column-stacks:begin */", css)
        self.assertIn(".site-footer-main.site-footer-main--column-stacks", css)
        self.assertIn("--sn-footer-stack-inset: 28px", css)
        self.assertIn(".site-footer-fleet-nav", css)
        self.assertIn(".site-footer-nav .site-footer-link:hover", css)
        self.assertIn("border-top: 1px solid var(--line)", css)
        self.assertIn("color: var(--sarawak-red);", css)
        self.assertIn("font-weight: 700", css)
        self.assertIn("text-decoration-color: var(--sarawak-red)", css)
        self.assertIn(".site-nav-link.is-active", css)
        self.assertIn("border-color: transparent", css)
        self.assertIn("background: var(--sarawak-black)", css)
        self.assertIn("font-size: clamp(40px, 6vw, 48px)", css)
        self.assertIn("font-weight: 700", css)
        self.assertIn(".js .story-card:not(.is-revealed)", css)
        self.assertIn("opacity: 0;\n  transform: translateY(12px);", css)
        self.assertIn(".js .story-card.is-revealed {\n  animation: story-reveal .7s cubic-bezier(.22, 1, .36, 1) both;\n}", css)
        self.assertNotIn("animation-delay: calc(.65s + var(--story-delay, 0) * 75ms)", css)
        self.assertNotIn("--story-delay", html)
        self.assertIn('document.documentElement.classList.add("js")', html)
        self.assertIn("IntersectionObserver", js)
        self.assertIn('rootMargin: "0px"', js)
        self.assertIn("threshold: 0", js)
        self.assertIn('classList.add("is-revealed")', js)
        self.assertIn("revealObserver.unobserve(entry.target)", js)
        self.assertIn("@keyframes story-reveal", css)
        self.assertIn(".brief {\n  max-width: 760px;", css)
        self.assertIn("animation: hero-reveal .85s cubic-bezier(.22, 1, .36, 1) both;", css)
        self.assertIn(".category-hero {\n  padding: 58px 0 40px;\n  border-bottom: 1px solid var(--line);\n  animation: hero-reveal .85s cubic-bezier(.22, 1, .36, 1) both;\n}", css)
        self.assertIn("position: relative;", css)
        self.assertNotIn("position: sticky;\n  top: 0;", css)
        self.assertIn("margin-left: calc(50% - 50vw);", css)
        self.assertIn(".bar-inner {", css)
        self.assertIn("overflow-x: clip;", css)
        self.assertNotIn("scroll-padding-top:", css)
        self.assertNotIn(".bar.is-scrolled", css)
        self.assertNotIn('classList.toggle("is-scrolled"', js)
        self.assertIn(".js .story-card:not(.is-revealed),\n  .js .story-card.is-revealed {\n    opacity: 1;\n    transform: none;\n    animation: none;\n  }", css)
        self.assertIn("@keyframes hero-reveal", css)
        self.assertIn("@keyframes hero-content-reveal", css)
        self.assertIn("background: var(--card)", css)
        self.assertIn('html[data-theme="dark"]', css)
        self.assertIn('html[data-theme="dark"] .brief { background: var(--page); }', css)
        self.assertIn("padding: 42px 44px 46px", css)
        self.assertIn(".brief-net", css)
        self.assertIn("color: #cfd3da", css)
        self.assertIn("opacity: 0.37", css)
        self.assertIn('html[data-theme="dark"] .brief-net', css)
        self.assertIn("opacity: 0.42", css)
        self.assertIn("margin: 0 auto 24px", css)
        self.assertIn(".story-list {\n  max-width: 760px;\n  margin: 0 auto;\n  display: grid;\n  gap: 14px;\n}", css)
        self.assertIn(".story-card {\n  width: 100%;\n  padding: 16px;", css)
        self.assertIn(".story-summary {\n  margin: 8px 0 0;", css)
        self.assertIn(".story-card {\n    grid-template-columns: 26px minmax(0, 1fr);\n    gap: 10px;\n    padding: 14px;\n  }", css)
        self.assertIn("grid-template-columns: 28px minmax(0, 1fr);", css)
        self.assertIn(".story-rank {\n  width: 26px;\n  height: 26px;", css)
        self.assertIn(".story-card:focus-visible {\n  outline: 3px solid var(--sarawak-yellow);\n  outline-offset: 3px;\n}", css)
        self.assertIn('.story-card:hover h2 a::after {\n    content: "↗";\n    margin-left: .28em;\n  }', css)
        self.assertIn("@media (hover: hover) {\n  .story-card:hover h2 a::after {\n    content: \"↗\";\n    margin-left: .28em;\n  }\n}", css)
        self.assertNotIn("is-mid-scroll", css)
        self.assertNotIn("is-mid-scroll", js)
        self.assertNotIn('rootMargin: "-45% 0px -45% 0px"', js)
        self.assertNotIn('matchMedia("(hover: none), (pointer: coarse)")', js)
        self.assertNotIn("@media (hover: none), (pointer: coarse) {\n  .story-card h2 a::after", css)
        self.assertNotIn(".story-source-prefix", css)
        self.assertNotIn(".story-source-arrow", css)
        self.assertNotIn("padding: 12px", css)
        self.assertNotIn("social-card.png", css)
        self.assertIn("--canvas: #0f1115", css)
        self.assertIn(".theme-toggle", css)
        self.assertIn("setTheme", js)
        self.assertIn("font-size: 16px", css)
        self.assertIn("--canvas: #ffffff", css)
        self.assertIn("--card: #ffffff", css)
        self.assertIn("background: var(--card)", css)
        self.assertIn("background: var(--sarawak-black)", css)
        self.assertIn(".back-to-top:hover", css)
        self.assertIn(".back-to-top .back-to-top-arrow", css)
        self.assertIn("sn-kit:back-to-top", css)
        self.assertIn("sn-kit:back-to-top", js)
        self.assertIn("rotate(-.25deg)", css)
        self.assertIn(".story-card:hover", css)
        self.assertIn(".story-card:hover h2 a", css)
        self.assertIn("color: var(--ink);", css)
        self.assertIn('tabindex="0"', html)
        self.assertIn('story.addEventListener("click"', js)
        self.assertIn(".back-to-top-label{display:none}", css)
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
        self.assertIn('window.scrollY >= 600', js)
        self.assertIn('window.scrollTo({ top: 0', js)
        # Old category chip labels must stay out of the filter UI (fleet may use short names).
        category_block = html.split("data-category-filter", 1)[1].split("</section>", 1)[0]
        for label in [">AI<", ">Tech<", ">PCDS 2030<", ">Startups<", ">Energy<", ">Events<"]:
            self.assertNotIn(label, category_block)
        public_items = json.loads((ROOT / "dist" / "items.json").read_text())
        self.assertEqual(len(public_items), expected_items)
        self.assertTrue(all(item["date"] for item in public_items))
        public_titles = {item["title"] for item in public_items}
        self.assertIn("AI to transform Sarawak's economy, services, workforce productivity", public_titles)
        self.assertIn("Digital State: Sarawak adopts AI to address citizen needs", public_titles)
        self.assertIn("Sarawak eyes sovereign AI infrastructure", public_titles)
        self.assertIn("Sarawak's AI future takes shape", public_titles)
        self.assertIn("Sarawak expands early intervention with AI screening", public_titles)
        self.assertIn("Managing transition to AI-native economy", public_titles)
        self.assertNotIn("Sarawak Digital Economy Research Grant", public_titles)
        self.assertNotIn("Sarawak Digital Economy Research Grant", html)
        self.assertTrue(all(item.get("url") for item in public_items))
        self.assertTrue(all(item.get("why_it_matters") for item in public_items))
        self.assertFalse(any("confidence" in item for item in public_items))
        self.assertFalse(any("caveat" in item for item in public_items))

        about = (ROOT / "dist" / "about.html").read_text()
        about_title = build.about_document_title(copy)
        about_description = build.about_meta_description(copy)
        self.assertEqual(len(about_description), 97)
        self.assertIn(f'<title>{about_title}</title>', about)
        self.assertIn(f'<meta property="og:title" content="{about_title}" />', about)
        self.assertIn(f'<meta name="twitter:title" content="{about_title}" />', about)
        self.assertNotIn(f'<meta property="og:title" content="{copy["title"]}" />', about)
        self.assertIn(f'<meta name="description" content="{about_description}" />', about)
        self.assertIn(f'<h1>About {copy["title"]}</h1>', about)
        self.assertIn(copy["about_lead"], about)
        card = social_card_url()
        self.assertIn(f'<meta property="og:image" content="{card}" />', about)
        self.assertIn('<meta property="og:image:width" content="1200" />', about)
        self.assertIn('<meta property="og:image:height" content="630" />', about)
        self.assertIn('<meta name="twitter:card" content="summary_large_image" />', about)
        self.assertIn(f'<meta name="twitter:image" content="{card}" />', about)
        self.assertNotIn('<meta name="twitter:card" content="summary" />', about)
        self.assertIn('<a class="site-nav-link" href="/">Home</a>', about)
        self.assertIn('<a class="site-nav-link" href="tracker.html">Tracker</a>', about)
        self.assertIn('<a class="site-nav-link is-active" href="about.html" aria-current="page">About</a>', about)
        self.assertNotIn("Who runs", about)
        self.assertIn("Why Sarawak AI", about)
        self.assertIn("This brief helps Sarawakians in general to keep track of them.", about)
        self.assertNotIn("policymakers, researchers, educators", about)
        self.assertIn("How stories are picked and checked", about)
        self.assertIn(
            "<p>Daily scan checks public news and official pages for Sarawak AI developments. Approved items get a short original summary and a link to the source.</p>",
            about,
        )
        self.assertNotIn("We never republish full articles", about)
        self.assertNotIn("puts AI at the centre of the news", about)
        self.assertNotIn("Purely promotional pages are left out", about)
        self.assertNotIn("The Borneo Post, DayakDaily", about)
        self.assertNotIn('class="about-steps"', about)
        self.assertNotIn("How often it updates", about)
        self.assertNotIn("about-cadence-title", about)
        self.assertIn("Every story is tagged with one of seven categories:", about)
        self.assertNotIn("each category has its own page", about)
        self.assertIn("Contact", about)
        self.assertIn('href="mailto:contact@sarawak.news"', about)
        self.assertIn("contact@sarawak.news", about)
        self.assertNotIn("To get in touch, visit", about)
        self.assertNotIn("Corrections", about)
        self.assertNotIn("[Nazirul to confirm", about)
        self.assertNotIn("[contact:", about)
        self.assertNotIn('class="about-facts"', about)
        self.assertNotIn('class="about-topics"', about)
        self.assertIn('class="theme-toggle"', about)
        self.assertIn('class="site-footer"', about)
        self.assertIn(
            '<nav aria-label="Explore" class="site-footer-nav site-footer-grid-explore">',
            about,
        )
        self.assertIn('<a class="site-footer-link" href="/">Home</a>', about)
        self.assertIn('<a class="site-footer-link" href="tracker.html">Tracker</a>', about)
        self.assertIn('<a class="site-footer-link" href="about.html" aria-current="page">About</a>', about)
        self.assertIn('aria-label="Hub"', about)
        self.assertIn('class="site-footer-fleet-nav"', about)
        self.assertIn('<a class="site-footer-link" href="https://sarawak.news/">Sarawak</a>', about)
        about_explore, _ = about.split(
            '<nav aria-label="Explore" class="site-footer-nav site-footer-grid-explore">',
            1,
        )[1].split(
            "</nav>", 1
        )
        self.assertNotIn('href="https://sarawak.news/"', about_explore)
        self.assertNotIn('rel="nofollow"', about.split("site-footer", 1)[1])
        self.assertIn('<a class="site-footer-link" href="mailto:contact@sarawak.news">Contact</a>', about)
        self.assertNotIn('site-footer-categories-title', about)
        self.assertIn('class="about-page"', about)
        self.assertIn('document.documentElement.classList.add("js")', about)
        self.assertNotIn('class="brief-net"', about)

    def test_build_preserves_only_supported_routes(self):
        alternative_dir = ROOT / "dist" / "alternative"
        alternative_dir.mkdir(parents=True, exist_ok=True)
        (alternative_dir / "legacy.html").write_text("stale alternative")
        deferred_about = ROOT / "dist" / "about.html"
        deferred_about.write_text("future about page")

        subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        self.assertFalse(alternative_dir.exists())
        self.assertTrue(deferred_about.exists())
        self.assertIn(f'About {site_copy()["title"]}', deferred_about.read_text())

    def test_analytics_loader_production_gate_and_internal_traffic(self):
        loader = build.render_analytics_loader()
        self.assertEqual(build.GA_MEASUREMENT_ID, "G-RJ2ZFQ52J7")
        self.assertEqual(build.GA_PRODUCTION_HOSTS, ("ai.sarawak.news", "www.ai.sarawak.news"))
        self.assertEqual(build.GA_INTERNAL_COOKIE, "sn_internal")
        self.assertEqual(build.GA_INTERNAL_MAX_AGE_SECONDS, 365 * 24 * 60 * 60)
        self.assertEqual(build.CLOUDFLARE_WEB_ANALYTICS_TOKEN, "092a061973fc4d899cd2e4b52952af89")
        self.assertIn("data-sn-analytics-loader", loader)
        self.assertIn("ai.sarawak.news", loader)
        self.assertIn("www.ai.sarawak.news", loader)
        self.assertIn("G-RJ2ZFQ52J7", loader)
        self.assertIn("sn_internal", loader)
        self.assertIn("31536000", loader)
        self.assertIn("get('internal')", loader)
        self.assertIn("/^1[`.)\\]]?$/.test(q.get('internal')||'')", loader)
        self.assertIn("traffic_type", loader)
        self.assertIn("'internal'", loader)
        self.assertIn("createElement('script')", loader)
        self.assertIn("static.cloudflareinsights.com/beacon.min.js", loader)
        self.assertIn("092a061973fc4d899cd2e4b52952af89", loader)
        self.assertIn("spa:true", loader)
        self.assertNotIn('<script async src="https://www.googletagmanager.com/gtag/js', loader)
        self.assertIn("H.indexOf(h)<0", loader)

    def test_internal_query_accepts_one_trailing_stray(self):
        """Mirror the loader regex: 1, or 1 + one of ` . ) ]."""
        import re
        from urllib.parse import parse_qs

        loader = build.render_analytics_loader()
        self.assertIn("/^1[`.)\\]]?$/.test(q.get('internal')||'')", loader)
        pattern = re.compile(r"^1[`.)\]]?$")
        accept = ("1", "1`", "1.", "1)", "1]")
        reject = ("10", "1x", "1``", "2", "1 ", "", "11", "1[")
        for value in accept:
            self.assertTrue(pattern.fullmatch(value), value)
        for value in reject:
            self.assertIsNone(pattern.fullmatch(value), value)
        # URLSearchParams decoding used by the loader (?internal=1%60 → 1`).
        self.assertEqual(parse_qs("internal=1%60")["internal"][0], "1`")
        self.assertTrue(pattern.fullmatch(parse_qs("internal=1%60")["internal"][0]))
        self.assertTrue(pattern.fullmatch(parse_qs("internal=1.")["internal"][0]))
        self.assertIsNone(pattern.fullmatch(parse_qs("internal=10")["internal"][0]))

    def test_published_pages_include_shared_analytics_loader(self):
        loader = build.render_analytics_loader()
        subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        pages = [
            ROOT / "dist" / "index.html",
            ROOT / "dist" / "tracker.html",
            ROOT / "dist" / "about.html",
        ]
        for page in pages:
            html = page.read_text()
            self.assertEqual(html.count("data-sn-analytics-loader"), 1, page.name)
            self.assertEqual(html.count(loader), 1, page.name)
            self.assertLess(html.index(loader), html.index("</head>"))
            self.assertIn("G-RJ2ZFQ52J7", html)
            self.assertIn("traffic_type", html)
            self.assertIn("sn_internal", html)
            self.assertNotIn("plausible.io", html)
            self.assertNotIn("umami", html)
        for name in ("index.html", "tracker.html", "about.html"):
            self.assertIn(
                '<meta name="google-site-verification" content="5Ro7_ZjEKgT00hwHzOx0paD1Cme1tLYEGdttr_CwHvo" />',
                (ROOT / "dist" / name).read_text(),
            )

    def test_tracker_page_matches_v2_shape(self):
        initiatives = json.loads((ROOT / "data" / "initiatives.json").read_text())
        items = {item["id"]: item for item in self.reviewed_items()}
        subprocess.run([sys.executable, "scripts/build.py"], cwd=ROOT, text=True, capture_output=True, check=True)
        html = (ROOT / "dist" / "tracker.html").read_text()
        css = (ROOT / "dist" / "style.css").read_text()
        self.assertIn('<a class="site-nav-link is-active" href="tracker.html" aria-current="page">Tracker</a>', html)
        self.assertIn("AI initiatives by Sarawak government agencies", html)
        self.assertIn("Each initiative links to the ai.sarawak.news story it comes from.", html)
        self.assertNotIn("tv2-summary", html)
        self.assertNotIn("tv2-metric", html)
        self.assertNotIn(".tv2-summary", css)
        self.assertNotIn(".tv2-metric", css)
        self.assertIn('data-agency="all">All</button>', html)
        self.assertIn('aria-label="Search initiatives"', html)
        self.assertIn('class="tv2-grid"', html)
        self.assertNotIn("Logo<br />pending", html)
        self.assertIn('class="tv2-status"', html)
        self.assertIn("Latest update", html)
        self.assertIn(">Sources</h3>", html)
        self.assertIn("ai.sarawak.news — ", html)
        self.assertIn(" — original report", html)
        self.assertIn(".tv2-grid", css)
        self.assertTrue((ROOT / "dist" / "logos" / "saic.webp").is_file())
        self.assertTrue((ROOT / "dist" / "logos" / "petros.png").is_file())
        self.assertTrue((ROOT / "dist" / "logos" / "sdec.jpg").is_file())
        self.assertTrue((ROOT / "dist" / "logos" / "sains.jpg").is_file())
        self.assertTrue((ROOT / "dist" / "logos" / "sarawak-government.svg").is_file())
        self.assertTrue((ROOT / "dist" / "logos" / "meitd-black.png").is_file())
        self.assertTrue((ROOT / "dist" / "logos" / "mphlg.jpg").is_file())
        self.assertTrue((ROOT / "dist" / "logos" / "mficord.jpg").is_file())
        self.assertIn('src="logos/sains.jpg"', html)
        self.assertIn('src="logos/sarawak-government.svg"', html)
        self.assertIn('src="logos/meitd-black.png"', html)
        self.assertIn('src="logos/mphlg.jpg"', html)
        self.assertIn('src="logos/mficord.jpg"', html)
        self.assertEqual(html.count('class="tv2-card"'), len(initiatives))
        for row in initiatives:
            story = items[row["story_id"]]
            self.assertIn(row["initiative"], html)
            self.assertIn(f'/#{row["story_id"]}', html)
            self.assertIn(build.esc(story["title"]), html)
            self.assertIn(story["url"], html)
        titles = [row["initiative"] for row in initiatives]
        positions = [html.index(title) for title in sorted(titles, key=str.casefold)]
        self.assertEqual(positions, sorted(positions))


if __name__ == "__main__":
    unittest.main()
