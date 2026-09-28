# Backlog

The product is Ongoing. Open work is on Notion Tasks under
"Sarawak AI News Backlog".

## Open Cards

- Ingest: skip already-reviewed URLs.
- Duplicate URL check for reviewed items.
- Standalone data validation (unique IDs / unique URLs).
- RSS or JSON feed.

## Recent Changes

See git history.

## Release Readiness Checklist

Before claiming a change is ready:

- Run `python3 scripts/build.py`.
- Run `python3 -m unittest discover -s tests -v`.
- For content changes, run `python3 scripts/audit_dates.py --item-id <id>` for
  every added or date-relevant edited item.
- For content changes, run `python3 scripts/audit_summaries.py`.
- Preview `dist/index.html` locally.
- Confirm no full article bodies have been copied into the repo.
- Confirm public publishing or outreach has approval when applicable.
