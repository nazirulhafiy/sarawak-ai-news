from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from html import unescape
from pathlib import Path
from typing import Callable, Iterable
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "items.json"
MALAYSIA_TZ = timezone(timedelta(hours=8))


@dataclass(frozen=True)
class DateMismatch:
    title: str
    url: str
    expected: str
    actual: str


@dataclass(frozen=True)
class DateFetchError(Exception):
    url: str
    reason: str


@dataclass(frozen=True)
class UnavailableSource:
    title: str
    url: str
    reason: str


def _strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _date_from_iso(value: str) -> str | None:
    value = value.strip()
    if not re.match(r"20\d{2}-\d{2}-\d{2}", value):
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.date().isoformat()
        return parsed.astimezone(MALAYSIA_TZ).date().isoformat()
    except ValueError:
        return value[:10]


def _date_from_human(value: str) -> str | None:
    value = re.sub(r"\s+", " ", value.strip())
    for fmt in ("%d %B %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def extract_published_date(html: str) -> str | None:
    """Extract the article's own publication date from metadata/byline signals.

    This intentionally prefers article metadata over visible page text because
    Sarawak news sites often render today's site header and related-news dates
    near the article. Those are not the article publication date.
    """
    metadata_patterns = [
        r"<meta[^>]+property=[\"']article:published_time[\"'][^>]+content=[\"']([^\"']+)",
        r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+property=[\"']article:published_time[\"']",
        r"<meta[^>]+name=[\"']pubdate[\"'][^>]+content=[\"']([^\"']+)",
        r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+name=[\"']pubdate[\"']",
        r"<time[^>]+datetime=[\"']([^\"']+)",
        r"[\"']datePublished[\"']\s*:\s*[\"']([^\"']+)",
    ]
    for pattern in metadata_patterns:
        for candidate in re.findall(pattern, html, flags=re.IGNORECASE | re.DOTALL):
            parsed = _date_from_iso(candidate)
            if parsed:
                return parsed

    # Fallback: only use visible dates near known article/byline blocks, not
    # arbitrary page text. This catches WordPress bylines when metadata is absent.
    byline_patterns = [
        r"<li[^>]*>\s*(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2})\s*</li>",
        r"<span[^>]+class=[\"'][^\"']*(?:date|posted-on|published)[^\"']*[\"'][^>]*>(.*?)</span>",
        r"<div[^>]+class=[\"'][^\"']*(?:date|posted-on|published)[^\"']*[\"'][^>]*>(.*?)</div>",
    ]
    for pattern in byline_patterns:
        for candidate in re.findall(pattern, html, flags=re.IGNORECASE | re.DOTALL):
            text = _strip_tags(candidate)
            human = re.search(
                r"\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+20\d{2})\b",
                text,
                flags=re.IGNORECASE,
            )
            if human:
                parsed = _date_from_human(human.group(1))
                if parsed:
                    return parsed
    return None


def fetch_html(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SarawakNewsDateAudit/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "ignore")
    except HTTPError as exc:
        raise DateFetchError(url, f"HTTP {exc.code}") from exc
    except URLError as exc:
        raise DateFetchError(url, str(exc.reason)) from exc
    except TimeoutError as exc:
        raise DateFetchError(url, "timeout") from exc


def load_items(path: Path = DATA) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def select_items(items: list[dict], item_ids: list[str]) -> list[dict]:
    requested = set(item_ids)
    selected = [item for item in items if item.get("id") in requested]
    found = {str(item.get("id")) for item in selected}
    missing = sorted(requested - found)
    if missing:
        raise ValueError(f"Unknown item id(s): {', '.join(missing)}")
    return selected


def changed_items(items: list[dict], baseline_items: list[dict]) -> list[dict]:
    """Return new items and records whose date-relevant source fields changed."""
    baseline = {str(item.get("id")): item for item in baseline_items}
    relevant_fields = ("title", "url", "date")
    return [
        item
        for item in items
        if str(item.get("id")) not in baseline
        or any(item.get(field) != baseline[str(item.get("id"))].get(field) for field in relevant_fields)
    ]


def load_items_from_git(ref: str, path: Path = DATA) -> list[dict]:
    try:
        relative_path = path.resolve().relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise ValueError("--changed-from requires --items to be inside the repository") from exc
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        reason = result.stderr.strip() or f"unable to read {relative_path}"
        raise ValueError(f"Could not load date-audit baseline {ref}: {reason}")
    return json.loads(result.stdout)


def find_date_mismatches(
    items: Iterable[dict], html_loader: Callable[[str], str] = fetch_html
) -> tuple[list[DateMismatch], list[UnavailableSource]]:
    mismatches: list[DateMismatch] = []
    unavailable: list[UnavailableSource] = []
    for item in items:
        try:
            expected = extract_published_date(html_loader(item["url"]))
        except DateFetchError as exc:
            unavailable.append(UnavailableSource(item["title"], item["url"], exc.reason))
            continue
        actual = str(item.get("date", ""))
        if expected and actual != expected:
            mismatches.append(DateMismatch(item["title"], item["url"], expected, actual))
    return mismatches, unavailable


def audit_items(items: list[dict], html_loader: Callable[[str], str] = fetch_html) -> int:
    if not items:
        print("Date audit skipped: no new or date-relevant item changes")
        return 0
    mismatches, unavailable = find_date_mismatches(items, html_loader)
    if unavailable:
        print("Date audit warning: skipped temporarily unavailable sources:", file=sys.stderr)
        for source in unavailable:
            print(f"- {source.title}\n  url: {source.url}\n  reason: {source.reason}", file=sys.stderr)
    if not mismatches:
        checked = len(items) - len(unavailable)
        print(f"Date audit passed for {checked}/{len(items)} reachable items")
        return 0
    print("Date audit failed:", file=sys.stderr)
    for mismatch in mismatches:
        print(
            f"- {mismatch.title}\n"
            f"  url: {mismatch.url}\n"
            f"  feed date: {mismatch.actual}\n"
            f"  source date: {mismatch.expected}",
            file=sys.stderr,
        )
    return 1


def audit(path: Path = DATA) -> int:
    return audit_items(load_items(path))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify feed dates against article published metadata.")
    parser.add_argument("--items", type=Path, default=DATA, help="Path to items.json")
    selectors = parser.add_mutually_exclusive_group()
    selectors.add_argument(
        "--item-id",
        action="append",
        dest="item_ids",
        help="Audit one item by id; repeat for multiple added or edited items",
    )
    selectors.add_argument(
        "--changed-from",
        metavar="GIT_REF",
        help="Audit only new items or records with changed title, URL, or date relative to a Git ref",
    )
    args = parser.parse_args(argv)
    items = load_items(args.items)
    try:
        if args.item_ids:
            items = select_items(items, args.item_ids)
        elif args.changed_from:
            items = changed_items(items, load_items_from_git(args.changed_from, args.items))
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return audit_items(items)


if __name__ == "__main__":
    raise SystemExit(main())
