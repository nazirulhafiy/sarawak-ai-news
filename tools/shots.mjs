#!/usr/bin/env node
/**
 * shots.mjs: consistent UI screenshots (phone 3x, desktop, light/dark, before/after).
 *
 * This file is site-agnostic and kept byte-identical across repos. Everything
 * site-specific (default URL, theme mechanism, default crop selector, output dir,
 * extra storage flags) lives in tools/shots.config.json next to this file.
 *
 * Usage:
 *   node tools/shots.mjs [--url <https-url|file|dir>] [options]
 *   node tools/shots.mjs --compare <before> <after> [options]
 *
 * Options:
 *   --url <target>          https URL, an HTML file, or a build dir (served on 127.0.0.1)
 *                           (default: config.defaultUrl)
 *   --out <dir>             Output directory (default: config.outDir, else "shots")
 *   --name <slug>           Filename prefix (default: config.name, else derived from URL)
 *   --crop <selector>       Crop to the first matching element (default: config.defaults.crop)
 *   --no-crop               Ignore the configured default crop
 *   --clip <x,y,w,h>        Explicit region in CSS px (page coordinates); overrides --crop
 *   --pad <n>               Padding around --crop in CSS px (default 24)
 *   --themes light,dark     Themes to capture (default: config.defaults.themes)
 *   --devices phone,desktop Devices to capture (default: config.defaults.devices)
 *   --desktop-scale <n>     deviceScaleFactor for desktop (default 1)
 *   --full-page             Without crop/clip, capture the full page instead of the first viewport
 *   --config <path>         Config file (default: tools/shots.config.json beside this script)
 *   -h, --help
 *
 * Devices: phone = 390x844 CSS px at deviceScaleFactor 3 (1170 px wide PNG, never
 * downscaled); desktop = 1280x900 at --desktop-scale.
 * Crops span the full viewport width and are kept roughly square: height is clamped
 * to [minAspect, maxAspect] x width (defaults 0.75 and 1.3). Short elements are
 * centred in the frame; tall ones are top-aligned and cut at maxAspect.
 * Output: <out>/<name>-<device>-<theme>[-before|-after|-compare].png
 *
 * Requires playwright-core and a system Chrome/Chromium (CHROME_PATH overrides).
 */

import { chromium } from "playwright-core";
import { createReadStream, existsSync, readFileSync, statSync } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_CONFIG_PATH = path.join(SCRIPT_DIR, "shots.config.json");

const DEVICES = {
  phone: { width: 390, height: 844, deviceScaleFactor: 3 },
  desktop: { width: 1280, height: 900, deviceScaleFactor: 1 },
};

const DEFAULT_CONFIG = {
  name: null,
  defaultUrl: null,
  outDir: "shots",
  defaults: { devices: ["phone"], themes: ["light", "dark"], crop: null, pad: 24 },
  crop: { minAspect: 0.75, maxAspect: 1.3 },
  theme: {
    supported: ["light", "dark"],
    localStorageKey: null,
    attribute: "data-theme",
    attributeValues: { light: "light", dark: "dark" },
    setColorScheme: false,
    themeColor: null,
  },
  localStorage: {},
  sessionStorage: {},
  readySelector: null,
  settleMs: 250,
};

const DISABLE_MOTION_CSS = `
  *, *::before, *::after {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    scroll-behavior: auto !important;
    caret-color: transparent !important;
  }
`;

const HELP = `Usage:
  node tools/shots.mjs [--url <url|file|dir>] [options]
  node tools/shots.mjs --compare <before> <after> [options]

Options:
  --url <target>          https URL, HTML file, or build dir (default: config.defaultUrl)
  --out <dir>             Output dir (default: config.outDir)
  --name <slug>           Filename prefix (default: config.name or derived from URL)
  --crop <selector>       Crop to element (default: config.defaults.crop)
  --no-crop               Ignore the configured default crop
  --clip x,y,w,h          Explicit region in CSS px (overrides --crop)
  --pad <n>               Padding around --crop (default 24)
  --themes light,dark     Themes (default: config.defaults.themes)
  --devices phone,desktop Devices (default: config.defaults.devices)
  --desktop-scale <n>     deviceScaleFactor for desktop (default 1)
  --full-page             Uncropped shots capture the full page
  --config <path>         Config file (default: tools/shots.config.json)
`;

