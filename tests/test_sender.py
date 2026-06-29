from news_digest_bot.sender import split_message


def test_split_message_keeps_short_message_as_single_chunk() -> None:
    assert split_message("short") == ["short"]


def test_split_message_splits_long_message() -> None:
    chunks = split_message("a" * 10, limit=4)

    assert chunks == ["aaaa", "aaaa", "aa"]
