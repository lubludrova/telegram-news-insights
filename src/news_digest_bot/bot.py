from __future__ import annotations

import time

import httpx

from news_digest_bot.config import Settings, SourceConfig
from news_digest_bot.modes import DEFAULT_MODE, MODES
from news_digest_bot.report import latest_markdown_digest
from news_digest_bot.sender import answer_callback, send_bot_document, send_bot_message


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
            [
                {"text": "Sources", "callback_data": "sources"},
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
            send_bot_message(settings, chat_id, "Выбери сохранённый daily report:", main_menu_markup())
        elif text.startswith("/telegram_fetch"):
            _send_latest_daily_report(settings, chat_id, "Telegram fetch")
        elif text.startswith("/reddit_fetch"):
            _send_latest_daily_report(settings, chat_id, "Reddit fetch")
        elif text.startswith("/sources"):
            send_bot_message(settings, chat_id, _format_sources(sources), main_menu_markup())
        else:
            send_bot_message(settings, chat_id, "Пока поддерживаю отправку сохранённого отчёта. Нажми /start.", main_menu_markup())
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
        _send_latest_daily_report(settings, chat_id, f"{source.title()} fetch")
        return
    if data == "sources":
        send_bot_message(settings, chat_id, _format_sources(sources), main_menu_markup())
        return


def _format_sources(sources: SourceConfig) -> str:
    lines = ["Используемые источники:", "", f"Telegram ({len(sources.telegram_channels)}):"]
    if sources.telegram_channels:
        for channel in sources.telegram_channels:
            handle = channel.handle if channel.handle.startswith("@") else f"@{channel.handle}"
            lines.append(f"- {channel.name}: {handle}")
    else:
        lines.append("- нет включённых каналов")

    lines.extend(["", f"Reddit ({len(sources.reddit_subreddits)}):"])
    if sources.reddit_subreddits:
        for subreddit in sources.reddit_subreddits:
            lines.append(f"- r/{subreddit.name}")
    else:
        lines.append("- нет включённых сабреддитов")
    return "\n".join(lines)


def _send_latest_daily_report(settings: Settings, chat_id: int | str, label: str) -> None:
    mode = MODES[DEFAULT_MODE]
    path = latest_markdown_digest(settings.database_path.parent / "digests", mode.file_prefix, max_age_hours=24)
    if path is None:
        send_bot_message(
            settings,
            chat_id,
            "Нет daily report за последние 24 часа. Новый отчёт генерируется автоматически в 12:00 МСК.",
            main_menu_markup(),
        )
        return
    send_bot_document(settings, chat_id, str(path), caption=f"{label}: latest daily report")
