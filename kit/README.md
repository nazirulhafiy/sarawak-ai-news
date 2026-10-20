# Sarawak News shared kit

This directory is the source for the header, nav marks, footer, back-to-top control, and analytics loader used by sarawak.news sites. The hub repo holds the source. Sister sites keep a copy pinned to a hub commit. There is no separate kit repository.

Sisters vendor the files and record the hub commit in `kit/PIN`. `python3 kit/sync.py --check` fails if that copy drifts from the pin. A git submodule of the whole hub is the wrong fit. It checks out the entire hub, needs a recursive submodule checkout in CI, and makes agents edit the wrong tree.

## Layout

| Path | Role |
| --- | --- |
| `python/shell.py` | `render_header`, `render_footer`, `render_back_to_top` |
| `python/analytics_registry.py` | Load and validate `data/analytics.json` |
| `python/analytics_loader.py` | `render_analytics_loader(registry)` |
| `assets/icons/nav-mark-transparent.svg` | Light nav mark |
| `assets/icons/nav-mark-transparent-dark.svg` | Dark nav mark |
| `css/back-to-top.css` | Back-to-top rules |
| `js/back-to-top.js` | Back-to-top behaviour |
| `MANIFEST.json` | Version, tracked paths, invariants |
| `sync.py` | Check or refresh |
| `PIN` | Sister only. Hub commit SHA. The hub has no PIN file. |

`render_footer` always emits Contact as `mailto:contact@sarawak.news`. Callers pass the other Explore links. The analytics loader reads `internal_cookie` from the site's own `data/analytics.json`. On the hub that value is `sn_internal`.

`css/back-to-top.css` is the control's own rules. The hub also lists `.back-to-top` inside the shared `prefers-reduced-motion` block in `site/style.css`. That shared block stays in the page stylesheet, because it resets other elements too.

## Hub

The hub has no `kit/PIN`.

Check the kit, the invariants, and the consumer copies.

```bash
python3 kit/sync.py --check
```

Refresh `site/icons/nav-mark-*.svg` and the back-to-top regions in `site/style.css` and `site/app.js` from the kit. `python3 kit/sync.py` with no flags does the same refresh.

```bash
python3 kit/sync.py --sync
```

Hub check does four things.

1. Every path in `MANIFEST.json` `files` exists.
2. Invariants hold. Those include Contact `mailto:contact@sarawak.news`, back-to-top `data-back-to-top` plus the label and arrow markup, the analytics loader attribute `data-sn-analytics-loader`, and the hub cookie name `sn_internal` in `data/analytics.json`.
3. Consumer copies match. `site/icons/nav-mark-*.svg` is byte-identical to `kit/assets/icons/`. The back-to-top block in `site/style.css` and `site/app.js` matches the kit file between `/* sn-kit:back-to-top:begin */` and `/* sn-kit:back-to-top:end */`. If the CSS markers are missing, the kit CSS must still be a contiguous substring of `site/style.css`.
4. `scripts/build.py` imports the shell and the analytics loader from `kit.python` and does not keep its own back-to-top markup or loader script.

## Sister copy

Run this from the sister repo. `$SN_HUB_PATH` is a clone of sarawak-news-hub. `$PIN` is the hub commit to vendor.

```bash
mkdir -p kit
git -C "$SN_HUB_PATH" archive "$PIN" kit | tar -x
printf '%s\n' "$PIN" > kit/PIN
python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"
```

`SN_HUB_PATH` may replace `--hub-path`.

To move the sister onto a newer hub commit, write the new SHA into `kit/PIN`, refresh, then check.

```bash
printf '%s\n' "<new-hub-sha>" > kit/PIN
python3 kit/sync.py --sync --hub-path "$SN_HUB_PATH"
python3 kit/sync.py --check --hub-path "$SN_HUB_PATH"
```

Sister check hashes each vendored file against `git show <pin>:kit/<path>`. A local edit fails the check. Do not hand-edit vendored kit files. Bump `kit/PIN` and sync instead.

Sister CI should run `python3 kit/sync.py --check` with the hub clone available at the pinned commit.
