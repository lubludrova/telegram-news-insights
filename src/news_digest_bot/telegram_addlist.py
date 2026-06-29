from __future__ import annotations

import asyncio
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from news_digest_bot.config import Settings


@dataclass(frozen=True)
class AddlistChat:
    title: str
    username: str | None
    chat_id: int


def extract_addlist_slug(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Telegram addlist URL or slug is required")
    if "://" not in value:
        return value

    parsed = urlparse(value)
    if parsed.scheme == "tg":
        slug = parse_qs(parsed.query).get("slug", [""])[0]
        if slug:
            return slug
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "addlist":
        return parts[1]
    raise ValueError(f"Could not extract addlist slug from: {value}")


async def fetch_addlist_chats(settings: Settings, url_or_slug: str) -> list[AddlistChat]:
    if settings.telegram_api_id is None or not settings.telegram_api_hash:
        raise ValueError("TELEGRAM_API_ID and TELEGRAM_API_HASH are required for addlist parsing")

    from telethon import TelegramClient
    from telethon.tl.functions.chatlists import CheckChatlistInviteRequest

    slug = extract_addlist_slug(url_or_slug)
    async with TelegramClient(
        settings.telegram_session,
        settings.telegram_api_id,
        settings.telegram_api_hash,
    ) as client:
        invite = await client(CheckChatlistInviteRequest(slug=slug))

    chats = []
    for chat in getattr(invite, "chats", []):
        chats.append(
            AddlistChat(
                title=getattr(chat, "title", str(getattr(chat, "id", "Unknown chat"))),
                username=getattr(chat, "username", None),
                chat_id=int(getattr(chat, "id")),
            )
        )
    return chats


def fetch_addlist_chats_sync(settings: Settings, url_or_slug: str) -> list[AddlistChat]:
    return asyncio.run(fetch_addlist_chats(settings, url_or_slug))


def render_sources_yaml(chats: list[AddlistChat]) -> str:
    lines = ["telegram:", "  channels:"]
    for chat in chats:
        safe_name = _yaml_string(chat.title)
        if chat.username:
            lines.extend(
                [
                    f"    - name: {safe_name}",
                    f"      handle: {chat.username}",
                    "      enabled: true",
                ]
            )
        else:
            lines.extend(
                [
                    f"    - name: {safe_name}",
                    f"      handle: private_chat_{chat.chat_id}",
                    "      enabled: false",
                    "      # No public username found; keep disabled unless you add a readable handle manually.",
                ]
            )
    return "\n".join(lines)


def _yaml_string(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'
