from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import httpx

from news_digest_bot.config import Settings

API = "https://api.telegra.ph"

_HEADING_RE = re.compile(r"^\s*(#{1,6})\s+(.*)$")
_RULE_RE = re.compile(r"^\s*[-—_*]{3,}\s*$")
_SOURCE_RE = re.compile(r"^\s*(?:Источник|Source)\s*:\s*(\S+)(.*)$", re.IGNORECASE)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)$")
_TOKEN_RE = re.compile(
    r"\[(?P<lt>[^\]]+)\]\((?P<lu>https?://[^\s)]+)\)"
    r"|\*\*(?P<b>.+?)\*\*"
    r"|__(?P<b2>.+?)__"
    r"|\*(?P<i>[^*\n]+?)\*"
    r"|`(?P<c>[^`]+?)`"
)
_MONTHS_RU = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/.,);]\"'")


def publish_digest(
    settings: Settings,
    title: str,
    markdown: str,
    image_map: dict[str, str],
    now: datetime | None = None,
) -> str:
    """Publish the Markdown digest as a Telegraph page and return its URL."""
    now = now or datetime.now(timezone.utc)
    token = _get_token(settings)
    nodes = markdown_to_nodes(markdown, image_map, now)
    return _create_page(token, title, nodes)


def markdown_to_nodes(markdown: str, image_map: dict[str, str], now: datetime) -> list:
    lines = markdown.splitlines()
    n_sources = sum(1 for ln in lines if _SOURCE_RE.match(ln))
    out: list = [_subtitle(now, n_sources)]
    buf: list = []

    def flush() -> None:
        out.extend(buf)
        buf.clear()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or _RULE_RE.match(line):
            continue
        source = _SOURCE_RE.match(line)
        if source:
            url = source.group(1).strip()
            image = image_map.get(normalize_url(url))
            if image:
                out.append({"tag": "figure", "children": [{"tag": "img", "attrs": {"src": image}}]})
            flush()
            out.append({"tag": "p", "children": ["🔗 ", {"tag": "a", "attrs": {"href": url}, "children": ["источник"]}]})
            continue
        heading = _HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            if level <= 1:
                continue  # the page title already covers the top-level heading
            flush()
            tag = "h3" if level == 2 else "h4"
            out.append({"tag": tag, "children": _inline(heading.group(2).strip())})
            continue
        bullet = _BULLET_RE.match(line)
        if bullet:
            buf.append({"tag": "p", "children": ["• ", *_inline(bullet.group(1))]})
            continue
        buf.append({"tag": "p", "children": _inline(line)})

    flush()
    return out


def _inline(text: str) -> list:
    nodes: list = []
    pos = 0
    for match in _TOKEN_RE.finditer(text):
        if match.start() > pos:
            nodes.append(text[pos:match.start()])
        if match.group("lt") is not None:
            nodes.append({"tag": "a", "attrs": {"href": match.group("lu")}, "children": [match.group("lt")]})
        elif match.group("b") is not None:
            nodes.append({"tag": "b", "children": [match.group("b")]})
        elif match.group("b2") is not None:
            nodes.append({"tag": "b", "children": [match.group("b2")]})
        elif match.group("i") is not None:
            nodes.append({"tag": "i", "children": [match.group("i")]})
        elif match.group("c") is not None:
            nodes.append({"tag": "code", "children": [match.group("c")]})
        pos = match.end()
    if pos < len(text):
        nodes.append(text[pos:])
    return nodes or [text]


def _subtitle(now: datetime, n_sources: int) -> dict:
    label = f"{now.day} {_MONTHS_RU[now.month - 1]} {now.year} · {n_sources} материалов"
    return {"tag": "p", "children": [{"tag": "i", "children": [label]}]}


def _get_token(settings: Settings) -> str:
    path = settings.database_path.parent / "telegraph_token"
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = _create_account()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token, encoding="utf-8")
    return token


def _create_account() -> str:
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{API}/createAccount",
            data={"short_name": "horizon-digest", "author_name": "Horizon Digest"},
        )
        response.raise_for_status()
        data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegraph createAccount failed: {data.get('error')}")
    return data["result"]["access_token"]


def _create_page(token: str, title: str, nodes: list) -> str:
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"{API}/createPage",
            data={
                "access_token": token,
                "title": (title or "Digest")[:256],
                "author_name": "Horizon Digest",
                "content": json.dumps(nodes, ensure_ascii=False),
                "return_content": "false",
            },
        )
        response.raise_for_status()
        data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegraph createPage failed: {data.get('error')}")
    return data["result"]["url"]
