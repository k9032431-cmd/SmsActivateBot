#!/usr/bin/env bash
# Установка и обновление SMS-бота одной командой.
#
#   Установка:   curl -fsSL https://raw.githubusercontent.com/k9032431-cmd/SmsActivateBot/HEAD/install.sh | sudo bash
#   Обновление:  sudo smsbot update   (или та же команда установки ещё раз)
#
# Переменные (необязательно): INSTALL_DIR, BRANCH, REPO_URL, GITHUB_TOKEN (для приватного репозитория).
set -euo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/smsbot}"
# При обновлении берём адрес репозитория из уже установленной копии.
if [ -z "${REPO_URL:-}" ] && [ -d "$INSTALL_DIR/.git" ]; then
    REPO_URL="$(git -C "$INSTALL_DIR" remote get-url origin 2>/dev/null || true)"
fi
REPO_URL="${REPO_URL:-https://github.com/k9032431-cmd/SmsActivateBot.git}"
BRANCH="${BRANCH:-}"
SERVICE="smsbot"

green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
blue()  { printf '\033[1;34m%s\033[0m\n' "$*"; }
red()   { printf '\033[1;31m%s\033[0m\n' "$*" >&2; }
die()   { red "✖ $*"; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Запустите от root: добавьте sudo перед командой"

# ---------- 1. Системные пакеты ----------
blue "▶ Проверяю системные пакеты…"
if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    need=()
    for pkg in git python3 python3-venv python3-pip; do
        dpkg -s "$pkg" >/dev/null 2>&1 || need+=("$pkg")
    done
    if [ ${#need[@]} -gt 0 ]; then
        apt-get update -qq
        apt-get install -y -qq "${need[@]}" >/dev/null
    fi
elif command -v dnf >/dev/null 2>&1; then
    dnf install -y -q git python3 python3-pip >/dev/null
elif command -v yum >/dev/null 2>&1; then
    yum install -y -q git python3 python3-pip >/dev/null
else
    command -v git >/dev/null && command -v python3 >/dev/null || die "Установите git и python3 вручную"
fi

python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
    || die "Нужен Python 3.10+, установлен $(python3 -V 2>&1). Используйте Ubuntu 22.04+ / Debian 12+"

# ---------- 2. Код бота ----------
clone_url="$REPO_URL"
if [ -n "${GITHUB_TOKEN:-}" ]; then
    clone_url="${REPO_URL/https:\/\//https://${GITHUB_TOKEN}@}"
fi

if [ -d "$INSTALL_DIR/.git" ]; then
    blue "▶ Обновляю код в $INSTALL_DIR…"
    cd "$INSTALL_DIR"
    [ -n "${GITHUB_TOKEN:-}" ] && git remote set-url origin "$clone_url"
    git fetch -q origin
    if [ -z "$BRANCH" ]; then
        BRANCH="$(git rev-parse --abbrev-ref HEAD)"
    fi
    before="${PREV_COMMIT:-$(git rev-parse --short HEAD)}"
    # .env и база данных не в git, поэтому они сохраняются.
    [ -f bot.db ] && cp -f bot.db "bot.db.bak"
    git checkout -q "$BRANCH" 2>/dev/null || git checkout -q -b "$BRANCH" "origin/$BRANCH"
    git reset -q --hard "origin/$BRANCH"
    after="$(git rev-parse --short HEAD)"
    if [ "$before" = "$after" ]; then
        green "✔ Уже последняя версия ($after)"
    else
        green "✔ Обновлено: $before → $after"
        git --no-pager log --oneline "$before..$after" | head -20 | sed 's/^/   • /'
    fi
else
    blue "▶ Скачиваю бота в $INSTALL_DIR…"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    if [ -n "$BRANCH" ]; then
        git clone -q -b "$BRANCH" "$clone_url" "$INSTALL_DIR"
    else
        git clone -q "$clone_url" "$INSTALL_DIR"
    fi
    cd "$INSTALL_DIR"
fi
# Токен не храним в конфиге git.
git remote set-url origin "$REPO_URL"

# ---------- 3. Python-зависимости ----------
blue "▶ Устанавливаю зависимости…"
[ -x venv/bin/python ] || python3 -m venv venv
venv/bin/pip install -q --upgrade pip >/dev/null
venv/bin/pip install -q -r requirements.txt

# ---------- 4. Настройки (.env) ----------
ask() {  # ask VAR "Вопрос" [по умолчанию]
    local var="$1" prompt="$2" def="${3:-}" value=""
    if { : </dev/tty; } 2>/dev/null; then
        if [ -n "$def" ]; then
            read -r -p "  $prompt [$def]: " value </dev/tty || true
        else
            read -r -p "  $prompt: " value </dev/tty || true
        fi
    fi
    value="${value:-$def}"
    venv/bin/python - "$var" "$value" <<'PY'
import re, sys
key, value = sys.argv[1], sys.argv[2]
text = open(".env", encoding="utf-8").read()
line = f"{key}={value}"
if re.search(rf"^{key}=.*$", text, flags=re.M):
    text = re.sub(rf"^{key}=.*$", lambda _: line, text, flags=re.M)
else:
    text += f"\n{line}\n"
open(".env", "w", encoding="utf-8").write(text)
PY
}

if [ ! -f .env ]; then
    cp .env.example .env
    chmod 600 .env
    echo
    blue "▶ Первичная настройка (Enter — пропустить, потом можно изменить: sudo smsbot config)"
    ask BOT_TOKEN "Токен бота от @BotFather"
    ask ADMIN_IDS "Ваш Telegram ID (узнать в @userinfobot)"
    ask GRIZZLY_API_KEY "API-ключ Grizzly SMS"
    ask GRIZZLY_CURRENCY "Валюта баланса Grizzly (RUB или USD)" "RUB"
    ask BOT_NAME "Название бота в меню" "SMS Number Bot"
    ask SUPPORT_USERNAME "Username поддержки без @ (необязательно)"
    ask CRYPTOPAY_TOKEN "Токен CryptoBot / Crypto Pay (необязательно)"
    ask PAYMENT_PROVIDER_TOKEN "Токен оплаты картой из @BotFather (необязательно)"
fi

# ---------- 5. Команда smsbot и автозапуск ----------
chmod +x install.sh smsbot.sh
ln -sf "$INSTALL_DIR/smsbot.sh" /usr/local/bin/smsbot

cat > "/etc/systemd/system/$SERVICE.service" <<EOF
[Unit]
Description=SMS Activate Telegram bot
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python -m bot
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable -q "$SERVICE"

if grep -qE '^(BOT_TOKEN|GRIZZLY_API_KEY)=\s*$' .env; then
    systemctl stop "$SERVICE" 2>/dev/null || true
    echo
    red "⚠ В .env не заполнены BOT_TOKEN или GRIZZLY_API_KEY — бот не запущен."
    echo "  Заполните их:  sudo smsbot config"
    exit 0
fi

systemctl restart "$SERVICE"
sleep 3
echo
if systemctl is-active -q "$SERVICE"; then
    green "✔ Бот запущен и будет работать 24/7 (автозапуск после перезагрузки включён)"
else
    red "✖ Бот не запустился. Последние строки лога:"
    journalctl -u "$SERVICE" -n 20 --no-pager || true
    exit 1
fi
cat <<'EOF'

Управление ботом:
  sudo smsbot update    — обновить до последней версии
  sudo smsbot config    — изменить настройки (.env)
  sudo smsbot restart   — перезапустить
  sudo smsbot logs      — смотреть логи
  sudo smsbot status    — статус
  sudo smsbot backup    — резервная копия базы
EOF
