"""Validate data/items.json sources and data/initiatives.json Tracker rows."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import initiatives_lib as I  # noqa: E402
import items_lib as L  # noqa: E402

items = L.load_json(L.ITEMS)
allowed = L.load_allowed_sources()
errs = L.validate_collection(items, allowed)

initiatives_path = I.INITIATIVES
if initiatives_path.is_file():
    initiatives = I.load_json(initiatives_path)
    item_ids = {item["id"] for item in items if isinstance(item, dict) and item.get("id")}
    errs.extend(I.validate_collection(initiatives, item_ids))
else:
    errs.append("missing data/initiatives.json")

if errs:
    print("\n".join(errs))
    sys.exit(1)

initiative_count = len(I.load_json(initiatives_path))
print(
    f"OK: {len(items)} items; sources in allowed set ({len(allowed)} names); "
    f"{initiative_count} initiatives"
)
