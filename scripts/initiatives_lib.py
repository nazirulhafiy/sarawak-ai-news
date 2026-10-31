"""Validation for data/initiatives.json (Tracker page)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
INITIATIVES = DATA / "initiatives.json"
ITEMS = DATA / "items.json"

VALID_STATUSES = frozenset({"Planning", "Ongoing", "Completed"})
REQUIRED_FIELDS = (
    "agency",
    "agency_short",
    "initiative",
    "what",
    "status",
    "evidence",
    "story_id",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_item_ids(path: Path = ITEMS) -> set[str]:
    items = load_json(path)
    if not isinstance(items, list):
        raise ValueError("data/items.json must be a JSON array")
    ids: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            eid = item.get("id")
            if isinstance(eid, str) and eid:
                ids.add(eid)
    return ids


def validate_initiative(
    entry: dict,
    item_ids: set[str],
    index: int | None = None,
) -> list[str]:
    """Return validation errors for one initiative row."""
    label = (
        entry.get("initiative")
        or entry.get("story_id")
        or (f"initiatives[{index}]" if index is not None else "<initiative>")
    )
    errs: list[str] = []
    if not isinstance(entry, dict):
        return [f"{label}: initiative must be an object"]

    missing = [f for f in REQUIRED_FIELDS if f not in entry]
    if missing:
        errs.append(f"{label}: missing fields: {', '.join(missing)}")

    status = entry.get("status")
    if status is None or (isinstance(status, str) and not status.strip()):
        errs.append(f"{label}: status is required")
    elif not isinstance(status, str):
        errs.append(f"{label}: status must be a string")
    elif status not in VALID_STATUSES:
        errs.append(
            f"{label}: status {status!r} must be one of "
            f"{', '.join(sorted(VALID_STATUSES))}"
        )

    story_id = entry.get("story_id")
    if story_id is None or (isinstance(story_id, str) and not story_id.strip()):
        errs.append(f"{label}: story_id is required")
    elif not isinstance(story_id, str):
        errs.append(f"{label}: story_id must be a string")
    elif story_id not in item_ids:
        errs.append(
            f"{label}: story_id {story_id!r} is not a real id in data/items.json"
        )

    for field in ("agency", "agency_short", "initiative", "what", "evidence"):
        value = entry.get(field)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            errs.append(f"{label}: {field} must be a non-empty string")

    logo = entry.get("logo")
    if logo is not None:
        if not isinstance(logo, str) or not logo.strip():
            errs.append(f"{label}: logo must be a non-empty string when set")

    return errs


def validate_collection(
    initiatives: list,
    item_ids: set[str] | None = None,
) -> list[str]:
    """Validate every initiative against published story ids and status values."""
    if item_ids is None:
        item_ids = load_item_ids()
    if not isinstance(initiatives, list):
        return ["initiatives.json must be a JSON array"]

    errs: list[str] = []
    for index, entry in enumerate(initiatives):
        if not isinstance(entry, dict):
            errs.append(f"initiatives[{index}]: must be an object")
            continue
        errs.extend(validate_initiative(entry, item_ids, index=index))
    return errs
