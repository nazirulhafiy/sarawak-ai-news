#!/usr/bin/env python3
"""Generated fact blocks for docs that must match repo sources."""

from __future__ import annotations

import difflib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from kit.python.analytics_registry import load_analytics

BLOCK_IDS = ("site-copy", "analytics", "hosting", "design-tokens")

_SITE_COPY_KEYS = ("title", "tagline", "description")
_TOKEN_SELECTORS = (":root", 'html[data-theme="dark"]')
_PROP_RE = re.compile(r"(--[A-Za-z0-9-]+)\s*:\s*([^;]+);")


@dataclass(frozen=True)
class Block:
    block_id: str
    targets: tuple[str, ...]


BLOCKS = (
    Block("site-copy", ("docs/design.md", "README.md")),
    Block("analytics", ("docs/design.md", "README.md")),
    Block("hosting", ("docs/design.md", "README.md")),
    Block("design-tokens", ("docs/design.md",)),
)


def _begin(block_id: str) -> str:
    return f"<!-- BEGIN GENERATED: {block_id} -->"


def _end(block_id: str) -> str:
    return f"<!-- END GENERATED: {block_id} -->"


def _cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> object:
    if not path.is_file():
        raise SystemExit(f"missing {path.name} at {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc


def render_site_copy(root: Path) -> str:
    payload = _read_json(root / "data" / "site.json")
    if not isinstance(payload, dict):
        raise SystemExit("data/site.json must be an object")
    rows: list[list[str]] = []
    for key in _SITE_COPY_KEYS:
        value = payload.get(key)
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"data/site.json is missing {key}")
        rows.append([f"`{key}`", _cell(value)])
    return _table(["Field", "Value"], rows)


def render_analytics(root: Path) -> str:
    registry = load_analytics(root / "data" / "analytics.json")
    hosts = ", ".join(f"`{name}`" for name in registry.hostnames)
    rows = [
        ["`ga4_measurement_id`", f"`{registry.primary_ga4_id()}`"],
        ["`cf_beacon_token`", f"`{registry.primary_cf_token()}`"],
        ["`internal_cookie`", f"`{registry.internal_cookie}`"],
        ["`hosts`", hosts],
    ]
    return _table(["Field", "Value"], rows)


def load_hosting(root: Path) -> tuple[str, str]:
    override = root / "data" / "hosting.json"
    if override.is_file():
        payload = _read_json(override)
        if not isinstance(payload, dict):
            raise SystemExit("data/hosting.json must be an object")
        unknown = set(payload) - {"target", "hostname"}
        if unknown:
            raise SystemExit(f"data/hosting.json unknown keys: {sorted(unknown)}")
        target = payload.get("target")
        hostname = payload.get("hostname")
        if not isinstance(target, str) or not target.strip():
            raise SystemExit("data/hosting.json target must be a non-empty string")
        if not isinstance(hostname, str) or not hostname.strip():
            raise SystemExit("data/hosting.json hostname must be a non-empty string")
        return hostname.strip(), target.strip()
    cname_path = root / "CNAME"
    if not cname_path.is_file():
        raise SystemExit("hosting facts need data/hosting.json or CNAME")
    hostname = cname_path.read_text(encoding="utf-8").strip()
    if not hostname or any(char.isspace() for char in hostname):
        raise SystemExit("CNAME must be a single hostname")
    return hostname, "GitHub Pages"


def render_hosting(root: Path) -> str:
    hostname, target = load_hosting(root)
    rows = [
        ["`hostname`", f"`{hostname}`"],
        ["`target`", _cell(target)],
    ]
    return _table(["Field", "Value"], rows)


def custom_properties(css: str, selector: str) -> dict[str, str]:
    """Custom properties from the first rule whose selector is exactly ``selector``.

    Later rules with the same selector are overrides, such as the 560px
    ``--page-gutter`` tweak. They are not the token set.
    """
    props: dict[str, str] = {}
    index = 0
    while True:
        found = css.find(selector, index)
        if found < 0:
            return props
        before = css[found - 1] if found else "\n"
        if before not in "{\n\t ;":
            index = found + len(selector)
            continue
        rest = css[found + len(selector) :]
        matched = re.match(r"[ \t]*\{", rest)
        if not matched:
            index = found + len(selector)
            continue
        body_start = found + len(selector) + matched.end()
        end = css.find("}", body_start)
        if end < 0:
            raise SystemExit(f"unclosed CSS rule for {selector}")
        for item in _PROP_RE.finditer(css[body_start:end]):
            props[item.group(1)] = item.group(2).strip()
        return props


