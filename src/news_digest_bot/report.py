from __future__ import annotations

from datetime import datetime
from pathlib import Path


def save_markdown_digest(
    text: str,
    now: datetime,
    output_dir: Path = Path("data/digests"),
    prefix: str = "digest",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{prefix}-{now.strftime('%Y-%m-%d-%H%M%S')}.md"
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return path
