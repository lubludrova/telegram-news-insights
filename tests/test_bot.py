from news_digest_bot.bot import main_menu_markup


def test_main_menu_markup_contains_digest_callbacks() -> None:
    markup = main_menu_markup()
    buttons = [button for row in markup["inline_keyboard"] for button in row]
    callbacks = {button["callback_data"] for button in buttons}

    assert "mode:general_news" in callbacks
    assert "mode:linkedin_ideas" in callbacks
    assert "collect" in callbacks
