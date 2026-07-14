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
- its date, source, and section.

The reviewed data behind each story also keeps an explanation of why it matters
to Sarawak, a confidence level, and a caveat for editorial review. These fields
are not displayed on the public story cards.

The brief covers areas such as government and policy, public services,
infrastructure, education, research, and the workforce.

## Who It Is For

The brief is designed for anyone who wants to understand Sarawak's changing AI
and digital landscape, including members of the public, policymakers,
researchers, educators, journalists, community leaders, and business owners.
No technical knowledge is required to read it.

## How It Works

1. A lightweight script checks selected public websites for possible stories.
2. A person opens and reviews each candidate at its original source.
3. Approved stories receive a short, source-attributed summary, context,
   confidence level, and caveat.
4. The reviewed data is turned into a static website and published through
   GitHub Pages.

Story discovery is partly automated, but publication is not. Nothing becomes
public until it has been manually reviewed. The project does not copy or
republish full articles.

## Current Status

This is a working public prototype, not a fully automated news service. As of
the latest content audit on 14 July 2026, it contains 27 reviewed stories.
Candidate discovery and website building work, while editorial review and
publishing remain human-controlled.

## Editorial Principles

- **Show the source.** Every story links back to the original publication.
- **Add context.** Each item explains why the development may matter locally.
- **Be transparent.** Confidence and caveats are kept with every item.
- **Keep it concise.** Summaries are original and intentionally short.
- **Require human review.** Discovery results stay private until approved.

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

Then open [http://127.0.0.1:4173](http://127.0.0.1:4173).

### Project Map

```text
data/items.json       Reviewed stories shown on the public site
data/sources.json     Public pages checked for possible stories
data/site.json        Site information, including the update time
scripts/build.py      Builds the website in dist/
scripts/ingest.py     Finds candidates for manual review
site/style.css        Production visual design
site/app.js           Category filtering
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

1. Run candidate discovery.
2. Review the original sources manually.
3. Add approved stories to `data/items.json`.
4. Update `last_updated` in `data/site.json`.
5. Run the checks below.
6. Build and preview the site.
7. Push the approved update to `main` for GitHub Pages to deploy it.

### Check Your Changes

```bash
python3 -m unittest discover -s tests -v
python3 scripts/audit_dates.py
python3 scripts/audit_summaries.py
python3 scripts/build.py
```

The date audit checks story dates against source-page metadata. It may warn if
a source page is temporarily unavailable. The summary audit checks for clear,
concise, non-hyped explanations.

GitHub Actions runs the tests, audits, and site build before deploying `dist/`
to GitHub Pages from `main`.

Public publishing, newsletter sending, domain setup, or outreach requires
Hafiy's explicit approval.
