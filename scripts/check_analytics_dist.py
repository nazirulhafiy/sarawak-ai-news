#!/usr/bin/env python3
"""Fail if dist HTML analytics loaders drift from data/analytics.json.

Checks each built ``*.html`` page:

- exactly one ``data-sn-analytics-loader`` script (zero or two+ fails; names the file)
- every GA4 id and CF beacon token found must appear in the registry
- every internal-cookie name referenced must be the registry primary or a
  per-host ``legacy_internal_cookies`` entry
- CF beacon ``spa`` must match the registry boolean
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analytics_registry import load_analytics  # noqa: E402

LOADER_ATTR = "data-sn-analytics-loader"
LOADER_BLOCK_RE = re.compile(
    rf"<script[^>]*\b{re.escape(LOADER_ATTR)}\b[^>]*>(.*?)</script>",
    re.DOTALL | re.IGNORECASE,
)
GA4_RE = re.compile(r"\bG-[A-Z0-9]+\b")
# Cloudflare Web Analytics site tokens are 32 lowercase hex chars.
CF_TOKEN_RE = re.compile(r"\b[a-f0-9]{32}\b")
# Primary cookie: var C="name" or ,C="name"
PRIMARY_COOKIE_RE = re.compile(r"""(?:\bvar\s+C|\bC)\s*=\s*(["'])([A-Za-z0-9_-]+)\1""")
# Honour list: L=["a","b"]
LEGACY_LIST_RE = re.compile(r"""\bL\s*=\s*\[(.*?)\]""", re.DOTALL)
QUOTED_NAME_RE = re.compile(r"""(["'])([A-Za-z0-9_-]+)\1""")
# Hand-typed dual loaders on main used GA_INTERNAL_COOKIE / ga_internal / sn_internal
# outside the marked loader — catch stray cookie literals next to document.cookie.
STRAY_COOKIE_RE = re.compile(
    r"""document\.cookie\s*=\s*(["'])([A-Za-z0-9_-]+)\1"""
    r"""|"""
    r"""(["'])([A-Za-z0-9_-]+)\3\s*\+\s*['"]=1['"]"""
    r"""|"""
    r"""indexOf\(\s*(["'])([A-Za-z0-9_-]+)\5\s*\+\s*['"]=1['"]\)"""
)
SPA_TRUE_RE = re.compile(r"""["']spa["']\s*:\s*true|\bspa\s*:\s*true\b|\bspa\s*:\s*!0""")
SPA_FALSE_RE = re.compile(r"""["']spa["']\s*:\s*false|\bspa\s*:\s*false\b|\bspa\s*:\s*!1""")

def html_pages(dist: Path) -> list[Path]:
    """Primary HTML pages that must carry the analytics loader.

    Legacy category redirect stubs (``policy.html`` and siblings) are noindex
    refresh pages without the shared shell; skip them.
    """
    pages = sorted(dist.glob("*.html"))
    if not pages:
        raise SystemExit(f"no HTML pages under {dist}")
    primary: list[Path] = []
    for path in pages:
        text = path.read_text(encoding="utf-8")
        if 'http-equiv="refresh"' in text or "http-equiv='refresh'" in text:
            continue
        primary.append(path)
    if not primary:
        raise SystemExit(f"no primary HTML pages under {dist}")
    return primary


def check_page(path: Path, registry) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rel = str(path)
    errors: list[str] = []

    loader_count = text.count(LOADER_ATTR)
    if loader_count == 0:
        errors.append(f"{rel}: zero analytics loaders (missing {LOADER_ATTR})")
    elif loader_count != 1:
        errors.append(f"{rel}: {loader_count} analytics loaders (want exactly one {LOADER_ATTR})")

    allowed_ga = registry.ga4_ids()
    allowed_tokens = registry.cf_tokens()
    allowed_cookies = set(registry.honour_cookies)

    for mid in sorted(set(GA4_RE.findall(text))):
        if mid not in allowed_ga:
            errors.append(f"{rel}: GA4 id {mid!r} not in data/analytics.json")

    # Only flag 32-hex strings that appear near CF beacon usage.
    if "cloudflareinsights.com/beacon" in text or "data-cf-beacon" in text:
        for token in sorted(set(CF_TOKEN_RE.findall(text))):
            if token not in allowed_tokens:
                errors.append(f"{rel}: CF beacon token {token!r} not in data/analytics.json")

    found_cookies: set[str] = set()
    for block in LOADER_BLOCK_RE.findall(text):
        for match in PRIMARY_COOKIE_RE.finditer(block):
            found_cookies.add(match.group(2))
        for list_match in LEGACY_LIST_RE.finditer(block):
            for quoted in QUOTED_NAME_RE.finditer(list_match.group(1)):
                found_cookies.add(quoted.group(2))
    # Also scan full page for document.cookie patterns (hand-typed dual scripts on main).
    if "traffic_type" in text or "cloudflareinsights.com/beacon" in text or LOADER_ATTR in text:
        for match in STRAY_COOKIE_RE.finditer(text):
            name = match.group(2) or match.group(4) or match.group(6)
            if name:
                found_cookies.add(name)

    for name in sorted(found_cookies):
        if name not in allowed_cookies:
            errors.append(
                f"{rel}: cookie name {name!r} is not registry internal_cookie "
                f"({registry.internal_cookie!r}) or legacy_internal_cookies "
                f"{registry.legacy_internal_cookies!r}"
            )
    has_spa_true = bool(SPA_TRUE_RE.search(text))
    has_spa_false = bool(SPA_FALSE_RE.search(text))
    if "cloudflareinsights.com/beacon" in text or "data-cf-beacon" in text:
        if registry.spa and not has_spa_true:
            errors.append(f"{rel}: registry spa is true but CF beacon config lacks spa:true")
        if not registry.spa and has_spa_true:
            errors.append(f"{rel}: registry spa is false but CF beacon sets spa:true (drift)")
        if not registry.spa and has_spa_false:
            # Explicit false is fine; no error.
            pass

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dist",
        type=Path,
        default=ROOT / "dist",
        help="Built site directory (default: dist/)",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=ROOT / "data" / "analytics.json",
        help="Analytics registry path",
    )
    args = parser.parse_args(argv)

    if not args.dist.is_dir():
        print(f"FAIL: dist directory missing: {args.dist}", file=sys.stderr)
        return 1

    registry = load_analytics(args.registry)
    errors: list[str] = []
    for page in html_pages(args.dist):
        errors.extend(check_page(page, registry))

    if errors:
        print("Analytics dist check FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    pages = html_pages(args.dist)
    print(
        f"Analytics dist check OK: {len(pages)} page(s), "
        f"version={registry.version}, cookie={registry.internal_cookie!r}, "
        f"spa={registry.spa}, ga4={sorted(registry.ga4_ids())}, "
        f"hosts={list(registry.hosts)}, "
        f"legacy_internal_cookies={registry.legacy_internal_cookies!r}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
