# SMS Activate Bot

Telegram-бот для продажи виртуальных номеров под приём СМС. Номера закупаются через API
[Grizzly SMS](https://grizzlysms.com) и продаются клиентам с наценкой (по умолчанию ×2).

## Возможности

- Языки: 🇷🇺 русский, 🇬🇧 английский, 🇹🇲 туркменский.
- Покупка номера: популярные сервисы, все сервисы, поиск по названию, страны отсортированы по цене.
- Код из СМС приходит автоматически. Есть кнопки «Ещё СМС», «Завершить», «Отменить» и копирование номера и кода.
- Если СМС не пришло за `ORDER_TIMEOUT_MIN` минут, номер отменяется и деньги возвращаются на баланс.
- Пополнение баланса:
  - **CryptoBot**: USDT, TON, BTC, ETH и другие, счёт выставляется в рублях;
  - **Telegram Stars**;
  - **банковская карта в рублях** через платёжного провайдера Telegram (ЮKassa и др.).
- Цветные кнопки: зелёные, синие и красные.
- Премиум-эмодзи в тексте сообщений и на кнопках.
- Админ-панель: статистика и прибыль, баланс Grizzly, рассылка, бан и разбан, начисление баланса,
  смена наценки и курсов, настройка эмодзи.

## Установка

```bash
git clone <repo> && cd SmsActivateBot
python3 -m venv venv && . venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполните файл
python -m bot
```

Нужен Python 3.10 или новее.

### Что заполнить в `.env`

| Переменная | Где взять |
|---|---|
| `BOT_TOKEN` | @BotFather → `/newbot` |
| `ADMIN_IDS` | ваш Telegram ID (@userinfobot) |
| `GRIZZLY_API_KEY` | grizzlysms.com → Кабинет → Настройки → API-ключ |
| `GRIZZLY_CURRENCY` | `RUB` или `USD`: в какой валюте баланс аккаунта Grizzly |
| `CRYPTOPAY_TOKEN` | @CryptoBot → Crypto Pay → Create App → API Token |
| `PAYMENT_PROVIDER_TOKEN` | @BotFather → бот → Payments → провайдер (ЮKassa и т.п.) |
| `STAR_RUB_RATE` | сколько рублей засчитывать за 1 ⭐ |

Если для способа оплаты не указан токен, этот способ просто не показывается.

Важно: бот покупает номера с **вашего** баланса в Grizzly, поэтому держите его пополненным.
Когда деньги там закончатся, бот пришлёт админам предупреждение.

## Премиум-эмодзи

1. У владельца бота должен быть Telegram Premium.
2. Отправьте боту `/emojis`, чтобы увидеть имена всех эмодзи (`buy`, `wallet`, `phone` …).
3. Отправьте `/setemoji buy` и в том же сообщении выбранный премиум-эмодзи.
   После этого он появится и в текстах, и на кнопках.
4. `/delemoji buy` возвращает обычный эмодзи.

## Команды админа

`/admin` — панель
`/user ID` — информация о пользователе
`/addbal ID сумма` — начислить или списать баланс
`/ban ID`, `/unban ID`
`/setmarkup 2` — наценка
`/setstar 1.8` — курс звезды
`/setusd 95` — курс доллара (нужен, если баланс Grizzly в $)

## Запуск 24/7 (systemd)

```ini
# /etc/systemd/system/smsbot.service
[Unit]
Description=SMS bot
After=network.target

[Service]
WorkingDirectory=/opt/SmsActivateBot
ExecStart=/opt/SmsActivateBot/venv/bin/python -m bot
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl enable --now smsbot
```
