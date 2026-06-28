from __future__ import annotations

import html
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DIST = ROOT / "dist"

SECTION_ORDER = [
    "Government & Policy",
    "Infrastructure",
    "Education & Workforce",
    "Research & Universities",
    "Business & Startups",
]


def load_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def item_card(item: dict) -> str:
    tags = "".join(f'<span class="tag">{esc(tag)}</span>' for tag in item.get("tags", []))
    caveat = item.get("caveat")
    caveat_html = f'<p class="caveat"><strong>Caveat:</strong> {esc(caveat)}</p>' if caveat else ""
    return f"""
    <article class="card">
      <div class="meta"><span>{esc(item['source'])}</span><span>{esc(item['date'])}</span><span>{esc(item.get('confidence', 'unknown'))} confidence</span></div>
      <h3><a href="{esc(item['url'])}" rel="noopener noreferrer">{esc(item['title'])}</a></h3>
      <div class="tags">{tags}</div>
      <p>{esc(item['summary'])}</p>
      <p class="why"><strong>Why it matters for Sarawak:</strong> {esc(item['why_it_matters'])}</p>
      {caveat_html}
    </article>
    """


def render_index(items: list[dict], sources: list[dict]) -> str:
    section_counts = Counter(item["section"] for item in items)
    tag_counts = Counter(tag for item in items for tag in item.get("tags", []))
    sections = []
    for section in SECTION_ORDER:
        section_items = [item for item in items if item["section"] == section]
        if not section_items:
            continue
        cards = "\n".join(item_card(item) for item in section_items)
        sections.append(f'<section><h2>{esc(section)}</h2>{cards}</section>')

    source_rows = "\n".join(
        f"<tr><td>{esc(src['tier'])}</td><td><a href=\"{esc(src['url'])}\">{esc(src['name'])}</a></td><td>{esc(src['category'])}</td><td>{esc(src['expected_yield'])}</td></tr>"
        for src in sorted(sources, key=lambda s: (s["tier"], s["name"]))
    )
    section_summary = "".join(f"<li>{esc(k)}: {v}</li>" for k, v in section_counts.items())
    top_tags = "".join(f'<span class="tag">{esc(tag)} × {count}</span>' for tag, count in tag_counts.most_common(12))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Sarawak AI News — PoC Brief</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="hero">
    <p class="eyebrow">Proof of Concept · Generated {date.today().isoformat()}</p>
    <h1>Sarawak AI News</h1>
    <p class="dek">A source-attributed regional intelligence brief for Sarawak AI, digital economy, infrastructure, public services, research, and workforce signals.</p>
    <div class="stats">
      <div><strong>{len(items)}</strong><span>seed items</span></div>
      <div><strong>{len(sources)}</strong><span>watch sources</span></div>
      <div><strong>{len(section_counts)}</strong><span>active sections</span></div>
    </div>
  </header>

  <main>
    <section class="brief-note">
      <h2>Editorial stance</h2>
      <p>This is not a live aggregator yet. It is a curated validation brief: every item must link to the original source, summarize in original wording, and explain why the signal matters for Sarawak.</p>
      <ul>{section_summary}</ul>
      <div class="tags">{top_tags}</div>
    </section>

    {''.join(sections)}

    <section>
      <h2>Source Watchlist</h2>
      <table>
        <thead><tr><th>Tier</th><th>Source</th><th>Category</th><th>Expected yield</th></tr></thead>
        <tbody>{source_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def build() -> None:
    items = sorted(load_json("items.json"), key=lambda item: item["date"], reverse=True)
    sources = load_json("sources.json")
    DIST.mkdir(exist_ok=True)
    (DIST / "index.html").write_text(render_index(items, sources), encoding="utf-8")
    (DIST / "style.css").write_text((ROOT / "site" / "style.css").read_text(encoding="utf-8"), encoding="utf-8")
    (DIST / "items.json").write_text(json.dumps(items, indent=2), encoding="utf-8")
    print(f"Built {DIST / 'index.html'} with {len(items)} items and {len(sources)} sources")


if __name__ == "__main__":
    build()
