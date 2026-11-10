import unittest

from scripts.audit_summaries import (
    SUMMARY_EVIDENCE_REQUIRED_FROM,
    find_strategic_term_warnings,
    find_summary_issues,
    sentence_count,
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

    def test_sentence_count_keeps_decimals_as_one_sentence(self):
        self.assertEqual(sentence_count("The stake is valued near 1.85 after the round."), 1)
        self.assertEqual(
            sentence_count(
                "SoftBank’s US$1.85 billion seed into Grab and Petros signals a larger "
                "regional AI infrastructure bet tied to Sarawak energy assets."
            ),
            1,
        )
        self.assertEqual(
            sentence_count(
                "The RM2.4bil facility expands compute capacity for public-sector AI "
                "workloads across Sarawak’s digital-economy roadmap this year."
            ),
            1,
        )
        self.assertEqual(
            sentence_count(
                "Uptake rose 3.5% after the statewide AI screening rollout gave clinics "
                "a clearer early-intervention pathway for children."
            ),
            1,
        )

    def test_sentence_count_keeps_abbreviation_periods_as_one_sentence(self):
        self.assertEqual(
            sentence_count(
                "Sarawak Digitech Sdn. Bhd. and Acme Corp. will pilot Dr. Lee’s AI "
                "tool for public-service case triage across two agencies."
            ),
            1,
        )
        self.assertEqual(
            sentence_count(
                "The brief cites, e.g., PCDS talent programmes and, i.e., workforce "
                "pathways that position Sarawak for regional AI adoption."
            ),
            1,
        )

    def test_decimal_and_currency_summaries_pass_audit(self):
        for summary in (
            (
                "SoftBank’s US$1.85 billion seed into Grab and Petros signals a larger "
                "regional AI infrastructure bet tied to Sarawak energy assets."
            ),
            (
                "The RM2.4bil facility expands compute capacity for public-sector AI "
                "workloads across Sarawak’s digital-economy roadmap this year."
            ),
            (
                "Uptake rose 3.5% after the statewide AI screening rollout gave clinics "
                "a clearer early-intervention pathway for children."
            ),
        ):
            with self.subTest(summary=summary[:32]):
                self.assertEqual(find_summary_issues([_item(summary=summary)]), [])

    def test_real_two_sentence_summary_still_fails(self):
        summary = (
            "SoftBank’s US$1.85 billion seed into Grab and Petros signals a larger "
            "regional AI infrastructure bet. The deal also frames Sarawak energy "
            "assets as part of that compute push."
        )
        self.assertEqual(sentence_count(summary), 2)
        issues = find_summary_issues([_item(summary=summary)])
        self.assertTrue(any("one sentence" in issue.reason for issue in issues))

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
