from datetime import datetime, timezone

from news_digest_bot.digest import SYSTEM_PROMPT, build_digest_prompt, dedupe_items
from news_digest_bot.models import NewsItem


def test_dedupe_items_prefers_newest_order_and_removes_same_url() -> None:
    older = NewsItem("telegram", "A", "1", "Title", "Text", "https://x.test/a", datetime(2026, 1, 1, tzinfo=timezone.utc))
    newer = NewsItem("reddit", "B", "2", "Other", "Other", "https://x.test/a", datetime(2026, 1, 2, tzinfo=timezone.utc))

    result = dedupe_items([older, newer])

    assert result == [newer]


def test_build_digest_prompt_contains_required_source_context() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    item = NewsItem("reddit", "r/test", "abc", "Interesting release", "Body", "https://reddit.test", now)

    prompt = build_digest_prompt([item], now)

    assert "Interesting release" in prompt
    assert "https://reddit.test" in prompt
    assert "reddit / r/test" in prompt


def test_system_prompt_requires_markdown_and_source_lines() -> None:
    assert "Return valid Markdown" in SYSTEM_PROMPT
    assert "Источник: <URL>" in SYSTEM_PROMPT
    assert "Важность: <1-10>/10" in SYSTEM_PROMPT
