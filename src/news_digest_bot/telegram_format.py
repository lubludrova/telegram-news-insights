from __future__ import annotations

import html
import re

_SOURCE_RE = re.compile(r"^\s*(?:Источник|Source)\s*:\s*(\S+)(.*)$", re.IGNORECASE)
_HEADING_RE = re.compile(r"^\s*#{1,6}\s+(.*)$")
_RULE_RE = re.compile(r"^\s*[-—_*]{3,}\s*$")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def markdown_to_telegram_html(text: str) -> str:
    """Convert the LLM's Markdown digest into Telegram-safe HTML.

    Headings become bold, ``Источник: <url>`` lines become a single clickable
    link, and inline ``**bold**`` / ``*italic*`` / ``code`` markers are mapped to
    the small set of tags Telegram's HTML parse mode supports.
    """
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            lines.append("")
            continue
        if _RULE_RE.match(line):
            continue
        source = _SOURCE_RE.match(line)
        if source:
            url = html.escape(source.group(1).strip(), quote=True)
            rest = html.escape(source.group(2).rstrip(), quote=False)
            lines.append(f'🔗 <a href="{url}">источник</a>{rest}')
            continue
        heading = _HEADING_RE.match(line)
        if heading:
            lines.append(f"<b>{_inline(heading.group(1))}</b>")
            continue
        lines.append(_inline(line))
    out = "\n".join(lines)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"^\s*[-*]\s+", "• ", s)
    s = _MD_LINK_RE.sub(r'<a href="\2">\1</a>', s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"__(.+?)__", r"<b>\1</b>", s)
    s = re.sub(r"\*([^*\n]+?)\*", r"<i>\1</i>", s)
    return s