def render_design_tokens(root: Path) -> str:
    css_path = root / "site" / "style.css"
    if not css_path.is_file():
        raise SystemExit("missing site/style.css")
    css = css_path.read_text(encoding="utf-8")
    columns = [custom_properties(css, selector) for selector in _TOKEN_SELECTORS]
    if not columns[0]:
        raise SystemExit("site/style.css has no :root custom properties")
    if not columns[1]:
        raise SystemExit('site/style.css has no html[data-theme="dark"] custom properties')
    names = list(columns[0])
    for name in columns[1]:
        if name not in columns[0]:
            names.append(name)
    rows = []
    for name in names:
        rows.append(
            [
                f"`{name}`",
                _cell(columns[0].get(name, "")),
                _cell(columns[1].get(name, "")),
            ]
        )
    headers = ["Token", "`:root`", '`html[data-theme="dark"]`']
    return _table(headers, rows)


_RENDERERS = {
    "site-copy": render_site_copy,
    "analytics": render_analytics,
    "hosting": render_hosting,
    "design-tokens": render_design_tokens,
}


def render_block(root: Path, block_id: str) -> str:
    try:
        render = _RENDERERS[block_id]
    except KeyError as exc:
        raise SystemExit(f"unknown block {block_id}") from exc
    return render(root)


def _marker_body(text: str, block_id: str) -> tuple[int, int] | str:
    begin = _begin(block_id)
    end = _end(block_id)
    if text.count(begin) != 1 or text.count(end) != 1:
        return f"expected one {block_id} marker pair"
    start = text.find(begin)
    stop = text.find(end)
    if stop < start:
        return f"end marker before begin for {block_id}"
    return start + len(begin), stop


def _canonical(body: str) -> str:
    return body.strip("\n") + "\n"


@dataclass(frozen=True)
class _Planned:
    path: Path
    rel: str
    block_id: str
    body: str
    text: str
    span: tuple[int, int]


def _plan(root: Path) -> tuple[list[str], list[_Planned]]:
    errors: list[str] = []
    planned: list[_Planned] = []
    for block in BLOCKS:
        body = render_block(root, block.block_id)
        for rel in block.targets:
            path = root / rel
            if not path.is_file():
                errors.append(f"missing {rel}")
                continue
            text = path.read_text(encoding="utf-8")
            span = _marker_body(text, block.block_id)
            if isinstance(span, str):
                errors.append(f"{rel}: {span}")
                continue
            planned.append(_Planned(path, rel, block.block_id, body, text, span))
    return errors, planned


def _rewrite(text: str, span: tuple[int, int], body: str) -> str:
    start, stop = span
    return text[:start] + "\n" + _canonical(body) + text[stop:]


def _report(errors: list[str]) -> None:
    for error in errors:
        print(f"FAIL generate_docs: {error}", file=sys.stderr)


def generate(root: Path) -> int:
    """Rewrite marker interiors from source files. Return 0, or 1 if markers are missing."""
    root = Path(root)
    errors, planned = _plan(root)
    if errors:
        _report(errors)
        return 1
    writes = 0
    by_path: dict[Path, str] = {}
    for item in planned:
        current = by_path.get(item.path, item.text)
        # Spans were computed against the original text. Apply one block at a time
        # by searching again so earlier writes do not shift later spans.
        span = _marker_body(current, item.block_id)
        if isinstance(span, str):
            print(f"FAIL generate_docs: {item.rel}: {span}", file=sys.stderr)
            return 1
        updated = _rewrite(current, span, item.body)
        by_path[item.path] = updated
    for path, updated in by_path.items():
        original = path.read_text(encoding="utf-8")
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            writes += 1
            print(f"updated {path.relative_to(root).as_posix()}")
    print(f"OK generate_docs ({writes} write(s))")
    return 0


def check(root: Path) -> int:
    """Return 0 when marker interiors match a fresh render, else 1."""
    root = Path(root)
    try:
        errors, planned = _plan(root)
    except SystemExit:
        raise
    if errors:
        _report(errors)
        return 1
    drifted = 0
    for item in planned:
        current = item.text[item.span[0] : item.span[1]]
        expected = _canonical(item.body)
        if current.strip() == expected.strip():
            continue
        drifted += 1
        print(
            f"FAIL generate_docs: {item.rel} block {item.block_id} drifted",
            file=sys.stderr,
        )
        diff = difflib.unified_diff(
            (current.strip() + "\n").splitlines(keepends=True),
            (expected.strip() + "\n").splitlines(keepends=True),
            fromfile=f"{item.rel}:{item.block_id}",
            tofile="generated",
        )
        sys.stdout.writelines(diff)
    if drifted:
        return 1
    print("OK generate_docs")
    return 0
