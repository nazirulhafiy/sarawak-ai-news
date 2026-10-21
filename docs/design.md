# Design Notes

## Current Production Design

Production is a compact editorial feed rendered by `scripts/build.py` and styled
by `site/style.css`.

The current direction is intentionally restrained:

- White page and white cards.
- Broad `840px` maximum body width with a restrained `760px` reading column for the feed.
- A borderless masthead panel with a centered editorial headline at a `40px` to `52px` responsive scale and balanced wrapping. Site wording (`title`, `tagline`, `description`, `about_lead`) is owned by `data/site.json`; the build fills the hero H1 from `tagline`, document `<title>` / schema `CollectionPage` name as `Sarawak AI News | {title}`, and other brand surfaces from that file. Do not hand-type those strings outside `data/site.json`, except inside a generated block. `tests/test_site_copy.py` fails if they appear elsewhere in source. `python3 kit/generate_docs.py` writes the site-copy table under Visual System from `data/site.json`. The homepage `.brief` only carries a decorative mid-density network motif on the right (inline SVG, light gray in light mode and a slightly lifted gray in dark mode). The motif has no Sarawak colour stripe and does not replace the live headline, deck, or updated line.
- Geist Sans typography self-hosted from `site/fonts/Geist-Variable.woff2`
  (variable weights 100–900; licence in `site/fonts/OFL.txt`). `scripts/build.py`
  preloads the WOFF2 in each HTML head and copies the font plus `OFL.txt` into
  `dist/fonts/`. `site/style.css` declares `@font-face` with `font-display: swap`
  and sets the body stack to `"Geist", ui-sans-serif, system-ui`, and
  fallbacks. The hero headline aligns to the reference `48px` desktop scale with
  a responsive `40px` mobile floor.
- Supporting introduction at `18px`, giving the hero more generous rhythm while keeping the brief's Sarawak AI coverage concise.
- Sarawak red, yellow, and black accents.
- Refined top brand bar with a `16px` wordmark, compact `Home` and `About`
  links, a theme toggle, compact desktop height, and a Sarawak-color rule.
  The home link (`.brand`) starts with Design Bot’s origami line hornbill
  (`#snnav` / hub `#snnav`), then the site `title` from `data/site.json`, with a small gap.
  Canonical mark files live in the vendored `kit/assets/icons/`
  (`nav-mark-transparent.svg` light, `nav-mark-transparent-dark.svg` dark;
  transparent, no `#111` square). Matching copies under `site/icons/` are kept
  as the local mirror; the build copies kit marks to `dist/icons/`. Images use
  `alt=""` and `aria-hidden`; the text labels the link. Mark height matches the
  wordmark line (`1.15em`). The brand stays on one line (`white-space: nowrap`)
  down to 375px. SVGs are used as supplied — no recolouring. Favicon and footer
  brand text are unchanged.
  The sticky bar is a full-viewport outer shell (edge-to-edge background and
  scrolled bottom border/shadow) with an inner `max-width: 760px` wrapper that
  keeps the wordmark, Home/About links, theme toggle, and menu aligned to the
  reading column. The tri-colour rule follows the same content rail on viewports
  wider than `560px` (tablet and desktop): the red segment anchors the wordmark;
  yellow and black divide the remaining space on that rail equally.   From
  `560px` down (mobile), the rule extends edge to edge across the viewport:
  the red segment offsets by the bar’s horizontal padding (`--page-gutter`),
  and the yellow/black segment extends past the mobile theme and menu controls
  to the right viewport edge while the bar background and scrolled shadow stay
  full-bleed.
  The bar is `position: sticky; top: 0` with a solid page-colour background in
  light and dark mode so feed content scrolls beneath it. After any scroll,
  `site/app.js` toggles `.is-scrolled` for a thin bottom edge and subtle
  shadow. `html` uses `scroll-padding-top` and `overflow-x: clip`, and heroes
  use `scroll-margin-top`, so in-page anchors clear the sticky bar without a
  horizontal scrollbar.
- Horizontal category filter using the seven canonical production labels, with
  24px between the filter and the first card. When the pill row overflows,
  non-interactive edge hints (48px fade plus chevron on the side that still has
  hidden categories) signal horizontal scrolling; hints stay hidden when every
  category fits. The homepage lists every reviewed story; there are no separate
  category archive pages. Legacy `/policy.html` (and the other six slugs) are
  noindex redirect stubs to the homepage.
