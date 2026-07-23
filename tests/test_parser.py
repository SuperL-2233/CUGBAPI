import unittest
from pathlib import Path

from cugb_jwc_api.parser import NoticeParseError, parse_notices


class ParserTests(unittest.TestCase):
    def test_parses_notice_fields_and_resolves_relative_url(self):
        html = Path("tests/fixtures/list.html").read_text(encoding="utf-8")
        notices = parse_notices(html, "https://jwc.cugb.edu.cn/xszq/")

        self.assertEqual(2, len(notices))
        self.assertEqual("第二条 & 测试通知", notices[0].title)
        self.assertEqual("2026-07-23", notices[0].published_date)
        self.assertEqual(
            "https://jwc.cugb.edu.cn/c/2026-07-23/100002.shtml", notices[0].url
        )

    def test_rejects_page_without_notice_list(self):
        with self.assertRaises(NoticeParseError):
            parse_notices("<html><body>empty</body></html>", "https://example.test/")


if __name__ == "__main__":
    unittest.main()
