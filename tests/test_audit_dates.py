import unittest

from scripts.audit_dates import (
    DateFetchError,
    audit_items,
    changed_items,
    extract_published_date,
    find_date_mismatches,
    select_items,
)


class AuditDatesTest(unittest.TestCase):
    def test_extracts_article_published_time_before_visible_header_dates(self):
        html = '''
        <html><head>
          <meta property="article:published_time" content="2025-11-12T19:09:48+08:00" />
        </head><body>
          <header>Sunday, 28 June, 2026</header>
          <h1>AI to transform Sarawak's economy</h1>
          <li>12 November 2025</li>
        </body></html>
        '''
        self.assertEqual(extract_published_date(html), "2025-11-12")

    def test_extracts_json_ld_date_published(self):
        html = '''
        <script type="application/ld+json">
        {"@type":"NewsArticle","datePublished":"2026-05-06T10:31:03+08:00"}
        </script>
        '''
        self.assertEqual(extract_published_date(html), "2026-05-06")

    def test_normalizes_utc_metadata_to_malaysia_publication_date(self):
        html = '<meta property="article:published_time" content="2026-03-31T16:27:26+00:00">'
        self.assertEqual(extract_published_date(html), "2026-04-01")

    def test_reports_feed_date_mismatch(self):
        items = [
            {"title": "Wrong", "url": "https://example.test/wrong", "date": "2026-06-28"},
            {"title": "Right", "url": "https://example.test/right", "date": "2026-05-20"},
        ]
        html_by_url = {
            "https://example.test/wrong": '<meta property="article:published_time" content="2026-05-06T10:31:03+08:00">',
            "https://example.test/right": '<meta property="article:published_time" content="2026-05-20T19:06:14+08:00">',
        }
        mismatches, unavailable = find_date_mismatches(items, lambda url: html_by_url[url])
        self.assertEqual(unavailable, [])
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0].expected, "2026-05-06")
        self.assertEqual(mismatches[0].actual, "2026-06-28")

    def test_treats_fetch_errors_as_unavailable_not_mismatch(self):
        items = [{"title": "Unavailable", "url": "https://example.test/down", "date": "2026-06-28"}]
        mismatches, unavailable = find_date_mismatches(
            items,
            lambda url: (_ for _ in ()).throw(DateFetchError(url, "HTTP 500")),
        )
        self.assertEqual(mismatches, [])
        self.assertEqual(len(unavailable), 1)
        self.assertEqual(unavailable[0].reason, "HTTP 500")

    def test_selects_only_requested_item_ids(self):
        items = [
            {"id": "old", "title": "Old", "url": "https://example.test/old", "date": "2026-07-01"},
            {"id": "new", "title": "New", "url": "https://example.test/new", "date": "2026-07-12"},
        ]
        self.assertEqual([item["id"] for item in select_items(items, ["new"])], ["new"])
        with self.assertRaisesRegex(ValueError, "Unknown item id"):
            select_items(items, ["missing"])

    def test_changed_items_include_only_new_or_date_relevant_edits(self):
        baseline = [
            {"id": "same", "title": "Same", "url": "https://example.test/same", "date": "2026-07-01", "summary": "Before"},
            {"id": "edited", "title": "Before", "url": "https://example.test/edited", "date": "2026-07-02"},
        ]
        current = [
            {"id": "same", "title": "Same", "url": "https://example.test/same", "date": "2026-07-01", "summary": "After"},
            {"id": "edited", "title": "After", "url": "https://example.test/edited", "date": "2026-07-02"},
            {"id": "new", "title": "New", "url": "https://example.test/new", "date": "2026-07-12"},
        ]
        self.assertEqual([item["id"] for item in changed_items(current, baseline)], ["edited", "new"])

    def test_incremental_audit_fetches_only_selected_items(self):
        items = [
            {"id": "new", "title": "New", "url": "https://example.test/new", "date": "2026-07-12"},
        ]
        fetched = []

        def load_html(url):
            fetched.append(url)
            return '<meta property="article:published_time" content="2026-07-12T06:01:00+08:00">'

        self.assertEqual(audit_items(items, load_html), 0)
        self.assertEqual(fetched, ["https://example.test/new"])


if __name__ == "__main__":
    unittest.main()
