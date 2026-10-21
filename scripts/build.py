from __future__ import annotations

import html
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"
SITE_META_PATH = DATA / "site.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kit.python.analytics_loader import (  # noqa: E402
    ANALYTICS_MAX_AGE,
    render_analytics_loader as kit_render_analytics_loader,
)
from kit.python.analytics_registry import AnalyticsRegistry, load_analytics  # noqa: E402
from kit.python.asset_urls import versioned_href  # noqa: E402
from kit.python.shell import (  # noqa: E402
    NavItem,
    render_back_to_top,
    render_footer as kit_render_footer,
    render_header as kit_render_header,
)

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
SOCIAL_CARD_PATH = ROOT / "site" / "social-card.png"
# Site title, tagline, description, and About lead live only in data/site.json.
SITE_COPY_FIELDS = ("title", "tagline", "description", "about_lead")
SITE_INTRODUCTION = (
    "Tracking artificial intelligence developments across Sarawak, bringing AI "
    "policy, projects, research and adoption into one source-linked brief."
)
# Footer summary note: two sentences joined by kit FOOTER_NOTE_BREAK.
FOOTER_BRAND_NOTE_PARTS = (
    "AI news updates are sourced from public reports, news outlets, and official "
    "announcements.",
    "Each item links to its source and includes a concise editorial summary.",
)
FOOTER_CREDIT_HTML = (
    'Built by <a class="site-footer-link site-footer-credit-link" '
    'href="https://hafiy.my" target="_blank" rel="noopener noreferrer">hafiy.my</a>, '
    "an independent publication. Not affiliated with the Sarawak Government."
)
BRIEF_NET_SVG = (ROOT / "site" / "brief-net.svg").read_text(encoding="utf-8").strip()


def analytics_registry() -> AnalyticsRegistry:
    return load_analytics()


# Resolved once at import for tests that still read module-level names.
_ANALYTICS = analytics_registry()
GA_MEASUREMENT_ID = _ANALYTICS.primary_ga4_id()
CLOUDFLARE_WEB_ANALYTICS_TOKEN = _ANALYTICS.primary_cf_token()
GA_PRODUCTION_HOSTS = _ANALYTICS.hostnames
GA_INTERNAL_COOKIE = _ANALYTICS.internal_cookie
GA_INTERNAL_MAX_AGE_SECONDS = ANALYTICS_MAX_AGE


def render_analytics_loader(registry: AnalyticsRegistry | None = None) -> str:
    """Emit the shared kit analytics loader from ``data/analytics.json``."""
    return kit_render_analytics_loader(
        registry if registry is not None else analytics_registry()
    )


def social_card_url() -> str:
    """Absolute social-card URL with a content-hash query string."""
    return versioned_href(f"{SITE_URL}social-card.png", SOCIAL_CARD_PATH)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_site(path: Path = SITE_META_PATH) -> dict[str, str]:
    """Load title/tagline/description/about_lead from data/site.json."""
    if not path.is_file():
        raise SystemExit(f"missing site copy file: {path.relative_to(ROOT)}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("data/site.json must be an object")
    site: dict[str, str] = {}
    for field in SITE_COPY_FIELDS:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"data/site.json is missing {field}")
        site[field] = value.strip()
    return site


def seo_document_title(site: dict[str, str]) -> str:
    return f"Sarawak AI News | {site['title']}"


def about_document_title(site: dict[str, str]) -> str:
    return f"About {site['title']} | Sarawak AI News"


def about_meta_description(site: dict[str, str]) -> str:
    return (
        f"What {site['title']} covers and how each Sarawak AI story is checked "
        "against its original source."
    )


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


def format_story_date(value: str) -> str:
    date = datetime.strptime(value, "%Y-%m-%d")
    return f"{date.day} {date.strftime('%b %Y')}"


