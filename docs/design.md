# Design Notes

## Current Production Design

Production is a compact editorial feed rendered by `scripts/build.py` and styled
by `site/style.css`.

The current direction is intentionally restrained:

- White page and white cards.
- Broad `840px` maximum body width with a restrained `760px` reading column for the feed.
- A borderless masthead panel with a centered editorial headline at a `40px` to `52px` responsive scale and balanced wrapping. The live hero copy reads `Sarawak AI news, in one place.` (matching `<title>` and structured data). The homepage `.brief` only carries a decorative mid-density network motif on the right (inline SVG, light gray in light mode and a slightly lifted gray in dark mode). The motif has no Sarawak colour stripe and does not replace the live headline, deck, or updated line.
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
  category fits.
- Ranked story cards with 16px padding (14px from 560px down), 8px between title and summary, and 14px between cards. On fine-pointer devices (`@media (hover: hover)`), `.story-card:hover` shares a subtle lift: `translateY(-3px)` with a slight tilt (`rotate(-.25deg)`, even cards `rotate(.25deg)`), softened border colour, and a light box shadow (stronger in dark mode). Title links underline on hover/focus and gain a trailing `↗` after the title text. `prefers-reduced-motion` disables the hover transform.
- Compact black index badges (26px desktop, 24px from 560px down) so the rank stays secondary to the title.
- Source name highlighted in yellow.
- On narrow viewports (`max-width: 560px`), each card’s meta row stacks as two lines: the date alone on the first line, then the yellow source chip and category on the second line with a middot separator (`SOURCE · CATEGORY`). Wider viewports keep the single-line `DATE · SOURCE · CATEGORY` meta row.
- Structured, contained footer with a source summary, a subtle desktop divider,
  vertical Home/About and category links, and a full-width builder and independence
  attribution row. A thin, edge-to-edge divider and controlled vertical spacing
  separate the Categories group from the main navigation links. The footer
  follows the story list with a restrained 40px section gap.
- Optional dark mode using the same hierarchy: near-black canvas, lifted dark
  cards, softened borders, brighter text, and preserved Sarawak yellow/red
  accents. The selected category filter pill keeps its black fill and white
  label but uses a Sarawak yellow border so the active filter stays visible
  against dark surfaces.
- The homepage and supporting routes use a shared 1200x630 social card with
  the site name, current headline, short description, and Sarawak colour rule.

The design is closer to an editorial memo or briefing page than to a dashboard.
It is appropriate for proving source-attributed curation before investing in a
larger product interface.

## Interaction Design

`site/app.js` progressively reveals the category filter and handles filtering
without dependencies.

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
  in a visible sequence on load, and category heroes keep that same load
  animation. Story cards do not share it. With `html.js`, an unrevealed
  `.story-card` stays at opacity 0 and `translateY(12px)` until an
  IntersectionObserver adds `is-revealed` once (`rootMargin: 0px`,
  `threshold: 0`) and then unobserves that card. The motion is `story-reveal`,
  0.7s, `cubic-bezier(.22, 1, .36, 1)`. Reduced motion shows the cards
  immediately. Hero and category-hero load animations are unchanged, and all
  reveal motion is disabled for reduced-motion users.
- The masthead theme toggle is a 36px circular control with a morphing moon/sun
  icon. It follows the system theme by default, persists an explicit choice in
  local storage, and updates its accessible label for the next mode.
- Home and About links are borderless at rest and use the selected-filter
  treatment on hover: black surface, white text, and a visible border. Footer
  links turn Sarawak red and bold on hover, with the same red underline as the
  builder credit.
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
  (independent of the category filter), so Home, About, and category pages all
  get the scrolled edge treatment.
- A fixed `Back to top` control sits in the viewport's bottom-right corner (not
  beside the content column). It appears after 600 px of scroll with a short
  opacity/translate fade (~180 ms); `prefers-reduced-motion` disables that
  motion. When hidden it is not focusable (`hidden`, `tabindex="-1"`,
  `aria-hidden="true"`).
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

Production tokens in `site/style.css`:

- Canvas/page/card: white.
- Ink: near-black.
- Muted text: gray.
- Accent red: `#d22630`.
- Accent yellow: `#f7c948`.
- Accent black: `#111111`.
- Dark canvas: `#0f1115`; dark card: `#171b22`; dark text and border tokens are
  defined under `html[data-theme="dark"]`.

Cards use 8 px radius or less in production. The layout stays restrained (no
dashboard chrome) but story cards still use the shared hover lift above; density
stays high enough for repeated scanning.

## Content Hierarchy

Homepage hierarchy:

1. Brand and `Home`/`About` navigation.
2. Hero headline: `Sarawak AI news, in one place.`
3. Short introduction covering Sarawak AI policy, projects, research, and adoption.
4. Last updated weekday and date.
5. Category filters.
6. Ranked story cards.
7. Independent-publication footer note.

The seven category pages use the same masthead, story cards, theme controls,
and footer. Each page starts with a compact topic introduction, a link back to
all news, and only the stories in that category.

The masthead contains the brand lockup, compact navigation, theme toggle, and
color rule. It stays pinned while the reader scrolls, with a solid background and
a scrolled shadow so story content does not show through. The About page moves
fuller publication context off the already wordy homepage while keeping the first
screen focused on the live brief.

The About page uses the same restrained system: a clear opening statement and
short sections for purpose, coverage, and workflow. It keeps the explanation
closer to the editorial feed instead of adding dashboard-like metrics or pills.

Each story card currently shows date, source, category, title, and summary. Its
category label exactly matches the corresponding browse filter. On phone-width
layouts the date sits on its own line above the source chip and category; desktop
meta order is unchanged. The card does not expose tags, confidence, caveat, or
why-it-matters copy in the HTML, although those fields are preserved in generated
JSON for editorial review.

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

## Analytics

Production pages are generated by `scripts/build.py` (for example `dist/index.html`
after a local build). Each HTML document includes:

- Google Analytics 4: measurement ID `G-RJ2ZFQ52J7`, loaded in `<head>` via
  `render_ga_script()` (`gtag.js` from `www.googletagmanager.com`).
- Cloudflare Web Analytics: deferred `beacon.min.js` from
  `static.cloudflareinsights.com` before `</body>` via `render_analytics_script()`,
  with `data-cf-beacon` token `092a061973fc4d899cd2e4b52952af89` and `"spa": true`.

- No Content-Security-Policy is set; if one is added, allow `www.googletagmanager.com`, `*.google-analytics.com` and `static.cloudflareinsights.com`.
