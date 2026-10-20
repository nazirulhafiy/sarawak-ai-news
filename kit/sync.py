#!/usr/bin/env python3
"""Vendor or check the Sarawak News shared kit.

Hub (no ``kit/PIN``):
  python3 kit/sync.py --check   # invariants + consumer mirrors
  python3 kit/sync.py --sync    # refresh site/ icons and BTT marker regions from kit
  python3 kit/sync.py           # same as --sync

Sister (``kit/PIN`` holds a hub commit SHA):
  python3 kit/sync.py --check --hub-path /path/to/sarawak-news-hub
  python3 kit/sync.py --sync  --hub-path /path/to/sarawak-news-hub

``SN_HUB_PATH`` may replace ``--hub-path``. Sisters must not hand-edit kit files;
bump the PIN and re-sync instead.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = KIT_ROOT.parent
PIN_PATH = KIT_ROOT / "PIN"
MANIFEST_PATH = KIT_ROOT / "MANIFEST.json"
CSS_BEGIN = "/* sn-kit:back-to-top:begin */"
CSS_END = "/* sn-kit:back-to-top:end */"
JS_BEGIN = "/* sn-kit:back-to-top:begin */"
JS_END = "/* sn-kit:back-to-top:end */"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def fail(msg: str) -> int:
    print(f"FAIL kit sync: {msg}", file=sys.stderr)
    return 1


def ok(msg: str) -> int:
    print(f"OK kit sync: {msg}")
    return 0


def extract_marked(text: str, begin: str, end: str) -> str | None:
    start = text.find(begin)
    stop = text.find(end)
    if start < 0 or stop < 0 or stop < start:
        return None
    inner = text[start + len(begin) : stop]
    if inner.startswith("\n"):
        inner = inner[1:]
    return inner


def replace_marked(text: str, begin: str, end: str, payload: str) -> str:
    start = text.find(begin)
    stop = text.find(end)
    if start < 0 or stop < 0 or stop < start:
        raise SystemExit(f"missing markers {begin!r} / {end!r}")
    body = payload if payload.endswith("\n") else payload + "\n"
    return text[: start + len(begin)] + "\n" + body + text[stop:]


def _inside_kit(path: Path) -> bool:
    try:
        path.resolve().relative_to(KIT_ROOT.resolve())
    except ValueError:
        return False
    return True


def check_invariants(manifest: dict, *, hub: bool) -> list[str]:
    errors: list[str] = []
    for inv in manifest.get("invariants", []):
        path = (KIT_ROOT / inv["path"]).resolve()
        # Paths outside kit/ (the hub cookie file) are hub-mode only.
        if not hub and not _inside_kit(path):
            continue
        if not path.is_file():
            errors.append(f"invariant {inv['id']}: missing {inv['path']}")
            continue
        text = path.read_text(encoding="utf-8")
        needle = inv["must_contain"]
        if needle not in text:
            errors.append(f"invariant {inv['id']}: {inv['path']} missing {needle!r}")
    return errors


def check_hub_consumers(manifest: dict) -> list[str]:
    errors: list[str] = []
    consumers = manifest.get("hub_consumers", {})
    for key, spec in consumers.items():
        kit_rel = spec["kit"]
        site_rel = spec["site"]
        kit_path = KIT_ROOT / kit_rel
        site_path = REPO_ROOT / site_rel
        if not kit_path.is_file():
            errors.append(f"consumer {key}: missing kit file {kit_rel}")
            continue
        if not site_path.is_file():
            errors.append(f"consumer {key}: missing site file {site_rel}")
            continue
        marker = spec.get("marker")
        if marker:
            begin = f"/* {marker}:begin */"
            end = f"/* {marker}:end */"
            site_text = site_path.read_text(encoding="utf-8")
            marked = extract_marked(site_text, begin, end)
            if marked is None:
                expected_raw = kit_path.read_text(encoding="utf-8")
                if site_rel.endswith(".css") and expected_raw in site_text:
                    continue
                errors.append(f"consumer {key}: missing markers in {site_rel}")
                continue
            expected = kit_path.read_text(encoding="utf-8")
            if not expected.endswith("\n"):
                expected += "\n"
            if marked != expected:
                errors.append(
                    f"consumer {key}: {site_rel} marker region drifted from kit/{kit_rel}"
                )
        else:
            if sha256_file(kit_path) != sha256_file(site_path):
                errors.append(
                    f"consumer {key}: {site_rel} hash differs from kit/{kit_rel}"
                )

    build_py = (REPO_ROOT / "scripts" / "build.py").read_text(encoding="utf-8")
    for needle in (
        "from kit.python.shell import",
        "from kit.python.analytics_loader import",
        "from kit.python.analytics_registry import",
    ):
        if needle not in build_py:
            errors.append(f"scripts/build.py must import kit via {needle!r}")

    # No hand-maintained duplicate loader body in build.py.
    if "def render_back_to_top" in build_py:
        errors.append("scripts/build.py must not define render_back_to_top")
    if "www.googletagmanager.com/gtag/js" in build_py:
        errors.append("scripts/build.py still contains a hand-typed analytics loader body")
    if 'data-back-to-top aria-label="Back to top"' in build_py:
        errors.append("scripts/build.py still hardcodes back-to-top markup")
    if "mailto:contact@sarawak.news" in build_py:
        errors.append(
            "scripts/build.py still hardcodes Contact mailto (must come from kit.python.shell)"
        )
    return errors


def hub_sync(manifest: dict) -> None:
    consumers = manifest.get("hub_consumers", {})
    for key, spec in consumers.items():
        kit_path = KIT_ROOT / spec["kit"]
        site_path = REPO_ROOT / spec["site"]
        marker = spec.get("marker")
        if marker:
            begin = f"/* {marker}:begin */"
            end = f"/* {marker}:end */"
            text = site_path.read_text(encoding="utf-8")
            payload = kit_path.read_text(encoding="utf-8")
            site_path.write_text(replace_marked(text, begin, end, payload), encoding="utf-8")
        else:
            site_path.parent.mkdir(parents=True, exist_ok=True)
            site_path.write_bytes(kit_path.read_bytes())
        print(f"synced {spec['site']} <- kit/{spec['kit']}")


def git_show(hub: Path, pin: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(hub), "show", f"{pin}:kit/{rel}"])


def pinned_file_list(hub: Path, pin: str) -> list[str]:
    try:
        raw = git_show(hub, pin, "MANIFEST.json")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"pin {pin[:12]} has no kit/MANIFEST.json") from exc
    remote = json.loads(raw.decode("utf-8"))
    files = remote.get("files", [])
    if not isinstance(files, list):
        raise SystemExit(f"pin {pin[:12]} kit/MANIFEST.json has no files list")
    return list(dict.fromkeys(["MANIFEST.json", *files]))


def check_sister(hub: Path) -> list[str]:
    errors: list[str] = []
    pin = PIN_PATH.read_text(encoding="utf-8").strip()
    if not pin:
        return ["PIN is empty"]
    try:
        subprocess.check_output(
            ["git", "-C", str(hub), "cat-file", "-e", f"{pin}^{{commit}}"],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        return [f"pin {pin} is not a commit in {hub}"]

    try:
        files = pinned_file_list(hub, pin)
    except SystemExit as exc:
        return [str(exc)]

    for rel in files:
        local = KIT_ROOT / rel
        if not local.is_file():
            errors.append(f"missing vendored kit/{rel}")
            continue
        try:
            remote = git_show(hub, pin, rel)
        except subprocess.CalledProcessError:
            errors.append(f"pin {pin[:12]} has no kit/{rel}")
            continue
        if sha256_file(local) != sha256_bytes(remote):
            errors.append(f"local edit or stale vendor: kit/{rel} != hub@{pin[:12]}")
    # PIN itself is sister-only and not compared to hub.
    return errors


def sister_sync(hub: Path) -> None:
    pin = PIN_PATH.read_text(encoding="utf-8").strip()
    if not pin:
        raise SystemExit("PIN is empty")
    for rel in pinned_file_list(hub, pin):
        data = git_show(hub, pin, rel)
        dest = KIT_ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print(f"synced kit/{rel} <- hub@{pin[:12]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="fail on drift / invariant breaks")
    ap.add_argument("--sync", action="store_true", help="refresh consumers or vendored kit")
    ap.add_argument("--hub-path", default=os.environ.get("SN_HUB_PATH", ""))
    args = ap.parse_args()
    if not args.check and not args.sync:
        args.sync = True

    if not MANIFEST_PATH.is_file():
        return fail("missing MANIFEST.json")
    manifest = load_manifest()

    sister = PIN_PATH.is_file()
    if sister:
        hub_path = Path(args.hub_path).expanduser() if args.hub_path else None
        if hub_path is None or not hub_path.is_dir():
            return fail("sister mode needs --hub-path or SN_HUB_PATH to the hub clone")
        if args.sync:
            sister_sync(hub_path)
        if args.check:
            errors = check_sister(hub_path) + check_invariants(manifest, hub=False)
            if errors:
                for err in errors:
                    print(f"FAIL kit sync: {err}", file=sys.stderr)
                return 1
            pin = PIN_PATH.read_text(encoding="utf-8").strip()
            return ok(f"vendored kit matches pin {pin[:12]}")
        return 0

    for rel in manifest["files"]:
        if not (KIT_ROOT / rel).is_file():
            return fail(f"manifest file missing: {rel}")

    if args.sync:
        hub_sync(manifest)
    if args.check:
        errors = check_invariants(manifest, hub=True) + check_hub_consumers(manifest)
        if errors:
            for err in errors:
                print(f"FAIL kit sync: {err}", file=sys.stderr)
            return 1
        return ok("hub kit source + consumers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
