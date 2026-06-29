from news_digest_bot.collectors.reddit import collect_reddit
from news_digest_bot.collectors.telegram import collect_telegram
from news_digest_bot.collectors.twitter import collect_twitter

__all__ = ["collect_reddit", "collect_telegram", "collect_twitter"]
