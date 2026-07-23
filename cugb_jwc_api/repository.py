from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Callable

from .client import NoticeClient
from .models import Snapshot


class NoticeRepository:
    """Thread-safe, expiring in-memory cache around the upstream client."""

    def __init__(
        self,
        client: NoticeClient,
        cache_ttl_seconds: float = 60,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.client = client
        self.cache_ttl_seconds = cache_ttl_seconds
        self.clock = clock
        self._snapshot: Snapshot | None = None
        self._expires_at = 0.0
        self._lock = threading.Lock()

    def get(self) -> Snapshot:
        now = self.clock()
        if self._snapshot is not None and now < self._expires_at:
            return self._snapshot

        with self._lock:
            now = self.clock()
            if self._snapshot is not None and now < self._expires_at:
                return self._snapshot
            try:
                notices = tuple(self.client.fetch())
            except Exception:
                if self._snapshot is not None:
                    return Snapshot(
                        notices=self._snapshot.notices,
                        fetched_at=self._snapshot.fetched_at,
                        stale=True,
                    )
                raise
            self._snapshot = Snapshot(
                notices=notices,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
            self._expires_at = now + self.cache_ttl_seconds
            return self._snapshot
