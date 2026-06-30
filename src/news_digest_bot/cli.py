from __future__ import annotations

import argparse
from datetime import datetime, timezone

import httpx

from news_digest_bot.config import load_settings, load_sources
from news_digest_bot.bot import run_bot
from news_digest_bot.modes import DEFAULT_MODE, MODES
from news_digest_bot.pipeline import collect_items, generate_mode_report, recent_image_map, run_pipeline
from news_digest_bot.report import save_latest_link
from news_digest_bot.sender import send_telegram_message
from news_digest_bot.telegram_addlist import fetch_addlist_chats_sync, render_sources_yaml
from news_digest_bot.telegram_format import markdown_to_telegram_html
from news_digest_bot.telegraph import publish_digest
from news_digest_bot.doctor import format_doctor_result, run_doctor


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and send a news digest.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("dry-run", help="Use sample items and do not call external APIs.")
    subparsers.add_parser("doctor", help="Validate local production configuration without calling external APIs.")

    addlist_parser = subparsers.add_parser(
        "telegram-addlist",
        help="Parse a Telegram addlist URL with Telethon and print sources YAML.",
    )
    addlist_parser.add_argument("url_or_slug", help="t.me/addlist URL, tg://addlist URL, or raw slug.")

    collect_parser = subparsers.add_parser("collect", help="Collect source items into the local SQLite cache.")
    collect_parser.add_argument("--print-count", action="store_true", help="Print number of newly cached items.")

    run_parser = subparsers.add_parser("run", help="Generate a mode-specific digest from cached data.")
    send_group = run_parser.add_mutually_exclusive_group()
    send_group.add_argument("--send", action="store_true", help="Send digest to Telegram.")
    send_group.add_argument("--no-send", action="store_true", help="Print digest only.")
    run_parser.add_argument("--dry-llm", action="store_true", help="Collect real data but do not call DeepSeek.")
    run_parser.add_argument("--mode", choices=sorted(MODES), default=DEFAULT_MODE, help="Digest mode.")
    run_parser.add_argument("--refresh", action="store_true", help="Refresh source cache before generation.")

    subparsers.add_parser("bot", help="Run Telegram long-polling bot with inline buttons.")

    args = parser.parse_args()
    settings = load_settings()
    sources = load_sources(settings.sources_path)

    if args.command == "dry-run":
        digest = run_pipeline(settings, sources, dry_run=True, use_sample_items=True)
        print(digest)
        return

    if args.command == "doctor":
        ok, lines = run_doctor(settings, sources)
        print(format_doctor_result(ok, lines))
        raise SystemExit(0 if ok else 1)

    if args.command == "telegram-addlist":
        chats = fetch_addlist_chats_sync(settings, args.url_or_slug)
        print(render_sources_yaml(chats))
        return

    if args.command == "collect":
        count = collect_items(settings, sources)
        if args.print_count:
            print(count)
        return

    if args.command == "bot":
        run_bot(settings, sources)
        return

    digest = generate_mode_report(settings, sources, mode_key=args.mode, dry_run=args.dry_llm, refresh=args.refresh)
    if args.send:
        if args.mode == "daily_news":
            link = publish_digest(settings, MODES[args.mode].label, digest, recent_image_map(settings))
            save_latest_link(link, datetime.now(timezone.utc), settings.database_path.parent / "digests", MODES[args.mode].file_prefix)
            send_telegram_message(settings, f"{MODES[args.mode].label}\n{link}", disable_preview=False)
        else:
            try:
                link = publish_digest(settings, MODES[args.mode].label, digest, recent_image_map(settings))
                send_telegram_message(settings, f"{MODES[args.mode].label}\n{link}", disable_preview=False)
            except (httpx.HTTPError, RuntimeError):
                send_telegram_message(settings, markdown_to_telegram_html(digest), parse_mode="HTML")
    else:
        print(digest)


if __name__ == "__main__":
    main()
