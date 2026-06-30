from __future__ import annotations

import time

import httpx

from news_digest_bot.config import Settings, SourceConfig
from news_digest_bot.modes import DEFAULT_MODE, MODES
from news_digest_bot.pipeline import collect_source_items, generate_mode_report, recent_image_map
from news_digest_bot.sender import answer_callback, send_bot_message
from news_digest_bot.telegram_format import markdown_to_telegram_html
from news_digest_bot.telegraph import publish_digest


def run_bot(settings: Settings, sources: SourceConfig, poll_interval: float = 2.0) -> None:
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required for bot mode")

    offset = 0
    send_bot_message(settings, settings.telegram_chat_id, "Бот запущен. Используй /start для меню.") if settings.telegram_chat_id else None
    while True:
        updates = _get_updates(settings, offset)
        for update in updates:
            offset = max(offset, int(update["update_id"]) + 1)
            _handle_update(settings, sources, update)
        time.sleep(poll_interval)


def main_menu_markup() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "Telegram fetch", "callback_data": "fetch:telegram"},
                {"text": "Reddit fetch", "callback_data": "fetch:reddit"},
            ],
        ]
    }


def _get_updates(settings: Settings, offset: int) -> list[dict]:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/getUpdates"
    with httpx.Client(timeout=35) as client:
        response = client.get(url, params={"offset": offset, "timeout": 25})
        response.raise_for_status()
    return response.json().get("result", [])


def _is_authorized_chat(settings: Settings, chat_id: int | str | None) -> bool:
    allowed = settings.telegram_chat_id.strip()
    if not allowed:
        return True
    return str(chat_id) == allowed


def _handle_update(settings: Settings, sources: SourceConfig, update: dict) -> None:
    if "message" in update:
        if not _is_authorized_chat(settings, update["message"]["chat"]["id"]):
            return
        message = update["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")
        if text.startswith("/start") or text.startswith("/menu"):
            send_bot_message(settings, chat_id, "Выбери источник для обновления кэша:", main_menu_markup())
        elif text.startswith("/telegram_fetch"):
            count = collect_source_items(settings, sources, "telegram")
            send_bot_message(settings, chat_id, f"Telegram cache updated. New items: {count}", main_menu_markup())
        elif text.startswith("/reddit_fetch"):
            count = collect_source_items(settings, sources, "reddit")
            send_bot_message(settings, chat_id, f"Reddit cache updated. New items: {count}", main_menu_markup())
        else:
            send_bot_message(settings, chat_id, "Пока поддерживаю fetch-кнопки. Нажми /start.", main_menu_markup())
        return

    if "callback_query" not in update:
        return

    callback = update["callback_query"]
    chat_id = callback["message"]["chat"]["id"]
    if not _is_authorized_chat(settings, chat_id):
        return
    data = callback.get("data", "")
    answer_callback(settings, callback["id"])
    if data.startswith("fetch:"):
        source = data.split(":", 1)[1]
        count = collect_source_items(settings, sources, source)
        send_bot_message(settings, chat_id, f"{source.title()} cache updated. New items: {count}", main_menu_markup())
        return
    if data == "daily_news":
        mode = MODES[DEFAULT_MODE]
        send_bot_message(settings, chat_id, f"Генерирую: {mode.label}. Это может занять до минуты.")
        digest = generate_mode_report(settings, sources, mode_key=DEFAULT_MODE, refresh=True)
        try:
            link = publish_digest(settings, mode.label, digest, recent_image_map(settings))
            send_bot_message(settings, chat_id, f"{mode.label}\n{link}", main_menu_markup(), disable_preview=False)
        except (httpx.HTTPError, RuntimeError):
            send_bot_message(settings, chat_id, markdown_to_telegram_html(digest), main_menu_markup(), parse_mode="HTML")
