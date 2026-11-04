import unittest

from scripts.audit_summaries import (
    SUMMARY_EVIDENCE_REQUIRED_FROM,
    find_strategic_term_warnings,
    find_summary_issues,
)


GOOD_SUMMARY = (
    "Sarawak’s AI screening rollout gives the state a practical public-service "
    "use case for AI, focused on early childhood intervention across SeDidik centres."
)


def _item(**overrides):
    base = {
        "id": "x",
        "title": "Sarawak expands early intervention with AI screening",
        "date": "2026-10-01",
        "summary": GOOD_SUMMARY,
    }
    base.update(overrides)
    return base


class AuditSummariesTest(unittest.TestCase):
    def test_flags_generic_summary_and_bad_word_count(self):
        items = [{"id": "x", "title": "X", "summary": "This article discusses AI development in Sarawak."}]
        issues = find_summary_issues(items)
        self.assertTrue(any("generic" in issue.reason for issue in issues))
        self.assertTrue(any("word count" in issue.reason for issue in issues))

    def test_accepts_specific_strategic_signal(self):
        items = [_item()]
        self.assertEqual(find_summary_issues(items), [])

    def test_accepts_user_approved_short_strategic_signal(self):
        items = [{
            "id": "x",
            "title": "Sarawak explores AI Grid networks, satellite integration to power next-generation digital economy",
            "date": "2026-10-01",
            "summary": "Sarawak’s AI Grid and satellite exploration points to a more distributed infrastructure strategy beyond conventional data centres.",
        }]
        self.assertEqual(find_summary_issues(items), [])

    def test_flags_multiple_sentences_and_hype_words(self):
        items = [{
            "id": "x",
            "title": "X",
            "summary": "Sarawak is launching a groundbreaking AI programme for public services. It is game-changing for future growth.",
        }]
        issues = find_summary_issues(items)
        self.assertTrue(any("one sentence" in issue.reason for issue in issues))
        self.assertTrue(any("hype" in issue.reason for issue in issues))

    def test_missing_strategic_terms_is_warning_only(self):
        summary = (
            "SK Limbang’s TeachLA Bot SB-01 won bronze at a national student "
            "innovation contest for classroom teaching support."
        )
        items = [_item(summary=summary, date="2026-10-01")]
        self.assertEqual(find_summary_issues(items), [])
        warnings = find_strategic_term_warnings(items)
        self.assertEqual(len(warnings), 1)
        self.assertIn("advisory", warnings[0].reason)

    def test_new_item_missing_evidence_fails(self):
        items = [_item(date=SUMMARY_EVIDENCE_REQUIRED_FROM)]
        issues = find_summary_issues(items)
        self.assertTrue(any("summary_evidence required" in issue.reason for issue in issues))

    def test_new_item_with_one_to_three_quotes_passes(self):
        for quotes in (
            ["First source quote about the programme."],
            ["One.", "Two."],
            ["One.", "Two.", "Three."],
        ):
            with self.subTest(n=len(quotes)):
                items = [_item(
                    date=SUMMARY_EVIDENCE_REQUIRED_FROM,
                    summary_evidence=quotes,
                )]
                self.assertEqual(find_summary_issues(items), [])

    def test_new_item_with_more_than_three_or_empty_strings_fails(self):
        over = [_item(
            date=SUMMARY_EVIDENCE_REQUIRED_FROM,
            summary_evidence=["a", "b", "c", "d"],
        )]
        empty_list = [_item(
            date=SUMMARY_EVIDENCE_REQUIRED_FROM,
            summary_evidence=[],
        )]
        blank = [_item(
            date=SUMMARY_EVIDENCE_REQUIRED_FROM,
            summary_evidence=["ok", "  "],
        )]
        not_list = [_item(
            date=SUMMARY_EVIDENCE_REQUIRED_FROM,
            summary_evidence="just a string",
        )]
        self.assertTrue(any("at most 3" in i.reason for i in find_summary_issues(over)))
        self.assertTrue(any("empty list" in i.reason for i in find_summary_issues(empty_list)))
        self.assertTrue(any("non-empty string" in i.reason for i in find_summary_issues(blank)))
        self.assertTrue(any("must be a list" in i.reason for i in find_summary_issues(not_list)))

    def test_old_item_without_evidence_passes(self):
        items = [_item(date="2026-11-03")]
        self.assertLess("2026-11-03", SUMMARY_EVIDENCE_REQUIRED_FROM)
        self.assertEqual(find_summary_issues(items), [])
        self.assertNotIn("summary_evidence", items[0])


if __name__ == "__main__":
    unittest.main()
