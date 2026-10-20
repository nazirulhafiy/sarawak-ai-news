#!/usr/bin/env python3
"""Tests for data/analytics.json validation and dist check."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


analytics_registry = _load_module("analytics_registry", "scripts/analytics_registry.py")
check_analytics_dist = _load_module("check_analytics_dist", "scripts/check_analytics_dist.py")
build = _load_module("build", "scripts/build.py")


class AnalyticsRegistryTests(unittest.TestCase):
    def test_load_repo_registry(self):
        reg = analytics_registry.load_analytics()
        self.assertEqual(reg.version, 1)
        self.assertEqual(reg.internal_cookie, "sn_internal")
        self.assertIs(reg.spa, True)
        self.assertEqual(list(reg.hosts), ["ai.sarawak.news"])
        entry = reg.hosts["ai.sarawak.news"]
        self.assertEqual(entry.ga4_measurement_id, "G-RJ2ZFQ52J7")
        self.assertEqual(entry.cf_beacon_token, "092a061973fc4d899cd2e4b52952af89")
        self.assertEqual(entry.aliases, ["www.ai.sarawak.news"])
        self.assertEqual(entry.legacy_internal_cookies, ["sn_internal"])
        self.assertEqual(reg.primary_ga4_id(), "G-RJ2ZFQ52J7")
        self.assertEqual(reg.primary_cf_token(), "092a061973fc4d899cd2e4b52952af89")
        self.assertEqual(reg.hostnames, ("ai.sarawak.news", "www.ai.sarawak.news"))
        self.assertEqual(reg.honour_cookies, ("sn_internal",))
        self.assertEqual(reg.legacy_internal_cookies, ["sn_internal"])

    def test_rejects_bad_ga4(self):
        payload = {
            "version": 1,
            "internal_cookie": "sn_internal",
            "spa": True,
            "hosts": {
                "ai.sarawak.news": {
                    "ga4_measurement_id": "not-a-id",
                    "cf_beacon_token": "092a061973fc4d899cd2e4b52952af89",
                    "aliases": [],
                    "legacy_internal_cookies": [],
                }
            },
        }
        with self.assertRaises(SystemExit):
            analytics_registry.validate_analytics_payload(payload)

    def test_rejects_top_level_legacy_cookies(self):
        payload = {
            "version": 1,
            "internal_cookie": "sn_internal",
            "spa": True,
            "legacy_cookies": ["sn_internal"],
            "hosts": {
                "ai.sarawak.news": {
                    "ga4_measurement_id": "G-RJ2ZFQ52J7",
                    "cf_beacon_token": "092a061973fc4d899cd2e4b52952af89",
                    "aliases": ["www.ai.sarawak.news"],
                    "legacy_internal_cookies": ["sn_internal"],
                }
            },
        }
        with self.assertRaises(SystemExit):
            analytics_registry.validate_analytics_payload(payload)


class AnalyticsDistCheckTests(unittest.TestCase):
    def test_built_dist_passes(self):
        import subprocess
        import sys

        subprocess.run(
            [sys.executable, "scripts/build.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        self.assertEqual(check_analytics_dist.main(["--dist", str(ROOT / "dist")]), 0)

    def test_zero_loaders_fails_and_names_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            (dist / "index.html").write_text("<html><head></head></html>", encoding="utf-8")
            code = check_analytics_dist.main(["--dist", str(dist)])
            self.assertEqual(code, 1)

    def test_spa_false_drift_fails(self):
        reg = analytics_registry.load_analytics()
        loader = build.render_analytics_loader(reg).replace("spa:true", "spa:false")
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            (dist / "index.html").write_text(
                f"<html><head>{loader}</head></html>", encoding="utf-8"
            )
            errors = check_analytics_dist.check_page(dist / "index.html", reg)
            self.assertTrue(
                any("spa:true" in e or "spa is true" in e for e in errors), errors
            )

    def test_foreign_cookie_fails(self):
        reg = analytics_registry.load_analytics()
        bad = build.render_analytics_loader(reg).replace("sn_internal", "ga_internal")
        with tempfile.TemporaryDirectory() as tmp:
            dist = Path(tmp)
            (dist / "about.html").write_text(
                f"<html><head>{bad}</head></html>", encoding="utf-8"
            )
            errors = check_analytics_dist.check_page(dist / "about.html", reg)
            self.assertTrue(any("ga_internal" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
