#!/usr/bin/env python3
"""Regenerate or check generated blocks in docs/design.md and README.md.

  python3 kit/generate_docs.py
  python3 kit/generate_docs.py --check
  python3 kit/generate_docs.py --root PATH

Marker pairs must already be in the target files. This command fills or
compares the interior. It does not choose where a block sits.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kit.python.docs_facts import check, generate  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 when a generated block does not match its source",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="repo root (default: the repo that contains this kit)",
    )
    args = parser.parse_args(argv)
    root = args.root if args.root is not None else ROOT
    if args.check:
        return check(root)
    return generate(root)


if __name__ == "__main__":
    raise SystemExit(main())
