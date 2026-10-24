#!/usr/bin/env python3
"""Shared header, footer, and back-to-top markup for sarawak.news sites."""

from __future__ import annotations

import html
import json
from collections.abc import Sequence
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

CONTACT_HREF = "mailto:contact@sarawak.news"
CONTACT_LABEL = "Contact"

FooterLayout = Literal["classic", "column_stacks"]

_FLEET_CROSS_LINKS_JSON = Path(__file__).resolve().parents[1] / "fleet-cross-links.json"


@lru_cache(maxsize=1)
def _fleet_cross_links_payload() -> dict:
    payload = json.loads(_FLEET_CROSS_LINKS_JSON.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fleet-cross-links.json must be an object")
    return payload


@lru_cache(maxsize=1)
def fleet_section_label() -> str:
    label = str(_fleet_cross_links_payload().get("section_label", "")).strip()
    if not label:
        raise ValueError("fleet-cross-links.json needs section_label")
    return label


@lru_cache(maxsize=1)
def _fleet_sites() -> tuple[tuple[str, str, str], ...]:
    sites = _fleet_cross_links_payload().get("sites")
    if not isinstance(sites, list):
        raise ValueError("fleet-cross-links.json must contain a sites array")
    out: list[tuple[str, str, str]] = []
    for entry in sites:
        if not isinstance(entry, dict):
            raise ValueError("fleet-cross-links.json sites entries must be objects")
        site_id = str(entry.get("id", "")).strip()
        href = str(entry.get("href", "")).strip()
        label = str(entry.get("label", "")).strip()
        if not site_id or not href or not label:
            raise ValueError("fleet-cross-links.json entries need id, href, and label")
        out.append((site_id, href, label))
    return tuple(out)


def fleet_cross_link_items(fleet_site: str) -> tuple[NavItem, ...]:
    """Footer sister-site links for the given fleet id (hub, ai, events, bantuan)."""
    return tuple(
        NavItem(site_id, href, label)
        for site_id, href, label in _fleet_sites()
        if site_id != fleet_site
    )

# Forced mid-note line break (AI.Sarawak.News footer). Sites opt in via brand_note_parts.
FOOTER_NOTE_BREAK = '<br class="site-footer-note-break" />'

THEME_TOGGLE_SVG = """<svg class="theme-icon-morph" aria-hidden="true" width="18" height="18" viewBox="0 0 24 24">
        <mask id="theme-toggle-moon-mask"><rect width="24" height="24" fill="#fff"></rect><circle cx="17" cy="7" r="7" fill="#000"></circle></mask>
        <circle class="theme-icon-moon" cx="12" cy="12" r="9" mask="url(#theme-toggle-moon-mask)"></circle>
        <circle class="theme-icon-sun" cx="12" cy="12" r="5"></circle>
        <g class="theme-icon-rays">
          <line x1="12" y1="1.6" x2="12" y2="3.8"></line><line x1="12" y1="20.2" x2="12" y2="22.4"></line>
          <line x1="1.6" y1="12" x2="3.8" y2="12"></line><line x1="20.2" y1="12" x2="22.4" y2="12"></line>
          <line x1="4.6" y1="4.6" x2="6.2" y2="6.2"></line><line x1="17.8" y1="17.8" x2="19.4" y2="19.4"></line>
          <line x1="4.6" y1="19.4" x2="6.2" y2="17.8"></line><line x1="17.8" y1="6.2" x2="19.4" y2="4.6"></line>
        </g>
      </svg>"""


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


@dataclass(frozen=True)
class NavItem:
    id: str
    href: str
    label: str


def render_back_to_top() -> str:
    return (
        '  <button class="back-to-top" type="button" data-back-to-top '
        'aria-label="Back to top" hidden>'
        '<span class="back-to-top-label">Back to top</span> '
        '<span class="back-to-top-arrow" aria-hidden="true">↑</span></button>'
    )


def render_header(
    *,
    brand_title: str,
    brand_href: str,
    active: str,
    nav_items: list[NavItem] | tuple[NavItem, ...],
    mark_dir: str = "icons",
) -> str:
    def link(item: NavItem) -> str:
        current = ' aria-current="page"' if active == item.id else ""
        klass = "site-nav-link is-active" if active == item.id else "site-nav-link"
        return f'<a class="{klass}" href="{esc(item.href)}"{current}>{esc(item.label)}</a>'

    nav = "\n      ".join(link(item) for item in nav_items)
    light = f"{mark_dir}/nav-mark-transparent.svg"
    dark = f"{mark_dir}/nav-mark-transparent-dark.svg"
    return f"""  <header class="bar">
    <div class="bar-inner">
    <span class="brand-lockup"><a class="brand" href="{esc(brand_href)}"><img class="brand-mark brand-mark-light" src="{esc(light)}" alt="" width="220" height="220" decoding="async" aria-hidden="true" /><img class="brand-mark brand-mark-dark" src="{esc(dark)}" alt="" width="220" height="220" decoding="async" aria-hidden="true" /><span class="brand-text">{esc(brand_title)}</span></a></span>
    <nav class="site-nav" id="primary-navigation" aria-label="Primary">
      {nav}
    </nav>
    <span class="bar-rule-tail" aria-hidden="true"></span>
    <button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="primary-navigation" aria-label="Open navigation" title="Open navigation">
      <span></span><span></span><span></span>
    </button>
    <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark mode" title="Switch to dark mode">
      {THEME_TOGGLE_SVG}
    </button>
    </div>
  </header>"""


def format_footer_note(
    brand_note: str = "",
    brand_note_parts: Sequence[str] | None = None,
) -> str:
    """Escape footer note text. With ``brand_note_parts``, join using FOOTER_NOTE_BREAK."""
    if brand_note_parts is not None:
        parts = [part.strip() for part in brand_note_parts if str(part).strip()]
        if len(parts) < 2:
            raise ValueError("brand_note_parts needs at least two non-empty strings")
        return FOOTER_NOTE_BREAK.join(esc(part) for part in parts)
    return esc(brand_note)


def _footer_explore_items(
    explore_items: list[NavItem] | tuple[NavItem, ...],
) -> list[NavItem]:
    items = list(explore_items)
    if not any(item.href == CONTACT_HREF for item in items):
        items.append(NavItem("contact", CONTACT_HREF, CONTACT_LABEL))
    return items


def _footer_link(item: NavItem, active: str) -> str:
    current = ' aria-current="page"' if active == item.id else ""
    return (
        f'<li><a class="site-footer-link" href="{esc(item.href)}"{current}>'
        f"{esc(item.label)}</a></li>"
    )


def _footer_fleet_nav_html(
    fleet_site: str,
    active: str,
    *,
    section_label_override: str | None,
) -> str:
    fleet_items = fleet_cross_link_items(fleet_site)
    fleet_links = "\n          ".join(_footer_link(item, active) for item in fleet_items)
    label = (
        section_label_override.strip()
        if section_label_override is not None
        else fleet_section_label()
    )
    section = esc(label)
    return f"""
        <nav aria-label="{section}" class="site-footer-fleet-nav">
          <h2>{section}</h2>
          <ul>
            {fleet_links}
          </ul>
        </nav>"""


def _render_footer_classic(
    *,
    brand_title: str,
    note_html: str,
    active: str,
    explore_items: list[NavItem],
    fleet_in_summary: str,
    credit_html: str,
) -> str:
    explore = "\n          ".join(_footer_link(item, active) for item in explore_items)
    return f"""  <footer class="site-footer">
    <div class="site-footer-main">
      <div class="site-footer-summary">
        <p class="site-footer-brand">{esc(brand_title)}</p>
        <p class="site-footer-note">{note_html}</p>{fleet_in_summary}
      </div>
      <nav aria-label="Explore" class="site-footer-nav">
        <h2>Explore</h2>
        <ul>
          {explore}
        </ul>
      </nav>
    </div>
    <div class="site-footer-bottom">
      <p>{credit_html}</p>
    </div>
  </footer>"""


def _render_footer_column_stacks(
    *,
    brand_title: str,
    note_html: str,
    active: str,
    explore_items: list[NavItem],
    fleet_html: str,
    extra_nav_right: str | None,
    credit_html: str,
) -> str:
    explore = "\n          ".join(_footer_link(item, active) for item in explore_items)
    right_tail = ""
    if extra_nav_right:
        right_tail = f"""
        <hr class="site-footer-grid-explore-divider" />
        <div class="site-footer-categories site-footer-grid-categories">
          {extra_nav_right}
        </div>"""
    fleet_block = ""
    if fleet_html.strip():
        fleet_block = f"""
        <div class="site-footer-grid-fleet">
          {fleet_html.strip()}
        </div>"""
    return f"""  <footer class="site-footer">
    <div class="site-footer-main site-footer-main--column-stacks">
      <div class="site-footer-grid-stack site-footer-grid-stack-left">
        <div class="site-footer-summary site-footer-grid-brand-cell">
          <div class="site-footer-grid-brand">
            <p class="site-footer-brand">{esc(brand_title)}</p>
            <p class="site-footer-note">{note_html}</p>
          </div>
        </div>{fleet_block}
      </div>
      <div class="site-footer-grid-stack site-footer-grid-stack-right">
        <nav aria-label="Explore" class="site-footer-nav site-footer-grid-explore">
          <h2>Explore</h2>
          <ul>
            {explore}
          </ul>
        </nav>{right_tail}
      </div>
    </div>
    <div class="site-footer-bottom">
      <p>{credit_html}</p>
    </div>
  </footer>"""


def render_footer(
    *,
    brand_title: str,
    brand_note: str = "",
    active: str,
    explore_items: list[NavItem] | tuple[NavItem, ...],
    brand_note_parts: Sequence[str] | None = None,
    credit_html: str | None = None,
    fleet_site: str | None = None,
    layout: FooterLayout = "classic",
    fleet_section_label: str | None = None,
    extra_nav_right: str | None = None,
) -> str:
    """Render the shared footer. Contact is always the last Explore link.

    Pass ``brand_note`` for a single escaped paragraph (hub, bantuan, events).
    Pass ``brand_note_parts`` (two or more strings) to insert
    ``<br class="site-footer-note-break" />`` between escaped sentences (AI).
    Pass ``fleet_site`` (hub, ai, events, or bantuan) to emit sister-site
    links (label from ``fleet-cross-links.json`` unless ``fleet_section_label``
    overrides the heading and ``aria-label`` only).
    Pass ``layout="column_stacks"`` for Events-style independent column stacks
    (fleet block in the left stack, optional ``extra_nav_right`` HTML for a
    Categories block after Explore and a full-width ``<hr>`` divider).
    """
    if layout not in ("classic", "column_stacks"):
        raise ValueError('layout must be "classic" or "column_stacks"')
    if layout == "column_stacks" and extra_nav_right is not None and not extra_nav_right.strip():
        raise ValueError("extra_nav_right must be omitted or non-empty HTML")

    items = _footer_explore_items(explore_items)
    note_html = format_footer_note(brand_note, brand_note_parts)
    if credit_html is None:
        credit_html = (
            'Built by <a class="site-footer-link site-footer-credit-link" '
            'href="https://hafiy.my">hafiy.my</a>, an independent publication. '
            "Not affiliated with the Sarawak Government."
        )

    fleet_in_summary = ""
    fleet_column_html = ""
    if fleet_site is not None:
        fleet_nav = _footer_fleet_nav_html(
            fleet_site,
            active,
            section_label_override=fleet_section_label,
        )
        if layout == "classic":
            fleet_in_summary = fleet_nav
        else:
            fleet_column_html = fleet_nav

    if layout == "column_stacks":
        return _render_footer_column_stacks(
            brand_title=brand_title,
            note_html=note_html,
            active=active,
            explore_items=items,
            fleet_html=fleet_column_html,
            extra_nav_right=extra_nav_right,
            credit_html=credit_html,
        )
    return _render_footer_classic(
        brand_title=brand_title,
        note_html=note_html,
        active=active,
        explore_items=items,
        fleet_in_summary=fleet_in_summary,
        credit_html=credit_html,
    )
