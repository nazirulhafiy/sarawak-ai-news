# Product Notes

## Product Shape

Sarawak AI News is an independent regional intelligence brief focused on
Sarawak-relevant AI and future-economy signals. It is closer to a curated signal
desk than a general news site: every public item should explain what changed,
why it matters, where the signal came from, and how confident the brief is.

Current production is a static homepage and a small About page generated from
reviewed JSON and the site's editorial workflow.
There is no CMS, database, scraper-to-summary pipeline, account system,
newsletter sender, or paid product surface. A scheduled weekly workflow can
publish qualifying feed updates after source verification and all required
checks pass.

## Audience

Primary readers:

- Sarawak digital economy watchers.
- Government, GLC, agency, and civic-tech operators.
- University, research, and workforce-development stakeholders.
- Founders, investors, vendors, and technologists tracking AI adoption.
- Journalists or analysts looking for source-attributed Sarawak AI context.

The current interface favors fast scanning over deep reading.

## Current User Experience

The homepage shows:

- Brand bar: `AI.Sarawak.News`, with `Home` and `About` navigation links and a
  theme toggle.
- Search title: `Sarawak AI News | AI.Sarawak.News`.
- Introductory copy describing the source-linked Sarawak AI coverage.
- Last-updated weekday and date derived at build time from the newest reviewed
  item date.
- Editorial headline and deck.
- Client-side category filters.
- Ranked story cards ordered newest first.
- Source links opening in new tabs.
- Structured footer with source context, a separated Explore column with
  vertical Home/About links, and a builder and independent-publication
  attribution row.

The About page explains the site's purpose, coverage categories, and
source-review workflow without adding signup, newsletter, or other product
promises. The independence note remains in the shared footer.

The generated `dist/items.json` preserves richer fields than the UI currently
shows, including `why_it_matters`, `confidence`, `caveat`, and `tags`. These
editorial fields are not displayed on public story cards.

## Content Scope

In scope:

- AI policy, adoption, and public-service use cases.
- Digital economy, cloud, data-centre, connectivity, and compute infrastructure.
- Universities, research collaborations, talent, and workforce readiness.
- Smart city, IoT, automation, robotics, and sector adoption.
- Sarawak-linked national or international partnerships.
- Contextual analysis or commentary that synthesises a clearly Sarawak-specific
  AI signal and is identified as analysis in its caveat.

Out of scope for the public feed unless a reviewed source makes the Sarawak AI
link clear:

- General Malaysia tech news with no Sarawak angle.
- General Sarawak news with no AI, digital-economy, infrastructure, or
  future-workforce angle.
- Unverified rumors, private tips, and unpublished outreach.
- Full article reproduction.

## Data Model

Reviewed public items live in `data/items.json`.

Required item fields:

- `id`: stable slug-like identifier.
- `date`: source publication date in `YYYY-MM-DD`.
- `source`: readable source name.
- `url`: canonical public source URL.
- `title`: source article title.
- `section`: one of the production filter sections.
- `tags`: short topical labels for internal/product use.
- `summary`: one-sentence strategic signal shown publicly.
- `why_it_matters`: editorial rationale, currently preserved in JSON.
- `confidence`: confidence level for the reviewed item.
- `caveat`: source or verification caveat.

Production filter sections are defined in `scripts/build.py`. The same
canonical label is shown in both the category filter and its story cards:

- Policy
- Public Services
- Education
- Workforce
- Research
- Infrastructure
- Business

Each section also has a permanent static page. The homepage and footer link to
these pages with normal HTML links, so readers and search engines can find them
without JavaScript. Each page has a unique title, description, canonical URL,
topic introduction, and filtered list of reviewed stories.

## Editorial Workflow

1. Run `python3 scripts/ingest.py --limit-per-source 5` and check any directly
   supplied source URLs; candidate discovery is an aid, not an editorial gate.
2. Review `dist/candidates.md` and source articles manually, including whether
   each source is reporting, analysis, commentary, or an announcement.
3. Add only approved items to `data/items.json`.
4. Keep summaries short, original, strategic, and focused on the Sarawak signal
   rather than phrases such as "the publication reports" or "the article says".
5. Keep source URL, confidence, caveat, and why-it-matters fields. Use the caveat
   to distinguish analysis from new programmes or implementation milestones.
6. Run build, unit tests, summary audit, and a targeted date audit using
   `python3 scripts/audit_dates.py --item-id <id>` for each added or edited item.
   The build sets the public last-updated date from the newest reviewed item.
7. Push to `main` only when the public feed is ready to redeploy.

The scheduled daily auto-publish path applies the same editorial gate. News
Bot owns the private screened-URL ledger and launches one Cursor Cloud Agent.
That agent searches approved public sources in Stage A and writes a structured
manifest of candidate URLs, headlines, dates, source names, and source-check
facts. Stage A summaries, recommendations, and caveats are not authoritative.
Leads are screened against existing items, known URLs, related developments,
and the ledger snapshot from News Bot. Stage B independently opens and checks
every surviving original source before it can consider publication. The
complete harness-neutral contract is in `docs/automation.md`.

With Hafiy's recurring approval, the workflow may commit and push qualifying
updates to `origin/main` after JSON validation, tests, date and summary audits,
the static build, local browser preview, `git diff --check`, and final scope
inspection all pass. It makes no content commit or push when there are no
qualifying stories, when Stage A returns `no_update`, or when any required
check fails. The automation may publish only `README.md`, `data/items.json`,
and `data/site.json`; it does not modify docs, assets, scripts, tests, or
unrelated local changes.

## Source Policy

`data/sources.json` currently watches a mix of media, institutional, government,
university, search, and focused topic pages, including SDEC, The Borneo Post,
DayakDaily, Sarawak Tribune, The Edge Malaysia, UKAS, SMA, SAINS, Swinburne
Sarawak, and UNIMAS.

Link scoring is a discovery prefilter. AI-led headlines that omit Sarawak may be
opened for body validation, but the article-body check still requires both a
Sarawak reference and a supported AI or future-economy focus. Source-page order
is preserved so recent items are reviewed before older keyword-dense links.

The source list is discovery infrastructure, not an endorsement list. Candidate
URLs must still be manually checked for article date, relevance, publication
context, and whether the source supports the summary.

Date validation is incremental during normal content work. Local updates select
the added or edited item IDs, and CI compares date-relevant fields with the
previous Git revision. Running `audit_dates.py` without a selector remains the
explicit full-audit option.

## Product Constraints

- Keep the build dependency-free for now.
- Treat `dist/` as generated output.
- Treat candidate files as internal review material.
- Do not send newsletters or publish new public surfaces without explicit
  approval. The recurring daily Cloud Agent is separately pre-authorized by
  Hafiy and remains limited to the verified publication paths described above.
- Prefer auditable source attribution over speed.

## Success Signals

Near-term success means:

- The weekly update flow is repeatable in under an hour.
- Every public item has a source, caveat, confidence, and why-it-matters field.
- The brief makes Sarawak's AI story easier to scan than reading scattered
  source sites.
- Dates and summaries pass audit checks.
- Readers can quickly distinguish policy, infrastructure, research, workforce,
  and public-service signals.
