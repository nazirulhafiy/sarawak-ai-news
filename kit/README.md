# Sarawak News shared kit

Single source for fleet chrome shared by [sarawak.news](https://sarawak.news) sites:

- Header bar (brand + origami hornbill nav marks + theme toggle shell)
- Footer Explore nav with **Contact** (`mailto:contact@sarawak.news`)
- Back-to-top control (markup, CSS, JS)
- Analytics loader (registry-driven; each site keeps its own `data/analytics.json`)

This directory in **sarawak-news-hub** is the source of truth. Sister sites vendor a copy pinned to a hub commit. Do **not** create a separate kit repository.

## Layout

| Path | Role |
| --- | --- |
| `shell.py` | `render_header`, `render_footer`, `render_back_to_top` |
| `analytics_registry.py` | Load/validate `data/analytics.json` |
| `analytics_loader.py` | `render_analytics_loader(registry)` |
| `assets/icons/nav-mark-*.svg` | Origami hornbill nav marks |
| `css/back-to-top.css` | Back-to-top rules |
| `js/back-to-top.js` | Back-to-top behaviour |
| `MANIFEST.json` | Tracked files + invariants |
| `sync.py` | `--check` / `--sync` |
| `PIN` | Sister-only: hub commit SHA (absent on hub) |

## Hub commands

```bash
python3 kit/sync.py --check
python3 kit/sync.py --sync    # refresh site/ icon copies + BTT marker regions from kit/
```

Hub mode (no `PIN`) checks:

1. Every `MANIFEST.json` file exists
2. Invariants hold (Contact mailto, `data-back-to-top`, analytics loader attr, …)
3. Consumer mirrors match (`site/icons/nav-mark-*.svg`, BTT marker regions in `site/style.css` / `site/app.js`)
4. `scripts/build.py` imports shell + analytics from `kit` (no hand-typed duplicates)

## Sister vendor + pin (for follow-up PRs)

From a sister repo, with a hub clone available at `$SN_HUB_PATH` and the hub PR tip SHA as `$PIN`:

```bash
mkdir -p kit
git -C "$SN_HUB_PATH" archive "$PIN" kit | tar -x --strip-components=0
# archive extracts ./kit/...; ensure files land in this repo's kit/
echo "$PIN" > kit/PIN
python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"
```

Or copy the `kit/` tree from the hub working tree at that commit, write `kit/PIN`, then `--check`.

Bump the pin when adopting a newer hub kit:

```bash
echo "<new-hub-sha>" > kit/PIN
python3 kit/sync.py --sync --hub-path "$SN_HUB_PATH"
python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"
```

CI on every sister should run `python3 kit/sync.py --check` (with hub available at the pin, e.g. a shallow clone).

## Delivery choice

Sisters **vendor** kit files at a pinned hub commit. A git submodule of the whole hub was rejected: it checks out the entire hub tree, needs `submodule update --init --recursive` in CI, and confuses agents about which tree to edit. No separate kit repo.
