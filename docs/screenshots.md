# Screenshot tool

Agents and contributors capture UI evidence with the shared Node helper at
`tools/shots.mjs`. It uses **playwright-core** and the system Chrome/Chromium
binary (no bundled browser download).

## Setup

```bash
cd tools && npm install
```

Set `CHROME_PATH` if Chrome is not on the default path.

## Usage

Single page:

```bash
node tools/shots.mjs --url https://ai.sarawak.news --out /tmp/shots \
  --name sarawak --crop '[data-category-filter]' --pad 24 \
  --themes light,dark --devices phone
```

Local `dist/` build (serves via `file://` when the path exists):

```bash
python3 scripts/build.py
node tools/shots.mjs --url dist --out /tmp/shots --devices desktop
```

Compare two URLs (writes `-before`, `-after`, and `-compare` PNGs; logs pixel
diff per theme/device):

```bash
node tools/shots.mjs --compare https://before.example https://after.example \
  --out /tmp/shots --themes light,dark --devices phone,desktop
```

### Options

| Flag | Purpose |
|------|---------|
| `--url` | HTTPS URL or local path to `dist/` / `index.html` |
| `--out` | Output directory (created if missing) |
| `--name` | Filename prefix (default: hostname with dots → dashes) |
| `--crop` | CSS selector; clip is full viewport width, padded, height capped at ~1.3× width |
| `--clip` | Explicit `x,y,w,h` clip in CSS pixels |
| `--pad` | Padding around `--crop` selector (default `24`) |
| `--themes` | Comma-separated `light` / `dark` (default both) |
| `--devices` | Comma-separated `phone` / `desktop` (default both) |
| `--desktop-scale` | `deviceScaleFactor` for desktop (default `1`; use `2` for retina) |

### Viewports

- **phone**: 390×844 CSS px, `deviceScaleFactor` 3 (~1170 px wide PNG, no downscaling).
- **desktop**: 1280×900 CSS px, `deviceScaleFactor` 1 (or `--desktop-scale`).

### Theme and stability

Before the first paint, the script sets `localStorage['sarawak-theme']` and
`html[data-theme]` to match production (`site/app.js`), injects CSS to disable
transitions/animations, waits for `document.fonts.ready`, and logs the computed
`body` background colour.

### Output names

`<name>-<device>-<theme>.png`, with `-before`, `-after`, or `-compare` when
using compare mode.
