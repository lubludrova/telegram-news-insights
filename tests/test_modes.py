import pytest

from news_digest_bot.modes import DEFAULT_MODE, MODES, get_mode


def test_modes_have_file_prefixes_and_source_rule() -> None:
    assert {"daily_news", "general_news", "linkedin_ideas", "projects_radar", "meme_radar", "best_of"}.issubset(MODES)
    for mode in MODES.values():
        assert mode.file_prefix
        assert "Источник: <URL>" in mode.system_prompt


def test_daily_news_mode_requires_classification_and_importance() -> None:
    prompt = MODES[DEFAULT_MODE].system_prompt

    assert DEFAULT_MODE == "daily_news"
    assert "Важность: <1-10>/10" in prompt
    assert "Класс: <one category from the list>" in prompt
    assert "Канал/сабреддит" in prompt
    assert "## Основные новости" in prompt
    assert "## Вакансии и хакатоны" in prompt
    assert "Do not include pure vacancies or hackathon announcements" in prompt


def test_get_mode_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError):
        get_mode("unknown")
