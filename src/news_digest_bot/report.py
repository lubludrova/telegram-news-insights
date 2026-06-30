from __future__ import annotations

from datetime import datetime, timedelta, timezone
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


def save_latest_markdown_digest(
    text: str,
    now: datetime,
    output_dir: Path = Path("data/digests"),
    prefix: str = "digest",
) -> tuple[Path, Path]:
    timestamped_path = save_markdown_digest(text, now, output_dir, prefix)
    latest_path = output_dir / f"{prefix}-latest.md"
    latest_path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return timestamped_path, latest_path


def latest_markdown_digest(
    output_dir: Path = Path("data/digests"),
    prefix: str = "digest",
    *,
    max_age_hours: int = 24,
    now: datetime | None = None,
) -> Path | None:
    path = output_dir / f"{prefix}-latest.md"
    if not path.exists():
        return None
    now = now or datetime.now(timezone.utc)
    generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if now - generated_at > timedelta(hours=max_age_hours):
        return None
    return path


def save_latest_link(
    link: str,
    now: datetime,
    output_dir: Path = Path("data/digests"),
    prefix: str = "digest",
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{prefix}-latest.url"
    path.write_text(link.strip() + "\n", encoding="utf-8")
    return path


def latest_link(
    output_dir: Path = Path("data/digests"),
    prefix: str = "digest",
    *,
    max_age_hours: int = 24,
    now: datetime | None = None,
) -> str | None:
    path = output_dir / f"{prefix}-latest.url"
    if not path.exists():
        return None
    now = now or datetime.now(timezone.utc)
    generated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if now - generated_at > timedelta(hours=max_age_hours):
        return None
    link = path.read_text(encoding="utf-8").strip()
    return link or None
