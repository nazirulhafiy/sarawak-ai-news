#!/usr/bin/env python3
"""Shared production analytics loader (hub #36 / bantuan #83 pattern)."""

from __future__ import annotations

import json
from typing import Protocol

ANALYTICS_MAX_AGE = 31536000  # ~1 year
ANALYTICS_LOADER_ATTR = "data-sn-analytics-loader"


class AnalyticsRegistryView(Protocol):
    internal_cookie: str
    spa: bool

    @property
    def hostnames(self) -> tuple[str, ...]: ...

    @property
    def honour_cookies(self) -> tuple[str, ...]: ...

    def primary_ga4_id(self) -> str: ...

    def primary_cf_token(self) -> str: ...


def render_analytics_loader(registry: AnalyticsRegistryView) -> str:
    """Emit one production analytics loader from a site registry.

    - Host gate: primary host keys plus aliases (never localhost / preview).
    - ``?internal=1`` sets the registry ``internal_cookie`` (~1 year);
      ``?internal=0`` clears the primary and every listed legacy cookie name.
    - ``internal`` is true when the primary or any honour cookie is ``=1``.
    - GA4 always loads on production hosts; when ``internal``, config includes
      ``traffic_type: 'internal'``.
    - CF Web Analytics beacon loads only when not ``internal``, with ``spa``
      from the registry.
    """
    hosts_js = ",".join(json.dumps(h) for h in registry.hostnames)
    primary = json.dumps(registry.internal_cookie)
    honour = ",".join(json.dumps(c) for c in registry.honour_cookies)
    mid = json.dumps(registry.primary_ga4_id())
    token = json.dumps(registry.primary_cf_token())
    spa_js = "true" if registry.spa else "false"
    max_age = ANALYTICS_MAX_AGE
    return (
        f"<script {ANALYTICS_LOADER_ATTR}>(function(){{"
        f"var H=[{hosts_js}],h=location.hostname;"
        "if(H.indexOf(h)<0)return;"
        f"var C={primary},L=[{honour}],q=new URLSearchParams(location.search),"
        "sec=location.protocol==='https:'?';Secure':'';"
        "if(q.get('internal')==='1')"
        f"document.cookie=C+'=1;path=/;max-age={max_age};SameSite=Lax'+sec;"
        "else if(q.get('internal')==='0')"
        "L.forEach(function(n){document.cookie=n+'=;path=/;max-age=0;SameSite=Lax'+sec;});"
        "var internal=L.some(function(n){return document.cookie.split(';').some(function(p){"
        "return p.trim()===n+'=1';});});"
        "window.dataLayer=window.dataLayer||[];"
        "function gtag(){dataLayer.push(arguments);}"
        "window.gtag=gtag;"
        "gtag('js',new Date());"
        f"var id={mid},cfg={{}};"
        "if(internal)cfg.traffic_type='internal';"
        "gtag('config',id,cfg);"
        "var gs=document.createElement('script');gs.async=true;"
        "gs.src='https://www.googletagmanager.com/gtag/js?id='+encodeURIComponent(id);"
        "document.head.appendChild(gs);"
        "if(internal)return;"
        "var s=document.createElement('script');s.defer=true;"
        "s.src='https://static.cloudflareinsights.com/beacon.min.js';"
        f"s.setAttribute('data-cf-beacon',JSON.stringify({{token:{token},spa:{spa_js}}}));"
        "document.head.appendChild(s);"
        "})();</script>"
    )
