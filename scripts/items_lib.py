"""Shared validation for published AI News items (data/items.json)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ITEMS = DATA / "items.json"
ALLOWED_SOURCES = DATA / "allowed-sources.json"

REQUIRED_FIELDS = (
    "id",
    "date",
    "source",
    "url",
    "title",
    "section",
    "tags",
    "summary",
    "why_it_matters",
    "confidence",
    "caveat",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_allowed_sources(path: Path = ALLOWED_SOURCES) -> set[str]:
    payload = load_json(path)
    if not isinstance(payload, list) or not payload:
        raise ValueError("data/allowed-sources.json must be a non-empty JSON array")
    allowed: set[str] = set()
    for entry in payload:
        if not isinstance(entry, str) or not entry.strip():
            raise ValueError("allowed sources must be non-empty strings")
        name = entry.strip()
        if name in allowed:
            raise ValueError(f"duplicate allowed source: {name}")
        allowed.add(name)
    return allowed


def validate_item(item: dict, allowed_sources: set[str]) -> list[str]:
    """Return validation errors for one published item."""
    errs: list[str] = []
    eid = item.get("id") or "<missing-id>"
    if not isinstance(item, dict):
        return [f"{eid}: item must be an object"]

    missing = [f for f in REQUIRED_FIELDS if f not in item]
    if missing:
        errs.append(f"{eid}: missing fields: {', '.join(missing)}")

    source = item.get("source")
    if source is None or (isinstance(source, str) and not source.strip()):
        errs.append(f"{eid}: source is required")
    elif not isinstance(source, str):
        errs.append(f"{eid}: source must be a string")
    elif source not in allowed_sources:
        errs.append(
            f"{eid}: source {source!r} is not in data/allowed-sources.json"
        )
    elif source != source.strip() or "  " in source:
        errs.append(f"{eid}: source has leading/trailing or doubled spaces")

    url = item.get("url")
    if url is not None and (not isinstance(url, str) or not url.startswith("https://")):
        errs.append(f"{eid}: url must be https")

    return errs


def validate_collection(
    items: list,
    allowed_sources: set[str] | None = None,
) -> list[str]:
    """Validate every published item in items.json."""
    if allowed_sources is None:
        allowed_sources = load_allowed_sources()
    if not isinstance(items, list):
        return ["items.json must be a JSON array"]

    errs: list[str] = []
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            errs.append(f"items[{index}]: must be an object")
            continue
        eid = item.get("id")
        if isinstance(eid, str) and eid:
            if eid in seen_ids:
                errs.append(f"{eid}: duplicate id")
            seen_ids.add(eid)
        url = item.get("url")
        if isinstance(url, str) and url:
            if url in seen_urls:
                errs.append(f"{eid or f'items[{index}]'}: duplicate url")
            seen_urls.add(url)
        errs.extend(validate_item(item, allowed_sources))
    return errs
