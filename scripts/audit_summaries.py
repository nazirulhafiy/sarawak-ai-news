from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "items.json"

# Items with item["date"] on or after this day must include summary_evidence.
# Set to the PR merge date; do not backfill older rows.
SUMMARY_EVIDENCE_REQUIRED_FROM = "2026-11-04"

GENERIC_PHRASES = [
    "this article discusses",
    "this article says",
    "the article discusses",
    "the article says",
    "ai development in sarawak",
    "improving digital transformation",
    "working with partners on technology",
    "supports innovation and future growth",
    "highlighted the importance of ai",
]

HYPE_WORDS = [
    "revolutionary",
    "groundbreaking",
    "game-changing",
    "cutting-edge",
    "world-class",
]

STRATEGIC_TERMS = [
    "signalling",
    "signals",
    "signal",
    "positioning",
    "position itself",
    "positions",
    "frames",
    "linking",
    "moving",
    "shifting",
    "gives",
    "rollout",
    "roadmap",
    "adoption",
    "capability",
    "infrastructure",
    "public-service",
    "public-sector",
    "talent",
    "workforce",
    "pcds",
    "digital-economy",
    "regional ai",
]


@dataclass(frozen=True)
class SummaryIssue:
    item_id: str
    reason: str


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w’'-]+\b", text))


# Periods in these tokens are not sentence ends (Bhd., Sdn., Corp., Dr., e.g., i.e.).
_ABBREVIATION_PERIOD = re.compile(
    r"\b(?:Bhd|Sdn|Corp|Dr|Mr|Mrs|Ms|Prof|Inc|Ltd|vs|etc|e\.g|i\.e)\.",
    re.IGNORECASE,
)
_DECIMAL_PERIOD = re.compile(r"(?<=\d)\.(?=\d)")
_PERIOD_PLACEHOLDER = "\0"


def _protect_non_sentence_periods(text: str) -> str:
    """Replace decimal and common abbreviation periods so they are not split points."""
    protected = _DECIMAL_PERIOD.sub(_PERIOD_PLACEHOLDER, text)
    chars = list(protected)
    for match in _ABBREVIATION_PERIOD.finditer(protected):
        for index in range(match.start(), match.end()):
            if chars[index] == ".":
                chars[index] = _PERIOD_PLACEHOLDER
    return "".join(chars)


def sentence_count(text: str) -> int:
    """Count sentences; decimal and common abbreviation periods are not boundaries."""
    stripped = text.strip()
    if not stripped:
        return 0
    protected = _protect_non_sentence_periods(stripped)
    return len([part for part in re.split(r"[.!?]+\s*", protected) if part])


def requires_summary_evidence(item: dict) -> bool:
    """True when item date is on/after SUMMARY_EVIDENCE_REQUIRED_FROM."""
    date = str(item.get("date") or "").strip()
    return bool(date) and date >= SUMMARY_EVIDENCE_REQUIRED_FROM


def validate_summary_evidence(item: dict) -> str | None:
    """Return a failure reason if summary_evidence is invalid for a post-cutoff item."""
    if not requires_summary_evidence(item):
        return None
    evidence = item.get("summary_evidence", None)
    if evidence is None:
        return (
            f"summary_evidence required for items dated on or after "
            f"{SUMMARY_EVIDENCE_REQUIRED_FROM}"
        )
    if not isinstance(evidence, list):
        return "summary_evidence must be a list of 1-3 non-empty strings"
    if not evidence:
        return "summary_evidence must contain 1-3 non-empty strings (got empty list)"
    if len(evidence) > 3:
        return f"summary_evidence must contain at most 3 quotes (got {len(evidence)})"
    for index, quote in enumerate(evidence):
        if not isinstance(quote, str) or not quote.strip():
            return (
                f"summary_evidence[{index}] must be a non-empty string"
            )
    return None


def find_strategic_term_warnings(items: Iterable[dict]) -> list[SummaryIssue]:
    """Advisory only: missing STRATEGIC_TERMS never fails the audit."""
    warnings: list[SummaryIssue] = []
    for item in items:
        item_id = str(item.get("id", item.get("title", "unknown")))
        summary = str(item.get("summary", "")).strip()
        lowered = summary.lower()
        if not any(term in lowered for term in STRATEGIC_TERMS):
            warnings.append(
                SummaryIssue(item_id, "missing clear strategic signal term (advisory)")
            )
    return warnings


def find_summary_issues(items: Iterable[dict]) -> list[SummaryIssue]:
    issues: list[SummaryIssue] = []
    for item in items:
        item_id = str(item.get("id", item.get("title", "unknown")))
        summary = str(item.get("summary", "")).strip()
        lowered = summary.lower()
        words = word_count(summary)
        if not 14 <= words <= 38:
            issues.append(SummaryIssue(item_id, f"word count {words} outside 14-38"))
        if sentence_count(summary) != 1:
            issues.append(SummaryIssue(item_id, "summary must be one sentence"))
        if any(phrase in lowered for phrase in GENERIC_PHRASES):
            issues.append(SummaryIssue(item_id, "generic wording detected"))
        if any(word in lowered for word in HYPE_WORDS):
            issues.append(SummaryIssue(item_id, "hype wording detected"))
        if summary.startswith(("This article", "The article")):
            issues.append(SummaryIssue(item_id, "do not start with article framing"))
        evidence_reason = validate_summary_evidence(item)
        if evidence_reason:
            issues.append(SummaryIssue(item_id, evidence_reason))
    return issues


def load_items(path: Path = DATA) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def audit(path: Path = DATA) -> int:
    items = load_items(path)
    issues = find_summary_issues(items)
    warnings = find_strategic_term_warnings(items)
    for warning in warnings:
        print(f"Warning: {warning.item_id}: {warning.reason}")
    if not issues:
        print(f"Summary audit passed for {len(items)} items")
        if warnings:
            print(f"({len(warnings)} strategic-term advisory warning(s))")
        return 0
    print("Summary audit failed:", file=sys.stderr)
    for issue in issues:
        print(f"- {issue.item_id}: {issue.reason}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify one-line Sarawak.News strategic article signals.")
    parser.add_argument("--items", type=Path, default=DATA, help="Path to items.json")
    args = parser.parse_args()
    return audit(args.items)


if __name__ == "__main__":
    raise SystemExit(main())
