from datetime import datetime, timezone

from news_digest_bot.report import latest_link, latest_markdown_digest, save_latest_link, save_latest_markdown_digest, save_markdown_digest


def test_save_markdown_digest_writes_timestamped_file(tmp_path) -> None:
    path = save_markdown_digest("# Digest", datetime(2026, 6, 29, 12, 0, 1, tzinfo=timezone.utc), tmp_path)

    assert path.name == "digest-2026-06-29-120001.md"
    assert path.read_text(encoding="utf-8") == "# Digest\n"


def test_save_markdown_digest_accepts_prefix(tmp_path) -> None:
    path = save_markdown_digest("# Digest", datetime(2026, 6, 29, 12, 0, 1, tzinfo=timezone.utc), tmp_path, "best-of")

    assert path.name == "best-of-2026-06-29-120001.md"


def test_save_latest_markdown_digest_writes_timestamped_and_latest(tmp_path) -> None:
    timestamped, latest = save_latest_markdown_digest(
        "# Daily",
        datetime(2026, 6, 29, 12, 0, 1, tzinfo=timezone.utc),
        tmp_path,
        "daily-news",
    )

    assert timestamped.name == "daily-news-2026-06-29-120001.md"
    assert latest.name == "daily-news-latest.md"
    assert latest.read_text(encoding="utf-8") == "# Daily\n"


def test_latest_markdown_digest_returns_none_when_missing(tmp_path) -> None:
    assert latest_markdown_digest(tmp_path, "daily-news") is None


def test_latest_markdown_digest_returns_fresh_file(tmp_path) -> None:
    _, latest = save_latest_markdown_digest(
        "# Daily",
        datetime(2026, 6, 29, 12, 0, 1, tzinfo=timezone.utc),
        tmp_path,
        "daily-news",
    )

    assert latest_markdown_digest(tmp_path, "daily-news", now=datetime.now(timezone.utc)) == latest


def test_save_latest_link_writes_latest_url(tmp_path) -> None:
    path = save_latest_link("https://telegra.ph/test", datetime.now(timezone.utc), tmp_path, "daily-news")

    assert path.name == "daily-news-latest.url"
    assert path.read_text(encoding="utf-8") == "https://telegra.ph/test\n"


def test_latest_link_returns_fresh_url(tmp_path) -> None:
    save_latest_link("https://telegra.ph/test", datetime.now(timezone.utc), tmp_path, "daily-news")

    assert latest_link(tmp_path, "daily-news", now=datetime.now(timezone.utc)) == "https://telegra.ph/test"


def test_latest_link_returns_none_when_missing(tmp_path) -> None:
    assert latest_link(tmp_path, "daily-news") is None
