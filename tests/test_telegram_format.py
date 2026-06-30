from news_digest_bot.telegram_format import markdown_to_telegram_html


def test_heading_becomes_bold() -> None:
    assert markdown_to_telegram_html("# Best of Today") == "<b>Best of Today</b>"


def test_bold_and_italic_inline() -> None:
    out = markdown_to_telegram_html("**MegaTrain** is *cool*")
    assert "<b>MegaTrain</b>" in out
    assert "<i>cool</i>" in out


def test_source_line_becomes_single_link() -> None:
    out = markdown_to_telegram_html("Источник: https://arxiv.org/abs/2604.05091")
    assert '<a href="https://arxiv.org/abs/2604.05091">источник</a>' in out
    assert "Источник:" not in out


def test_html_special_chars_are_escaped() -> None:
    out = markdown_to_telegram_html("a < b & c > d")
    assert "&lt;" in out
    assert "&amp;" in out
    assert "&gt;" in out


def test_no_raw_markdown_markers_remain() -> None:
    out = markdown_to_telegram_html("## Title\n**bold**\nИсточник: https://x.com/1")
    assert "##" not in out
    assert "**" not in out


def test_horizontal_rule_is_dropped() -> None:
    out = markdown_to_telegram_html("line\n\n---\n\nother")
    assert "---" not in out
