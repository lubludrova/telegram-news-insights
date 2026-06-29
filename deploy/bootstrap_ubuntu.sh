#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/news-digest-bot}"
APP_USER="${APP_USER:-newsdigest}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo APP_DIR=${APP_DIR} APP_USER=${APP_USER} bash deploy/bootstrap_ubuntu.sh" >&2
  exit 1
fi

apt-get update
apt-get install -y python3 python3-venv python3-pip git

if ! id "${APP_USER}" >/dev/null 2>&1; then
  useradd --system --create-home --shell /usr/sbin/nologin "${APP_USER}"
fi

mkdir -p "${APP_DIR}"
mkdir -p "${APP_DIR}/data/digests"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

echo "Bootstrap complete. Copy the project to ${APP_DIR}, create ${APP_DIR}/.env, then install systemd units."
