from __future__ import annotations

import httpx

from news_digest_bot.config import Settings


MAX_TELEGRAM_LENGTH = 3900


def send_telegram_message(
    settings: Settings,
    text: str,
    parse_mode: str | None = None,
    disable_preview: bool = True,
) -> None:
    chat_id = daily_destination_chat_id(settings)
    if not settings.telegram_bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID or TELEGRAM_CHANNEL_ID are required for sending")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    with httpx.Client(timeout=30) as client:
        for chunk in split_message(text):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": disable_preview,
            }
            if parse_mode:
                payload["parse_mode"] = parse_mode
            response = client.post(url, json=payload)
            response.raise_for_status()


def send_telegram_document(settings: Settings, path: str, caption: str | None = None) -> None:
    chat_id = daily_destination_chat_id(settings)
    if not settings.telegram_bot_token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID or TELEGRAM_CHANNEL_ID are required for sending")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendDocument"
    with httpx.Client(timeout=60) as client:
        with open(path, "rb") as file:
            response = client.post(
                url,
                data={"chat_id": chat_id, "caption": caption or ""},
                files={"document": file},
            )
            response.raise_for_status()


def send_bot_message(
    settings: Settings,
    chat_id: int | str,
    text: str,
    reply_markup: dict | None = None,
    parse_mode: str | None = None,
    disable_preview: bool = True,
) -> None:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required for bot messages")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    with httpx.Client(timeout=30) as client:
        for chunk in split_message(text):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": disable_preview,
            }
            if reply_markup:
                payload["reply_markup"] = reply_markup
            if parse_mode:
                payload["parse_mode"] = parse_mode
            response = client.post(url, json=payload)
            response.raise_for_status()


def send_bot_document(settings: Settings, chat_id: int | str, path: str, caption: str | None = None) -> None:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required for bot documents")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendDocument"
    with httpx.Client(timeout=60) as client:
        with open(path, "rb") as file:
            response = client.post(
                url,
                data={"chat_id": chat_id, "caption": caption or ""},
                files={"document": file},
            )
            response.raise_for_status()


def answer_callback(settings: Settings, callback_query_id: str, text: str = "Запущено") -> None:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required for callback answers")

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/answerCallbackQuery"
    with httpx.Client(timeout=15) as client:
        response = client.post(url, json={"callback_query_id": callback_query_id, "text": text})
        response.raise_for_status()


def split_message(text: str, limit: int = MAX_TELEGRAM_LENGTH) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit)
        if split_at < limit // 2:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks


def daily_destination_chat_id(settings: Settings) -> str:
    return settings.telegram_channel_id.strip() or settings.telegram_chat_id.strip()
