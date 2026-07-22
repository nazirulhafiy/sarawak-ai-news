# Backlog

This backlog documents recommended next tasks from the project audit on
2026-07-08, updated for the 2026-07-22 masthead review. It is not a
commitment to rewrite the app yet.

## Recent Changes

- Refined the production masthead with a larger wordmark, neutral divider, and
  short Sarawak-color signature while keeping the first screen free of extra
  descriptive copy.
- Added a reviewed policy-context item on Sarawak's transition toward an
  AI-native economy, with a caveat distinguishing analysis from a new programme
  or implementation milestone.
- Added The Borneo Post AI tag page to the discovery watchlist.
- Allowed AI-led headlines without "Sarawak" in the title to reach strict
  article-body validation, which still requires both Sarawak and a supported
  technology focus.
- Preserved source-page order during candidate selection so recent links are
  checked before older, keyword-dense headlines.
- Clarified that public summaries lead with the Sarawak signal while source type
  and limitations belong in the attribution and caveat fields.
- Added incremental date auditing by item ID for local updates and by Git diff
  for ordinary CI runs; manual workflow runs retain the full audit.

## Known Issues

- `data/site.json` uses a manual `last_updated` timestamp, so it can drift from
  the newest reviewed item if not updated during the weekly flow.
- The production HTML does not show `why_it_matters`, `tags`, or confidence for
  high-confidence items, even though those fields are preserved in JSON.
- Some item caveats still say the source should be revisited before direct
  quotation. This is acceptable for a PoC but should be tightened before a more
  formal publication cadence.
- `scripts/ingest.py` remains keyword-based and can still miss relevant stories
  that are absent from watched landing pages or beyond the first result page.
- Candidate discovery does not exclude URLs already present in `data/items.json`.
- `scripts/audit_dates.py` depends on live source availability, so targeted CI
  checks can still warn or fail because of external outages or markup changes.
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
- Keep source tier, confidence, caveat, and why-it-matters metadata internal
  unless a future editorial decision explicitly approves public display.

## Next Engineering Tasks

- Extend the existing test validation into a standalone data command that also
  checks unique IDs and unique URLs.
- Update ingestion to suppress already-reviewed URLs.
- Add an optional `--since` or date-window mode to candidate discovery.
- Add bounded pagination for source search and tag pages where first-page
  coverage is insufficient.
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
- Revisit the reviewed About-page concept later, using a restrained outlined
  About link in the masthead and moving fuller publication context off the
  already wordy homepage.
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
- For content changes, run `python3 scripts/audit_dates.py --item-id <id>` for
  every added or date-relevant edited item.
- For content changes, run `python3 scripts/audit_summaries.py`.
- Preview `dist/index.html` locally.
- Confirm no full article bodies have been copied into the repo.
- Confirm public publishing or outreach has approval when applicable.
