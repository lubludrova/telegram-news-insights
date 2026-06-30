# systemd Deployment

These units assume the app lives at:

```text
/opt/news-digest-bot
```

and runs as:

```text
newsdigest:newsdigest
```

Install:

```bash
sudo cp deploy/systemd/news-digest-*.service /etc/systemd/system/
sudo cp deploy/systemd/news-digest-collect.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now news-digest-collect.timer
sudo systemctl enable --now news-digest-bot.service
```

The timer sends the daily 24-hour report at 08:30 Moscow time.

Check status:

```bash
systemctl status news-digest-bot.service
systemctl status news-digest-collect.timer
journalctl -u news-digest-bot.service -f
journalctl -u news-digest-collect.service -n 100
```
