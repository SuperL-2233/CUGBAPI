from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin

from .models import Notice


class NoticeParseError(ValueError):
    """Raised when the expected notice list cannot be found."""


class _NoticeListParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.notices: list[Notice] = []
        self._container_depth = 0
        self._anchor_href: str | None = None
        self._title_parts: list[str] = []
        self._date_parts: list[str] = []
        self._capture: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "div" and values.get("id") == "list_detail_box":
            self._container_depth = 1
            return
        if not self._container_depth:
            return
        if tag == "div":
            self._container_depth += 1
        if tag == "a" and values.get("href"):
            self._anchor_href = values["href"]
            self._title_parts = []
            self._date_parts = []
        classes = set((values.get("class") or "").split())
        if self._anchor_href and "list_con_main" in classes:
            self._capture = "title"
        elif self._anchor_href and "list_con_time" in classes:
            self._capture = "date"

    def handle_endtag(self, tag: str) -> None:
        if not self._container_depth:
            return
        if tag == "a" and self._anchor_href:
            title = " ".join("".join(self._title_parts).split())
            published_date = " ".join("".join(self._date_parts).split())
            if title and published_date:
                self.notices.append(
                    Notice(
                        title=title,
                        published_date=published_date,
                        url=urljoin(self.base_url, self._anchor_href),
                    )
                )
            self._anchor_href = None
            self._capture = None
        elif tag == "div":
            self._capture = None
            self._container_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._capture == "title":
            self._title_parts.append(data)
        elif self._capture == "date":
            self._date_parts.append(data)


def parse_notices(html: str, base_url: str) -> list[Notice]:
    parser = _NoticeListParser(base_url)
    parser.feed(html)
    parser.close()
    if not parser.notices:
        raise NoticeParseError(
            "No notices found in #list_detail_box; the upstream layout may have changed"
        )
    return parser.notices
