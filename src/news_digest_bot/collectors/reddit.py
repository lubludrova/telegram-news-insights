from __future__ import annotations

from datetime import datetime, timezone

from news_digest_bot.config import RedditSubreddit, Settings
from news_digest_bot.models import NewsItem


def collect_reddit(
    settings: Settings,
    subreddits: tuple[RedditSubreddit, ...],
    since: datetime,
) -> list[NewsItem]:
    if not subreddits:
        return []
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        return []

    import praw

    reddit = praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )
    items: list[NewsItem] = []
    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit.name).new(limit=settings.max_items_per_source):
            created_at = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
            if created_at < since:
                continue
            text = submission.selftext or submission.url or ""
            items.append(
                NewsItem(
                    source="reddit",
                    source_name=f"r/{subreddit.name}",
                    external_id=submission.id,
                    title=submission.title,
                    text=text,
                    url=f"https://www.reddit.com{submission.permalink}",
                    created_at=created_at,
                )
            )
    return items
