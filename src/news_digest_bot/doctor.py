from __future__ import annotations

from pathlib import Path

from news_digest_bot.config import Settings, SourceConfig
from news_digest_bot.modes import MODES


def run_doctor(settings: Settings, sources: SourceConfig) -> tuple[bool, list[str]]:
    lines: list[str] = []
    ok = True

    ok &= _check(bool(settings.deepseek_api_key), "DEEPSEEK_API_KEY is set", "DEEPSEEK_API_KEY is missing", lines)
    ok &= _check(bool(settings.telegram_bot_token), "TELEGRAM_BOT_TOKEN is set", "TELEGRAM_BOT_TOKEN is missing", lines)
    ok &= _check(bool(settings.telegram_chat_id), "TELEGRAM_CHAT_ID is set", "TELEGRAM_CHAT_ID is missing", lines)
    ok &= _check(settings.sources_path.exists(), f"Sources file exists: {settings.sources_path}", f"Sources file missing: {settings.sources_path}", lines)
    ok &= _check(
        bool(sources.telegram_channels or sources.reddit_subreddits),
        f"Enabled sources: telegram={len(sources.telegram_channels)}, reddit={len(sources.reddit_subreddits)}",
        "No enabled Telegram channels or Reddit subreddits",
        lines,
    )

    if settings.telegram_api_id and settings.telegram_api_hash:
        lines.append("OK Telegram API credentials are set; Telethon can be used.")
    else:
        lines.append("WARN TELEGRAM_API_ID/API_HASH are empty; public Telegram web fallback will be used.")

    try:
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        probe = settings.database_path.parent / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        lines.append(f"OK Database directory is writable: {settings.database_path.parent}")
    except OSError as exc:
        ok = False
        lines.append(f"FAIL Database directory is not writable: {settings.database_path.parent} ({exc})")

    lines.append("OK Modes: " + ", ".join(sorted(MODES)))
    return ok, lines


def format_doctor_result(ok: bool, lines: list[str]) -> str:
    status = "OK" if ok else "FAIL"
    return "\n".join([f"Doctor status: {status}", *lines])


def _check(condition: bool, ok_message: str, fail_message: str, lines: list[str]) -> bool:
    if condition:
        lines.append(f"OK {ok_message}")
        return True
    lines.append(f"FAIL {fail_message}")
    return False
