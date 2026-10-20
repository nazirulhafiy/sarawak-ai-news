#!/usr/bin/env python3
"""Content-hash query strings for published asset URLs."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# Split so this file does not contain the stamp it forbids.
_QUERY_STAMP = "?" + "v="
_GENERATED_BEGIN = "<!-- BEGIN GENERATED:"
_GENERATED_END = "<!-- END GENERATED:"
_SKIP_PARTS = frozenset({"__pycache__", "dist", ".git"})
_BINARY_SUFFIXES = frozenset({".png", ".ico", ".woff", ".woff2", ".pyc", ".jpg", ".jpeg", ".gif", ".webp"})
_SITE_SUFFIXES = frozenset({".html", ".js", ".css", ".svg"})


def content_hash(path: Path, n: int = 12) -> str:
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if n < 1 or n > len(digest):
        raise ValueError(f"n must be between 1 and {len(digest)}")
    return digest[:n]


def versioned_href(href: str, file_path: Path) -> str:
    """Set the asset query on ``href`` from the bytes at ``file_path``."""
    digest = content_hash(file_path)
    parts = urlsplit(href)
    pairs = parse_qsl(parts.query, keep_blank_values=True)
    replaced = False
    stamped: list[tuple[str, str]] = []
    for key, value in pairs:
        if key == "v":
            stamped.append((key, digest))
            replaced = True
        else:
            stamped.append((key, value))
    if not replaced:
        stamped.append(("v", digest))
    query = urlencode(stamped)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def _visible_lines(text: str) -> list[tuple[int, str]]:
    skipping = False
    visible: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if skipping:
            if _GENERATED_END in line:
                skipping = False
            continue
        if _GENERATED_BEGIN in line:
            skipping = _GENERATED_END not in line
            continue
        visible.append((line_no, line))
    return visible


def _scan_files(root: Path) -> list[Path]:
    files: list[Path] = []

    def add_tree(base: Path, suffixes: frozenset[str] | None) -> None:
        if not base.exists():
            return
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _SKIP_PARTS for part in path.parts):
                continue
            if path.suffix.lower() in _BINARY_SUFFIXES:
                continue
            if suffixes is not None and path.suffix.lower() not in suffixes:
                continue
            files.append(path)

    add_tree(root / "scripts", None)
    add_tree(root / "kit", None)
    add_tree(root / "docs", None)
    add_tree(root / "site", _SITE_SUFFIXES)
    for name in ("README.md", "AGENTS.md"):
        path = root / name
        if path.is_file():
            files.append(path)
    return files


def assert_no_hand_typed_v(root: Path) -> None:
    """Raise if source trees contain a hand-typed asset query stamp.

    Scans ``scripts/``, ``kit/``, ``docs/``, ``README.md``, ``AGENTS.md``, and
    site HTML, JS, CSS, and SVG. Skips ``dist/`` and the interior of
    ``BEGIN GENERATED`` / ``END GENERATED`` blocks.
    """
    root = Path(root)
    violations: list[str] = []
    for path in _scan_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(root).as_posix()
        for line_no, line in _visible_lines(text):
            if _QUERY_STAMP in line:
                violations.append(f"{rel}:{line_no}: {line.strip()}")
    if violations:
        preview = "\n".join(violations[:40])
        extra = "" if len(violations) <= 40 else f"\n... and {len(violations) - 40} more"
        raise AssertionError(
            f"hand-typed asset query stamp ({len(violations)}):\n{preview}{extra}"
        )
