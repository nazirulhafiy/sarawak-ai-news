# Design Notes

## Current Production Design

Production is a compact editorial feed rendered by `scripts/build.py` and styled
by `site/style.css`.

The current direction is intentionally restrained:

- White page and white cards.
- Narrow `680px` maximum body width.
- Centered editorial headline at `42px` on desktop with balanced wrapping.
- Sarawak red, yellow, and black accents.
- Thin top brand bar with a Sarawak-color rule.
- Horizontal category filter using the seven canonical production labels.
- Ranked story cards with compact metadata.
- Source name highlighted in yellow.
- Minimal footer with independence note.

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
- Hidden story cards use the `hidden` attribute.
- Story ranks are renumbered after filtering.
- A visually hidden live region reports the current result count.

The page still works as a readable feed without JavaScript.

## Visual System

Production tokens in `site/style.css`:

- Canvas/page/card: white.
- Ink: near-black.
- Muted text: gray.
- Accent red: `#d22630`.
- Accent yellow: `#f7c948`.
- Accent black: `#111111`.

Cards use 8 px radius or less in production. The current layout avoids heavy
decoration and keeps density high enough for repeated scanning.

## Content Hierarchy

Current hierarchy:

1. Brand.
2. Last updated weekday, date, and time.
3. Large thesis headline.
4. Short deck.
5. Category filters.
6. Ranked story cards.
7. Independent-publication footer note.

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