def last_updated(items: list[dict]) -> tuple[str, str, str]:
    dates = [item["date"] for item in items if item.get("date")]
    if not dates:
        raise ValueError("Cannot derive last_updated without dated reviewed items")
    value = max(dates)
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
    return f"""
    <article class="story-card" id="{slug(item['id'])}" data-section="{slug(item['section'])}" tabindex="0" aria-label="Open story: {esc(item['title'])}">
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
      <div class="category-filter-scroll" data-category-scroll>
        <div class="category-filter-options">
          {' '.join(buttons)}
        </div>
        <span class="category-filter-hint category-filter-hint-start" aria-hidden="true"><span class="category-filter-chevron"></span></span>
        <span class="category-filter-hint category-filter-hint-end" aria-hidden="true"><span class="category-filter-chevron"></span></span>
      </div>
      <p class="visually-hidden" data-filter-status aria-live="polite">Showing all {len(items)} stories</p>
    </section>
    """


def render_site_header(active_page: str, site: dict[str, str] | None = None) -> str:
    site = load_site() if site is None else site
    return kit_render_header(
        brand_title=site["title"],
        brand_href="/",
        active=active_page,
        nav_items=(
            NavItem("home", "/", "Home"),
            NavItem("about", "about.html", "About"),
        ),
    )


def render_site_footer(active_page: str, site: dict[str, str] | None = None) -> str:
    site = load_site() if site is None else site
    return kit_render_footer(
        brand_title=site["title"],
        brand_note_parts=FOOTER_BRAND_NOTE_PARTS,
        active=active_page,
        explore_items=(
            NavItem("home", "/", "Home"),
            NavItem("about", "about.html", "About"),
        ),
        credit_html=FOOTER_CREDIT_HTML,
    )


def render_compact_body(items: list[dict], site: dict[str, str] | None = None) -> str:
    site = load_site() if site is None else site
    feed = "\n".join(render_compact_signal(item, index) for index, item in enumerate(items, 1))
    category_filter = render_category_filter(items)
    updated_iso, _, updated_compact = last_updated(items)

    return f"""<body>
  <a class="skip-link" href="#content">Skip to content</a>

{render_site_header("home", site)}

  <main id="content">
    <header class="brief">
      {BRIEF_NET_SVG}
      <h1 id="brief-title">{esc(site["tagline"])}</h1>
      <p class="brief-deck">{esc(SITE_INTRODUCTION)}</p>
      <p class="updated"><span class="updated-label">Last updated</span><time datetime="{esc(updated_iso)}">{esc(updated_compact)}</time></p>
    </header>

    {category_filter}

    <section class="story-list" aria-label="Latest intelligence signals" data-story-list>
      {feed}
    </section>
  </main>

{render_back_to_top()}

{render_site_footer("home", site)}
</body>"""


def render_about_body(site: dict[str, str] | None = None) -> str:
    site = load_site() if site is None else site
    return f"""<body>
  <a class="skip-link" href="#content">Skip to content</a>

{render_site_header("about", site)}

  <main id="content" class="about-page">
    <header class="about-hero">
      <h1>About {esc(site["title"])}</h1>
      <p class="about-lede">{esc(site["about_lead"])}</p>
    </header>

    <section class="about-section" aria-labelledby="about-why-title">
      <h2 id="about-why-title">Why Sarawak AI</h2>
      <p>Sarawak has set a target to become Malaysia's leading AI hub by 2027, as part of its push toward a developed, high-income state by 2030. Announcements about plans, platforms, partnerships, training and investment now arrive almost every week. This brief helps Sarawakians in general to keep track of them.</p>
    </section>

    <section class="about-section" aria-labelledby="about-coverage-title">
      <h2 id="about-coverage-title">What we cover</h2>
      <p>Every story is tagged with one of seven categories:</p>
      <ul class="about-category-list">
        <li><strong>Policy:</strong> plans, laws, governance and public decisions about AI.</li>
        <li><strong>Public Services:</strong> AI used by agencies, councils and health services.</li>
        <li><strong>Education:</strong> AI in schools, colleges, universities and student projects.</li>
        <li><strong>Workforce:</strong> skills, training and talent programmes.</li>
        <li><strong>Research:</strong> university and industry research with a clear Sarawak link.</li>
        <li><strong>Infrastructure:</strong> compute, data centres, connectivity and sovereign AI projects.</li>
        <li><strong>Business:</strong> adoption, start-ups, investment and industry capability.</li>
      </ul>
    </section>

    <section class="about-section" aria-labelledby="about-method-title">
      <h2 id="about-method-title">How stories are picked and checked</h2>
      <p>Daily scan checks public news and official pages for Sarawak AI developments. Approved items get a short original summary and a link to the source.</p>
    </section>

    <section class="about-section" aria-labelledby="about-contact-title">
      <h2 id="about-contact-title">Contact</h2>
      <p><a href="mailto:contact@sarawak.news">contact@sarawak.news</a></p>
    </section>

  </main>

{render_site_footer("about", site)}
</body>"""


