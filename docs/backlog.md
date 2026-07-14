# Backlog

This backlog documents recommended next tasks from the project audit on
2026-07-08. It is not a commitment to rewrite the app yet.

## Known Issues

- `README.md` previously reported a stale public item count; the current seed
  dataset has 27 reviewed items.
- `data/site.json` uses a manual `last_updated` timestamp, so it can drift from
  the newest reviewed item if not updated during the weekly flow.
- The production HTML does not show `why_it_matters`, `tags`, or confidence for
  high-confidence items, even though those fields are preserved in JSON.
- Some item caveats still say the source should be revisited before direct
  quotation. This is acceptable for a PoC but should be tightened before a more
  formal publication cadence.
- `scripts/ingest.py` is keyword-based and can miss relevant stories with
  indirect wording or include weak candidates that need manual rejection.
- Candidate discovery does not exclude URLs already present in `data/items.json`.
- `scripts/audit_dates.py` depends on live source availability, so CI can warn
  or fail because of external site outages or markup changes.
- Variant D is a static prototype with placeholder content and feature promises
  that are not production-backed.
- `scripts/generate_design_variants.py` does not regenerate Variant D.
- There is no archive, feed export, RSS, newsletter system, or source-review
  dashboard.

## Next Documentation Tasks

- Keep `docs/product.md` updated whenever the content model or workflow changes.
- Add a short editorial style guide for item summaries, caveats, confidence, and
  date verification.
- Add a source-review checklist for manually promoting candidates into
  `data/items.json`.

## Next Content Tasks

- Re-review items whose caveats mention search-result-derived title/date before
  using direct quotations.
- Decide whether `why_it_matters` should appear publicly on story cards or be
  reserved for JSON/API consumers.
- Add a simple duplicate URL check for reviewed items.
- Add validation for allowed `section` values.
- Keep source tier, confidence, caveat, and why-it-matters metadata internal
  unless a future editorial decision explicitly approves public display.

## Next Engineering Tasks

- Add a data validation command for required fields, allowed sections, unique
  IDs, unique URLs, HTTPS URLs, and summary length.
- Update ingestion to suppress already-reviewed URLs.
- Add an optional `--since` or date-window mode to candidate discovery.
- Split renderer helpers into smaller functions only if build complexity grows.
- Decide whether generated `dist/candidates.*` should stay in `dist/` or move to
  a non-public review directory.
- Add RSS or JSON feed output if the site becomes a recurring publication.
- Add stable category URLs or query-string state for filtered views.
- Consider an archive page once the feed grows beyond one screen of current
  signals.

## Next Design Tasks

- Keep production on the compact editorial layout until content operations are
  reliable.
- Prototype a data-backed version of Variant D using real reviewed items.
- Remove or disable unapproved newsletter, sponsor, custom-report, and daily
  update affordances from any productionized Variant D work.
- Test mobile layouts for headline wrapping, filter overflow, and long source
  names.
- Keep caveat, confidence, tags, and why-it-matters metadata out of public story
  cards unless a future editorial redesign explicitly approves showing them.

## Release Readiness Checklist

Before claiming a change is ready:

- Run `python3 scripts/build.py`.
- Run `python3 -m unittest discover -s tests -v`.
- For content changes, run `python3 scripts/audit_dates.py`.
- For content changes, run `python3 scripts/audit_summaries.py`.
- Preview `dist/index.html` locally.
- Confirm no full article bodies have been copied into the repo.
- Confirm public publishing or outreach has approval when applicable.
