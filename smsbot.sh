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
EOF
        ;;
esac