- Ranked story cards with 16px padding (14px from 560px down), 8px between title and summary, and 14px between cards. On fine-pointer devices (`@media (hover: hover)`), `.story-card:hover` shares a subtle lift: `translateY(-3px)` with a slight tilt (`rotate(-.25deg)`, even cards `rotate(.25deg)`), softened border colour, and a light box shadow (stronger in dark mode). Title links underline on hover/focus and gain a trailing `↗` after the title text. `prefers-reduced-motion` disables the hover transform.
- Compact black index badges (26px desktop, 24px from 560px down) so the rank stays secondary to the title.
- Source name highlighted in yellow.
- On narrow viewports (`max-width: 560px`), each card’s meta row stacks as two lines: the date alone on the first line, then the yellow source chip and category on the second line with a middot separator (`SOURCE · CATEGORY`). Wider viewports keep the single-line `DATE · SOURCE · CATEGORY` meta row.
- Structured, contained footer rendered by `kit.python.shell.render_footer`: a
  source summary, a subtle desktop divider, vertical Home/About/Contact links
  (Contact always uses `mailto:contact@sarawak.news`), and a full-width builder
  and independence attribution row. The footer note is two sentences joined by
  the kit’s forced `<br class="site-footer-note-break" />` (`brand_note_parts`
  / `FOOTER_NOTE_BREAK` in `kit.python.shell`). The footer follows the story
  list with a restrained 40px section gap.
- Optional dark mode using the same hierarchy: near-black canvas, lifted dark
  cards, softened borders, brighter text, and preserved Sarawak yellow/red
  accents. The selected category filter pill keeps its black fill and white
  label but uses a Sarawak yellow border so the active filter stays visible
  against dark surfaces.
- The homepage and supporting routes use a shared 1200x630 social card with
  the site name, current headline, short description, and Sarawak colour rule.
  Home and About point `og:image` and `twitter:image` at
  `https://ai.sarawak.news/social-card.png` plus a content-hash query string
  from `versioned_href` in `kit/python/asset_urls.py` (first 12 hex characters
  of the SHA-256 of `site/social-card.png`). The tab favicon stays the inline
  emoji data URI; there is no published apple-touch icon or web app manifest
  yet. `tests/test_asset_urls.py` fails if source trees contain a hand-typed
  asset query stamp outside a generated block.

The design is closer to an editorial memo or briefing page than to a dashboard.
It is appropriate for proving source-attributed curation before investing in a
larger product interface.

## Interaction Design

`site/app.js` progressively reveals the category filter and handles filtering
without dependencies. It does not read a hash or query string to preselect a
filter.

Behavior:

- Filter starts hidden in HTML and appears when JavaScript loads.
- When the category row overflows, `site/app.js` toggles `can-scroll-start` and
  `can-scroll-end` on `[data-category-scroll]` from scroll position, resize,
  and font load. Matching CSS shows a 48px page-colour fade and chevron on the
  start or end edge; hints use `pointer-events: none`, `aria-hidden="true"`, and
  stay off when all pills fit without scrolling.
- Filter buttons and story cards use the same canonical category labels:
  Policy, Public Services, Education, Workforce, Research, Infrastructure, and
  Business.
- Buttons use `aria-pressed`.
- Hovering a category temporarily previews the selected treatment and returns
  the current selection to its resting appearance without changing results or
  `aria-pressed`; moving away restores the actual selection.
- Clicking an already-selected category resets the feed to `All`; clicking the
  active `All` button leaves the full feed unchanged.
- Hidden story cards use the `hidden` attribute.
- Story cards lift slightly and tilt by a quarter-degree on hover, alternating
  direction for a tactile browsing cue; the effect is disabled for reduced-motion users.
  On fine-pointer desktop hover, the title keeps its underline treatment and
  gains a trailing external-link arrow (`↗`) after the title text. On touch
  devices (`hover: none` or `pointer: coarse`), that `↗` is not shown.
- The hero panel and its headline, introduction, and update line still reveal
  in a visible sequence on load. Story cards do not share it. With `html.js`,
  an unrevealed `.story-card` stays at opacity 0 and `translateY(12px)` until an
  IntersectionObserver adds `is-revealed` once (`rootMargin: 0px`,
  `threshold: 0`) and then unobserves that card. The motion is `story-reveal`,
  0.7s, `cubic-bezier(.22, 1, .36, 1)`. Reduced motion shows the cards
  immediately. Hero load animations are unchanged, and all reveal motion is
  disabled for reduced-motion users.
