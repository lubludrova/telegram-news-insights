from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from news_digest_bot.models import NewsItem


class SeenStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def filter_new(self, items: list[NewsItem]) -> list[NewsItem]:
        new_items: list[NewsItem] = []
        with sqlite3.connect(self.path) as conn:
            for item in items:
                key = item.dedupe_key
                exists = conn.execute("select 1 from seen_items where dedupe_key = ?", (key,)).fetchone()
                if exists:
                    continue
                conn.execute(
                    "insert into seen_items(dedupe_key, source, source_name, external_id, url, created_at) values (?, ?, ?, ?, ?, ?)",
                    (key, item.source, item.source_name, item.external_id, item.url, item.created_at.isoformat()),
                )
                new_items.append(item)
        return new_items

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                create table if not exists seen_items (
                    dedupe_key text primary key,
                    source text not null,
                    source_name text not null,
                    external_id text not null,
                    url text,
                    created_at text not null,
                    inserted_at text not null default current_timestamp
                )
                """
            )


class ItemStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def upsert_items(self, items: list[NewsItem]) -> int:
        changed = 0
        with sqlite3.connect(self.path) as conn:
            for item in items:
                cursor = conn.execute(
                    """
                    insert or ignore into raw_items(
                        dedupe_key, source, source_name, external_id, title, text, url, created_at, image_url
                    ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.dedupe_key,
                        item.source,
                        item.source_name,
                        item.external_id,
                        item.title,
                        item.text,
                        item.url,
                        item.created_at.isoformat(),
                        item.image_url,
                    ),
                )
                changed += cursor.rowcount
        return changed

    def recent_items(self, since: datetime, limit: int = 300) -> list[NewsItem]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """
                select source, source_name, external_id, title, text, url, created_at, image_url
                from raw_items
                where created_at >= ?
                order by created_at desc
                limit ?
                """,
                (since.isoformat(), limit),
            ).fetchall()
        return [
            NewsItem(
                source=row[0],
                source_name=row[1],
                external_id=row[2],
                title=row[3],
                text=row[4],
                url=row[5],
                created_at=_parse_datetime(row[6]),
                image_url=row[7],
            )
            for row in rows
        ]

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                create table if not exists raw_items (
                    dedupe_key text primary key,
                    source text not null,
                    source_name text not null,
                    external_id text not null,
                    title text not null,
                    text text not null,
                    url text,
                    created_at text not null,
                    image_url text,
                    inserted_at text not null default current_timestamp
                )
                """
            )
            columns = {row[1] for row in conn.execute("pragma table_info(raw_items)")}
            if "image_url" not in columns:
                conn.execute("alter table raw_items add column image_url text")
            conn.execute("create index if not exists idx_raw_items_created_at on raw_items(created_at)")


def _parse_datetime(value: str) -> datetime:
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        return result.replace(tzinfo=timezone.utc)
    return result
