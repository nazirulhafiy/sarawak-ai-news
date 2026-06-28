# Sarawak AI News PoC

Proof-of-concept for an AI-assisted regional intelligence brief tracking Sarawak-relevant AI, automation, digital economy, public-sector digital services, infrastructure, education, research, and workforce signals.

## What this PoC proves

- A small curated dataset can render into a readable weekly briefing page.
- Source attribution, caveats, and tags are first-class fields.
- The project can be hosted as a static site later without a backend.
- Automation is intentionally deferred until source signal is validated.

## Run locally

```bash
python3 scripts/build.py
python3 -m http.server 4173 -d dist
# open http://127.0.0.1:4173
```

## Test

```bash
python3 -m unittest discover -s tests -v
```

## Project rules

- Do not republish full articles.
- Link prominently to original sources.
- Use original summaries and analysis.
- Mark caveats and confidence.
- Treat current data as PoC seed data, not a finished publication.

## Current status

PoC only. No live publishing automation yet.
