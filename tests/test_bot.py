from dataclasses import replace
from datetime import datetime, timezone

from news_digest_bot.bot import _format_sources, _is_authorized_chat, _send_latest_daily_report, main_menu_markup
from news_digest_bot.config import RedditSubreddit, SourceConfig, TelegramChannel, TwitterConfig, load_settings
from news_digest_bot.report import save_latest_markdown_digest


def _settings_with_chat(chat_id: str):
    return replace(load_settings(), telegram_chat_id=chat_id)


def test_authorized_chat_matches_configured_id() -> None:
    settings = _settings_with_chat("12345")
    assert _is_authorized_chat(settings, 12345) is True
    assert _is_authorized_chat(settings, "12345") is True
    assert _is_authorized_chat(settings, 99999) is False


def test_authorized_chat_open_when_no_id_configured() -> None:
    settings = _settings_with_chat("")
    assert _is_authorized_chat(settings, 99999) is True


def test_main_menu_markup_contains_digest_callbacks() -> None:
    markup = main_menu_markup()
    buttons = [button for row in markup["inline_keyboard"] for button in row]
    callbacks = {button["callback_data"] for button in buttons}

    assert callbacks == {"fetch:telegram", "fetch:reddit", "sources"}


def test_format_sources_lists_telegram_and_reddit_sources() -> None:
    sources = SourceConfig(
        telegram_channels=(TelegramChannel("AI News", "ai_news"), TelegramChannel("ML", "@ml")),
        reddit_subreddits=(RedditSubreddit("LocalLLaMA"),),
        twitter=TwitterConfig(False, (), ()),
    )

    out = _format_sources(sources)

    assert "Telegram (2):" in out
    assert "AI News: @ai_news" in out
    assert "ML: @ml" in out
    assert "Reddit (1):" in out
    assert "r/LocalLLaMA" in out


def test_format_sources_handles_empty_sources() -> None:
    sources = SourceConfig(telegram_channels=(), reddit_subreddits=(), twitter=TwitterConfig(False, (), ()))

    out = _format_sources(sources)

    assert "Telegram (0):" in out
    assert "нет включённых каналов" in out
    assert "Reddit (0):" in out
    assert "нет включённых сабреддитов" in out


def test_send_latest_daily_report_sends_saved_file(tmp_path, monkeypatch) -> None:
    settings = replace(load_settings(), database_path=tmp_path / "news.sqlite3")
    _, latest = save_latest_markdown_digest(
        "# Daily",
        datetime.now(timezone.utc),
        tmp_path / "digests",
        "daily-news",
    )
    calls = []

    monkeypatch.setattr("news_digest_bot.bot.send_bot_document", lambda *args, **kwargs: calls.append(args))

    _send_latest_daily_report(settings, 123, "Telegram fetch")

    assert calls[0][0] == settings
    assert calls[0][1] == 123
    assert calls[0][2] == str(latest)


def test_send_latest_daily_report_does_not_generate_when_missing(tmp_path, monkeypatch) -> None:
    settings = replace(load_settings(), database_path=tmp_path / "news.sqlite3")
    messages = []

    monkeypatch.setattr("news_digest_bot.bot.send_bot_message", lambda *args, **kwargs: messages.append(args))

    _send_latest_daily_report(settings, 123, "Telegram fetch")

    assert "Нет daily report" in messages[0][2]
