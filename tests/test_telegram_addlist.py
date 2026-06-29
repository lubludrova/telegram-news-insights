import pytest

from news_digest_bot.telegram_addlist import AddlistChat, extract_addlist_slug, render_sources_yaml


def test_extract_addlist_slug_from_tme_url() -> None:
    assert extract_addlist_slug("https://t.me/addlist/wJrgfwSHk_sxODIy") == "wJrgfwSHk_sxODIy"


def test_extract_addlist_slug_from_tg_url() -> None:
    assert extract_addlist_slug("tg://addlist?slug=wJrgfwSHk_sxODIy") == "wJrgfwSHk_sxODIy"


def test_extract_addlist_slug_rejects_unknown_url() -> None:
    with pytest.raises(ValueError):
        extract_addlist_slug("https://example.com/not-addlist")


def test_render_sources_yaml_disables_private_chats() -> None:
    yaml = render_sources_yaml(
        [
            AddlistChat(title="Public", username="public_channel", chat_id=1),
            AddlistChat(title="Private", username=None, chat_id=2),
        ]
    )

    assert "handle: public_channel" in yaml
    assert "handle: private_chat_2" in yaml
    assert "No public username found" in yaml
