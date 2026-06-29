from datetime import datetime, timezone

from news_digest_bot.models import NewsItem
from news_digest_bot.storage import ItemStore


def test_item_store_upserts_and_reads_recent_items(tmp_path) -> None:
    path = tmp_path / "items.sqlite3"
    store = ItemStore(path)
    item = NewsItem("telegram_web", "source", "1", "Title", "Text", "https://t.me/x/1", datetime(2026, 1, 2, tzinfo=timezone.utc))

    assert store.upsert_items([item]) == 1
    assert store.upsert_items([item]) == 0

    items = store.recent_items(datetime(2026, 1, 1, tzinfo=timezone.utc))

    assert items == [item]