function isPlainObject(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

function deepMerge(base, over) {
  const out = { ...base };
  for (const [k, v] of Object.entries(over || {})) {
    out[k] = isPlainObject(v) && isPlainObject(base[k]) ? deepMerge(base[k], v) : v;
  }
  return out;
}

function splitList(value, flag) {
  if (value === undefined) throw new Error(`${flag} needs a value`);
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

function takeValue(rest, flag) {
  const value = rest.shift();
  if (value === undefined || value.startsWith("--")) throw new Error(`${flag} needs a value`);
  return value;
}

function parseArgs(argv) {
  const args = {};
  const rest = [...argv];
  while (rest.length) {
    const flag = rest.shift();
    switch (flag) {
      case "--url": args.url = takeValue(rest, flag); break;
      case "--out": args.out = takeValue(rest, flag); break;
      case "--name": args.name = takeValue(rest, flag); break;
      case "--crop": args.crop = takeValue(rest, flag); break;
      case "--no-crop": args.noCrop = true; break;
      case "--clip": args.clip = parseClip(takeValue(rest, flag)); break;
      case "--pad": args.pad = Number(takeValue(rest, flag)); break;
      case "--themes": args.themes = splitList(rest.shift(), flag); break;
      case "--devices": args.devices = splitList(rest.shift(), flag); break;
      case "--desktop-scale": args.desktopScale = Number(takeValue(rest, flag)); break;
      case "--full-page": args.fullPage = true; break;
      case "--config": args.config = takeValue(rest, flag); break;
      case "--compare": args.compare = [takeValue(rest, flag), takeValue(rest, flag)]; break;
      case "-h":
      case "--help": args.help = true; break;
      default: throw new Error(`Unknown argument: ${flag}`);
    }
  }
  return args;
}

function parseClip(value) {
  const parts = value.split(",").map((n) => Number(n.trim()));
  if (parts.length !== 4 || parts.some((n) => !Number.isFinite(n))) {
    throw new Error("--clip expects x,y,width,height in CSS px");
  }
  const [x, y, width, height] = parts;
  return { x, y, width, height };
}

function loadConfig(configPath) {
  const file = configPath ? path.resolve(configPath) : DEFAULT_CONFIG_PATH;
  if (!existsSync(file)) {
    if (configPath) throw new Error(`Config not found: ${file}`);
    console.warn(`[shots] no config at ${file}; using generic defaults`);
    return DEFAULT_CONFIG;
  }
  const raw = JSON.parse(readFileSync(file, "utf8"));
  return deepMerge(DEFAULT_CONFIG, raw);
}

function resolveOptions(args, config) {
  if (args.url && args.compare) throw new Error("Use either --url or --compare, not both");
  const opts = {
    url: args.url ?? (args.compare ? null : config.defaultUrl),
    compare: args.compare ?? null,
    out: path.resolve(args.out ?? config.outDir ?? "shots"),
    name: args.name ?? config.name ?? null,
    clip: args.clip ?? null,
    crop: args.noCrop ? null : (args.crop ?? config.defaults.crop ?? null),
    pad: args.pad ?? config.defaults.pad ?? 24,
    themes: args.themes ?? config.defaults.themes,
    devices: args.devices ?? config.defaults.devices,
    desktopScale: args.desktopScale ?? 1,
    fullPage: Boolean(args.fullPage),
  };
  if (opts.clip) opts.crop = null;
  if (!opts.url && !opts.compare) throw new Error("--url is required (no config.defaultUrl set)");
  if (!Number.isFinite(opts.pad) || opts.pad < 0) throw new Error("--pad must be a number >= 0");
  if (!Number.isFinite(opts.desktopScale) || opts.desktopScale <= 0) {
    throw new Error("--desktop-scale must be a positive number");
  }
  for (const t of opts.themes) {
    if (!config.theme.supported.includes(t)) {
      throw new Error(`Unsupported theme "${t}" (config supports: ${config.theme.supported.join(", ")})`);
    }
  }
  for (const d of opts.devices) {
    if (!DEVICES[d]) throw new Error(`Unknown device "${d}" (use: ${Object.keys(DEVICES).join(", ")})`);
  }
  return opts;
}

function slugify(s) {
  return (
    String(s)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 80) || "shot"
  );
}

function deriveName(input) {
  if (/^https?:\/\//i.test(input)) {
    try {
      const u = new URL(input);
      const seg = u.pathname.replace(/\/+/g, "-").replace(/^-|-$/g, "");
      return slugify(seg ? `${u.hostname}-${seg}` : u.hostname);
    } catch {
      return "shot";
    }
  }
  return slugify(path.basename(path.resolve(input), path.extname(input)) || "local");
}

const servers = [];

async function resolveTarget(input) {
  if (/^https?:\/\//i.test(input)) return input;
  const abs = path.resolve(input);
  if (!existsSync(abs)) throw new Error(`URL or path not found: ${input}`);
  if (statSync(abs).isFile()) return pathToFileURL(abs).href;

  const root = abs;
  const server = http.createServer((req, res) => {
    const urlPath = decodeURIComponent(new URL(req.url, "http://local").pathname);
    let filePath = path.join(root, urlPath);
    if (!filePath.startsWith(root)) filePath = path.join(root, "index.html");
    if (existsSync(filePath) && statSync(filePath).isDirectory()) {
      filePath = path.join(filePath, "index.html");
    }
    if (!existsSync(filePath)) filePath = path.join(root, "index.html");
    const stream = createReadStream(filePath);
    stream.on("error", () => {
      res.statusCode = 404;
      res.end("Not found");
    });
    stream.pipe(res);
  });
  await new Promise((ok, fail) => {
    server.once("error", fail);
    server.listen(0, "127.0.0.1", ok);
  });
  servers.push(server);
  return `http://127.0.0.1:${server.address().port}/`;
}

function resolveChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    "/usr/local/bin/google-chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ].filter(Boolean);
  return candidates.find((p) => existsSync(p));
}

async function launchBrowser() {
  const executablePath = resolveChrome();
  const launchArgs = ["--font-render-hinting=medium", "--disable-dev-shm-usage", "--hide-scrollbars"];
  if (executablePath) return chromium.launch({ headless: true, executablePath, args: launchArgs });
  try {
    return await chromium.launch({ headless: true, channel: "chrome", args: launchArgs });
  } catch (err) {
    throw new Error(`System Chrome/Chromium not found; set CHROME_PATH (${err.message})`);
  }
}

// Runs in the page before any site script.
function pageInitScript({ theme, themeConfig, localStorageItems, sessionStorageItems, css }) {
  try {
    if (themeConfig.localStorageKey) localStorage.setItem(themeConfig.localStorageKey, theme);
    for (const [k, v] of Object.entries(localStorageItems)) localStorage.setItem(k, String(v));
    for (const [k, v] of Object.entries(sessionStorageItems)) sessionStorage.setItem(k, String(v));
  } catch {
    /* storage unavailable (e.g. file://) */
  }
  const root = document.documentElement;
  const apply = () => {
    if (themeConfig.attribute) {
      const value = (themeConfig.attributeValues || {})[theme];
      if (value === null || value === undefined) root.removeAttribute(themeConfig.attribute);
      else root.setAttribute(themeConfig.attribute, value);
    }
    if (themeConfig.setColorScheme) root.style.colorScheme = theme;
    if (themeConfig.themeColor && themeConfig.themeColor[theme]) {
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", themeConfig.themeColor[theme]);
    }
  };
  apply();
  document.addEventListener("DOMContentLoaded", apply, { once: true });
  const style = document.createElement("style");
  style.setAttribute("data-shots-tool", "");
  style.textContent = css;
  root.appendChild(style);
}

async function waitForRender(page, config, crop) {
  try {
    await page.waitForLoadState("networkidle", { timeout: 10_000 });
  } catch {
    /* long-polling sites never go idle; "load" already fired */
  }
  await page.evaluate(() => document.fonts && document.fonts.ready);
  if (config.readySelector) {
    await page.locator(config.readySelector).first().waitFor({ state: "attached", timeout: 30_000 });
  }
  if (crop) {
    const target = page.locator(crop).first();
    await target.waitFor({ state: "visible", timeout: 30_000 });
    // Trigger lazy/IntersectionObserver content, then return to the top for a stable layout.
    await target.scrollIntoViewIfNeeded();
    await page.waitForTimeout(100);
    await page.evaluate(() => window.scrollTo(0, 0));
  }
  await page.evaluate(() => document.fonts && document.fonts.ready);
  await page.waitForTimeout(config.settleMs ?? 250);
}

async function cropClip(page, selector, pad, cropConfig) {
  const rect = await page.locator(selector).first().evaluate((el) => {
    const r = el.getBoundingClientRect();
    return {
      top: r.top + window.scrollY,
      height: r.height,
      docHeight: Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0),
    };
  });
  if (!rect || rect.height <= 0) throw new Error(`Crop selector not visible: ${selector}`);
  const width = page.viewportSize().width;
  const minH = Math.round(width * cropConfig.minAspect);
  const maxH = Math.round(width * cropConfig.maxAspect);
  const wanted = Math.ceil(rect.height + pad * 2);
  const height = Math.min(Math.max(wanted, minH), maxH);
  let y = wanted >= height ? rect.top - pad : rect.top + rect.height / 2 - height / 2;
  y = Math.max(0, Math.min(y, Math.max(0, rect.docHeight - height)));
  return { x: 0, y: Math.round(y), width, height };
}

