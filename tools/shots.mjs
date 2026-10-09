#!/usr/bin/env node
/**
 * Sarawak AI News screenshot helper (Playwright + system Chrome).
 *
 * Install (once): cd tools && npm install
 *
 * Single URL:
 *   node tools/shots.mjs --url <https-url-or-local-dist-path> --out <dir> \\
 *     [--name <prefix>] [--crop <css-selector> | --clip x,y,w,h] [--pad 24] \\
 *     [--themes light,dark] [--devices phone,desktop] [--desktop-scale 2]
 *
 * Compare two URLs (same shots, side-by-side, pixel diff logged):
 *   node tools/shots.mjs --compare <beforeUrl> <afterUrl> --out <dir> [same options]
 *
 * Phone: 390×844 viewport @ deviceScaleFactor 3 (PNG at ~1170px wide, no downscale).
 * Desktop: 1280×900 @ DPR 1 (optional --desktop-scale 2).
 *
 * Theme is applied before first paint via localStorage key `sarawak-theme` and
 * html[data-theme], matching site/app.js.
 */

import { chromium } from "playwright-core";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { PNG } from "pngjs";
import pixelmatch from "pixelmatch";

const THEME_STORAGE_KEY = "sarawak-theme";

const DEVICES = {
  phone: { width: 390, height: 844, deviceScaleFactor: 3 },
  desktop: { width: 1280, height: 900, deviceScaleFactor: 1 },
};

function parseArgs(argv) {
  const args = { pad: 24, themes: ["light", "dark"], devices: ["phone", "desktop"], desktopScale: 1 };
  const rest = [...argv];
  while (rest.length) {
    const flag = rest.shift();
    switch (flag) {
      case "--url":
        args.url = rest.shift();
        break;
      case "--out":
        args.out = rest.shift();
        break;
      case "--name":
        args.name = rest.shift();
        break;
      case "--crop":
        args.crop = rest.shift();
        break;
      case "--clip":
        args.clip = rest.shift();
        break;
      case "--pad":
        args.pad = Number(rest.shift());
        break;
      case "--themes":
        args.themes = rest.shift().split(",").map((s) => s.trim()).filter(Boolean);
        break;
      case "--devices":
        args.devices = rest.shift().split(",").map((s) => s.trim()).filter(Boolean);
        break;
      case "--desktop-scale":
        args.desktopScale = Number(rest.shift());
        break;
      case "--compare":
        args.compare = [rest.shift(), rest.shift()];
        break;
      case "-h":
      case "--help":
        args.help = true;
        break;
      default:
        throw new Error(`Unknown argument: ${flag}`);
    }
  }
  return args;
}

function usage() {
  console.log(`Usage:
  node tools/shots.mjs --url <url-or-path> --out <dir> [options]
  node tools/shots.mjs --compare <before> <after> --out <dir> [options]

Options:
  --name <prefix>       Output filename prefix (default: derived from URL)
  --crop <selector>     Crop to element (+ pad, full viewport width, height cap)
  --clip x,y,w,h        Explicit clip rectangle in CSS pixels
  --pad <n>             Padding around crop selector (default: 24)
  --themes light,dark   Comma-separated themes (default: light,dark)
  --devices phone,desktop
  --desktop-scale <n>   deviceScaleFactor for desktop (default: 1)
`);
}

function resolveTargetUrl(input) {
  const abs = resolve(input);
  if (existsSync(abs)) {
    const stat = existsSync(join(abs, "index.html"));
    const file = stat ? join(abs, "index.html") : abs;
    return `file://${file}`;
  }
  if (/^https?:\/\//i.test(input)) return input;
  throw new Error(`URL or path not found: ${input}`);
}

function defaultNameFromUrl(url) {
  try {
    const u = new URL(url);
    return u.hostname.replace(/\./g, "-") || "local";
  } catch {
    return "local";
  }
}

function themeInitScript(theme) {
  const isDark = theme === "dark";
  return ({ key, dark }) => {
    try {
      localStorage.setItem(key, dark ? "dark" : "light");
    } catch (_) {}
    if (dark) document.documentElement.setAttribute("data-theme", "dark");
    else document.documentElement.removeAttribute("data-theme");
    const style = document.createElement("style");
    style.textContent = `
      *, *::before, *::after {
        transition: none !important;
        animation: none !important;
        caret-color: auto !important;
      }
    `;
    document.documentElement.appendChild(style);
  };
}

async function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  for (const path of candidates) {
    if (existsSync(path)) return path;
  }
  throw new Error("System Chrome/Chromium not found. Set CHROME_PATH.");
}

async function computeClip(page, viewport, options) {
  if (options.clip) {
    const parts = options.clip.split(",").map((n) => Number(n.trim()));
    if (parts.length !== 4 || parts.some((n) => Number.isNaN(n))) {
      throw new Error("--clip requires x,y,w,h as numbers");
    }
    return { x: parts[0], y: parts[1], width: parts[2], height: parts[3] };
  }
  if (!options.crop) return null;

  const pad = options.pad ?? 24;
  const box = await page.locator(options.crop).first().boundingBox();
  if (!box) throw new Error(`Crop selector not found: ${options.crop}`);

  const vw = viewport.width;
  const maxHeight = Math.round(vw * 1.3);
  let y = Math.max(0, box.y - pad);
  let height = box.height + pad * 2;
  if (height > maxHeight) height = maxHeight;

  return { x: 0, y, width: vw, height };
}

