from __future__ import annotations

import time

import httpx

from news_digest_bot.config import Settings, SourceConfig
from news_digest_bot.modes import MODES, get_mode
from news_digest_bot.pipeline import collect_items, generate_mode_report, recent_image_map
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
                {"text": MODES["general_news"].label, "callback_data": "mode:general_news"},
                {"text": MODES["best_of"].label, "callback_data": "mode:best_of"},
            ],
            [
                {"text": MODES["linkedin_ideas"].label, "callback_data": "mode:linkedin_ideas"},
                {"text": MODES["projects_radar"].label, "callback_data": "mode:projects_radar"},
            ],
            [
                {"text": MODES["meme_radar"].label, "callback_data": "mode:meme_radar"},
                {"text": "🔄 Обновить кэш", "callback_data": "collect"},
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
            send_bot_message(settings, chat_id, "Выбери режим дайджеста:", main_menu_markup())
        elif text.startswith("/collect"):
            count = collect_items(settings, sources)
            send_bot_message(settings, chat_id, f"Кэш обновлён. Новых items: {count}", main_menu_markup())
        else:
            send_bot_message(settings, chat_id, "Пока поддерживаю кнопки. Нажми /start.", main_menu_markup())
        return

    if "callback_query" not in update:
        return

    callback = update["callback_query"]
    chat_id = callback["message"]["chat"]["id"]
    if not _is_authorized_chat(settings, chat_id):
        return
    data = callback.get("data", "")
    answer_callback(settings, callback["id"])
    if data == "collect":
        count = collect_items(settings, sources)
        send_bot_message(settings, chat_id, f"Кэш обновлён. Новых items: {count}", main_menu_markup())
        return
    if data.startswith("mode:"):
        mode_key = data.split(":", 1)[1]
        mode = get_mode(mode_key)
        send_bot_message(settings, chat_id, f"Генерирую: {mode.label}. Это может занять до минуты.")
        digest = generate_mode_report(settings, sources, mode_key=mode_key, refresh=False)
        try:
            link = publish_digest(settings, mode.label, digest, recent_image_map(settings))
            send_bot_message(settings, chat_id, f"{mode.label}\n{link}", main_menu_markup(), disable_preview=False)
        except (httpx.HTTPError, RuntimeError):
            send_bot_message(settings, chat_id, markdown_to_telegram_html(digest), main_menu_markup(), parse_mode="HTML")
