from datetime import datetime, timezone

from news_digest_bot.collectors.telegram import parse_public_channel_html
from news_digest_bot.config import TelegramChannel


def test_parse_public_channel_html_extracts_recent_post() -> None:
    html = """
    <div class="tgme_widget_message" data-post="test_channel/123">
      <div class="tgme_widget_message_text">First line<br/>Second line</div>
      <time datetime="2026-06-29T10:00:00+00:00"></time>
    </div>
    """
    channel = TelegramChannel(name="test", handle="test_channel")

    items = parse_public_channel_html(channel, html, datetime(2026, 6, 29, 0, 0, tzinfo=timezone.utc))

    assert len(items) == 1
    assert items[0].source == "telegram_web"
    assert items[0].url == "https://t.me/test_channel/123"
    assert items[0].title == "First line"


def test_parse_public_channel_html_skips_old_post() -> None:
    html = """
    <div class="tgme_widget_message" data-post="test_channel/123">
      <div class="tgme_widget_message_text">Old post</div>
      <time datetime="2026-06-28T10:00:00+00:00"></time>
    </div>
    """
    channel = TelegramChannel(name="test", handle="test_channel")

    items = parse_public_channel_html(channel, html, datetime(2026, 6, 29, 0, 0, tzinfo=timezone.utc))

    assert items == []
