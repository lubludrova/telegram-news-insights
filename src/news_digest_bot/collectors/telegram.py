from __future__ import annotations

import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from news_digest_bot.config import Settings, TelegramChannel
from news_digest_bot.models import NewsItem


async def collect_telegram(
    settings: Settings,
    channels: tuple[TelegramChannel, ...],
    since: datetime,
) -> list[NewsItem]:
    if not channels:
        return []
    if settings.telegram_api_id is None or not settings.telegram_api_hash:
        return collect_public_telegram_web(settings, channels, since)

    from telethon import TelegramClient

    items: list[NewsItem] = []
    async with TelegramClient(
        settings.telegram_session,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    ) as client:
        for channel in channels:
            async for message in client.iter_messages(
                channel.entity,
                limit=settings.max_items_per_source,
            ):
                if not message.text or not message.date or message.date < since:
                    continue
                url = f"https://t.me/{channel.handle.lstrip('@')}/{message.id}"
                items.append(
                    NewsItem(
                        source="telegram",
                        source_name=channel.name,
                        external_id=str(message.id),
                        title=_first_line(message.text),
                        text=message.text,
                        url=url,
                        created_at=message.date,
                    )
                )
    return items


def collect_public_telegram_web(
    settings: Settings,
    channels: tuple[TelegramChannel, ...],
    since: datetime,
) -> list[NewsItem]:
    items: list[NewsItem] = []
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        for channel in channels:
            handle = channel.handle.lstrip("@")
            response = client.get(f"https://t.me/s/{handle}")
            if response.status_code >= 400:
                continue
            items.extend(parse_public_channel_html(channel, response.text, since))
            if len(items) >= settings.max_items_per_source * max(len(channels), 1):
                break
    return items


def parse_public_channel_html(channel: TelegramChannel, html: str, since: datetime) -> list[NewsItem]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[NewsItem] = []
    for post in soup.select(".tgme_widget_message"):
        post_id = post.get("data-post") or ""
        if not post_id:
            continue
        time_tag = post.select_one("time[datetime]")
        if not time_tag or not time_tag.get("datetime"):
            continue
        created_at = datetime.fromisoformat(str(time_tag["datetime"]).replace("Z", "+00:00"))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if created_at < since:
            continue
        text_node = post.select_one(".tgme_widget_message_text")
        text = text_node.get_text("\n", strip=True) if text_node else ""
        if not text:
            continue
        url = f"https://t.me/{post_id}"
        items.append(
            NewsItem(
                source="telegram_web",
                source_name=channel.name,
                external_id=post_id,
                title=_first_line(text),
                text=text,
                url=url,
                created_at=created_at,
                image_url=_extract_image(post),
            )
        )
    return items


_BG_IMAGE_RE = re.compile(r"background-image:\s*url\('([^']+)'\)")


def _extract_image(post) -> str | None:
    for selector in (
        ".tgme_widget_message_photo_wrap",
        ".tgme_widget_message_link_preview .link_preview_image",
        "i.link_preview_image",
        "i.tgme_widget_message_video_thumb",
        ".tgme_widget_message_video_thumb",
    ):
        node = post.select_one(selector)
        if not node:
            continue
        match = _BG_IMAGE_RE.search(node.get("style", "") or "")
        if match:
            return match.group(1)
    return None


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:160]
    return "Telegram post"
