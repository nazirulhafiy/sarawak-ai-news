# Screenshot tool

Agents and contributors capture UI evidence with the shared Node helper at
`tools/shots.mjs`. It uses **playwright-core** and the system Chrome/Chromium
binary (no bundled browser download).

Site-specific defaults (default URL, theme keys, default crop selector, output
directory, and related flags) live in `tools/shots.config.json` beside the
script. Override any default on the CLI.

## Setup

```bash
cd tools && npm install
```

Set `CHROME_PATH` if Chrome is not on the default path.

## Config (`tools/shots.config.json`)

| Field | Purpose |
|-------|---------|
| `defaultUrl` | Target when `--url` is omitted (e.g. `https://ai.sarawak.news`) |
| `outDir` | Default `--out` directory (`shots/`, gitignored) |
| `name` | Default filename prefix |
| `defaults.devices` / `defaults.themes` | Default `--devices` and `--themes` |
| `defaults.crop` / `defaults.pad` | Default `--crop` and `--pad` (use `--no-crop` to skip) |
| `crop.minAspect` / `crop.maxAspect` | Crop height bounds as multiples of width |
| `theme.*` | How to set light/dark before paint (`localStorage`, `data-theme`, etc.) |
| `readySelector` / `settleMs` | Optional wait before capture |

Point at another file with `--config <path>`.

## Usage

With repo defaults (live site, phone, light+dark, category-filter crop):

```bash
node tools/shots.mjs --out /tmp/shots
```

Explicit URL and options:

```bash
node tools/shots.mjs --url https://ai.sarawak.news --out /tmp/shots \
  --name sarawak --crop '[data-category-filter]' --pad 24 \
  --themes light,dark --devices phone
```

Local `dist/` build (served on `127.0.0.1` when the path is a directory):

```bash
python3 scripts/build.py
node tools/shots.mjs --url dist --out /tmp/shots --devices desktop --no-crop
```

Full-page phone capture (no crop):

```bash
node tools/shots.mjs --full-page --devices phone --no-crop
```

Explicit clip region (`x,y,w,h` in CSS px; overrides `--crop`):

```bash
node tools/shots.mjs --clip 0,120,390,400 --devices phone
```

Compare two URLs (writes `-before`, `-after`, and side-by-side `-compare` PNGs):

```bash
node tools/shots.mjs --compare https://before.example https://after.example \
  --out /tmp/shots --themes light,dark --devices phone,desktop
```

### Options

| Flag | Purpose |
|------|---------|
| `--config` | Path to JSON config (default: `tools/shots.config.json`) |
| `--url` | HTTPS URL, HTML file, or build directory (default: `defaultUrl` in config) |
| `--out` | Output directory (default: `outDir` in config) |
| `--name` | Filename prefix (default: `name` in config or derived from URL) |
| `--crop` | CSS selector; clip is full viewport width, padded, height capped by `maxAspect` |
| `--no-crop` | Do not apply the configured or default crop |
| `--clip` | Explicit `x,y,w,h` clip in CSS pixels (overrides `--crop`) |
| `--pad` | Padding around `--crop` selector (default from config, usually `24`) |
| `--themes` | Comma-separated `light` / `dark` |
| `--devices` | Comma-separated `phone` / `desktop` |
| `--desktop-scale` | `deviceScaleFactor` for desktop (default `1`; use `2` for retina) |
| `--full-page` | Without crop/clip, capture the full scrollable page |
| `--compare` | Two URLs; capture before/after/compare sets per theme and device |

### Viewports

- **phone**: 390×844 CSS px, `deviceScaleFactor` 3 (~1170 px wide PNG, no downscaling).
- **desktop**: 1280×900 CSS px, `deviceScaleFactor` 1 (or `--desktop-scale`).

### Theme and stability

Before the first paint, the script applies `tools/shots.config.json` theme settings
(for Sarawak: `localStorage['sarawak-theme']` and `html[data-theme]`), injects
CSS to disable transitions/animations, waits for `document.fonts.ready`, and
logs the computed `body` background colour.

### Output names

`<name>-<device>-<theme>.png`, with `-before`, `-after`, or `-compare` when
using compare mode.
