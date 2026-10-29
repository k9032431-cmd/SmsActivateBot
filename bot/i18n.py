"""Тексты бота на трёх языках.

[[имя]] — место для (премиум-)эмодзи из emoji.py.
"""
import re

from .emoji import e

LANGS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "tk": "🇹🇲 Türkmençe"}
DEFAULT_LANG = "ru"

TEXTS: dict[str, dict[str, str]] = {
    "choose_lang": {
        "ru": "[[lang]] <b>Выберите язык</b>",
        "en": "[[lang]] <b>Choose your language</b>",
        "tk": "[[lang]] <b>Dili saýlaň</b>",
    },
    "lang_set": {
        "ru": "[[ok]] Язык изменён",
        "en": "[[ok]] Language changed",
        "tk": "[[ok]] Dil üýtgedildi",
    },
    "main": {
        "ru": "[[wave]] Приветствую, <b><i>{name}</i></b>\n\n"
              "<b>{bot_name}</b> — виртуальные номера для приёма СМС на любые сервисы.\n\n"
              "[[ok]] Моментальная выдача\n"
              "[[ok]] Возврат, если СМС не пришло\n"
              "[[ok]] {countries}+ стран и {services}+ сервисов\n\n"
              "Выберите нужный раздел ниже.",
        "en": "[[wave]] Welcome, <b><i>{name}</i></b>\n\n"
              "<b>{bot_name}</b> — virtual numbers to receive SMS for any service.\n\n"
              "[[ok]] Instant delivery\n"
              "[[ok]] Refund if no SMS arrives\n"
              "[[ok]] {countries}+ countries and {services}+ services\n\n"
              "Choose a section below.",
        "tk": "[[wave]] Hoş geldiňiz, <b><i>{name}</i></b>\n\n"
              "<b>{bot_name}</b> — islendik hyzmat üçin SMS kabul edýän wirtual belgiler.\n\n"
              "[[ok]] Derrew berilýär\n"
              "[[ok]] SMS gelmese, pul yzyna gaýtarylýar\n"
              "[[ok]] {countries}+ ýurt we {services}+ hyzmat\n\n"
              "Aşakdan bölümi saýlaň.",
    },
    "btn_buy": {"ru": "Купить номер", "en": "Buy number", "tk": "Belgi satyn al"},
    "btn_profile": {"ru": "Профиль", "en": "Profile", "tk": "Profil"},
    "btn_topup": {"ru": "Пополнить", "en": "Top up", "tk": "Doldur"},
    "btn_orders": {"ru": "Мои номера", "en": "My numbers", "tk": "Belgilerim"},
    "btn_lang": {"ru": "Язык", "en": "Language", "tk": "Dil"},
    "btn_support": {"ru": "Поддержка", "en": "Support", "tk": "Goldaw"},
    "btn_channel": {"ru": "Наш канал", "en": "Our channel", "tk": "Kanalymyz"},
    "btn_back": {"ru": "Назад", "en": "Back", "tk": "Yza"},
    "btn_home": {"ru": "Главное меню", "en": "Main menu", "tk": "Baş menýu"},
    "btn_search": {"ru": "Поиск", "en": "Search", "tk": "Gözleg"},
    "btn_all_services": {"ru": "Все сервисы", "en": "All services", "tk": "Ähli hyzmatlar"},

    "profile": {
        "ru": "[[user]] <b>ПРОФИЛЬ</b>\n\n"
              "[[id]] ID: <code>{user_id}</code>\n"
              "[[wallet]] Баланс: <b>{balance}</b>\n"
              "[[orders]] Куплено номеров: <b>{orders}</b>\n"
              "[[clock]] С нами с: <b>{since}</b>",
        "en": "[[user]] <b>PROFILE</b>\n\n"
              "[[id]] ID: <code>{user_id}</code>\n"
              "[[wallet]] Balance: <b>{balance}</b>\n"
              "[[orders]] Numbers bought: <b>{orders}</b>\n"
              "[[clock]] Member since: <b>{since}</b>",
        "tk": "[[user]] <b>PROFIL</b>\n\n"
              "[[id]] ID: <code>{user_id}</code>\n"
              "[[wallet]] Balans: <b>{balance}</b>\n"
              "[[orders]] Satyn alnan belgiler: <b>{orders}</b>\n"
              "[[clock]] Agza bolan senesi: <b>{since}</b>",
    },

    "choose_service": {
        "ru": "[[buy]] <b>ПОКУПКА НОМЕРА</b>\n\n"
              "Выберите сервис или напишите его название.",
        "en": "[[buy]] <b>BUY A NUMBER</b>\n\n"
              "Choose a service or type its name.",
        "tk": "[[buy]] <b>BELGI SATYN ALMAK</b>\n\n"
              "Hyzmaty saýlaň ýa-da adyny ýazyň.",
    },
    "all_services": {
        "ru": "[[service]] <b>ВСЕ СЕРВИСЫ</b>\n\nСтраница {page} из {pages}",
        "en": "[[service]] <b>ALL SERVICES</b>\n\nPage {page} of {pages}",
        "tk": "[[service]] <b>ÄHLI HYZMATLAR</b>\n\nSahypa {page} / {pages}",
    },
    "search_prompt": {
        "ru": "[[search]] <b>ПОИСК</b>\n\nНапишите название сервиса, например <i>Telegram</i>.",
        "en": "[[search]] <b>SEARCH</b>\n\nType the service name, for example <i>Telegram</i>.",
        "tk": "[[search]] <b>GÖZLEG</b>\n\nHyzmatyň adyny ýazyň, mysal üçin <i>Telegram</i>.",
    },
    "search_results": {
        "ru": "[[search]] <b>РЕЗУЛЬТАТЫ</b>\n\nПо запросу «{query}»:",
        "en": "[[search]] <b>RESULTS</b>\n\nFor «{query}»:",
        "tk": "[[search]] <b>NETIJELER</b>\n\n«{query}» boýunça:",
    },
    "search_empty": {
        "ru": "[[warning]] По запросу «{query}» ничего не найдено.",
        "en": "[[warning]] Nothing found for «{query}».",
        "tk": "[[warning]] «{query}» boýunça hiç zat tapylmady.",
    },
    "choose_country": {
        "ru": "[[service]] <b>{service}</b>\n\n"
              "[[globe]] Стран: <b>{total}</b>\n"
              "[[price]] Цены от: <b>{min_price}</b>\n\n"
              "Выберите страну.",
        "en": "[[service]] <b>{service}</b>\n\n"
              "[[globe]] Countries: <b>{total}</b>\n"
              "[[price]] Prices from: <b>{min_price}</b>\n\n"
              "Choose a country.",
        "tk": "[[service]] <b>{service}</b>\n\n"
              "[[globe]] Ýurtlar: <b>{total}</b>\n"
              "[[price]] Bahasy: <b>{min_price}</b>-dan\n\n"
              "Ýurdy saýlaň.",
    },
    "no_countries": {
        "ru": "[[warning]] Для <b>{service}</b> сейчас нет номеров. Попробуйте позже.",
        "en": "[[warning]] No numbers for <b>{service}</b> right now. Try later.",
        "tk": "[[warning]] Häzir <b>{service}</b> üçin belgi ýok. Soňrak synanyşyň.",
    },
    "confirm": {
        "ru": "[[buy]] <b>ОФОРМЛЕНИЕ</b>\n\n"
              "[[service]] {service} · {country}\n"
              "[[price]] Цена: <b>{price}</b>\n"
              "[[stock]] В наличии: <b>{count} шт.</b>\n"
              "[[wallet]] Баланс: <b>{balance}</b>\n\n"
              "Если СМС не придёт — деньги вернутся на баланс.",
        "en": "[[buy]] <b>CHECKOUT</b>\n\n"
              "[[service]] {service} · {country}\n"
              "[[price]] Price: <b>{price}</b>\n"
              "[[stock]] In stock: <b>{count}</b>\n"
              "[[wallet]] Balance: <b>{balance}</b>\n\n"
              "If no SMS arrives, the money returns to your balance.",
        "tk": "[[buy]] <b>SARGYT</b>\n\n"
              "[[service]] {service} · {country}\n"
              "[[price]] Bahasy: <b>{price}</b>\n"
              "[[stock]] Elýeterli: <b>{count} sany</b>\n"
              "[[wallet]] Balans: <b>{balance}</b>\n\n"
              "SMS gelmese, pul balansyňyza gaýdyp geler.",
    },
    "btn_confirm_buy": {"ru": "Купить за {price}", "en": "Buy for {price}", "tk": "{price} bahasyna al"},
    "not_enough": {
        "ru": "\n\n[[warning]] Не хватает <b>{missing}</b> — пополните баланс.",
        "en": "\n\n[[warning]] You need <b>{missing}</b> more — top up your balance.",
        "tk": "\n\n[[warning]] <b>{missing}</b> ýetmeýär — balansy dolduryň.",
    },
    "buying": {
        "ru": "[[wait]] Получаем номер…",
        "en": "[[wait]] Getting a number…",
        "tk": "[[wait]] Belgi alynýar…",
    },
    "no_numbers": {
        "ru": "[[warning]] Номера закончились или цена изменилась. Деньги не списаны — выберите другую страну.",
        "en": "[[warning]] Numbers ran out or the price changed. You were not charged — choose another country.",
        "tk": "[[warning]] Belgiler gutardy ýa-da baha üýtgedi. Pul alynmady — başga ýurt saýlaň.",
    },
    "buy_error": {
        "ru": "[[warning]] Не удалось получить номер, деньги не списаны. Попробуйте через минуту.",
        "en": "[[warning]] Couldn't get a number, you were not charged. Try again in a minute.",
        "tk": "[[warning]] Belgi alyp bolmady, pul alynmady. Bir minutdan synanyşyň.",
    },
    "order_waiting": {
        "ru": "[[phone]] <b>НОМЕР ВЫДАН</b>\n\n"
              "<code>+{phone}</code>\n\n"
              "[[service]] {service} · {country}\n"
              "[[price]] Цена: <b>{price}</b>\n"
              "[[clock]] Ожидание СМС: <b>{left} мин</b>\n\n"
              "Код придёт сюда автоматически.",
        "en": "[[phone]] <b>NUMBER ISSUED</b>\n\n"
              "<code>+{phone}</code>\n\n"
              "[[service]] {service} · {country}\n"
              "[[price]] Price: <b>{price}</b>\n"
              "[[clock]] Waiting for SMS: <b>{left} min</b>\n\n"
              "The code will appear here automatically.",
        "tk": "[[phone]] <b>BELGI BERILDI</b>\n\n"
              "<code>+{phone}</code>\n\n"
              "[[service]] {service} · {country}\n"
              "[[price]] Bahasy: <b>{price}</b>\n"
              "[[clock]] SMS garaşylýar: <b>{left} min</b>\n\n"
              "Kod şu ýere awtomatik geler.",
    },
    "order_code": {
        "ru": "[[ok]] <b>КОД ПОЛУЧЕН</b>\n\n"
              "[[code]] <code>{code}</code>\n\n"
              "[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}",
        "en": "[[ok]] <b>CODE RECEIVED</b>\n\n"
              "[[code]] <code>{code}</code>\n\n"
              "[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}",
        "tk": "[[ok]] <b>KOD GELDI</b>\n\n"
              "[[code]] <code>{code}</code>\n\n"
              "[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}",
    },
    "order_done": {
        "ru": "[[done]] <b>ГОТОВО</b>\n\n"
              "[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}\n"
              "[[code]] Код: <code>{code}</code>",
        "en": "[[done]] <b>DONE</b>\n\n"
              "[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}\n"
              "[[code]] Code: <code>{code}</code>",
        "tk": "[[done]] <b>TAÝÝAR</b>\n\n"
              "[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}\n"
              "[[code]] Kod: <code>{code}</code>",
    },
    "order_cancelled": {
        "ru": "[[cancel]] <b>НОМЕР ОТМЕНЁН</b>\n\n"
              "[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Возвращено: <b>{price}</b>",
        "en": "[[cancel]] <b>NUMBER CANCELLED</b>\n\n"
              "[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Refunded: <b>{price}</b>",
        "tk": "[[cancel]] <b>BELGI ÝATYRYLDY</b>\n\n"
              "[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Gaýtaryldy: <b>{price}</b>",
    },
    "order_timeout": {
        "ru": "[[wait]] <b>СМС НЕ ПРИШЛО</b>\n\n"
              "[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Возвращено: <b>{price}</b>\n\n"
              "Попробуйте другую страну.",
        "en": "[[wait]] <b>NO SMS ARRIVED</b>\n\n"
              "[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Refunded: <b>{price}</b>\n\n"
              "Try another country.",
        "tk": "[[wait]] <b>SMS GELMEDI</b>\n\n"
              "[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Gaýtaryldy: <b>{price}</b>\n\n"
              "Başga ýurt synap görüň.",
    },
    "cancel_early": {
        "ru": "Отменить можно через 2 минуты после покупки",
        "en": "You can cancel 2 minutes after purchase",
        "tk": "Satyn alnandan 2 minut soň ýatyryp bolýar",
    },
    "cancel_failed": {
        "ru": "Не удалось отменить, попробуйте чуть позже",
        "en": "Couldn't cancel, try again a bit later",
        "tk": "Ýatyryp bolmady, birazdan synanyşyň",
    },
    "another_sms_sent": {
        "ru": "Ждём следующее СМС…",
        "en": "Waiting for the next SMS…",
        "tk": "Indiki SMS garaşylýar…",
    },
    "btn_cancel_order": {"ru": "Отменить", "en": "Cancel", "tk": "Ýatyr"},
    "btn_another_sms": {"ru": "Ещё СМС", "en": "Another SMS", "tk": "Ýene SMS"},
    "btn_finish": {"ru": "Завершить", "en": "Finish", "tk": "Tamamla"},
    "btn_copy_phone": {"ru": "Скопировать номер", "en": "Copy number", "tk": "Belgini göçür"},
    "btn_copy_code": {"ru": "Скопировать код", "en": "Copy code", "tk": "Kody göçür"},
    "btn_buy_more": {"ru": "Купить ещё", "en": "Buy more", "tk": "Ýene al"},

    "orders_title": {
        "ru": "[[orders]] <b>МОИ НОМЕРА</b>\n",
        "en": "[[orders]] <b>MY NUMBERS</b>\n",
        "tk": "[[orders]] <b>BELGILERIM</b>\n",
    },
    "orders_empty": {
        "ru": "[[orders]] <b>МОИ НОМЕРА</b>\n\nЗдесь пока пусто.",
        "en": "[[orders]] <b>MY NUMBERS</b>\n\nNothing here yet.",
        "tk": "[[orders]] <b>BELGILERIM</b>\n\nEntek hiç zat ýok.",
    },
    "orders_active_hint": {
        "ru": "\nАктивные номера — в кнопках ниже.",
        "en": "\nActive numbers are in the buttons below.",
        "tk": "\nIşjeň belgiler aşakdaky düwmelerde.",
    },
    "status_waiting": {"ru": "ожидает СМС", "en": "waiting for SMS", "tk": "SMS garaşylýar"},
    "status_got_code": {"ru": "код получен", "en": "code received", "tk": "kod geldi"},
    "status_done": {"ru": "завершён", "en": "completed", "tk": "tamamlandy"},
    "status_cancelled": {"ru": "возврат", "en": "refunded", "tk": "gaýtaryldy"},

    "topup": {
        "ru": "[[wallet]] <b>ПОПОЛНЕНИЕ</b>\n\n"
              "[[money]] Баланс: <b>{balance}</b>\n\n"
              "Выберите способ оплаты.",
        "en": "[[wallet]] <b>TOP UP</b>\n\n"
              "[[money]] Balance: <b>{balance}</b>\n\n"
              "Choose a payment method.",
        "tk": "[[wallet]] <b>DOLDURMAK</b>\n\n"
              "[[money]] Balans: <b>{balance}</b>\n\n"
              "Töleg usulyny saýlaň.",
    },
    "btn_pay_ym_card": {"ru": "Карта: Мир, Visa, Mastercard", "en": "Card: Mir, Visa, Mastercard",
                        "tk": "Karta: Mir, Visa, Mastercard"},
    "btn_pay_ym_wallet": {"ru": "ЮMoney", "en": "YooMoney", "tk": "YooMoney"},
    "btn_pay_cryptomus": {"ru": "Крипта: USDT, TON, BTC", "en": "Crypto: USDT, TON, BTC", "tk": "Kripto: USDT, TON, BTC"},
    "btn_pay_crypto": {"ru": "CryptoBot", "en": "CryptoBot", "tk": "CryptoBot"},
    "btn_pay_stars": {"ru": "Telegram Stars", "en": "Telegram Stars", "tk": "Telegram Stars"},
    "btn_pay_card": {"ru": "Банковская карта", "en": "Bank card", "tk": "Bank kartasy"},
    "choose_network": {
        "ru": "[[crypto]] <b>ВЫБОР СЕТИ</b>\n\n"
              "[[money]] Сумма: <b>{amount}</b>\n\n"
              "Выберите монету и сеть, в которой будете отправлять.",
        "en": "[[crypto]] <b>CHOOSE NETWORK</b>\n\n"
              "[[money]] Amount: <b>{amount}</b>\n\n"
              "Choose the coin and network you will send from.",
        "tk": "[[crypto]] <b>TORY SAÝLAŇ</b>\n\n"
              "[[money]] Mukdar: <b>{amount}</b>\n\n"
              "Iberjek teňňäňizi we toryňyzy saýlaň.",
    },
    "cryptomus_invoice": {
        "ru": "[[crypto]] <b>ОПЛАТА {coin}</b>\n\n"
              "Отправьте ровно:\n<code>{pay_amount}</code> {currency}\n\n"
              "На адрес ({network}):\n<code>{address}</code>\n\n"
              "[[money]] Будет зачислено: <b>{amount}</b>\n"
              "[[clock]] Счёт действует 1 час\n\n"
              "[[warning]] Отправляйте только {currency} в сети {network}, иначе деньги потеряются.",
        "en": "[[crypto]] <b>PAY WITH {coin}</b>\n\n"
              "Send exactly:\n<code>{pay_amount}</code> {currency}\n\n"
              "To the address ({network}):\n<code>{address}</code>\n\n"
              "[[money]] You will get: <b>{amount}</b>\n"
              "[[clock]] Valid for 1 hour\n\n"
              "[[warning]] Send only {currency} on the {network} network, otherwise the funds will be lost.",
        "tk": "[[crypto]] <b>{coin} BILEN TÖLEG</b>\n\n"
              "Takyk şu mukdary iberiň:\n<code>{pay_amount}</code> {currency}\n\n"
              "Şu salga ({network}):\n<code>{address}</code>\n\n"
              "[[money]] Goşular: <b>{amount}</b>\n"
              "[[clock]] Hasap 1 sagat hereket edýär\n\n"
              "[[warning]] Diňe {network} torunda {currency} iberiň, ýogsa pul ýiter.",
    },
    "ym_invoice": {
        "ru": "[[card]] <b>ОПЛАТА {method}</b>\n\n"
              "[[money]] Сумма: <b>{amount}</b>\n\n"
              "Нажмите «Оплатить» и завершите оплату на странице ЮMoney. "
              "Баланс пополнится автоматически в течение минуты.",
        "en": "[[card]] <b>PAY: {method}</b>\n\n"
              "[[money]] Amount: <b>{amount}</b>\n\n"
              "Tap «Pay» and complete the payment on the YooMoney page. "
              "Your balance is topped up automatically within a minute.",
        "tk": "[[card]] <b>TÖLEG: {method}</b>\n\n"
              "[[money]] Mukdar: <b>{amount}</b>\n\n"
              "«Töle» basyň we YooMoney sahypasynda tölegi tamamlaň. "
              "Balans bir minudyň içinde awtomatik doldurylýar.",
    },
    "btn_copy_address": {"ru": "Скопировать адрес", "en": "Copy address", "tk": "Salgyny göçür"},
    "btn_copy_amount": {"ru": "Скопировать сумму", "en": "Copy amount", "tk": "Mukdary göçür"},
    "btn_pay_page": {"ru": "Страница оплаты", "en": "Payment page", "tk": "Töleg sahypasy"},
    "choose_amount": {
        "ru": "[[money]] <b>{method}</b>\n\n"
              "Выберите сумму или отправьте свою.\n"
              "Минимум: <b>{min} ₽</b>",
        "en": "[[money]] <b>{method}</b>\n\n"
              "Choose an amount or send your own.\n"
              "Minimum: <b>{min} ₽</b>",
        "tk": "[[money]] <b>{method}</b>\n\n"
              "Mukdary saýlaň ýa-da öz mukdaryňyzy iberiň.\n"
              "Iň az: <b>{min} ₽</b>",
    },
    "bad_amount": {
        "ru": "[[warning]] Введите число от {min} до 100 000 ₽",
        "en": "[[warning]] Enter a number from {min} to 100 000 ₽",
        "tk": "[[warning]] {min} we 100 000 ₽ aralygynda san giriziň",
    },
    "crypto_invoice": {
        "ru": "[[crypto]] <b>СЧЁТ НА {amount}</b>\n\n"
              "[[ok]]USDT, TON, BTC, ETH и другие\n"
              "[[clock]] Действует 1 час\n\n"
              "Баланс пополнится автоматически после оплаты.",
        "en": "[[crypto]] <b>INVOICE FOR {amount}</b>\n\n"
              "[[ok]]USDT, TON, BTC, ETH and more\n"
              "[[clock]] Valid for 1 hour\n\n"
              "Your balance is topped up automatically after payment.",
        "tk": "[[crypto]] <b>{amount} HASAP</b>\n\n"
              "[[ok]]USDT, TON, BTC, ETH we başgalar\n"
              "[[clock]] 1 sagat hereket edýär\n\n"
              "Tölegden soň balans awtomatik doldurylýar.",
    },
    "stars_invoice_desc": {
        "ru": "Пополнение баланса на {amount}",
        "en": "Balance top-up of {amount}",
        "tk": "Balansy {amount} doldurmak",
    },
    "btn_pay": {"ru": "Оплатить", "en": "Pay", "tk": "Töle"},
    "btn_check_pay": {"ru": "Проверить оплату", "en": "Check payment", "tk": "Tölegi barla"},
    "pay_not_found": {
        "ru": "Оплата пока не найдена. Если вы оплатили — подождите минуту.",
        "en": "Payment not found yet. If you paid, wait a minute.",
        "tk": "Töleg entek tapylmady. Tölän bolsaňyz, bir minut garaşyň.",
    },
    "pay_ok": {
        "ru": "[[ok]] <b>ОПЛАТА ПОЛУЧЕНА</b>\n\n"
              "[[gift]] Зачислено: <b>+{amount}</b>\n"
              "[[wallet]] Баланс: <b>{balance}</b>",
        "en": "[[ok]] <b>PAYMENT RECEIVED</b>\n\n"
              "[[gift]] Credited: <b>+{amount}</b>\n"
              "[[wallet]] Balance: <b>{balance}</b>",
        "tk": "[[ok]] <b>TÖLEG KABUL EDILDI</b>\n\n"
              "[[gift]] Goşuldy: <b>+{amount}</b>\n"
              "[[wallet]] Balans: <b>{balance}</b>",
    },
    "pay_unavailable": {
        "ru": "[[warning]] Этот способ оплаты сейчас недоступен.",
        "en": "[[warning]] This payment method is unavailable right now.",
        "tk": "[[warning]] Bu töleg usuly häzir elýeterli däl.",
    },
    "banned": {
        "ru": "[[cancel]] Доступ ограничен. Обратитесь в поддержку.",
        "en": "[[cancel]] Access restricted. Please contact support.",
        "tk": "[[cancel]] Giriş çäklendirildi. Goldaw bilen habarlaşyň.",
    },
    "banned_short": {"ru": "Доступ ограничен", "en": "Access restricted", "tk": "Giriş çäklendirildi"},
    "btn_mail": {"ru": "Временная почта", "en": "Temp mail", "tk": "Wagtlaýyn poçta"},
    "btn_refresh": {"ru": "Обновить", "en": "Refresh", "tk": "Täzele"},
    "btn_my_mails": {"ru": "Мои почты", "en": "My mailboxes", "tk": "Poçtalarym"},
    "btn_inbox": {"ru": "Входящие", "en": "Inbox", "tk": "Gelen hatlar"},
    "btn_copy_mail": {"ru": "Скопировать адрес", "en": "Copy address", "tk": "Salgyny göçür"},
    "tier_10min": {"ru": "10 минут", "en": "10 minutes", "tk": "10 minut"},
    "tier_1hour": {"ru": "1 час", "en": "1 hour", "tk": "1 sagat"},
    "tier_1day": {"ru": "1 день", "en": "1 day", "tk": "1 gün"},
    "tier_permanent": {"ru": "60 дней", "en": "60 days", "tk": "60 gün"},
    "mail_menu": {
        "ru": "[[mail]] <b>ВРЕМЕННАЯ ПОЧТА</b>\n\n"
              "Одноразовый e-mail для регистраций и кодов подтверждения.\n\n"
              "[[ok]] Адрес выдаётся сразу\n"
              "[[ok]] Письма приходят прямо в бот\n"
              "[[ok]] Коды из писем — с кнопкой «Скопировать»\n\n"
              "Выберите срок действия:",
        "en": "[[mail]] <b>TEMP MAIL</b>\n\n"
              "A disposable e-mail for sign-ups and verification codes.\n\n"
              "[[ok]] Address is issued instantly\n"
              "[[ok]] Emails arrive right in the bot\n"
              "[[ok]] Codes from emails come with a «Copy» button\n\n"
              "Choose how long it should last:",
        "tk": "[[mail]] <b>WAGTLAÝYN POÇTA</b>\n\n"
              "Hasaba durmak we tassyklama kodlary üçin bir gezeklik e-mail.\n\n"
              "[[ok]] Salgy derrew berilýär\n"
              "[[ok]] Hatlar göni bota gelýär\n"
              "[[ok]] Hatlardaky kodlar «Göçür» düwmesi bilen\n\n"
              "Möhletini saýlaň:",
    },
    "mail_card": {
        "ru": "[[mail]] <b>ВАША ПОЧТА</b>\n\n"
              "<code>{address}</code>\n\n"
              "[[clock]] Действует до: <b>{expires}</b>\n"
              "[[inbox]] Писем: <b>{count}</b>\n\n"
              "Новые письма придут сюда автоматически.",
        "en": "[[mail]] <b>YOUR MAILBOX</b>\n\n"
              "<code>{address}</code>\n\n"
              "[[clock]] Valid until: <b>{expires}</b>\n"
              "[[inbox]] Emails: <b>{count}</b>\n\n"
              "New emails will arrive here automatically.",
        "tk": "[[mail]] <b>POÇTAŇYZ</b>\n\n"
              "<code>{address}</code>\n\n"
              "[[clock]] Möhleti: <b>{expires}</b> çenli\n"
              "[[inbox]] Hatlar: <b>{count}</b>\n\n"
              "Täze hatlar şu ýere awtomatik geler.",
    },
    "mail_expired": {
        "ru": "[[mail]] <b>ПОЧТА ИСТЕКЛА</b>\n\n<code>{address}</code>\n\n[[inbox]] Писем было: <b>{count}</b>",
        "en": "[[mail]] <b>MAILBOX EXPIRED</b>\n\n<code>{address}</code>\n\n[[inbox]] Emails received: <b>{count}</b>",
        "tk": "[[mail]] <b>POÇTANYŇ MÖHLETI GUTARDY</b>\n\n<code>{address}</code>\n\n[[inbox]] Gelen hatlar: <b>{count}</b>",
    },
    "mail_new": {
        "ru": "[[inbox]] <b>НОВОЕ ПИСЬМО</b>\n\n"
              "[[mail]] Кому: <code>{address}</code>\n"
              "[[user]] От: {sender}\n"
              "[[info]] Тема: <b>{subject}</b>{code_line}\n\n"
              "{body}",
        "en": "[[inbox]] <b>NEW EMAIL</b>\n\n"
              "[[mail]] To: <code>{address}</code>\n"
              "[[user]] From: {sender}\n"
              "[[info]] Subject: <b>{subject}</b>{code_line}\n\n"
              "{body}",
        "tk": "[[inbox]] <b>TÄZE HAT</b>\n\n"
              "[[mail]] Kime: <code>{address}</code>\n"
              "[[user]] Kimden: {sender}\n"
              "[[info]] Tema: <b>{subject}</b>{code_line}\n\n"
              "{body}",
    },
    "mail_code_line": {
        "ru": "\n[[code]] Код: <code>{code}</code>",
        "en": "\n[[code]] Code: <code>{code}</code>",
        "tk": "\n[[code]] Kod: <code>{code}</code>",
    },
    "inbox_title": {
        "ru": "[[inbox]] <b>ВХОДЯЩИЕ</b> · <code>{address}</code>\n",
        "en": "[[inbox]] <b>INBOX</b> · <code>{address}</code>\n",
        "tk": "[[inbox]] <b>GELEN HATLAR</b> · <code>{address}</code>\n",
    },
    "inbox_empty": {
        "ru": "\nПисем пока нет. Как только придёт письмо — бот пришлёт его сюда.",
        "en": "\nNo emails yet. As soon as one arrives, the bot will send it here.",
        "tk": "\nEntek hat ýok. Hat gelen badyna bot ony şu ýere iberer.",
    },
    "my_mails_title": {
        "ru": "[[mail]] <b>МОИ ПОЧТЫ</b>\n",
        "en": "[[mail]] <b>MY MAILBOXES</b>\n",
        "tk": "[[mail]] <b>POÇTALARYM</b>\n",
    },
    "my_mails_empty": {
        "ru": "[[mail]] <b>МОИ ПОЧТЫ</b>\n\nЗдесь пока пусто.",
        "en": "[[mail]] <b>MY MAILBOXES</b>\n\nNothing here yet.",
        "tk": "[[mail]] <b>POÇTALARYM</b>\n\nEntek hiç zat ýok.",
    },
    "mail_active": {"ru": "активна", "en": "active", "tk": "işjeň"},
    "mail_expired_short": {"ru": "истекла", "en": "expired", "tk": "möhleti gutardy"},
    "mail_error": {
        "ru": "[[warning]] Не удалось создать почту, деньги не списаны. Попробуйте через минуту.",
        "en": "[[warning]] Couldn't create a mailbox, you were not charged. Try again in a minute.",
        "tk": "[[warning]] Poçta döredip bolmady, pul alynmady. Bir minutdan synanyşyň.",
    },
    "mail_not_enough": {
        "ru": "[[warning]] Не хватает <b>{missing}</b> — пополните баланс.",
        "en": "[[warning]] You need <b>{missing}</b> more — top up your balance.",
        "tk": "[[warning]] <b>{missing}</b> ýetmeýär — balansy dolduryň.",
    },
    "support": {
        "ru": "[[support]] <b>ПОДДЕРЖКА</b>\n\nОтветим на любые вопросы: {contact}",
        "en": "[[support]] <b>SUPPORT</b>\n\nWe answer any questions: {contact}",
        "tk": "[[support]] <b>GOLDAW</b>\n\nIslendik soraga jogap berýäris: {contact}",
    },
}

_marker = re.compile(r"\[\[([a-z_]+)\]\]")


def t(lang: str | None, key: str, **kwargs) -> str:
    variants = TEXTS[key]
    text = variants.get(lang or DEFAULT_LANG) or variants[DEFAULT_LANG]
    # Эмодзи подставляются до format, чтобы пользовательский текст не превращался в эмодзи.
    text = _marker.sub(lambda m: e(m.group(1)), text)
    if kwargs:
        text = text.format(**kwargs)
    return text


def plain_t(lang: str | None, key: str, **kwargs) -> str:
    """Текст без эмодзи и разметки — для всплывающих уведомлений."""
    variants = TEXTS[key]
    text = variants.get(lang or DEFAULT_LANG) or variants[DEFAULT_LANG]
    text = _marker.sub("", text).strip()
    return text.format(**kwargs) if kwargs else text


def fmt_money(kopecks: int) -> str:
    if kopecks % 100 == 0:
        return f"{kopecks // 100:,} ₽".replace(",", " ")
    return f"{kopecks / 100:,.2f} ₽".replace(",", " ")
