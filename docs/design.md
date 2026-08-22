# Design Notes

## Current Production Design

Production is a compact editorial feed rendered by `scripts/build.py` and styled
by `site/style.css`.

The current direction is intentionally restrained:

- White page and white cards.
- Broad `840px` maximum body width with a restrained `760px` reading column for the feed.
- A borderless masthead panel with a centered editorial headline at a `40px` to `52px` responsive scale and balanced wrapping.
- Supporting introduction at `18px`, giving the hero more generous rhythm while keeping the brief's Sarawak AI coverage concise.
- Sarawak red, yellow, and black accents.
- Refined top brand bar with a `16px` wordmark, compact `Home` and `About`
  links, a theme toggle, and a full-width Sarawak-color rule. The red segment
  anchors the wordmark; yellow and black divide the remaining space equally.
- Horizontal category filter using the seven canonical production labels.
- Ranked story cards with compact metadata.
- Source name highlighted in yellow.
- Structured, contained footer with a source summary, a subtle desktop divider,
  vertical Home/About links, and a full-width builder and independence
  attribution row.
- Optional dark mode using the same hierarchy: near-black canvas, lifted dark
  cards, softened borders, brighter text, and preserved Sarawak yellow/red
  accents.

The design is closer to an editorial memo or briefing page than to a dashboard.
It is appropriate for proving source-attributed curation before investing in a
larger product interface.

## Interaction Design

`site/app.js` progressively reveals the category filter and handles filtering
without dependencies.

Behavior:

- Filter starts hidden in HTML and appears when JavaScript loads.
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
- The hero panel and its headline, introduction, and update line reveal in a
  visible sequence, followed by story cards that fade and lift in with a short
  stagger capped after the first ten cards. The feed waits briefly for the hero
  to establish the page hierarchy; all reveal motion is disabled for reduced-
  motion users.
- The masthead theme toggle is a 36px circular control with a morphing moon/sun
  icon. It follows the system theme by default, persists an explicit choice in
  local storage, and updates its accessible label for the next mode.
- Story ranks are renumbered after filtering.
- A visually hidden live region reports the current result count.
- Reloading the page resets the viewport to the top, while ordinary history
  navigation can preserve the reader's position.
- A compact fixed `Back to top` control appears after 600 px of scrolling and
  uses the active category filter palette permanently: black surface, white label,
  and yellow arrow. It respects the reader's reduced-motion preference.
  On screens up to 560 px wide it becomes a 40 px arrow-only control, using the
  active filter's black surface and yellow accent while retaining its accessible
  `Back to top` name.

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

Cards use 8 px radius or less in production. The current layout avoids heavy
decoration and keeps density high enough for repeated scanning.

## Content Hierarchy

Homepage hierarchy:

1. Brand and `Home`/`About` navigation.
2. Search-focused `Sarawak AI news` headline.
3. Short introduction covering Sarawak AI policy, projects, research, and adoption.
4. Last updated weekday and date.
5. Category filters.
6. Ranked story cards.
7. Independent-publication footer note.

The masthead contains the brand lockup, compact navigation, theme toggle, and
color rule. The About page moves fuller publication context off the already
wordy homepage while keeping the first screen focused on the live brief.

The About page uses the same restrained system: a clear opening statement and
short sections for purpose, coverage, and workflow. It keeps the explanation
closer to the editorial feed instead of adding dashboard-like metrics or pills.

Each story card currently shows date, source, category, title, and summary. Its
category label exactly matches the corresponding browse filter. The card
does not expose tags, confidence, caveat, or why-it-matters copy in the HTML,
although those fields are preserved in generated JSON for editorial review.

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

- The production UI hides some useful editorial metadata.
- Variant D is more polished but may imply product features that do not exist
  yet, such as newsletter signup, custom reports, topic counts, and daily
  updates.
- The current mobile headline uses viewport-based sizing; future UI work should
  verify text fit carefully across common mobile widths.
- The brief currently has no archive, item detail view, or persistent category
  URL state.
