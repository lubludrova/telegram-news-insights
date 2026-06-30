from dataclasses import replace

from news_digest_bot.config import load_settings
from news_digest_bot.sender import daily_destination_chat_id, split_message


def test_split_message_keeps_short_message_as_single_chunk() -> None:
    assert split_message("short") == ["short"]


def test_split_message_splits_long_message() -> None:
    chunks = split_message("a" * 10, limit=4)

    assert chunks == ["aaaa", "aaaa", "aa"]


def test_daily_destination_prefers_channel_id() -> None:
    settings = replace(load_settings(), telegram_chat_id="group", telegram_channel_id="channel")

    assert daily_destination_chat_id(settings) == "channel"


def test_daily_destination_falls_back_to_group_chat_id() -> None:
    settings = replace(load_settings(), telegram_chat_id="group", telegram_channel_id="")

    assert daily_destination_chat_id(settings) == "group"
