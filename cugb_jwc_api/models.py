from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class Notice:
    title: str
    published_date: str
    url: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Snapshot:
    notices: tuple[Notice, ...]
    fetched_at: str
    stale: bool = False
