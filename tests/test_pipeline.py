from news_digest_bot.config import RedditSubreddit, SourceConfig, TelegramChannel, TwitterConfig, Settings
from datetime import datetime, timezone

from news_digest_bot.models import NewsItem
from news_digest_bot.pipeline import collect_source_items, generate_mode_report, run_pipeline
from news_digest_bot.storage import ItemStore


def test_dry_run_pipeline_uses_sample_items(tmp_path) -> None:
    settings = Settings(
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        telegram_api_id=None,
        telegram_api_hash="",
        telegram_session="test",
        telegram_bot_token="",
        telegram_chat_id="",
        telegram_channel_id="",
        reddit_client_id="",
        reddit_client_secret="",
        reddit_user_agent="test",
        lookback_hours=24,
        max_items_per_source=10,
        database_path=tmp_path / "test.sqlite3",
        sources_path=tmp_path / "sources.yaml",
    )
    sources = SourceConfig(telegram_channels=(), reddit_subreddits=(), twitter=TwitterConfig(False, (), ()))

    result = run_pipeline(settings, sources, dry_run=True, use_sample_items=True)

    assert "DRY RUN" in result
    assert "Daily AI/Tech News" in result
    assert "Example AI Channel" in result


def test_generate_mode_report_reads_cached_items_in_dry_run(tmp_path) -> None:
    settings = Settings(
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        telegram_api_id=None,
        telegram_api_hash="",
        telegram_session="test",
        telegram_bot_token="",
        telegram_chat_id="",
        telegram_channel_id="",
        reddit_client_id="",
        reddit_client_secret="",
        reddit_user_agent="test",
        lookback_hours=24,
        max_items_per_source=10,
        database_path=tmp_path / "test.sqlite3",
        sources_path=tmp_path / "sources.yaml",
    )
    sources = SourceConfig(telegram_channels=(), reddit_subreddits=(), twitter=TwitterConfig(False, (), ()))
    ItemStore(settings.database_path).upsert_items(
        [
            NewsItem(
                source="telegram_web",
                source_name="test",
                external_id="1",
                title="Cool GitHub project",
                text="A useful open-source AI project.",
                url="https://github.com/example/project",
                created_at=datetime.now(timezone.utc),
            )
        ]
    )

    result = generate_mode_report(settings, sources, mode_key="linkedin_ideas", dry_run=True)

    assert "LinkedIn-worthy ideas" in result
    assert "Cool GitHub project" in result


def test_collect_source_items_rejects_unknown_source(tmp_path) -> None:
    settings = Settings(
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        telegram_api_id=None,
        telegram_api_hash="",
        telegram_session="test",
        telegram_bot_token="",
        telegram_chat_id="",
        telegram_channel_id="",
        reddit_client_id="",
        reddit_client_secret="",
        reddit_user_agent="test",
        lookback_hours=24,
        max_items_per_source=10,
        database_path=tmp_path / "test.sqlite3",
        sources_path=tmp_path / "sources.yaml",
    )
    sources = SourceConfig(telegram_channels=(), reddit_subreddits=(), twitter=TwitterConfig(False, (), ()))

    try:
        collect_source_items(settings, sources, "x")
    except ValueError as exc:
        assert "Unknown source" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_collect_source_items_uses_only_configured_telegram_channels(tmp_path, monkeypatch) -> None:
    settings = Settings(
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        telegram_api_id=None,
        telegram_api_hash="",
        telegram_session="test",
        telegram_bot_token="",
        telegram_chat_id="",
        telegram_channel_id="",
        reddit_client_id="",
        reddit_client_secret="",
        reddit_user_agent="test",
        lookback_hours=24,
        max_items_per_source=10,
        database_path=tmp_path / "test.sqlite3",
        sources_path=tmp_path / "sources.yaml",
    )
    channels = (TelegramChannel("A", "a"), TelegramChannel("B", "b"))
    sources = SourceConfig(telegram_channels=channels, reddit_subreddits=(), twitter=TwitterConfig(False, (), ()))
    seen = {}

    async def fake_collect_telegram(_settings, passed_channels, _since):
        seen["channels"] = passed_channels
        return []

    monkeypatch.setattr("news_digest_bot.pipeline.collect_telegram", fake_collect_telegram)

    assert collect_source_items(settings, sources, "telegram") == 0
    assert seen["channels"] == channels


def test_collect_source_items_uses_only_configured_reddit_subreddits(tmp_path, monkeypatch) -> None:
    settings = Settings(
        deepseek_api_key="",
        deepseek_base_url="https://api.deepseek.com",
        deepseek_model="deepseek-chat",
        telegram_api_id=None,
        telegram_api_hash="",
        telegram_session="test",
        telegram_bot_token="",
        telegram_chat_id="",
        telegram_channel_id="",
        reddit_client_id="id",
        reddit_client_secret="secret",
        reddit_user_agent="test",
        lookback_hours=24,
        max_items_per_source=10,
        database_path=tmp_path / "test.sqlite3",
        sources_path=tmp_path / "sources.yaml",
    )
    subreddits = (RedditSubreddit("LocalLLaMA"), RedditSubreddit("MachineLearning"))
    sources = SourceConfig(telegram_channels=(), reddit_subreddits=subreddits, twitter=TwitterConfig(False, (), ()))
    seen = {}

    def fake_collect_reddit(_settings, passed_subreddits, _since):
        seen["subreddits"] = passed_subreddits
        return []

    monkeypatch.setattr("news_digest_bot.pipeline.collect_reddit", fake_collect_reddit)

    assert collect_source_items(settings, sources, "reddit") == 0
    assert seen["subreddits"] == subreddits
