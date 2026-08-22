from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"

SECTION_FILTERS = (
    "Policy",
    "Public Services",
    "Education",
    "Workforce",
    "Research",
    "Infrastructure",
    "Business",
)

SITE_URL = "https://ai.sarawak.news/"
SITE_NAME = "AI.Sarawak.News"
SEO_TITLE = "Sarawak AI News | AI.Sarawak.News"
SEO_DESCRIPTION = (
    "Follow Sarawak AI news across policy, public services, education, workforce, "
    "research, infrastructure and business."
)
SITE_INTRODUCTION = (
    "AI.Sarawak.News tracks artificial intelligence developments across Sarawak, "
    "bringing Sarawak AI policy, projects, research and adoption into one source-linked brief."
)
ABOUT_SEO_TITLE = "About | AI.Sarawak.News"
ABOUT_SEO_DESCRIPTION = (
    "Learn how AI.Sarawak.News reviews and links Sarawak AI news, policy, projects, "
    "research and adoption."
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def format_story_date(value: str) -> str:
    date = datetime.strptime(value, "%Y-%m-%d")
    return f"{date.day} {date.strftime('%b %Y')}"


def last_updated() -> tuple[str, str, str]:
    value = load_json(DATA / "site.json")["last_updated"]
    updated = parse_datetime(value)
    time = updated.strftime("%I:%M %p").lstrip("0")
    current = f"{updated.strftime('%A, %B')} {updated.day}, {updated.year}, {time}".upper()
    compact = f"{updated.strftime('%A').upper()}, {updated.day} {updated.strftime('%b %Y').upper()}"
    return value, current, compact


def reviewed_items() -> list[dict]:
    items = load_json(DATA / "items.json")
    return [
        {
            "id": item["id"],
            "title": item["title"],
            "url": item["url"],
            "source": item["source"],
            "date": item["date"],
            "section": item["section"],
            "tags": item["tags"],
            "note": item["summary"],
            "why_it_matters": item["why_it_matters"],
            "confidence": item["confidence"],
            "caveat": item["caveat"],
        }
        for item in sorted(items, key=lambda row: row["date"], reverse=True)
        if item.get("date") and item.get("why_it_matters")
    ]


def load_feed_items() -> list[dict]:
    # Public feed uses reviewed editorial items only. Raw ingestion candidates
    # stay internal until date, relevance, and source quality are checked.
    return reviewed_items()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def render_compact_signal(item: dict, index: int) -> str:
    reveal_delay = min(index - 1, 10)
    return f"""
    <article class="story-card" id="{slug(item['id'])}" data-section="{slug(item['section'])}" style="--story-delay: {reveal_delay}" tabindex="0" aria-label="Open story: {esc(item['title'])}">
      <div class="story-rank" aria-label="Chronological item {index}">{index}</div>
      <div class="story-body">
        <p class="story-meta-row">
          <time datetime="{esc(item['date'])}">{esc(format_story_date(item['date']))}</time>
          <span class="story-source"><span class="story-source-label">{esc(item['source'])}</span></span>
          <span class="story-section">{esc(item['section'])}</span>
        </p>
        <h2><a href="{esc(item['url'])}" target="_blank" rel="noopener noreferrer">{esc(item['title'])}</a></h2>
        <p class="story-summary">{esc(item['note'])}</p>
      </div>
    </article>
    """


def render_category_filter(items: list[dict]) -> str:
    counts = {section: sum(item["section"] == section for item in items) for section in SECTION_FILTERS}
    buttons = [
        f'<button type="button" class="category-filter-button is-active" data-section-filter="all" '
        f'data-filter-label="All stories" aria-pressed="true">All '
        f'<span class="category-filter-count" aria-hidden="true">{len(items)}</span></button>'
    ]
    buttons.extend(
        f'<button type="button" class="category-filter-button" data-section-filter="{slug(section)}" '
        f'data-filter-label="{esc(section)}" aria-pressed="false">{esc(section)} '
        f'<span class="category-filter-count" aria-hidden="true">{counts[section]}</span></button>'
        for section in SECTION_FILTERS
        if counts[section]
    )
    return f"""
    <section class="category-filter" aria-labelledby="category-filter-title" data-category-filter hidden>
      <p class="category-filter-title" id="category-filter-title">Browse by category</p>
      <div class="category-filter-options">
        {' '.join(buttons)}
      </div>
      <p class="visually-hidden" data-filter-status aria-live="polite">Showing all {len(items)} stories</p>
    </section>
    """


def render_site_header(active_page: str) -> str:
    home_current = ' class="site-nav-link is-active" aria-current="page"' if active_page == "home" else ' class="site-nav-link"'
    about_current = ' class="site-nav-link is-active" aria-current="page"' if active_page == "about" else ' class="site-nav-link"'
    return f"""
  <header class="bar">
    <span class="brand-lockup"><a class="brand" href="/">AI.Sarawak.News</a></span>
    <nav class="site-nav" id="primary-navigation" aria-label="Primary">
      <a{home_current} href="/">Home</a>
      <a{about_current} href="about.html">About</a>
    </nav>
    <span class="bar-rule-tail" aria-hidden="true"></span>
    <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-navigation" aria-label="Open navigation" title="Open navigation">
      <span></span><span></span><span></span>
    </button>
    <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
      <svg class="theme-icon-morph" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24">
        <mask id="theme-toggle-moon-mask"><rect width="24" height="24" fill="#fff"></rect><circle cx="17" cy="7" r="7" fill="#000"></circle></mask>
        <circle class="theme-icon-moon" cx="12" cy="12" r="9" mask="url(#theme-toggle-moon-mask)"></circle>
        <circle class="theme-icon-sun" cx="12" cy="12" r="5"></circle>
        <g class="theme-icon-rays">
          <line x1="12" y1="1.6" x2="12" y2="3.8"></line><line x1="12" y1="20.2" x2="12" y2="22.4"></line>
          <line x1="1.6" y1="12" x2="3.8" y2="12"></line><line x1="20.2" y1="12" x2="22.4" y2="12"></line>
          <line x1="4.6" y1="4.6" x2="6.2" y2="6.2"></line><line x1="17.8" y1="17.8" x2="19.4" y2="19.4"></line>
          <line x1="4.6" y1="19.4" x2="6.2" y2="17.8"></line><line x1="17.8" y1="6.2" x2="19.4" y2="4.6"></line>
        </g>
      </svg>
    </button>
  </header>"""


def render_site_footer(active_page: str) -> str:
    home_current = ' aria-current="page"' if active_page == "home" else ""
    about_current = ' aria-current="page"' if active_page == "about" else ""
    return f"""
  <footer class="site-footer">
    <div class="site-footer-main">
      <div class="site-footer-summary">
        <p class="site-footer-brand">AI.Sarawak.News</p>
        <p class="site-footer-note">AI news updates are sourced from public reports, news outlets, and official announcements.<br class="site-footer-note-break" />Each item links to its source and includes a concise editorial summary.</p>
      </div>
      <nav aria-label="Explore" class="site-footer-nav">
        <h2>Explore</h2>
        <ul>
          <li><a class="site-footer-link" href="/"{home_current}>Home</a></li>
          <li><a class="site-footer-link" href="about.html"{about_current}>About</a></li>
        </ul>
      </nav>
    </div>
    <div class="site-footer-bottom">
      <p>Built by <a class="site-footer-link site-footer-credit-link" href="https://hafiy.my" target="_blank" rel="noopener noreferrer">hafiy.my</a>, an independent publication. Not affiliated with the Sarawak Government.</p>
    </div>
  </footer>"""


def render_compact_body(items: list[dict]) -> str:
    feed = "\n".join(render_compact_signal(item, index) for index, item in enumerate(items, 1))
    category_filter = render_category_filter(items)
    updated_iso, _, updated_compact = last_updated()

    return f"""<body>
  <a class="skip-link" href="#content">Skip to content</a>

{render_site_header("home")}

  <main id="content">
    <header class="brief">
      <h1 id="brief-title">Sarawak AI news, in one place.</h1>
      <p class="brief-deck">{esc(SITE_INTRODUCTION)}</p>
      <p class="updated"><span class="updated-label">Last updated</span><time datetime="{esc(updated_iso)}">{esc(updated_compact)}</time></p>
    </header>

    {category_filter}

    <section class="story-list" aria-label="Latest intelligence signals" data-story-list>
      {feed}
    </section>
  </main>

  <button class="back-to-top" type="button" data-back-to-top aria-label="Back to top" hidden><span class="back-to-top-label">Back to top</span> <span class="back-to-top-arrow" aria-hidden="true">↑</span></button>

{render_site_footer("home")}
</body>"""


def render_about_body() -> str:
    return f"""<body>
  <a class="skip-link" href="#content">Skip to content</a>

{render_site_header("about")}

  <main id="content" class="about-page">
    <header class="about-hero">
      <p class="about-eyebrow">About the brief</p>
      <h1>About AI.Sarawak.News</h1>
      <p class="about-lede">An independent, source-linked briefing about how artificial intelligence and digital change are affecting Sarawak.</p>
    </header>

    <section class="about-section" aria-labelledby="about-purpose-title">
      <h2 id="about-purpose-title">What this site does</h2>
      <p>AI.Sarawak.News brings reviewed public reporting into one concise feed. Each story links to its original source and adds a short summary of the Sarawak AI signal, so readers can scan what changed without losing the source behind it.</p>
    </section>

    <section class="about-section" aria-labelledby="about-coverage-title">
      <h2 id="about-coverage-title">What we cover</h2>
      <p>The brief follows AI policy, public services, education, workforce readiness, research, infrastructure and business across Sarawak.</p>
    </section>

    <section class="about-section" aria-labelledby="about-method-title">
      <h2 id="about-method-title">How stories are selected</h2>
      <ol class="about-steps">
        <li><strong>Find the signal.</strong> Public sources are checked for developments with a clear Sarawak and AI or digital-economy connection.</li>
        <li><strong>Verify the source.</strong> Candidate links are opened at the original publication and checked for date, context and relevance.</li>
        <li><strong>Keep the brief concise.</strong> Approved stories receive an original, source-attributed summary. Full article bodies are not republished.</li>
      </ol>
    </section>

  </main>

{render_site_footer("about")}
</body>"""


def render_index(items: list[dict]) -> str:
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebSite",
                    "@id": f"{SITE_URL}#website",
                    "url": SITE_URL,
                    "name": SITE_NAME,
                    "description": SEO_DESCRIPTION,
                    "inLanguage": "en",
                },
                {
                    "@type": "CollectionPage",
                    "@id": f"{SITE_URL}#collection",
                    "url": SITE_URL,
                    "name": SEO_TITLE,
                    "description": SEO_DESCRIPTION,
                    "isPartOf": {"@id": f"{SITE_URL}#website"},
                    "inLanguage": "en",
                },
            ],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{esc(SEO_DESCRIPTION)}" />
  <meta name="google-site-verification" content="5Ro7_ZjEKgT00hwHzOx0paD1Cme1tLYEGdttr_CwHvo" />
  <meta name="robots" content="index,follow" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(SEO_TITLE)}" />
  <meta property="og:description" content="{esc(SEO_DESCRIPTION)}" />
  <meta property="og:url" content="{esc(SITE_URL)}" />
  <meta property="og:site_name" content="{esc(SITE_NAME)}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(SEO_TITLE)}" />
  <meta name="twitter:description" content="{esc(SEO_DESCRIPTION)}" />
  <link rel="canonical" href="{esc(SITE_URL)}" />
  <title>{esc(SEO_TITLE)}</title>
  <script type="application/ld+json">{structured_data}</script>
  <script>
    try {{
      const storedTheme = localStorage.getItem("sarawak-theme");
      if (storedTheme === "dark" || (storedTheme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {{
        document.documentElement.dataset.theme = "dark";
      }}
    }} catch (error) {{}}
  </script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>" />
  <link rel="stylesheet" href="style.css" />
  <script src="app.js" defer></script>
</head>
{render_compact_body(items)}
</html>
"""


def render_about() -> str:
    about_url = f"{SITE_URL}about.html"
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "@id": f"{about_url}#about",
            "url": about_url,
            "name": ABOUT_SEO_TITLE,
            "description": ABOUT_SEO_DESCRIPTION,
            "isPartOf": {"@id": f"{SITE_URL}#website"},
            "inLanguage": "en",
        },
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="{esc(ABOUT_SEO_DESCRIPTION)}" />
  <meta name="google-site-verification" content="5Ro7_ZjEKgT00hwHzOx0paD1Cme1tLYEGdttr_CwHvo" />
  <meta name="robots" content="index,follow" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(ABOUT_SEO_TITLE)}" />
  <meta property="og:description" content="{esc(ABOUT_SEO_DESCRIPTION)}" />
  <meta property="og:url" content="{esc(about_url)}" />
  <meta property="og:site_name" content="{esc(SITE_NAME)}" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="{esc(ABOUT_SEO_TITLE)}" />
  <meta name="twitter:description" content="{esc(ABOUT_SEO_DESCRIPTION)}" />
  <link rel="canonical" href="{esc(about_url)}" />
  <title>{esc(ABOUT_SEO_TITLE)}</title>
  <script type="application/ld+json">{structured_data}</script>
  <script>
    try {{
      const storedTheme = localStorage.getItem("sarawak-theme");
      if (storedTheme === "dark" || (storedTheme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {{
        document.documentElement.dataset.theme = "dark";
      }}
    }} catch (error) {{}}
  </script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>" />
  <link rel="stylesheet" href="style.css" />
  <script src="app.js" defer></script>
</head>
{render_about_body()}
</html>
"""


def build() -> None:
    items = load_feed_items()
    sitemap_lastmod = last_updated()[0][:10]
    DIST.mkdir(exist_ok=True)
    alternative_dir = DIST / "alternative"
    if alternative_dir.exists():
        shutil.rmtree(alternative_dir)
    (DIST / "index.html").write_text(render_index(items), encoding="utf-8")
    (DIST / "about.html").write_text(render_about(), encoding="utf-8")
    compact_css = (ROOT / "site" / "style.css").read_text(encoding="utf-8")
    (DIST / "style.css").write_text(compact_css, encoding="utf-8")
    (DIST / "app.js").write_text((ROOT / "site" / "app.js").read_text(encoding="utf-8"), encoding="utf-8")
    (DIST / "items.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://ai.sarawak.news/sitemap.xml\n", encoding="utf-8")
    (DIST / "sitemap.xml").write_text(f"""<?xml version='1.0' encoding='UTF-8'?>
<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
  <url>
    <loc>https://ai.sarawak.news/</loc>
    <lastmod>{sitemap_lastmod}</lastmod>
  </url>
  <url>
    <loc>https://ai.sarawak.news/about.html</loc>
    <lastmod>{sitemap_lastmod}</lastmod>
  </url>
</urlset>
""", encoding="utf-8")
    print(f"Built {DIST / 'index.html'} with {len(items)} feed items")


if __name__ == "__main__":
    build()