- The masthead theme toggle is a 36px circular control with a morphing moon/sun
  icon. It follows the system theme by default, persists an explicit choice in
  local storage, and updates its accessible label for the next mode.
- Home and About links are borderless at rest and use a selected treatment on
  hover: black surface, white text, and a visible border. Footer links turn
  Sarawak red and bold on hover, with the same red underline as the builder
  credit.
- Desktop navigation uses a light 12px treatment with subtle tracking and an
  open line height, balancing its type against the adjacent 16px theme glyph.
- Geist is self-hosted (not loaded from a CDN) and inherited by the body and
  controls, including buttons, so typography stays consistent across navigation,
  filters, cards, and footer.
- Story ranks are renumbered after filtering.
- A visually hidden live region reports the current result count.
- Reloading the page resets the viewport to the top, while ordinary history
  navigation can preserve the reader's position.
- The masthead sticky state is driven by a passive scroll listener on `.bar`
  (independent of the category filter), so Home and About both get the scrolled
  edge treatment.
- Markup comes from `kit.python.shell.render_back_to_top`. CSS and JS are owned
  by `kit/css/back-to-top.css` and `kit/js/back-to-top.js`, mirrored into
  `site/style.css` / `site/app.js` between `/* sn-kit:back-to-top:begin|end */`
  markers. The control sits in the viewport's bottom-right corner (not beside
  the content column). It appears after 600 px of scroll with a short
  opacity/translate fade (~180 ms); `prefers-reduced-motion` disables that
  motion. When hidden it is not focusable (`hidden`).
- Desktop (wider than 560 px): text pill `Back to top ↑`, `24px` from the
  viewport right and bottom edges. Typography and spacing are hardcoded on
  `.back-to-top` (not inherited from body tokens): Geist stack at `11px` /
  `850` / `1.3`, `letter-spacing: normal`, `padding: 8px 12px`, `gap: 3.08px`,
  `border-radius: 999px`, `1px` border, and the shared shadow — so the pill
  matches the Sarawak hub standard when copied verbatim.
- Phone (560 px and below): icon-only ↑ on a `44×44` circle (`border-radius:
  50%`), inset `max(14px, env(safe-area-inset-*) + 14px)` from the right and
  bottom; `18px` arrow size on the same hardcoded font stack.
- Both themes: `#111` chip, `#f7c948` label/arrow; light mode `1px` border
  `#111`, dark mode `1px` border `#f7c948`. Focus: `3px` yellow ring, `2px`
  offset. Click scrolls smoothly to the top (instant when reduced motion is on).

The page still works as a readable feed without JavaScript.

## Visual System

Site wording from `data/site.json`:

<!-- BEGIN GENERATED: site-copy -->
| Field | Value |
| --- | --- |
| `title` | AI.Sarawak.News |
| `tagline` | Sarawak AI news, in one place. |
| `description` | Sarawak AI news in one place: reviewed, source-linked updates on AI policy, public services, education, workforce, research, infrastructure and business. |
<!-- END GENERATED: site-copy -->

Production tokens come from `:root` and `html[data-theme="dark"]` in
`site/style.css`. The table is generated from those rules.

<!-- BEGIN GENERATED: design-tokens -->
| Token | `:root` | `html[data-theme="dark"]` |
| --- | --- | --- |
| `--canvas` | #ffffff | #0f1115 |
| `--page` | #ffffff | #0f1115 |
| `--card` | #ffffff | #171b22 |
| `--ink` | #111827 | #f3f5f7 |
| `--muted` | #6b7280 | #aeb6c2 |
| `--line` | #e2e4e9 | #2c333d |
| `--sarawak-red` | #d22630 | #f15b61 |
| `--sarawak-red-ink` | #9f1d26 | #ff8d92 |
| `--sarawak-yellow` | #f7c948 | #f7c948 |
| `--sarawak-yellow-soft` | #fffbea | #3a3110 |
| `--sarawak-black` | #111111 | #111111 |
| `--page-gutter` | 20px |  |
<!-- END GENERATED: design-tokens -->

Cards use 8 px radius or less in production. The layout stays restrained (no
dashboard chrome) but story cards still use the shared hover lift above; density
stays high enough for repeated scanning.

## Content Hierarchy

Homepage hierarchy:

1. Brand (`title` from `data/site.json`) and `Home`/`About` navigation.
2. Hero headline: `tagline` from `data/site.json`.
3. Brief deck (`p.brief-deck`, max-width `600px`): `Tracking artificial intelligence developments across Sarawak, bringing AI policy, projects, research and adoption into one source-linked brief.`
4. Last updated weekday and date.
5. Category filters.
6. Ranked story cards (full reviewed feed).
7. Independent-publication footer note.

