#!/usr/bin/env bash
# Управление ботом: smsbot update | config | restart | start | stop | status | logs | backup
set -euo pipefail

DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
SERVICE="smsbot"

need_root() { [ "$(id -u)" -eq 0 ] || { echo "Запустите с sudo: sudo smsbot $1" >&2; exit 1; }; }

case "${1:-help}" in
    update)
        need_root update
        cd "$DIR"
        prev="$(git rev-parse --short HEAD)"
        git fetch -q origin
        branch="$(git rev-parse --abbrev-ref HEAD)"
        git reset -q --hard "origin/$branch"
        # Запускаем уже обновлённый установщик: он поставит зависимости и перезапустит бота.
        INSTALL_DIR="$DIR" BRANCH="$branch" PREV_COMMIT="$prev" exec bash "$DIR/install.sh"
        ;;
    config)
        need_root config
        "${EDITOR:-nano}" "$DIR/.env"
        systemctl restart "$SERVICE"
        echo "✔ Настройки сохранены, бот перезапущен"
        ;;
    restart|start|stop)
        need_root "$1"
        systemctl "$1" "$SERVICE"
        echo "✔ $1"
        ;;
    status)
        systemctl status "$SERVICE" --no-pager
        ;;
    logs)
        journalctl -u "$SERVICE" -f -n 100
        ;;
    yoomoney)
        need_root yoomoney
        cd "$DIR"
        "$DIR/venv/bin/python" -m bot.yoomoney_auth
        systemctl restart "$SERVICE"
        echo "✔ Бот перезапущен — оплата через ЮMoney включена"
        ;;
    export)
        # Архив для переезда на другой сервер: настройки (.env) и база (клиенты, балансы, заказы, эмодзи).
        need_root export
        out="${2:-/root/smsbot-transfer.tar.gz}"
        tmp="$(mktemp -d)"
        cp "$DIR/.env" "$tmp/.env"
        if [ -f "$DIR/bot.db" ]; then
            "$DIR/venv/bin/python" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d)" \
                "$DIR/bot.db" "$tmp/bot.db"
        fi
        tar -czf "$out" -C "$tmp" .
        rm -rf "$tmp"
        chmod 600 "$out"
        echo "✔ Архив для переезда: $out"
        echo "  В нём ваши ключи и база клиентов — не отправляйте его посторонним."
        ;;
    import)
        # Восстановление из архива export на новом сервере.
        need_root import
        src="${2:-/root/smsbot-transfer.tar.gz}"
        [ -f "$src" ] || { echo "Не найден архив: $src" >&2; exit 1; }
        systemctl stop "$SERVICE" 2>/dev/null || true
        [ -f "$DIR/bot.db" ] && cp -f "$DIR/bot.db" "$DIR/bot.db.before-import"
        tar -xzf "$src" -C "$DIR" ./.env $(tar -tzf "$src" | grep -q '^\./bot\.db$' && echo ./bot.db)
        chmod 600 "$DIR/.env"
        systemctl start "$SERVICE"
        sleep 3
        if systemctl is-active -q "$SERVICE"; then
            echo "✔ Данные перенесены, бот запущен"
        else
            echo "✖ Бот не запустился, смотрите: sudo smsbot logs" >&2
            exit 1
        fi
        ;;
    backup)
        need_root backup
        mkdir -p "$DIR/backups"
        file="$DIR/backups/bot-$(date +%Y%m%d-%H%M%S).db"
        venv="$DIR/venv/bin/python"
        "$venv" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d)" \
            "$DIR/bot.db" "$file"
        echo "✔ Копия базы: $file"
        ;;
    *)
        cat <<'EOF'
Использование: sudo smsbot <команда>

  update    обновить бота до последней версии
  config    изменить настройки (.env) и перезапустить
  restart   перезапустить бота
  start     запустить
  stop      остановить
  status    статус
  logs      логи в реальном времени (выход: Ctrl+C)
  backup    резервная копия базы данных
  yoomoney  подключить кошелёк ЮMoney (оплата картами Мир, Visa, Mastercard)
  export    собрать архив для переезда на новый сервер (настройки + база)
  import    восстановить бота из такого архива на новом сервере
EOF
        ;;
esac
