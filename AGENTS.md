# AGENTS.md

## Project
Sarawak AI News is a dependency-free static proof of concept for a
source-attributed regional AI intelligence brief at `ai.sarawak.news`.

The current app is intentionally small:

- `data/items.json` contains reviewed public feed items.
- `data/sources.json` contains watched source/search pages for candidate discovery.
- `data/site.json` contains manual site metadata such as `last_updated`.
- `scripts/build.py` renders the static site into `dist/`.
- `scripts/ingest.py` discovers candidate URLs for manual review only.
- `site/style.css` and `site/app.js` are the production front-end assets.
- `design-variants/` contains static design explorations, not production routes.
- `tests/` covers build output, ingestion scoring, date auditing, and summary quality.

## Project Rules
- Do not republish full article bodies.
- Maintain source URL, caveat, confidence, and why-it-matters fields for every item.
- Treat ingestion output as internal review material until a human checks the source.
- Keep the build dependency-free unless there is a clear reason to add tooling.
- Public publishing, newsletter sending, domain setup, or outreach requires Hafiy's explicit approval.
- Do not rewrite the app when the request is only for audit, planning, or documentation.

## Required Checks
Run the unit test suite before claiming changes work:

```bash
python3 -m unittest discover -s tests -v
```

For content/data changes, also run:

```bash
python3 scripts/audit_dates.py --item-id <added-or-edited-item-id>
python3 scripts/audit_summaries.py
python3 scripts/build.py
```

Repeat `--item-id` when a change contains more than one added or edited item.
Omit the selector only for a deliberate full audit. CI uses `--changed-from` to
check new or date-relevant records on ordinary pushes and pull requests, while a
manual workflow run keeps the full-audit path. Live source checks may warn when
a selected source is temporarily unavailable.

## Useful Commands

```bash
python3 scripts/build.py
python3 scripts/ingest.py --limit-per-source 5
python3 scripts/audit_dates.py --item-id <item-id>
python3 -m unittest discover -s tests -v
python3 -m http.server 4173 -d dist
```

## Documentation Map
- `README.md` is the operational overview.
- `docs/product.md` records product scope, content model, workflow, and constraints.
- `docs/design.md` records the current production design and design direction.
- `docs/backlog.md` records known issues and recommended next tasks.