There are no public category archive pages. The sitemap lists only the homepage
and About. Former category URLs remain as noindex redirect stubs to
`https://ai.sarawak.news/`.

The masthead contains the brand lockup, compact navigation, theme toggle, and
color rule. It stays pinned while the reader scrolls, with a solid background and
a scrolled shadow so story content does not show through. The About page moves
fuller publication context off the already wordy homepage while keeping the first
screen focused on the live brief.

The About page uses the same restrained system: the hero opens on
`About {title}` from `data/site.json` (no eyebrow label), then the `about_lead`
lede and sections for why Sarawak AI, coverage categories (tags, not separate
pages), how stories are picked and checked (one short paragraph in
`scripts/build.py`: daily scan checks public sources; approved items get a short
original summary and source link — no fixed clock time in the copy), and contact
(`mailto:contact@sarawak.news` only). It keeps the
explanation closer to the editorial feed instead of adding dashboard-like
metrics or pills.

Each story card currently shows date, source, category, title, and summary. Its
category label exactly matches the corresponding browse filter. On phone-width
layouts the date sits on its own line above the source chip and category; desktop
meta order is unchanged. The card does not expose tags, confidence, caveat, or
why-it-matters copy in the HTML. Generated `dist/items.json` still carries
`why_it_matters` and `tags` for machine readers but omits internal `confidence`
and `caveat` fields (those stay in `data/items.json` only).

### Discovery and syndication

The homepage `<head>` carries JSON-LD (`Organization` with the versioned hornbill
mark URL, `WebSite`, `CollectionPage`, and an `ItemList` aligned to the rendered
story order) plus `<link rel="alternate" type="application/rss+xml">` pointing at
`feed.xml`. The build writes RSS 2.0 to `dist/feed.xml` (channel metadata from
`data/site.json`, one `<item>` per reviewed story linking to the original source
URL) and lists `feed.xml` in `sitemap.xml` alongside `/` and `about.html`.

## Design Variants

`design-variants/` contains static explorations:

- Variant A: near-clone editorial memo.
- Variant B: Sarawak-branded brief.
- Variant C: productized intelligence brief.
- Variant D: civic intelligence feed.

`design-variants/README.md` currently recommends Variant D as the next serious
product direction. Variant D introduces a broader Sarawak.News civic
intelligence feel with navigation, feature modules, newsletter affordances, and
category breadth. It is only a static prototype and contains placeholder copy.

Important implementation note: `scripts/generate_design_variants.py` currently
generates only variants A, B, and C. Variant D exists as a standalone checked-in
HTML file.

## Recommended Direction

Keep the current compact production feed until the content workflow is reliable.
For the next app iteration, use Variant D as inspiration, but rebuild it against
real `data/items.json` and the existing source-attribution rules.

Recommended adjustments before moving Variant D into production:

- Replace placeholder stories with real reviewed items.
- Preserve source URL, caveat, confidence, and why-it-matters fields.
- Avoid newsletter/signup actions until approved.
- Keep the first screen focused on the live brief, not marketing copy.
- Make modules data-backed or omit them.
- Keep card radii and density consistent with the existing app unless a full
  design-system update is approved.

## Design Risks

- On narrow screens, the inline Home and About links are hidden and remain available in an accessible hamburger menu at the far right, immediately after the theme toggle; desktop keeps the inline links. The mobile menu closes after a link selection, an outside tap, or Escape, and touch devices do not retain hover styling after tapping the controls.
- The hamburger and theme controls use equal 36px icon-only touch targets at every breakpoint. The hamburger keeps its 18px, 1.6px-stroke mark while the denser theme glyph is optically balanced at 16px, inspired by OpenClaw’s compact header treatment and with no circular outlines. Keyboard focus remains visibly indicated.
- The masthead, hero, category filter, story list, and footer share a 760px desktop content rail so their outer edges align; the three-colour rule follows the same rail.
- On desktop, Home and About sit on the right side of the masthead immediately before the theme control; on mobile they collapse into the hamburger menu.

- The production UI hides some useful editorial metadata.
- Variant D is more polished but may imply product features that do not exist
  yet, such as newsletter signup, custom reports, topic counts, and daily
  updates.
- The current mobile headline uses viewport-based sizing; future UI work should
  verify text fit carefully across common mobile widths.
