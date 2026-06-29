from pathlib import Path

from news_digest_bot.config import load_sources


def test_load_sources_filters_disabled_and_normalizes_channel_entity(tmp_path: Path) -> None:
    path = tmp_path / "sources.yaml"
    path.write_text(
        """
telegram:
  channels:
    - name: Enabled
      handle: enabled_channel
      enabled: true
    - name: Disabled
      handle: disabled_channel
      enabled: false
reddit:
  subreddits:
    - name: LocalLLaMA
      enabled: true
    - name: unused
      enabled: false
twitter:
  enabled: false
  accounts: [some_account]
  searches: [some query]
""",
        encoding="utf-8",
    )

    sources = load_sources(path)

    assert len(sources.telegram_channels) == 1
    assert sources.telegram_channels[0].entity == "@enabled_channel"
    assert [sr.name for sr in sources.reddit_subreddits] == ["LocalLLaMA"]
    assert sources.twitter.enabled is False
