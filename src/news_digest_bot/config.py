from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class TelegramChannel:
    name: str
    handle: str
    enabled: bool = True

    @property
    def entity(self) -> str:
        return self.handle if self.handle.startswith("@") else f"@{self.handle}"


@dataclass(frozen=True)
class RedditSubreddit:
    name: str
    enabled: bool = True


@dataclass(frozen=True)
class TwitterConfig:
    enabled: bool
    accounts: tuple[str, ...]
    searches: tuple[str, ...]


@dataclass(frozen=True)
class SourceConfig:
    telegram_channels: tuple[TelegramChannel, ...]
    reddit_subreddits: tuple[RedditSubreddit, ...]
    twitter: TwitterConfig


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str
    deepseek_base_url: str
    deepseek_model: str
    telegram_api_id: int | None
    telegram_api_hash: str
    telegram_session: str
    telegram_bot_token: str
    telegram_chat_id: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str
    lookback_hours: int
    max_items_per_source: int
    database_path: Path
    sources_path: Path


def load_settings(env_path: str | Path = ".env") -> Settings:
    load_dotenv(env_path)
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro"),
        telegram_api_id=_optional_int(os.getenv("TELEGRAM_API_ID", "")),
        telegram_api_hash=os.getenv("TELEGRAM_API_HASH", ""),
        telegram_session=os.getenv("TELEGRAM_SESSION", "news_digest_reader"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
        reddit_client_id=os.getenv("REDDIT_CLIENT_ID", ""),
        reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET", ""),
        reddit_user_agent=os.getenv("REDDIT_USER_AGENT", "news-digest-bot/0.1"),
        lookback_hours=int(os.getenv("LOOKBACK_HOURS", "24")),
        max_items_per_source=int(os.getenv("MAX_ITEMS_PER_SOURCE", "30")),
        database_path=Path(os.getenv("DATABASE_PATH", "data/news_digest.sqlite3")),
        sources_path=Path(os.getenv("SOURCES_PATH", "config/sources.yaml")),
    )


def load_sources(path: str | Path) -> SourceConfig:
    data = _read_yaml(path)
    telegram_channels = tuple(
        TelegramChannel(
            name=str(item["name"]),
            handle=str(item["handle"]),
            enabled=bool(item.get("enabled", True)),
        )
        for item in data.get("telegram", {}).get("channels", [])
    )
    reddit_subreddits = tuple(
        RedditSubreddit(name=str(item["name"]), enabled=bool(item.get("enabled", True)))
        for item in data.get("reddit", {}).get("subreddits", [])
    )
    twitter_data = data.get("twitter", {})
    return SourceConfig(
        telegram_channels=tuple(ch for ch in telegram_channels if ch.enabled),
        reddit_subreddits=tuple(sr for sr in reddit_subreddits if sr.enabled),
        twitter=TwitterConfig(
            enabled=bool(twitter_data.get("enabled", False)),
            accounts=tuple(str(x) for x in twitter_data.get("accounts", [])),
            searches=tuple(str(x) for x in twitter_data.get("searches", [])),
        ),
    )


def _read_yaml(path: str | Path) -> dict[str, Any]:
    source_path = Path(path)
    if not source_path.exists():
        return {}
    with source_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _optional_int(value: str) -> int | None:
    value = value.strip()
    return int(value) if value else None
