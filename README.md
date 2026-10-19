# Sarawak AI News

Sarawak has set a target to become Malaysia’s leading AI hub by 2027, as part
of its talent-development and digital-economy push toward a developed,
high-income state by 2030.

This is an independent aggregator that tracks public news against that backdrop.

**Read the live briefing:** [ai.sarawak.news](https://ai.sarawak.news/)

The homepage hero headline is **Sarawak AI news, in one place.** The document
`<title>` and schema `CollectionPage` name are **Sarawak AI News | AI.Sarawak.News**.

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

## Analytics

Google Analytics 4 (`G-RJ2ZFQ52J7`) and [Cloudflare Web
Analytics](https://developers.cloudflare.com/web-analytics/) are injected at
build time (`render_ga_script()` in `<head>`,
`render_analytics_script()` before `</body>` in `scripts/build.py`). Both load
only on `ai.sarawak.news` / `www.ai.sarawak.news`. On those hosts,
`?internal=1` sets a long-lived `sn_internal` cookie so gtag sends
`traffic_type: 'internal'` and the Cloudflare beacon is skipped; `?internal=0`
clears it. The Cloudflare token is `092a061973fc4d899cd2e4b52952af89`
(`spa: true` on the deferred `beacon.min.js` tag). See `docs/design.md`
(Analytics).
