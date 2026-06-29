# Production Runbook

Target layout:

```text
/opt/news-digest-bot
├── .env
├── .venv/
├── config/sources.yaml
├── data/news_digest.sqlite3
└── data/digests/
```

## 1. Create User

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin newsdigest
```

Or use the Ubuntu bootstrap helper:

```bash
sudo bash deploy/bootstrap_ubuntu.sh
```

## 2. Install Project

```bash
sudo mkdir -p /opt/news-digest-bot
sudo chown -R newsdigest:newsdigest /opt/news-digest-bot
```

Copy the project into `/opt/news-digest-bot`, then:

```bash
cd /opt/news-digest-bot
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

Fill `.env` with:

```env
DEEPSEEK_API_KEY=...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

LOOKBACK_HOURS=24
MAX_ITEMS_PER_SOURCE=30
DATABASE_PATH=data/news_digest.sqlite3
SOURCES_PATH=config/sources.yaml
```

For the current public-web Telegram parser, `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` may stay empty.

Reddit is intentionally disabled for now. Keep these empty until Reddit API credentials are available:

```env
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=news-digest-bot/0.1 by your_username
```

When Reddit credentials are ready, enable subreddits in `config/sources.yaml` and rerun `news-digest doctor`.

Lock down secrets:

```bash
chmod 600 .env
```

## 3. Validate

```bash
.venv/bin/news-digest doctor
.venv/bin/news-digest collect --print-count
.venv/bin/news-digest run --mode best_of --no-send
```

## 4. Install systemd Units

```bash
sudo cp deploy/systemd/news-digest-*.service /etc/systemd/system/
sudo cp deploy/systemd/news-digest-collect.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now news-digest-collect.timer
sudo systemctl enable --now news-digest-bot.service
```

## 5. Operations

Logs:

```bash
journalctl -u news-digest-bot.service -f
journalctl -u news-digest-collect.service -n 100
```

Restart bot:

```bash
sudo systemctl restart news-digest-bot.service
```

Run collector manually:

```bash
sudo -u newsdigest /opt/news-digest-bot/.venv/bin/news-digest collect --print-count
```

Generate and send a report manually:

```bash
sudo -u newsdigest /opt/news-digest-bot/.venv/bin/news-digest run --mode general_news --send
```

## 6. Update

```bash
cd /opt/news-digest-bot
sudo -u newsdigest git pull
sudo -u newsdigest .venv/bin/pip install -e '.[dev]'
sudo systemctl restart news-digest-bot.service
```

If not using git, copy the updated files and restart the bot service.

## 7. Backups

Back up:

```text
.env
config/sources.yaml
data/news_digest.sqlite3
data/digests/
```

Do not publish `.env`, `*.session`, or SQLite files if they contain private source data.