function pngSize(buffer) {
  if (buffer.length < 24 || buffer.toString("ascii", 1, 4) !== "PNG") throw new Error("Not a PNG");
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

async function capture(browser, config, opts, { url, device, theme, label }) {
  const base = DEVICES[device];
  const scale = device === "desktop" ? opts.desktopScale : base.deviceScaleFactor;
  const context = await browser.newContext({
    viewport: { width: base.width, height: base.height },
    deviceScaleFactor: scale,
    colorScheme: theme === "dark" ? "dark" : "light",
    reducedMotion: "reduce",
  });
  await context.addInitScript(pageInitScript, {
    theme,
    themeConfig: config.theme,
    localStorageItems: config.localStorage || {},
    sessionStorageItems: config.sessionStorage || {},
    css: DISABLE_MOTION_CSS,
  });
  const page = await context.newPage();
  try {
    await page.goto(url, { waitUntil: "load", timeout: 120_000 });
    await waitForRender(page, config, opts.crop);

    const probe = await page.evaluate((attr) => ({
      body: getComputedStyle(document.body).backgroundColor,
      attr: attr ? document.documentElement.getAttribute(attr) : null,
    }), config.theme.attribute);
    const tag = `[shots] ${device}/${theme}${label ? `/${label}` : ""}`;
    console.log(`${tag} body background: ${probe.body}${config.theme.attribute ? ` (${config.theme.attribute}=${probe.attr ?? "unset"})` : ""}`);

    const shot = { type: "png", animations: "disabled", caret: "hide", scale: "device", omitBackground: false };
    if (opts.clip) {
      shot.clip = opts.clip;
      shot.fullPage = true;
    } else if (opts.crop) {
      shot.clip = await cropClip(page, opts.crop, opts.pad, config.crop);
      shot.fullPage = true;
    } else if (opts.fullPage) {
      shot.fullPage = true;
    }
    const buffer = await page.screenshot(shot);
    return { buffer, bodyBackground: probe.body, scale };
  } finally {
    await context.close();
  }
}

async function save(opts, name, device, theme, suffix, buffer) {
  await mkdir(opts.out, { recursive: true });
  const file = path.join(opts.out, `${[name, device, theme, suffix].filter(Boolean).join("-")}.png`);
  await writeFile(file, buffer);
  const { width, height } = pngSize(buffer);
  console.log(`[shots] wrote ${file} (${width}x${height})`);
  return { file, width, height };
}

function checkCropSize(info, device, scale, opts, config) {
  if (!opts.crop) return;
  const expectedW = Math.round(DEVICES[device].width * scale);
  const maxH = Math.ceil(expectedW * config.crop.maxAspect) + Math.ceil(scale);
  if (info.width !== expectedW || info.height > maxH) {
    console.warn(`[shots] warning: ${info.file} is ${info.width}x${info.height}; expected width ${expectedW}, height <= ${maxH}`);
  }
}

async function composite(browser, before, after) {
  const page = await browser.newPage();
  try {
    const result = await page.evaluate(async ({ a, b }) => {
      const load = (src) => new Promise((ok, fail) => {
        const img = new Image();
        img.onload = () => ok(img);
        img.onerror = fail;
        img.src = `data:image/png;base64,${src}`;
      });
      const [imgA, imgB] = await Promise.all([load(a), load(b)]);
      const w = Math.max(imgA.width, imgB.width);
      const h = Math.max(imgA.height, imgB.height);
      const pixels = (img) => {
        const c = document.createElement("canvas");
        c.width = w;
        c.height = h;
        const ctx = c.getContext("2d");
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, w, h);
        ctx.drawImage(img, 0, 0);
        return ctx.getImageData(0, 0, w, h).data;
      };
      const da = pixels(imgA);
      const db = pixels(imgB);
      let diff = 0;
      for (let i = 0; i < da.length; i += 4) {
        if (da[i] !== db[i] || da[i + 1] !== db[i + 1] || da[i + 2] !== db[i + 2] || da[i + 3] !== db[i + 3]) diff += 1;
      }
      const gap = Math.max(8, Math.round(w * 0.02));
      const side = document.createElement("canvas");
      side.width = w * 2 + gap;
      side.height = h;
      const sctx = side.getContext("2d");
      sctx.fillStyle = "#ff00ff";
      sctx.fillRect(0, 0, side.width, side.height);
      sctx.drawImage(imgA, 0, 0);
      sctx.drawImage(imgB, w + gap, 0);
      return { diff, total: w * h, sameSize: imgA.width === imgB.width && imgA.height === imgB.height, b64: side.toDataURL("image/png").split(",")[1] };
    }, { a: before.toString("base64"), b: after.toString("base64") });
    return { ...result, buffer: Buffer.from(result.b64, "base64") };
  } finally {
    await page.close();
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(HELP);
    return;
  }
  const config = loadConfig(args.config);
  const opts = resolveOptions(args, config);
  const browser = await launchBrowser();
  try {
    if (opts.compare) {
      const [beforeIn, afterIn] = opts.compare;
      const beforeUrl = await resolveTarget(beforeIn);
      const afterUrl = await resolveTarget(afterIn);
      const name = slugify(opts.name ?? deriveName(afterIn));
      for (const device of opts.devices) {
        for (const theme of opts.themes) {
          const b = await capture(browser, config, opts, { url: beforeUrl, device, theme, label: "before" });
          const a = await capture(browser, config, opts, { url: afterUrl, device, theme, label: "after" });
          checkCropSize(await save(opts, name, device, theme, "before", b.buffer), device, b.scale, opts, config);
          checkCropSize(await save(opts, name, device, theme, "after", a.buffer), device, a.scale, opts, config);
          const c = await composite(browser, b.buffer, a.buffer);
          await save(opts, name, device, theme, "compare", c.buffer);
          const pct = ((100 * c.diff) / c.total).toFixed(2);
          console.log(`[shots] ${device}/${theme}: ${c.diff} differing pixels (${pct}%)${c.sameSize ? "" : " (sizes differ; padded white)"}`);
        }
      }
    } else {
      const url = await resolveTarget(opts.url);
      const name = slugify(opts.name ?? deriveName(opts.url));
      const backgrounds = new Map();
      for (const device of opts.devices) {
        for (const theme of opts.themes) {
          const r = await capture(browser, config, opts, { url, device, theme });
          checkCropSize(await save(opts, name, device, theme, null, r.buffer), device, r.scale, opts, config);
          backgrounds.set(`${device}/${theme}`, r.bodyBackground);
        }
        const light = backgrounds.get(`${device}/light`);
        if (light && light === backgrounds.get(`${device}/dark`)) {
          console.warn(`[shots] warning: ${device} light and dark body backgrounds match (${light}); theme may not have applied`);
        }
      }
    }
  } finally {
    await browser.close();
    for (const s of servers) s.close();
  }
}

main().catch((err) => {
  console.error(`[shots] ${err.message || err}`);
  process.exit(1);
});
