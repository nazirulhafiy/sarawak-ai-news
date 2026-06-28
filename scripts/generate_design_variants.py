from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "design-variants"
ITEMS = json.loads((ROOT / "data" / "items.json").read_text(encoding="utf-8"))
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def signals(limit: int = 4) -> str:
    return "\n".join(
        f"""
        <article class="signal">
          <p class="meta">{esc(item['source'])} · {esc(item['date'])} · {esc(item['confidence'])} confidence</p>
          <h3><a href="{esc(item['url'])}">{esc(item['title'])}</a></h3>
          <p>{esc(item['summary'])}</p>
          <p class="why">Why it matters: {esc(item['why_it_matters'])}</p>
        </article>
        """
        for item in ITEMS[:limit]
    )


def source_list(limit: int = 6) -> str:
    return "\n".join(f"<li>{esc(src['name'])}<span>{esc(src['category'])} · tier {esc(src['tier'])}</span></li>" for src in SOURCES[:limit])


def page(title: str, body_class: str, style: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{esc(title)}</title>
<style>{style}</style>
</head>
<body class="{body_class}">
{body}
</body>
</html>
"""


NEAR_CLONE_CSS = r"""
:root{--ink:#080808;--muted:#707070;--line:#ededed;--link:#1b56d8}*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font:16px/1.55 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.nav{max-width:1020px;margin:0 auto;padding:12px 18px;border-bottom:1px solid var(--line);display:flex;gap:18px;font-size:14px}.brand{margin-right:auto;font-weight:700;text-decoration:none}.wrap{width:min(670px,calc(100vw - 34px));margin:0 auto;padding:18px 0 70px}.tools{display:flex;gap:16px;justify-content:center;margin:4px 0 34px;font-size:14px}.live,.edition,.meta{font-size:12px;letter-spacing:.075em;text-transform:uppercase;color:var(--muted);font-weight:700}.live{text-align:center;margin:0 0 10px}.edition{text-align:center;margin:0 0 18px;color:#111}h1{font-size:clamp(2.7rem,9vw,5.8rem);letter-spacing:-.08em;line-height:.9;text-align:center;margin:0 0 28px;font-weight:880}.lede{font-size:19px;max-width:540px;margin:0 auto 32px}.lede p{margin:0 0 14px}.section{max-width:540px;margin:34px auto 0}.section h2{font-size:18px;margin:0 0 14px;letter-spacing:-.03em}.section>p{margin:0 0 13px}.signal{border-top:1px solid var(--line);padding-top:13px;margin:17px 0 23px}.meta{margin:0 0 5px;font-size:11px}.signal h3{font-size:16px;line-height:1.3;margin:0 0 7px}.signal p{margin:0 0 10px}.why{color:#333}.sources{border-top:1px solid var(--line);margin-top:42px;padding-top:16px;color:#222}.sources h2{font-size:16px}.sources li{margin:0 0 9px}.sources span{display:block;color:var(--muted);font-size:12px}a{color:inherit;text-decoration-color:#c7c7c7;text-underline-offset:.18em}a:hover{color:var(--link)}
"""

SARAWAK_CSS = r"""
:root{--ink:#101915;--muted:#667069;--line:#dfe7df;--green:#0b6b46;--gold:#c7932b;--red:#a83a2d;--bg:#fbfcf8}*{box-sizing:border-box}body{margin:0;background:linear-gradient(90deg,var(--green) 0 8px,var(--gold) 8px 13px,var(--red) 13px 18px,var(--bg) 18px);color:var(--ink);font:17px/1.62 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.nav{max-width:1060px;margin:0 auto;padding:16px 24px 12px 42px;display:flex;gap:18px;border-bottom:1px solid var(--line);font-size:14px}.brand{margin-right:auto;font-weight:850;text-decoration:none;color:var(--green)}.wrap{width:min(840px,calc(100vw - 48px));margin:0 auto;padding:30px 0 78px}.kicker{color:var(--green);font-size:12px;text-transform:uppercase;letter-spacing:.1em;font-weight:850}.hero{display:grid;grid-template-columns:1.45fr .75fr;gap:34px;align-items:end;border-bottom:1px solid var(--line);padding-bottom:30px}.hero h1{font-size:clamp(2.6rem,7vw,5.2rem);line-height:.95;letter-spacing:-.065em;margin:10px 0 18px}.thesis{font-size:20px}.side{border-left:3px solid var(--gold);padding-left:18px;color:#24332b}.section{display:grid;grid-template-columns:170px 1fr;gap:22px;margin:30px 0}.section h2{font-size:14px;text-transform:uppercase;letter-spacing:.08em;color:var(--green);margin:5px 0}.signal{border-top:1px solid var(--line);padding:14px 0 16px}.meta{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.07em;font-weight:800;margin:0 0 5px}.signal h3{font-size:20px;line-height:1.25;margin:0 0 7px}.signal p{margin:0 0 10px}.why{color:#33443a}.sources{margin-top:42px;border-top:1px solid var(--line);padding-top:18px}.sources ol{columns:2}.sources li{break-inside:avoid;margin:0 0 10px}.sources span{display:block;font-size:12px;color:var(--muted)}a{color:inherit;text-decoration-color:var(--gold);text-underline-offset:.18em}@media(max-width:760px){body{background:var(--bg);border-left:10px solid var(--green)}.hero,.section{display:block}.sources ol{columns:1}.nav{padding-left:18px}.wrap{width:min(100% - 30px,840px)}}
"""

PRODUCT_CSS = r"""
:root{--bg:#080b10;--panel:#101722;--panel2:#0d131c;--ink:#eef5ff;--muted:#8f9db1;--line:#223044;--cyan:#67e8f9;--green:#86efac}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 18% 0,#182638 0,#080b10 42%);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}.nav{max-width:1180px;margin:0 auto;padding:18px 22px;display:flex;gap:18px;border-bottom:1px solid var(--line);font-size:13px;color:var(--muted)}.brand{margin-right:auto;color:var(--ink);font-weight:800;text-decoration:none}.wrap{max-width:1120px;margin:0 auto;padding:34px 22px 80px}.hero{display:grid;grid-template-columns:1.2fr .8fr;gap:22px}.panel{background:linear-gradient(180deg,rgba(16,23,34,.94),rgba(13,19,28,.94));border:1px solid var(--line);border-radius:22px;padding:24px}.kicker{color:var(--cyan);font-size:12px;text-transform:uppercase;letter-spacing:.11em;font-weight:850}.hero h1{font-size:clamp(2.3rem,6vw,5rem);line-height:.95;letter-spacing:-.06em;margin:12px 0 16px}.thesis{font-size:19px;color:#d8e6f5}.stats{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.stat{background:#0b111a;border:1px solid var(--line);border-radius:16px;padding:16px}.stat strong{display:block;font-size:28px;color:var(--green)}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-top:18px}.signal{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px}.meta{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em;font-weight:800;margin:0 0 8px}.signal h3{font-size:20px;line-height:1.2;margin:0 0 9px}.signal p{color:#c8d5e4;margin:0 0 10px}.why{color:#eef5ff!important}.sources{margin-top:18px}.sources ol{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 18px;padding-left:20px}.sources li{color:#dce8f5}.sources span{display:block;color:var(--muted);font-size:12px}a{color:inherit;text-decoration-color:var(--cyan);text-underline-offset:.18em}@media(max-width:820px){.hero,.grid{grid-template-columns:1fr}.sources ol{grid-template-columns:1fr}}
"""


def build() -> None:
    OUT.mkdir(exist_ok=True)
    near = page(
        "Variant A — Near-clone editorial memo",
        "near-clone",
        NEAR_CLONE_CSS,
        f"""
<nav class="nav"><a class="brand">Sarawak AI News</a><a>How This Is Built</a><a>Source Watchlist</a><a>Make This Page Shorter</a></nav>
<main class="wrap">
  <div class="tools"><a>How This Is Built</a><a>Source Watchlist</a><a>Make This Page Shorter</a></div>
  <p class="live">LIVE — Sunday, June 28, 2026 — Updated 10:35 AM</p>
  <p class="edition">Sarawak signal brief</p>
  <h1>Sarawak’s AI Stack Is Becoming Visible</h1>
  <div class="lede"><p>This is no longer just digital-economy branding.</p><p>The signal is resolving into institutions, infrastructure, public services, talent, and applied sector projects.</p><p>The question is whether this repeats every week.</p></div>
  <section class="section"><h2>The pattern</h2><p>Sarawak AI is showing up as a stack, not as one product launch.</p><p>Public-service assistants, sovereign infrastructure, agency coordination, research partnerships, and workforce readiness now appear in the same narrative.</p></section>
  <section class="section"><h2>Latest signals</h2>{signals()}</section>
  <section class="sources"><h2>Source watchlist</h2><ol>{source_list()}</ol></section>
</main>
""",
    )
    sarawak = page(
        "Variant B — Sarawak-branded brief",
        "sarawak",
        SARAWAK_CSS,
        f"""
<nav class="nav"><a class="brand">Sarawak AI News</a><a>Brief</a><a>Sources</a><a>Data</a></nav>
<main class="wrap">
  <section class="hero">
    <div><p class="kicker">Regional intelligence brief · Kuching</p><h1>Sarawak’s AI Push Is Moving From Policy To Infrastructure</h1><p class="thesis">A locally grounded brief for tracking AI, deep-tech, public services, digital economy programmes, and research capacity across Sarawak.</p></div>
    <aside class="side"><p><strong>Today’s read:</strong> the strongest signal is institutional coordination — SAIC, SDEC, SAINS, universities, and state-linked platforms are starting to overlap.</p><p>Best if we want a recognisable Sarawak identity without losing the briefing format.</p></aside>
  </section>
  <section class="section"><h2>Briefing thesis</h2><div><p>The story is not just “AI adoption.” It is state capacity: who owns the infrastructure, who trains the workforce, and which public services actually change.</p></div></section>
  <section class="section"><h2>Signals</h2><div>{signals()}</div></section>
  <section class="sources"><h2>Source watchlist</h2><ol>{source_list()}</ol></section>
</main>
""",
    )
    product = page(
        "Variant C — Productized intelligence brief",
        "product",
        PRODUCT_CSS,
        f"""
<nav class="nav"><a class="brand">Sarawak AI News</a><a>Signals</a><a>Watchlist</a><a>Archive</a><a>Method</a></nav>
<main class="wrap">
  <section class="hero">
    <div class="panel"><p class="kicker">AI-assisted regional intelligence</p><h1>Sarawak AI Signal Board</h1><p class="thesis">A higher-density product direction for founders, policymakers, researchers, and digital-economy watchers who need to monitor weak signals fast.</p></div>
    <div class="stats"><div class="stat"><strong>{len(ITEMS)}</strong>seed signals</div><div class="stat"><strong>{len(SOURCES)}</strong>watched sources</div><div class="stat"><strong>3</strong>source errors</div><div class="stat"><strong>weekly</strong>target cadence</div></div>
  </section>
  <section class="grid">{signals()}</section>
  <section class="panel sources"><h2>Watchlist</h2><ol>{source_list(10)}</ol></section>
</main>
""",
    )
    files = {
        "variant-a-near-clone-editorial.html": near,
        "variant-b-sarawak-branded.html": sarawak,
        "variant-c-productized-intelligence.html": product,
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
    print("Wrote design variants:")
    for name in files:
        print(OUT / name)


if __name__ == "__main__":
    build()
