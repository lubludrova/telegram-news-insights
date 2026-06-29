from __future__ import annotations

from datetime import datetime

from news_digest_bot.config import TwitterConfig
from news_digest_bot.models import NewsItem


def collect_twitter(config: TwitterConfig, since: datetime) -> list[NewsItem]:
    if not config.enabled:
        return []
    raise NotImplementedError(
        "X/Twitter collection is reserved for a later twscrape integration. "
        "Set twitter.enabled=false for now."
    )
