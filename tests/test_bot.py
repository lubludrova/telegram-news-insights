from dataclasses import replace

from news_digest_bot.bot import _is_authorized_chat, main_menu_markup
from news_digest_bot.config import load_settings


def _settings_with_chat(chat_id: str):
    return replace(load_settings(), telegram_chat_id=chat_id)


def test_authorized_chat_matches_configured_id() -> None:
    settings = _settings_with_chat("12345")
    assert _is_authorized_chat(settings, 12345) is True
    assert _is_authorized_chat(settings, "12345") is True
    assert _is_authorized_chat(settings, 99999) is False


def test_authorized_chat_open_when_no_id_configured() -> None:
    settings = _settings_with_chat("")
    assert _is_authorized_chat(settings, 99999) is True


def test_main_menu_markup_contains_digest_callbacks() -> None:
    markup = main_menu_markup()
    buttons = [button for row in markup["inline_keyboard"] for button in row]
    callbacks = {button["callback_data"] for button in buttons}

    assert "mode:general_news" in callbacks
    assert "mode:linkedin_ideas" in callbacks
    assert "collect" in callbacks