def render_index(items: list[dict], site: dict[str, str] | None = None) -> str:
    site = load_site() if site is None else site
    page_title = seo_document_title(site)
    description = site["description"]
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "WebSite",
                    "@id": f"{SITE_URL}#website",
                    "url": SITE_URL,
                    "name": site["title"],
                    "description": description,
                    "inLanguage": "en",
                },
                {
                    "@type": "CollectionPage",
                    "@id": f"{SITE_URL}#collection",
                    "url": SITE_URL,
                    "name": page_title,
                    "description": description,
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
  <meta name="description" content="{esc(description)}" />
  <meta name="google-site-verification" content="5Ro7_ZjEKgT00hwHzOx0paD1Cme1tLYEGdttr_CwHvo" />
  <meta name="robots" content="index,follow" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(site["title"])}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{esc(SITE_URL)}" />
  <meta property="og:site_name" content="{esc(site["title"])}" />
  <meta property="og:image" content="{esc(social_card_url())}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(site["title"])}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{esc(social_card_url())}" />
  <link rel="canonical" href="{esc(SITE_URL)}" />
  <title>{esc(page_title)}</title>
  <script type="application/ld+json">{structured_data}</script>
  <script>
    document.documentElement.classList.add("js");
    try {{
      const storedTheme = localStorage.getItem("sarawak-theme");
      if (storedTheme === "dark" || (storedTheme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {{
        document.documentElement.dataset.theme = "dark";
      }}
    }} catch (error) {{}}
  </script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>" />
  <link rel="preload" href="fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="stylesheet" href="style.css" />
  <script src="app.js" defer></script>
  {render_analytics_loader()}
</head>
{render_compact_body(items, site)}
</html>
"""


def render_about(site: dict[str, str] | None = None) -> str:
    site = load_site() if site is None else site
    about_url = f"{SITE_URL}about.html"
    page_title = about_document_title(site)
    description = about_meta_description(site)
    structured_data = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "@id": f"{about_url}#about",
            "url": about_url,
            "name": page_title,
            "description": description,
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
  <meta name="description" content="{esc(description)}" />
  <meta name="google-site-verification" content="5Ro7_ZjEKgT00hwHzOx0paD1Cme1tLYEGdttr_CwHvo" />
  <meta name="robots" content="index,follow" />
  <meta property="og:type" content="website" />
  <meta property="og:title" content="{esc(page_title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:url" content="{esc(about_url)}" />
  <meta property="og:site_name" content="{esc(site["title"])}" />
  <meta property="og:image" content="{esc(social_card_url())}" />
  <meta property="og:image:width" content="1200" />
  <meta property="og:image:height" content="630" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(page_title)}" />
  <meta name="twitter:description" content="{esc(description)}" />
  <meta name="twitter:image" content="{esc(social_card_url())}" />
  <link rel="canonical" href="{esc(about_url)}" />
  <title>{esc(page_title)}</title>
  <script type="application/ld+json">{structured_data}</script>
  <script>
    document.documentElement.classList.add("js");
    try {{
      const storedTheme = localStorage.getItem("sarawak-theme");
      if (storedTheme === "dark" || (storedTheme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {{
        document.documentElement.dataset.theme = "dark";
      }}
    }} catch (error) {{}}
  </script>
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧠</text></svg>" />
  <link rel="preload" href="fonts/Geist-Variable.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="stylesheet" href="style.css" />
  <script src="app.js" defer></script>
  {render_analytics_loader()}
</head>
{render_about_body(site)}
</html>
"""



def render_category_redirect(section: str, site: dict[str, str] | None = None) -> str:
    """Legacy category URL stub. Main has no filter preselect, so stubs go home."""
    site = load_site() if site is None else site
    target = SITE_URL
    title = f"{section} stories moved | {site['title']}"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex,follow" />
  <meta http-equiv="refresh" content="0;url={esc(target)}" />
  <link rel="canonical" href="{esc(target)}" />
  <title>{esc(title)}</title>
  <script>location.replace({json.dumps(target)});</script>
</head>
<body>
  <p>{esc(section)} stories now live on the homepage. <a href="{esc(target)}">Continue to {esc(site["title"])}</a>.</p>
</body>
</html>
"""


def copy_site_fonts() -> None:
    source = ROOT / "site" / "fonts"
    woff = source / "Geist-Variable.woff2"
    license_file = source / "OFL.txt"
    if not woff.is_file() or not license_file.is_file():
        raise SystemExit("site/fonts must contain Geist-Variable.woff2 and OFL.txt")
    target = DIST / "fonts"
    target.mkdir(exist_ok=True)
    shutil.copy2(woff, target / woff.name)
    shutil.copy2(license_file, target / license_file.name)


def copy_nav_marks() -> None:
    """Copy origami nav marks from the vendored kit (site/icons is the mirror)."""
    icons_dist = DIST / "icons"
    icons_dist.mkdir(exist_ok=True)
    for mark_name in ("nav-mark-transparent.svg", "nav-mark-transparent-dark.svg"):
        mark_src = ROOT / "kit" / "assets" / "icons" / mark_name
        if not mark_src.is_file():
            raise SystemExit(f"missing kit nav mark {mark_src.relative_to(ROOT)}")
        site_mirror = ROOT / "site" / "icons" / mark_name
        site_mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mark_src, site_mirror)
        shutil.copy2(mark_src, icons_dist / mark_name)


def build() -> None:
    items = load_feed_items()
    site = load_site()
    sitemap_lastmod = last_updated(items)[0]
    DIST.mkdir(exist_ok=True)
    alternative_dir = DIST / "alternative"
    if alternative_dir.exists():
        shutil.rmtree(alternative_dir)
    (DIST / "index.html").write_text(render_index(items, site), encoding="utf-8")
    (DIST / "about.html").write_text(render_about(site), encoding="utf-8")
    for section in SECTION_FILTERS:
        (DIST / f"{slug(section)}.html").write_text(
            render_category_redirect(section, site), encoding="utf-8"
        )
    compact_css = (ROOT / "site" / "style.css").read_text(encoding="utf-8")
    (DIST / "style.css").write_text(compact_css, encoding="utf-8")
    (DIST / "app.js").write_text((ROOT / "site" / "app.js").read_text(encoding="utf-8"), encoding="utf-8")
    shutil.copy2(SOCIAL_CARD_PATH, DIST / "social-card.png")
    copy_site_fonts()
    copy_nav_marks()
    (DIST / "items.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    (DIST / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://ai.sarawak.news/sitemap.xml\n", encoding="utf-8")
    sitemap_urls = [SITE_URL, f"{SITE_URL}about.html"]
    sitemap_entries = "\n".join(
        f"  <url>\n    <loc>{esc(url)}</loc>\n    <lastmod>{sitemap_lastmod}</lastmod>\n  </url>"
        for url in sitemap_urls
    )
    (DIST / "sitemap.xml").write_text(f"""<?xml version='1.0' encoding='UTF-8'?>
<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
{sitemap_entries}
</urlset>
""", encoding="utf-8")
    print(f"Built {DIST / 'index.html'} with {len(items)} feed items")


if __name__ == "__main__":
    build()
