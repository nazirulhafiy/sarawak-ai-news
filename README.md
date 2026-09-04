# Sarawak AI News

An independent, source-linked briefing about how artificial intelligence and
digital change are affecting Sarawak.

**Read the live briefing:** [ai.sarawak.news](https://ai.sarawak.news/)

This repository is a proof of concept, which means it is a small working
version used to test the idea before building a larger publication.

## What You Will Find

Sarawak AI News turns scattered public information into a short, easy-to-scan
brief. Each public story card includes:

- a link to the original source;
- a concise, original summary; and
- its date, source, and category.

The reviewed data behind each story also keeps an explanation of why it matters
to Sarawak, a confidence level, and a caveat for editorial review. These fields
are not displayed on the public story cards.

The production categories are Policy, Public Services, Education, Workforce,
Research, Infrastructure, and Business. The same category label appears in the
browse filter and on every matching story card. Each category also has a
permanent public page with a unique introduction and canonical URL.

## Who It Is For

The brief is designed for anyone who wants to understand Sarawak's changing AI
and digital landscape, including members of the public, policymakers,
researchers, educators, journalists, community leaders, and business owners.
No technical knowledge is required to read it.

## How It Works

1. News Bot runs the daily routine in `Asia/Kuching` and launches one Cursor
   Cloud Agent when a run is due.
2. That Cloud Agent searches approved public sources (Stage A), then
   independently reopens each surviving original page (Stage B).
3. Qualifying stories receive a short, source-attributed summary, context,
   confidence level, and caveat.
4. After the required tests, audits, build, preview, and scope checks pass, the
   reviewed data is committed to `main` and published through GitHub Pages.

Discovery and the daily publishing checks are partly automated, but the
Cloud Agent does not publish blindly. Every candidate still requires original
source verification and editorial qualification. With Hafiy's recurring
approval, the workflow may commit and push qualifying feed updates; if no
story qualifies or any required check fails, it makes no publication commit.
The project does not copy or republish full articles.

For the scheduled Cloud Agent, Stage A is the discovery gate. Stage B still
reopens every surviving original page. AI-led headlines may proceed to
article-body checks when the headline itself does not mention Sarawak, but
the body must still make the Sarawak and AI or specific digital-technology
relevance clear before the item is considered. General words such as "smart",
"innovation", or "new technology" do not qualify without a named system,
method, or technical function.

## Current Status

This is a working public prototype, not a fully automated news service. As of
the latest content audit on 4 September 2026, it contains 60 reviewed stories.
Candidate discovery, source checks, and website building are supported by
automation, while the editorial criteria and recurring publishing approval
remain explicitly controlled by Hafiy. The portable operating contract is in
[`docs/automation.md`](docs/automation.md).

## Editorial Principles

- **Show the source.** Every story links back to the original publication.
- **Add context.** Each item explains why the development may matter locally.
- **Lead with the signal.** Summaries describe the Sarawak development directly;
  publication attribution stays in the source label.
- **Be transparent.** Confidence and caveats are kept with every item.
- **Keep it concise.** Summaries are original and intentionally short.
- **Require source review.** Discovery results stay private until the original
  source has been checked and the item passes the editorial criteria.

## For Contributors and Developers

The project is deliberately small and dependency-free. You only need Python 3
to build and test it.

### Run It Locally

Build the site:

```bash
python3 scripts/build.py
```

Start a local preview:

```bash
python3 -m http.server 4173 -d dist
```

Then open [http://127.0.0.1:4173](http://127.0.0.1:4173) or the local About page at
[http://127.0.0.1:4173/about.html](http://127.0.0.1:4173/about.html).

### Project Map

```text
data/items.json       Reviewed stories shown on the public site
data/sources.json     Public pages checked for possible stories
data/site.json        Site information; last-updated is derived at build time
scripts/build.py      Builds the website in dist/
scripts/ingest.py     Finds candidates for manual review
site/style.css        Production visual design
site/app.js           Category filtering
dist/about.html       Generated About page explaining the editorial workflow
dist/<category>.html  Generated permanent pages for each production category
tests/                Automated checks
design-variants/      Design experiments, not production pages
```

### Find Candidate Stories

```bash
python3 scripts/ingest.py --limit-per-source 5
```

This creates `dist/candidates.json` and `dist/candidates.md` for internal
review. It does not publish or summarize anything. Read the original source
before adding a story to `data/items.json`.

### Update the Brief

1. Run candidate discovery and check any directly supplied source URLs.
2. Review the original sources manually, including their publication context.
3. Add approved stories to `data/items.json`.
4. Run the checks below. The build derives last-updated from the newest item.
5. Build and preview the site.
6. Push the approved update to `main` for GitHub Pages to deploy it.

The scheduled daily workflow follows the same editorial gate. News Bot owns
the private screened-URL ledger and launches one Cloud Agent. That agent
searches the approved public sources, screens URLs against the reviewed feed
and the ledger snapshot, and independently reopens every surviving original
source before publication. Only verified English source pages qualify. If
Stage A finds no unscreened candidate, the run returns `no_update` and makes
no repository change.

### Check Your Changes

```bash
python3 -m unittest discover -s tests -v
python3 scripts/audit_dates.py --item-id <added-or-edited-item-id>
python3 scripts/audit_summaries.py
python3 scripts/build.py
```

Repeat `--item-id` for multiple additions. The targeted date audit checks only
those stories against source-page metadata and may warn if a selected page is
temporarily unavailable. Run `python3 scripts/audit_dates.py` without a selector
for a deliberate full audit. CI automatically checks records changed from the
previous commit, while a manual workflow run performs the full audit. The
summary audit checks for clear, concise, non-hyped explanations.

GitHub Actions runs the tests, audits, and site build before deploying `dist/`
to GitHub Pages from `main`.

Public publishing, newsletter sending, domain setup, or outreach requires
Hafiy's explicit approval.
