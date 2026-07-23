import unittest

from cugb_jwc_api.models import Notice
from cugb_jwc_api.repository import NoticeRepository


class FakeClient:
    def __init__(self, notices):
        self.notices = notices
        self.calls = 0
        self.error = None

    def fetch(self):
        self.calls += 1
        if self.error:
            raise self.error
        return list(self.notices)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        self.now = 100.0
        self.notice = Notice("测试通知", "2026-07-23", "https://example.test/1")
        self.client = FakeClient([self.notice])
        self.repository = NoticeRepository(
            self.client, cache_ttl_seconds=60, clock=lambda: self.now
        )

    def test_reuses_fresh_cache(self):
        first = self.repository.get()
        second = self.repository.get()
        self.assertIs(first, second)
        self.assertEqual(1, self.client.calls)

    def test_refreshes_expired_cache(self):
        self.repository.get()
        self.now += 61
        self.repository.get()
        self.assertEqual(2, self.client.calls)

    def test_serves_stale_cache_when_refresh_fails(self):
        fresh = self.repository.get()
        self.now += 61
        self.client.error = RuntimeError("offline")
        stale = self.repository.get()
        self.assertEqual(fresh.notices, stale.notices)
        self.assertTrue(stale.stale)

    def test_initial_failure_is_not_hidden(self):
        self.client.error = RuntimeError("offline")
        with self.assertRaisesRegex(RuntimeError, "offline"):
            self.repository.get()


if __name__ == "__main__":
    unittest.main()
