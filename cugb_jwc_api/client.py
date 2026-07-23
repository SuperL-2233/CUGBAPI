from __future__ import annotations

import gzip
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import Notice
from .parser import parse_notices


class FetchError(RuntimeError):
    """Raised after all attempts to download the notice page fail."""


class NoticeClient:
    def __init__(
        self,
        source_url: str,
        timeout_seconds: float = 10,
        retries: int = 2,
    ) -> None:
        self.source_url = source_url
        self.timeout_seconds = timeout_seconds
        self.retries = retries

    def fetch(self) -> list[Notice]:
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                request = Request(
                    self.source_url,
                    headers={
                        "User-Agent": "CUGB-JWC-API/1.0",
                        "Accept": "text/html,application/xhtml+xml",
                        "Accept-Encoding": "gzip",
                    },
                )
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = response.read()
                    if response.headers.get("Content-Encoding", "").lower() == "gzip":
                        body = gzip.decompress(body)
                    charset = response.headers.get_content_charset() or "utf-8"
                    html = body.decode(charset, errors="replace")
                    return parse_notices(html, response.geturl())
            except (HTTPError, URLError, TimeoutError, OSError, UnicodeError) as error:
                last_error = error
                if attempt < self.retries:
                    time.sleep(2**attempt)
        raise FetchError(
            f"Failed to fetch {self.source_url!r} after {self.retries + 1} attempts"
        ) from last_error
