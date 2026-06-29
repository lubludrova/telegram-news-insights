from pathlib import Path

from news_digest_bot.config import Settings, SourceConfig, TelegramChannel, TwitterConfig
from news_digest_bot.doctor import run_doctor


def test_run_doctor_passes_with_minimal_valid_config(tmp_path: Path) -> None:
    sources_path = tmp_path / "sources.yaml"
    sources_path.write_text("telegram: {}\n", encoding="utf-8")
    settings = Settings(
        deepseek_api_key="sk-test",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        telegram_api_id=None,
        telegram_api_hash="",
        telegram_session="test",
        telegram_bot_token="123:testtoken",
        telegram_chat_id="123",
        reddit_client_id="",
        reddit_client_secret="",
        reddit_user_agent="test",
        lookback_hours=24,
        max_items_per_source=10,
        database_path=tmp_path / "data" / "db.sqlite3",
        sources_path=sources_path,
    )
    sources = SourceConfig(
        telegram_channels=(TelegramChannel("test", "test"),),
        reddit_subreddits=(),
        twitter=TwitterConfig(False, (), ()),
    )

    ok, lines = run_doctor(settings, sources)

    assert ok is True
    assert any("public Telegram web fallback" in line for line in lines)


def test_run_doctor_fails_without_required_secrets(tmp_path: Path) -> None:
    settings = Settings(
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        telegram_api_id=None,
        telegram_api_hash="",
        telegram_session="test",
        telegram_bot_token="",
        telegram_chat_id="",
        reddit_client_id="",
        reddit_client_secret="",
        reddit_user_agent="test",
        lookback_hours=24,
        max_items_per_source=10,
        database_path=tmp_path / "data" / "db.sqlite3",
        sources_path=tmp_path / "missing.yaml",
    )
    sources = SourceConfig(telegram_channels=(), reddit_subreddits=(), twitter=TwitterConfig(False, (), ()))

    ok, lines = run_doctor(settings, sources)

    assert ok is False
    assert any("DEEPSEEK_API_KEY is missing" in line for line in lines)
