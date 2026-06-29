import pytest

from news_digest_bot.modes import MODES, get_mode


def test_modes_have_file_prefixes_and_source_rule() -> None:
    assert {"general_news", "linkedin_ideas", "projects_radar", "meme_radar", "best_of"}.issubset(MODES)
    for mode in MODES.values():
        assert mode.file_prefix
        assert "Источник: <URL>" in mode.system_prompt


def test_get_mode_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError):
        get_mode("unknown")
