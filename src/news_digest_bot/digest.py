from __future__ import annotations

from datetime import datetime

from news_digest_bot.modes import DigestMode, get_mode
from news_digest_bot.models import NewsItem


SYSTEM_PROMPT = get_mode("daily_news").system_prompt


def build_digest_prompt(items: list[NewsItem], now: datetime) -> str:
    if not items:
        return "No new items were collected. Say that there is not enough data for a digest."

    lines = [f"Collected at: {now.isoformat()}", "", "Source items:"]
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                f"[{index}] {item.source} / {item.source_name}",
                f"Time: {item.created_at.isoformat()}",
                f"Title: {item.title}",
                f"URL: {item.url or 'n/a'}",
                f"Text: {_clip(item.text, 1200)}",
                "",
            ]
        )
    return "\n".join(lines)


def format_dry_digest(items: list[NewsItem], now: datetime) -> str:
    prompt = build_digest_prompt(items, now)
    return f"DRY RUN: DeepSeek was not called.\n\n{SYSTEM_PROMPT}\n\n{prompt}"


def format_dry_mode_digest(items: list[NewsItem], now: datetime, mode: DigestMode) -> str:
    prompt = build_digest_prompt(items, now)
    return f"DRY RUN: DeepSeek was not called.\n\n{mode.system_prompt}\n\n{prompt}"


def dedupe_items(items: list[NewsItem]) -> list[NewsItem]:
    seen: set[str] = set()
    result: list[NewsItem] = []
    for item in sorted(items, key=lambda x: x.created_at, reverse=True):
        key = item.dedupe_key
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _clip(text: str, limit: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."
