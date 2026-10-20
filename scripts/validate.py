"""Validate data/items.json: every published item needs an allowed source."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import items_lib as L  # noqa: E402

items = L.load_json(L.ITEMS)
allowed = L.load_allowed_sources()
errs = L.validate_collection(items, allowed)
if errs:
    print("\n".join(errs))
    sys.exit(1)
print(f"OK: {len(items)} items; sources in allowed set ({len(allowed)} names)")
