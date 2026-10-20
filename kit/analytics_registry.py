#!/usr/bin/env python3
"""Load and validate data/analytics.json (shared kit registry shape)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

KIT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = KIT_ROOT.parent
ROOT = REPO_ROOT
ANALYTICS_PATH = ROOT / "data" / "analytics.json"

GA4_ID_RE = re.compile(r"^G-[A-Z0-9]+$")
CF_TOKEN_RE = re.compile(r"^[a-f0-9]{32}$")
HOST_RE = re.compile(r"^[a-z0-9.-]+$")
COOKIE_RE = re.compile(r"^[A-Za-z0-9_-]+$")

TOP_LEVEL_KEYS = frozenset({"version", "internal_cookie", "spa", "hosts"})
HOST_ENTRY_KEYS = frozenset(
    {"ga4_measurement_id", "cf_beacon_token", "aliases", "legacy_internal_cookies"}
)


class HostEntry:
    """One primary host and its aliases / tokens."""

    def __init__(
        self,
        *,
        primary: str,
        ga4_measurement_id: str,
        cf_beacon_token: str,
        aliases: list[str],
        legacy_internal_cookies: list[str],
    ) -> None:
        self.primary = primary
        self.ga4_measurement_id = ga4_measurement_id
        self.cf_beacon_token = cf_beacon_token
        self.aliases = aliases
        self.legacy_internal_cookies = legacy_internal_cookies

    @property
    def hostnames(self) -> tuple[str, ...]:
        return (self.primary, *self.aliases)


class AnalyticsRegistry:
    """Typed view of the analytics registry (kit shape v1)."""

    def __init__(
        self,
        *,
        version: int,
        internal_cookie: str,
        spa: bool,
        hosts: dict[str, HostEntry],
    ) -> None:
        self.version = version
        self.internal_cookie = internal_cookie
        self.spa = spa
        self.hosts = hosts

    @property
    def hostnames(self) -> tuple[str, ...]:
        """Primary host keys plus every alias (deduped, primary-first order)."""
        seen: list[str] = []
        for entry in self.hosts.values():
            for name in entry.hostnames:
                if name not in seen:
                    seen.append(name)
        return tuple(seen)

    @property
    def legacy_internal_cookies(self) -> list[str]:
        """Union of per-host legacy cookie lists (order preserved, deduped)."""
        seen: list[str] = []
        for entry in self.hosts.values():
            for name in entry.legacy_internal_cookies:
                if name not in seen:
                    seen.append(name)
        return seen

    @property
    def honour_cookies(self) -> tuple[str, ...]:
        """Primary internal_cookie plus unique per-host legacy names."""
        seen: list[str] = []
        for name in (self.internal_cookie, *self.legacy_internal_cookies):
            if name not in seen:
                seen.append(name)
        return tuple(seen)

    def ga4_ids(self) -> set[str]:
        return {entry.ga4_measurement_id for entry in self.hosts.values()}

    def cf_tokens(self) -> set[str]:
        return {entry.cf_beacon_token for entry in self.hosts.values()}

    def primary_ga4_id(self) -> str:
        ids = sorted(self.ga4_ids())
        if len(ids) != 1:
            raise SystemExit(
                "analytics registry expects one GA4 measurement id across hosts for this "
                f"site build, got {ids!r}"
            )
        return ids[0]

    def primary_cf_token(self) -> str:
        tokens = sorted(self.cf_tokens())
        if len(tokens) != 1:
            raise SystemExit(
                "analytics registry expects one CF beacon token across hosts for this site "
                f"build, got {tokens!r}"
            )
        return tokens[0]


def _require_str(obj: dict[str, Any], key: str, *, path: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{path}: {key} must be a non-empty string")
    return value.strip()


def _require_str_list(obj: dict[str, Any], key: str, *, path: str) -> list[str]:
    raw = obj.get(key)
    if not isinstance(raw, list):
        raise SystemExit(f"{path}: {key} must be an array of strings")
    out: list[str] = []
    for i, item in enumerate(raw):
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(f"{path}: {key}[{i}] must be a non-empty string")
        out.append(item.strip())
    return out


def validate_analytics_payload(payload: Any, *, path: str = "data/analytics.json") -> AnalyticsRegistry:
    """Validate kit-aligned registry shape (version 1)."""
    if not isinstance(payload, dict):
        raise SystemExit(f"{path} must be a JSON object")

    unknown = set(payload) - TOP_LEVEL_KEYS
    if unknown:
        raise SystemExit(f"{path}: unknown keys: {sorted(unknown)}")
    missing = TOP_LEVEL_KEYS - set(payload)
    if missing:
        raise SystemExit(f"{path}: missing keys: {sorted(missing)}")

    version = payload["version"]
    if version != 1:
        raise SystemExit(f"{path}: version must be 1, got {version!r}")

    internal_cookie = _require_str(payload, "internal_cookie", path=path)
    if not COOKIE_RE.fullmatch(internal_cookie):
        raise SystemExit(f"{path}: internal_cookie has invalid characters: {internal_cookie!r}")

    spa = payload.get("spa")
    if not isinstance(spa, bool):
        raise SystemExit(f"{path}: spa must be a boolean")

    hosts_raw = payload.get("hosts")
    if not isinstance(hosts_raw, dict) or not hosts_raw:
        raise SystemExit(f"{path}: hosts must be a non-empty object keyed by hostname")

    hosts: dict[str, HostEntry] = {}
    seen_names: set[str] = set()
    for host, entry in hosts_raw.items():
        if not isinstance(host, str) or not HOST_RE.fullmatch(host):
            raise SystemExit(f"{path}: invalid host key {host!r}")
        if host in seen_names:
            raise SystemExit(f"{path}: duplicate hostname {host!r}")
        seen_names.add(host)
        if not isinstance(entry, dict):
            raise SystemExit(f"{path}: hosts[{host!r}] must be an object")
        entry_path = f"{path}.hosts[{host!r}]"
        entry_unknown = set(entry) - HOST_ENTRY_KEYS
        if entry_unknown:
            raise SystemExit(f"{entry_path}: unknown keys: {sorted(entry_unknown)}")
        entry_missing = HOST_ENTRY_KEYS - set(entry)
        if entry_missing:
            raise SystemExit(f"{entry_path}: missing keys: {sorted(entry_missing)}")

        ga4_id = _require_str(entry, "ga4_measurement_id", path=entry_path)
        if not GA4_ID_RE.fullmatch(ga4_id):
            raise SystemExit(f"{entry_path}: ga4_measurement_id invalid: {ga4_id!r}")
        token = _require_str(entry, "cf_beacon_token", path=entry_path)
        if not CF_TOKEN_RE.fullmatch(token):
            raise SystemExit(f"{entry_path}: cf_beacon_token invalid: {token!r}")

        aliases = _require_str_list(entry, "aliases", path=entry_path)
        for i, alias in enumerate(aliases):
            if not HOST_RE.fullmatch(alias):
                raise SystemExit(f"{entry_path}: aliases[{i}] invalid: {alias!r}")
            if alias == host:
                raise SystemExit(f"{entry_path}: aliases must not repeat the primary host")
            if alias in seen_names:
                raise SystemExit(f"{entry_path}: duplicate hostname via aliases: {alias!r}")
            seen_names.add(alias)

        legacy = _require_str_list(entry, "legacy_internal_cookies", path=entry_path)
        for i, name in enumerate(legacy):
            if not COOKIE_RE.fullmatch(name):
                raise SystemExit(
                    f"{entry_path}: legacy_internal_cookies[{i}] has invalid characters: {name!r}"
                )

        hosts[host] = HostEntry(
            primary=host,
            ga4_measurement_id=ga4_id,
            cf_beacon_token=token,
            aliases=aliases,
            legacy_internal_cookies=legacy,
        )

    return AnalyticsRegistry(
        version=version,
        internal_cookie=internal_cookie,
        spa=spa,
        hosts=hosts,
    )


def load_analytics(path: Path = ANALYTICS_PATH) -> AnalyticsRegistry:
    if not path.is_file():
        raise SystemExit(f"missing analytics registry: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON: {exc}") from exc
    rel = str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    return validate_analytics_payload(payload, path=rel)
