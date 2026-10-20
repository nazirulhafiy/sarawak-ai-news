# Sarawak AI News

Sarawak has set a target to become Malaysia’s leading AI hub by 2027, as part
of its talent-development and digital-economy push toward a developed,
high-income state by 2030.

This is an independent aggregator that tracks public news against that backdrop.

**Read the live briefing:** [ai.sarawak.news](https://ai.sarawak.news/)

Site title, tagline, description, and About lead live only in
[`data/site.json`](data/site.json); the build fills every page surface from that
file. `tests/test_site_copy.py` fails if those strings are hand-typed elsewhere
in source. The table below is generated from the same file.

<!-- BEGIN GENERATED: site-copy -->
| Field | Value |
| --- | --- |
| `title` | AI.Sarawak.News |
| `tagline` | Sarawak AI news, in one place. |
| `description` | Sarawak AI news in one place: reviewed, source-linked updates on AI policy, public services, education, workforce, research, infrastructure and business. |
<!-- END GENERATED: site-copy -->

## What You Will Find

Sarawak AI News turns scattered public information into a short, easy-to-scan
brief. The homepage lists every reviewed story with a client-side category
filter. Each public story card includes:

- a link to the original source;
- a concise, original summary; and
- its date, source, and category.

The reviewed data behind each story also keeps an explanation of why it matters
to Sarawak, a confidence level, and a caveat for editorial review. These fields
are not displayed on the public story cards.

The production categories are Policy, Public Services, Education, Workforce,
Research, Infrastructure, and Business. The same category label appears in the
browse filter and on every matching story card.

## Who It Is For

The brief is designed for anyone who wants to understand Sarawak's changing AI
and digital landscape, including members of the public, policymakers,
researchers, educators, journalists, community leaders, and business owners.
No technical knowledge is required to read it.

## Editorial Principles

- **Show the source.** Every story links back to the original publication.
- **Add context.** Each item explains why the development may matter locally.
- **Lead with the signal.** Summaries describe the Sarawak development directly;
  publication attribution stays in the source label.
- **Be transparent.** Confidence and caveats are kept with every item.
- **Keep it concise.** Summaries are original and intentionally short.
- **Require source review.** Discovery results stay private until the original
  source has been checked and the item passes the editorial criteria.

## Deploy

`.github/workflows/build.yml` runs the tests, builds `dist/`, and deploys that
folder with GitHub Pages. Hosting facts are owned by
[`data/hosting.json`](data/hosting.json).

<!-- BEGIN GENERATED: hosting -->
| Field | Value |
| --- | --- |
| `hostname` | `ai.sarawak.news` |
| `target` | GitHub Pages |
<!-- END GENERATED: hosting -->

## Analytics

GA4 ID, CF beacon token, shared `internal_cookie` (`sn_internal`), per-host
`legacy_internal_cookies` and `aliases`, and `spa` (`true`) live in
[`data/analytics.json`](data/analytics.json). `scripts/build.py` emits one
`data-sn-analytics-loader` script per page from that registry. Both trackers
load only on the hosts in the table below. Open the live site with
`?internal=1` for agent and QA visits. GA4 gets `traffic_type: 'internal'` and
the CF beacon is skipped (see `AGENTS.md`). CI runs
`scripts/check_analytics_dist.py` after the build. Details are in
`docs/design.md` under “Analytics”.

<!-- BEGIN GENERATED: analytics -->
| Field | Value |
| --- | --- |
| `ga4_measurement_id` | `G-RJ2ZFQ52J7` |
| `cf_beacon_token` | `092a061973fc4d899cd2e4b52952af89` |
| `internal_cookie` | `sn_internal` |
| `hosts` | `ai.sarawak.news`, `www.ai.sarawak.news` |
<!-- END GENERATED: analytics -->

## Checks

```bash
python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"
python3 kit/generate_docs.py --check
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
python3 scripts/build.py
python3 scripts/check_analytics_dist.py
```

Shared kit chrome is vendored from hub at [`kit/PIN`](kit/PIN). See
[`kit/README.md`](kit/README.md).
