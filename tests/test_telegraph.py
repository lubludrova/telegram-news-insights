from datetime import datetime, timezone

from news_digest_bot.telegraph import _inline, markdown_to_nodes

NOW = datetime(2026, 6, 30, tzinfo=timezone.utc)


def _tags(nodes):
    return [n["tag"] for n in nodes if isinstance(n, dict)]


def test_headings_mapped_and_h1_skipped() -> None:
    nodes = markdown_to_nodes("# Big\n## Section\n### Sub", {}, NOW)
    tags = _tags(nodes)
    assert "h3" in tags
    assert "h4" in tags
    heading_text = [
        child
        for n in nodes
        if isinstance(n, dict) and n["tag"] in ("h3", "h4")
        for child in n["children"]
    ]
    assert "Big" not in heading_text


def test_source_without_image_has_no_figure() -> None:
    nodes = markdown_to_nodes("body\nИсточник: https://t.me/x/1", {}, NOW)
    assert "figure" not in _tags(nodes)


def test_source_with_image_inserts_figure() -> None:
    url = "https://t.me/x/1"
    nodes = markdown_to_nodes(f"**Title**\nИсточник: {url}", {url: "https://cdn/img.jpg"}, NOW)
    figures = [n for n in nodes if isinstance(n, dict) and n["tag"] == "figure"]
    assert len(figures) == 1
    image = figures[0]["children"][0]
    assert image["tag"] == "img"
    assert image["attrs"]["src"] == "https://cdn/img.jpg"


def test_node_order_image_then_text_then_source() -> None:
    url = "https://t.me/x/1"
    nodes = markdown_to_nodes(f"## Sec\n**Title**\nИсточник: {url}", {url: "https://cdn/i.jpg"}, NOW)
    assert _tags(nodes) == ["p", "h3", "figure", "p", "p"]


def test_inline_bold_italic_link() -> None:
    nodes = _inline("**b** and *i* and [t](https://e.com)")
    kinds = [n["tag"] for n in nodes if isinstance(n, dict)]
    assert "b" in kinds
    assert "i" in kinds
    assert "a" in kinds
