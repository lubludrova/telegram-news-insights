from datetime import datetime, timezone

from news_digest_bot.report import save_markdown_digest


def test_save_markdown_digest_writes_timestamped_file(tmp_path) -> None:
    path = save_markdown_digest("# Digest", datetime(2026, 6, 29, 12, 0, 1, tzinfo=timezone.utc), tmp_path)

    assert path.name == "digest-2026-06-29-120001.md"
    assert path.read_text(encoding="utf-8") == "# Digest\n"


def test_save_markdown_digest_accepts_prefix(tmp_path) -> None:
    path = save_markdown_digest("# Digest", datetime(2026, 6, 29, 12, 0, 1, tzinfo=timezone.utc), tmp_path, "best-of")

    assert path.name == "best-of-2026-06-29-120001.md"