async function captureOne(browser, url, theme, deviceKey, device, options, suffix) {
  const context = await browser.newContext({
    viewport: { width: device.width, height: device.height },
    deviceScaleFactor: device.deviceScaleFactor,
    colorScheme: theme === "dark" ? "dark" : "light",
  });
  await context.addInitScript(themeInitScript(theme), {
    key: THEME_STORAGE_KEY,
    dark: theme === "dark",
  });
  const page = await context.newPage();

  try {
    await page.goto(url, { waitUntil: "load", timeout: 120_000 });
    await page.evaluate(() => document.fonts?.ready);
    if (options.crop) {
      await page.locator(options.crop).first().waitFor({ state: "visible", timeout: 30_000 });
    }

    const bodyBg = await page.evaluate(
      () => getComputedStyle(document.body).backgroundColor,
    );
    console.log(
      `[${deviceKey}/${theme}${suffix ? `/${suffix}` : ""}] body background: ${bodyBg}`,
    );

    const clip = await computeClip(page, device, options);
    const shotOptions = {
      type: "png",
      omitBackground: false,
      scale: "device",
    };
    if (clip) shotOptions.clip = clip;

    const buffer = await page.screenshot(shotOptions);
    return { buffer, clip, bodyBg };
  } finally {
    await context.close();
  }
}

async function withBrowser(fn) {
  const executablePath = await findChrome();
  const browser = await chromium.launch({
    executablePath,
    headless: true,
    args: ["--font-render-hinting=medium"],
  });
  try {
    return await fn(browser);
  } finally {
    await browser.close();
  }
}

function pngDimensions(buffer) {
  const png = PNG.sync.read(buffer);
  return { width: png.width, height: png.height, data: png.data };
}

function writePng(path, buffer) {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, buffer);
  return path;
}

function sideBySide(leftBuf, rightBuf) {
  const left = PNG.sync.read(leftBuf);
  const right = PNG.sync.read(rightBuf);
  const height = Math.max(left.height, right.height);
  const out = new PNG({ width: left.width + right.width, height });
  PNG.bitblt(left, out, 0, 0, left.width, left.height, 0, 0);
  PNG.bitblt(right, out, 0, 0, right.width, right.height, left.width, 0);
  return PNG.sync.write(out);
}

function countPixelDiff(aBuf, bBuf) {
  const a = PNG.sync.read(aBuf);
  const b = PNG.sync.read(bBuf);
  const w = Math.min(a.width, b.width);
  const h = Math.min(a.height, b.height);
  const aCrop = new PNG({ width: w, height: h });
  const bCrop = new PNG({ width: w, height: h });
  PNG.bitblt(a, aCrop, 0, 0, w, h, 0, 0);
  PNG.bitblt(b, bCrop, 0, 0, w, h, 0, 0);
  const diff = new PNG({ width: w, height: h });
  const numDiff = pixelmatch(aCrop.data, bCrop.data, diff.data, w, h, {
    threshold: 0.1,
    includeAA: true,
  });
  const sizeMismatch =
    a.width !== b.width || a.height !== b.height
      ? ` (compared ${w}×${h} overlap; sizes ${a.width}×${a.height} vs ${b.width}×${b.height})`
      : "";
  return { numDiff, sizeMismatch, w, h };
}

async function runCaptures(browser, targets, options) {
  const results = [];

  for (const target of targets) {
    const { url, label } = target;
    const resolved = resolveTargetUrl(url);
    for (const deviceKey of options.devices) {
      const device = { ...DEVICES[deviceKey] };
      if (!device) throw new Error(`Unknown device: ${deviceKey}`);
      if (deviceKey === "desktop") {
        device.deviceScaleFactor = options.desktopScale || 1;
      }
      for (const theme of options.themes) {
        const name = options.name || defaultNameFromUrl(resolved);
        const suffix = label ? `-${label}` : "";
        const fileBase = `${name}-${deviceKey}-${theme}${suffix}`;
        const { buffer } = await captureOne(
          browser,
          resolved,
          theme,
          deviceKey,
          device,
          options,
          label,
        );
        const outPath = join(options.out, `${fileBase}.png`);
        writePng(outPath, buffer);
        const { width, height } = pngDimensions(buffer);
        console.log(`Wrote ${outPath} (${width}×${height})`);
        results.push({ fileBase, outPath, buffer, width, height, theme, deviceKey, label });
      }
    }
  }
  return results;
}

async function runCompare(browser, beforeUrl, afterUrl, options) {
  const before = await runCaptures(browser, [{ url: beforeUrl, label: "before" }], options);
  const after = await runCaptures(browser, [{ url: afterUrl, label: "after" }], options);

  for (const b of before) {
    const a = after.find(
      (x) => x.deviceKey === b.deviceKey && x.theme === b.theme,
    );
    if (!a) continue;
    const compareBuf = sideBySide(b.buffer, a.buffer);
    const name = options.name || defaultNameFromUrl(resolveTargetUrl(beforeUrl));
    const comparePath = join(
      options.out,
      `${name}-${b.deviceKey}-${b.theme}-compare.png`,
    );
    writePng(comparePath, compareBuf);
    const { width, height } = pngDimensions(compareBuf);
    console.log(`Wrote ${comparePath} (${width}×${height})`);

    const { numDiff, sizeMismatch, w, h } = countPixelDiff(b.buffer, a.buffer);
    console.log(
      `Pixel diff ${name}-${b.deviceKey}-${b.theme}: ${numDiff} differing pixels in ${w}×${h}${sizeMismatch}`,
    );
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    usage();
    return;
  }
  if (!args.out) throw new Error("--out <dir> is required");
  mkdirSync(args.out, { recursive: true });

  if (args.compare) {
    const [before, after] = args.compare;
    if (!before || !after) throw new Error("--compare requires two URLs");
    await withBrowser((browser) => runCompare(browser, before, after, args));
    return;
  }

  if (!args.url) throw new Error("--url is required (or use --compare)");
  await withBrowser((browser) =>
    runCaptures(browser, [{ url: args.url, label: "" }], args),
  );
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
