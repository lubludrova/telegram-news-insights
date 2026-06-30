from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone

from news_digest_bot.collectors import collect_reddit, collect_telegram, collect_twitter
from news_digest_bot.config import Settings, SourceConfig
from news_digest_bot.digest import build_digest_prompt, dedupe_items, format_dry_digest, format_dry_mode_digest
from news_digest_bot.llm import generate_digest, generate_mode_digest
from news_digest_bot.modes import DEFAULT_MODE, get_mode
from news_digest_bot.models import NewsItem
from news_digest_bot.report import save_latest_markdown_digest, save_markdown_digest
from news_digest_bot.storage import ItemStore, SeenStore
from news_digest_bot.telegraph import normalize_url

_URL_RE = re.compile(r'https?://[^\s)\]<>"]+')


def run_pipeline(
    settings: Settings,
    sources: SourceConfig,
    *,
    dry_run: bool,
    use_sample_items: bool = False,
) -> str:
    now = datetime.now(timezone.utc)
    if use_sample_items:
        items = sample_items(now)
    else:
        collect_items(settings, sources, now=now)
        items = recent_cached_items(settings, now=now)
    if dry_run:
        return format_dry_digest(items, now)
    digest = generate_digest(settings, build_digest_prompt(items, now))
    path = save_markdown_digest(digest, now)
    return f"{digest}\n\n---\nMarkdown file: {path}"


def collect_items(settings: Settings, sources: SourceConfig, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=settings.lookback_hours)
    items = dedupe_items(collect_all(settings, sources, since))
    return ItemStore(settings.database_path).upsert_items(items)


def collect_source_items(settings: Settings, sources: SourceConfig, source: str, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=settings.lookback_hours)
    if source == "telegram":
        items = asyncio.run(collect_telegram(settings, sources.telegram_channels, since))
    elif source == "reddit":
        items = collect_reddit(settings, sources.reddit_subreddits, since)
    else:
        raise ValueError(f"Unknown source: {source}")
    return ItemStore(settings.database_path).upsert_items(dedupe_items(items))


def recent_cached_items(settings: Settings, now: datetime | None = None) -> list[NewsItem]:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=settings.lookback_hours)
    limit = settings.max_items_per_source * 20
    return dedupe_items(ItemStore(settings.database_path).recent_items(since, limit=limit))


def recent_image_map(settings: Settings, now: datetime | None = None) -> dict[str, str]:
    """Map every URL that can appear as a digest source to its post image.

    The digest cites sources that may be the Telegram post URL itself or an
    external link mentioned inside the post body, so both are keyed to the
    post's image to maximize image coverage in the rendered article.
    """
    mapping: dict[str, str] = {}
    for item in recent_cached_items(settings, now=now):
        if not item.image_url:
            continue
        if item.url:
            mapping.setdefault(normalize_url(item.url), item.image_url)
        for found in _URL_RE.findall(item.text or ""):
            mapping.setdefault(normalize_url(found), item.image_url)
    return mapping


def generate_mode_report(
    settings: Settings,
    sources: SourceConfig,
    *,
    mode_key: str = DEFAULT_MODE,
    dry_run: bool = False,
    refresh: bool = False,
    use_sample_items: bool = False,
) -> str:
    now = datetime.now(timezone.utc)
    mode = get_mode(mode_key)
    if use_sample_items:
        items = sample_items(now)
    else:
        if refresh:
            collect_items(settings, sources, now=now)
        items = recent_cached_items(settings, now=now)
        if not items:
            collect_items(settings, sources, now=now)
            items = recent_cached_items(settings, now=now)
    if dry_run:
        return format_dry_mode_digest(items, now, mode)
    digest = generate_mode_digest(settings, mode, build_digest_prompt(items, now))
    if mode.key == DEFAULT_MODE:
        save_latest_markdown_digest(digest, now, settings.database_path.parent / "digests", mode.file_prefix)
    return digest


def collect_all(settings: Settings, sources: SourceConfig, since: datetime) -> list[NewsItem]:
    items: list[NewsItem] = []
    items.extend(asyncio.run(collect_telegram(settings, sources.telegram_channels, since)))
    items.extend(collect_reddit(settings, sources.reddit_subreddits, since))
    items.extend(collect_twitter(sources.twitter, since))
    return items


def sample_items(now: datetime) -> list[NewsItem]:
    return [
        NewsItem(
            source="telegram",
            source_name="Example AI Channel",
            external_id="1",
            title="New open-source small model release",
            text="A team released a compact model with strong coding benchmarks and permissive license.",
            url="https://t.me/example/1",
            created_at=now,
        ),
        NewsItem(
            source="reddit",
            source_name="r/LocalLLaMA",
            external_id="abc123",
            title="Practical notes on running agents with small LMs",
            text="Discussion highlights memory, tool-use reliability, and evaluation pitfalls.",
            url="https://www.reddit.com/r/LocalLLaMA/comments/abc123/example/",
            created_at=now,
        ),
    ]