- The brief currently has no archive, item detail view, or persistent category
  URL state.

## Shared kit

Fleet chrome shared with other sarawak.news sites is vendored from
[sarawak-news-hub](https://github.com/nazirulhafiy/sarawak-news-hub) `kit/` at the
commit recorded in `kit/PIN`. Delivery is a **vendored copy + PIN +
`python3 kit/sync.py --check --hub-path …`**, not a git submodule. See
`kit/README.md`.

| Kit path | Provides |
| --- | --- |
| `kit/python/shell.py` | Header, footer (Contact `mailto:contact@sarawak.news`; optional `brand_note_parts` / `FOOTER_NOTE_BREAK`), back-to-top markup |
| `kit/python/analytics_loader.py` | Registry-driven production loader (`data-sn-analytics-loader`) |
| `kit/python/analytics_registry.py` | `data/analytics.json` validation (this site keeps its own registry file) |
| `kit/python/asset_urls.py` | Content-hash query strings for share-image URLs |
| `kit/python/docs_facts.py` | Generated fact blocks for `docs/design.md` and `README.md` |
| `kit/generate_docs.py` | Writes those blocks, or checks them with `--check` |
| `kit/favicon_sheet.py` | 16 / 32 / 48 favicon contact sheet (proof script, not a CI gate) |
| `kit/assets/icons/` | Origami hornbill nav marks |
| `kit/css/back-to-top.css` / `kit/js/back-to-top.js` | Back-to-top rules and behaviour (mirrored into `site/style.css` / `site/app.js` inside `sn-kit:back-to-top` markers) |

CI runs `python3 kit/sync.py --check --hub-path .hub-kit-ref` before tests, then
`python3 kit/generate_docs.py --check`. Kit sync fails on local kit edits, a
stale PIN, or invariant breaks (for example removing Contact). The docs
generator fails when a generated block does not match `data/site.json`, the
analytics registry, `data/hosting.json`, or the custom properties in
`site/style.css`. The prose docs check (`.github/workflows/docs-check.yml`)
stays separate.

## Deploy

`scripts/build.py` writes `dist/` only. `.github/workflows/build.yml` tests and
builds on every pull request. A push to `main` deploys that build with GitHub
Pages. Hosting facts are owned by `data/hosting.json`.

<!-- BEGIN GENERATED: hosting -->
| Field | Value |
| --- | --- |
| `hostname` | `ai.sarawak.news` |
| `target` | GitHub Pages |
<!-- END GENERATED: hosting -->

## Analytics

IDs, cookie name, and CF `spa` live in `data/analytics.json` (fleet kit shape,
`version: 1`). Do not change them when bumping the kit pin. The loader
implementation lives in `kit/python/analytics_loader.py`; `scripts/build.py` →
`render_analytics_loader()` emits **one** inline
`<script data-sn-analytics-loader>` per page in `<head>` (edit the registry /
kit, not `dist/`). CI runs `scripts/check_analytics_dist.py` so each built HTML
page has exactly one loader, only registry GA4 / CF tokens, only the registry
cookie (plus per-host `legacy_internal_cookies` honour), and CF `spa` matching
the registry (`true` here).

<!-- BEGIN GENERATED: analytics -->
| Field | Value |
| --- | --- |
| `ga4_measurement_id` | `G-RJ2ZFQ52J7` |
| `cf_beacon_token` | `092a061973fc4d899cd2e4b52952af89` |
| `internal_cookie` | `sn_internal` |
| `hosts` | `ai.sarawak.news`, `www.ai.sarawak.news` |
<!-- END GENERATED: analytics -->

- Host gate: registry hosts only. Preview hosts never load GA or the Cloudflare
  beacon.
- Internal traffic: `?internal=1` sets first-party `sn_internal=1`
  (`path=/`, `max-age=31536000` ≈ 1 year, `SameSite=Lax`, `Secure` on https).
  `?internal=0` clears the primary and every listed legacy cookie. While
  internal, GA4 gets `traffic_type: 'internal'` and the CF beacon is skipped.
  Agents and screenshot checks should open
  `https://ai.sarawak.news/?internal=1` (see `AGENTS.md` and
  `tools/shots.config.json`).
- Cloudflare Web Analytics: `spa: true`, same production hosts, only when not
  internal.

- No Content-Security-Policy is set; if one is added, allow `www.googletagmanager.com`, `*.google-analytics.com` and `static.cloudflareinsights.com`.
