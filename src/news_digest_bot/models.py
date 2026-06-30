from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class NewsItem:
    source: str
    source_name: str
    external_id: str
    title: str
    text: str
    url: str | None
    created_at: datetime
    image_url: str | None = None

    @property
    def dedupe_key(self) -> str:
        if self.url:
            return f"url:{self.url.strip().lower()}"
        text = " ".join(f"{self.title} {self.text[:180]}".split()).lower()
        return f"text:{self.source}:{self.source_name}:{text}"

    def is_recent(self, since: datetime) -> bool:
        created_at = self.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        return created_at >= since
