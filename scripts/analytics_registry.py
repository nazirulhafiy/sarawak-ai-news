#!/usr/bin/env python3
"""Re-export the shared kit analytics registry for existing script imports."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from kit.analytics_registry import *  # noqa: E402,F403
from kit.analytics_registry import (  # noqa: E402
    ANALYTICS_PATH,
    AnalyticsRegistry,
    HostEntry,
    load_analytics,
    validate_analytics_payload,
)

__all__ = [
    "ANALYTICS_PATH",
    "AnalyticsRegistry",
    "HostEntry",
    "load_analytics",
    "validate_analytics_payload",
]
