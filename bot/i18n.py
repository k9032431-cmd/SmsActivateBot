"""Тексты бота на трёх языках.

[[имя]] — место для (премиум-)эмодзи из emoji.py.
Рамки сделаны цитатными блоками Telegram (<blockquote>), они выглядят как карточки.
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
        "ru": "[[logo]] <b>{bot_name}</b> [[sparkle]]\n"
              "<i>Виртуальные номера для приёма СМС</i>\n\n"
              "<blockquote>[[user]] <b>{name}</b>\n"
              "[[id]] ID · <code>{user_id}</code>\n"
              "[[wallet]] Баланс · <b>{balance}</b></blockquote>\n\n"
              "<blockquote>[[lightning]] Номер выдаётся моментально\n"
              "[[shield]] Нет СМС — деньги вернутся\n"
              "[[globe]] {countries}+ стран · {services}+ сервисов</blockquote>\n\n"
              "[[down]] <b>Выберите действие</b>",
        "en": "[[logo]] <b>{bot_name}</b> [[sparkle]]\n"
              "<i>Virtual numbers to receive SMS</i>\n\n"
              "<blockquote>[[user]] <b>{name}</b>\n"
              "[[id]] ID · <code>{user_id}</code>\n"
              "[[wallet]] Balance · <b>{balance}</b></blockquote>\n\n"
              "<blockquote>[[lightning]] Instant number delivery\n"
              "[[shield]] No SMS — full refund\n"
              "[[globe]] {countries}+ countries · {services}+ services</blockquote>\n\n"
              "[[down]] <b>Choose an action</b>",
        "tk": "[[logo]] <b>{bot_name}</b> [[sparkle]]\n"
              "<i>SMS kabul etmek üçin wirtual belgiler</i>\n\n"
              "<blockquote>[[user]] <b>{name}</b>\n"
              "[[id]] ID · <code>{user_id}</code>\n"
              "[[wallet]] Balans · <b>{balance}</b></blockquote>\n\n"
              "<blockquote>[[lightning]] Belgi derrew berilýär\n"
              "[[shield]] SMS gelmese — pul yzyna gaýtarylýar\n"
              "[[globe]] {countries}+ ýurt · {services}+ hyzmat</blockquote>\n\n"
              "[[down]] <b>Hereketi saýlaň</b>",
    },
    "btn_buy": {"ru": "Купить номер", "en": "Buy number", "tk": "Belgi satyn al"},
    "btn_topup": {"ru": "Пополнить", "en": "Top up", "tk": "Doldur"},
    "btn_orders": {"ru": "Мои номера", "en": "My numbers", "tk": "Belgilerim"},
    "btn_lang": {"ru": "Язык", "en": "Language", "tk": "Dil"},
    "btn_support": {"ru": "Поддержка", "en": "Support", "tk": "Goldaw"},
    "btn_channel": {"ru": "Наш канал", "en": "Our channel", "tk": "Kanalymyz"},
    "btn_back": {"ru": "Назад", "en": "Back", "tk": "Yza"},
    "btn_home": {"ru": "Главное меню", "en": "Main menu", "tk": "Baş menýu"},
    "btn_search": {"ru": "Поиск", "en": "Search", "tk": "Gözleg"},
    "btn_all_services": {"ru": "Все сервисы", "en": "All services", "tk": "Ähli hyzmatlar"},

    "choose_service": {
        "ru": "[[buy]] <b>Покупка номера</b>\n\n"
              "<blockquote>[[fire]] Ниже — самые популярные сервисы\n"
              "[[search]] Нужного нет? Нажмите «Поиск» или просто напишите название</blockquote>\n\n"
              "[[down]] <b>Выберите сервис</b>",
        "en": "[[buy]] <b>Buy a number</b>\n\n"
              "<blockquote>[[fire]] The most popular services are below\n"
              "[[search]] Not there? Tap «Search» or just type the name</blockquote>\n\n"
              "[[down]] <b>Choose a service</b>",
        "tk": "[[buy]] <b>Belgi satyn almak</b>\n\n"
              "<blockquote>[[fire]] Aşakda iň meşhur hyzmatlar\n"
              "[[search]] Gerekli ýokmy? «Gözleg» basyň ýa-da adyny ýazyň</blockquote>\n\n"
              "[[down]] <b>Hyzmaty saýlaň</b>",
    },
    "all_services": {
        "ru": "[[service]] <b>Все сервисы</b>\n<blockquote>[[info]] Страница {page} из {pages}</blockquote>",
        "en": "[[service]] <b>All services</b>\n<blockquote>[[info]] Page {page} of {pages}</blockquote>",
        "tk": "[[service]] <b>Ähli hyzmatlar</b>\n<blockquote>[[info]] Sahypa {page} / {pages}</blockquote>",
    },
    "search_prompt": {
        "ru": "[[search]] <b>Поиск сервиса</b>\n\n"
              "<blockquote>Отправьте название, например:\n<i>Telegram · WhatsApp · Google</i></blockquote>",
        "en": "[[search]] <b>Service search</b>\n\n"
              "<blockquote>Send the name, for example:\n<i>Telegram · WhatsApp · Google</i></blockquote>",
        "tk": "[[search]] <b>Hyzmat gözlemek</b>\n\n"
              "<blockquote>Adyny iberiň, mysal üçin:\n<i>Telegram · WhatsApp · Google</i></blockquote>",
    },
    "search_results": {
        "ru": "[[search]] <b>Результаты поиска</b>\n<blockquote>По запросу «<b>{query}</b>»</blockquote>",
        "en": "[[search]] <b>Search results</b>\n<blockquote>For «<b>{query}</b>»</blockquote>",
        "tk": "[[search]] <b>Gözleg netijeleri</b>\n<blockquote>«<b>{query}</b>» boýunça</blockquote>",
    },
    "search_empty": {
        "ru": "[[warning]] <b>Ничего не найдено</b>\n"
              "<blockquote>По запросу «<b>{query}</b>» сервисов нет.\nПопробуйте другое название.</blockquote>",
        "en": "[[warning]] <b>Nothing found</b>\n"
              "<blockquote>No services for «<b>{query}</b>».\nTry another name.</blockquote>",
        "tk": "[[warning]] <b>Hiç zat tapylmady</b>\n"
              "<blockquote>«<b>{query}</b>» boýunça hyzmat ýok.\nBaşga at synap görüň.</blockquote>",
    },
    "choose_country": {
        "ru": "[[service]] <b>{service}</b>\n\n"
              "<blockquote>[[globe]] Доступно стран · <b>{total}</b>\n"
              "[[price]] Цены от · <b>{min_price}</b>\n"
              "[[info]] Страница {page} из {pages}</blockquote>\n\n"
              "[[down]] <b>Выберите страну</b> <i>(сначала дешёвые)</i>",
        "en": "[[service]] <b>{service}</b>\n\n"
              "<blockquote>[[globe]] Countries available · <b>{total}</b>\n"
              "[[price]] Prices from · <b>{min_price}</b>\n"
              "[[info]] Page {page} of {pages}</blockquote>\n\n"
              "[[down]] <b>Choose a country</b> <i>(cheapest first)</i>",
        "tk": "[[service]] <b>{service}</b>\n\n"
              "<blockquote>[[globe]] Elýeterli ýurtlar · <b>{total}</b>\n"
              "[[price]] Bahasy · <b>{min_price}</b>-dan\n"
              "[[info]] Sahypa {page} / {pages}</blockquote>\n\n"
              "[[down]] <b>Ýurdy saýlaň</b> <i>(arzanlary ilki)</i>",
    },
    "no_countries": {
        "ru": "[[warning]] <b>Нет свободных номеров</b>\n"
              "<blockquote>Для <b>{service}</b> сейчас номеров нет.\nПопробуйте немного позже.</blockquote>",
        "en": "[[warning]] <b>No numbers available</b>\n"
              "<blockquote>No numbers for <b>{service}</b> right now.\nPlease try a bit later.</blockquote>",
        "tk": "[[warning]] <b>Boş belgi ýok</b>\n"
              "<blockquote>Häzir <b>{service}</b> üçin belgi ýok.\nBiraz soňrak synanyşyň.</blockquote>",
    },
    "confirm": {
        "ru": "[[buy]] <b>Оформление заказа</b>\n\n"
              "<blockquote>[[service]] Сервис · <b>{service}</b>\n"
              "[[globe]] Страна · <b>{country}</b>\n"
              "[[stock]] В наличии · <b>{count}</b> шт.</blockquote>\n\n"
              "<blockquote>[[price]] Цена · <b>{price}</b>\n"
              "[[wallet]] Ваш баланс · <b>{balance}</b></blockquote>\n\n"
              "[[shield]] <i>Если СМС не придёт — деньги автоматически вернутся на баланс</i>",
        "en": "[[buy]] <b>Checkout</b>\n\n"
              "<blockquote>[[service]] Service · <b>{service}</b>\n"
              "[[globe]] Country · <b>{country}</b>\n"
              "[[stock]] In stock · <b>{count}</b></blockquote>\n\n"
              "<blockquote>[[price]] Price · <b>{price}</b>\n"
              "[[wallet]] Your balance · <b>{balance}</b></blockquote>\n\n"
              "[[shield]] <i>If no SMS arrives, the money is returned to your balance automatically</i>",
        "tk": "[[buy]] <b>Sargyt etmek</b>\n\n"
              "<blockquote>[[service]] Hyzmat · <b>{service}</b>\n"
              "[[globe]] Ýurt · <b>{country}</b>\n"
              "[[stock]] Elýeterli · <b>{count}</b> sany</blockquote>\n\n"
              "<blockquote>[[price]] Bahasy · <b>{price}</b>\n"
              "[[wallet]] Balansyňyz · <b>{balance}</b></blockquote>\n\n"
              "[[shield]] <i>SMS gelmese — pul balansyňyza awtomatik gaýtarylýar</i>",
    },
    "btn_confirm_buy": {"ru": "Купить за {price}", "en": "Buy for {price}", "tk": "{price} bahasyna al"},
    "not_enough": {
        "ru": "\n\n[[warning]] <b>Недостаточно средств</b>\n"
              "<blockquote>Не хватает · <b>{missing}</b>\nПополните баланс и возвращайтесь [[down]]</blockquote>",
        "en": "\n\n[[warning]] <b>Insufficient funds</b>\n"
              "<blockquote>Missing · <b>{missing}</b>\nTop up your balance and come back [[down]]</blockquote>",
        "tk": "\n\n[[warning]] <b>Balans ýeterlik däl</b>\n"
              "<blockquote>Ýetmeýär · <b>{missing}</b>\nBalansy dolduryň we yzyna geliň [[down]]</blockquote>",
    },
    "buying": {
        "ru": "[[wait]] Получаем номер…",
        "en": "[[wait]] Getting a number…",
        "tk": "[[wait]] Belgi alynýar…",
    },
    "no_numbers": {
        "ru": "[[warning]] <b>Номер не получен</b>\n"
              "<blockquote>Номера закончились или цена изменилась.\nДеньги не списаны — выберите другую страну.</blockquote>",
        "en": "[[warning]] <b>Number not received</b>\n"
              "<blockquote>Numbers ran out or the price changed.\nYou were not charged — choose another country.</blockquote>",
        "tk": "[[warning]] <b>Belgi alynmady</b>\n"
              "<blockquote>Belgiler gutardy ýa-da baha üýtgedi.\nPul alynmady — başga ýurt saýlaň.</blockquote>",
    },
    "buy_error": {
        "ru": "[[warning]] <b>Временная ошибка</b>\n"
              "<blockquote>Не удалось получить номер, деньги не списаны.\nПопробуйте через минуту.</blockquote>",
        "en": "[[warning]] <b>Temporary error</b>\n"
              "<blockquote>Couldn't get a number, you were not charged.\nPlease try again in a minute.</blockquote>",
        "tk": "[[warning]] <b>Wagtlaýyn ýalňyşlyk</b>\n"
              "<blockquote>Belgi alyp bolmady, pul alynmady.\nBir minutdan synanyşyň.</blockquote>",
    },
    "order_waiting": {
        "ru": "[[ok]] <b>Номер выдан</b> [[sparkle]]\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code></blockquote>\n\n"
              "<blockquote>[[service]] Сервис · <b>{service}</b>\n"
              "[[globe]] Страна · <b>{country}</b>\n"
              "[[price]] Цена · <b>{price}</b></blockquote>\n\n"
              "<blockquote>[[wait]] <b>Ожидаем СМС…</b>\n"
              "{bar}\n"
              "[[clock]] Осталось · <b>{left} мин</b></blockquote>\n\n"
              "[[bell]] <i>Код придёт сюда автоматически</i>",
        "en": "[[ok]] <b>Number issued</b> [[sparkle]]\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code></blockquote>\n\n"
              "<blockquote>[[service]] Service · <b>{service}</b>\n"
              "[[globe]] Country · <b>{country}</b>\n"
              "[[price]] Price · <b>{price}</b></blockquote>\n\n"
              "<blockquote>[[wait]] <b>Waiting for SMS…</b>\n"
              "{bar}\n"
              "[[clock]] Time left · <b>{left} min</b></blockquote>\n\n"
              "[[bell]] <i>The code will appear here automatically</i>",
        "tk": "[[ok]] <b>Belgi berildi</b> [[sparkle]]\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code></blockquote>\n\n"
              "<blockquote>[[service]] Hyzmat · <b>{service}</b>\n"
              "[[globe]] Ýurt · <b>{country}</b>\n"
              "[[price]] Bahasy · <b>{price}</b></blockquote>\n\n"
              "<blockquote>[[wait]] <b>SMS garaşylýar…</b>\n"
              "{bar}\n"
              "[[clock]] Galan wagt · <b>{left} min</b></blockquote>\n\n"
              "[[bell]] <i>Kod şu ýere awtomatik geler</i>",
    },
    "order_code": {
        "ru": "[[ok]] <b>СМС получено!</b> [[sparkle]]\n\n"
              "<blockquote>[[code]] Код · <code>{code}</code></blockquote>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}</blockquote>\n\n"
              "[[sms]] <i>Нужен ещё код на этот номер? Нажмите «Ещё СМС»</i>",
        "en": "[[ok]] <b>SMS received!</b> [[sparkle]]\n\n"
              "<blockquote>[[code]] Code · <code>{code}</code></blockquote>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}</blockquote>\n\n"
              "[[sms]] <i>Need another code on this number? Tap «Another SMS»</i>",
        "tk": "[[ok]] <b>SMS geldi!</b> [[sparkle]]\n\n"
              "<blockquote>[[code]] Kod · <code>{code}</code></blockquote>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}</blockquote>\n\n"
              "[[sms]] <i>Şu belgä ýene kod gerekmi? «Ýene SMS» basyň</i>",
    },
    "order_done": {
        "ru": "[[done]] <b>Активация завершена</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}\n"
              "[[code]] Код · <code>{code}</code></blockquote>\n\n"
              "[[sparkle]] <i>Спасибо за покупку!</i>",
        "en": "[[done]] <b>Activation completed</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}\n"
              "[[code]] Code · <code>{code}</code></blockquote>\n\n"
              "[[sparkle]] <i>Thank you for your purchase!</i>",
        "tk": "[[done]] <b>Aktiwasiýa tamamlandy</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code>\n"
              "[[service]] {service} · {country}\n"
              "[[code]] Kod · <code>{code}</code></blockquote>\n\n"
              "[[sparkle]] <i>Satyn alanyňyz üçin sag boluň!</i>",
    },
    "order_cancelled": {
        "ru": "[[cancel]] <b>Номер отменён</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Возвращено · <b>{price}</b></blockquote>",
        "en": "[[cancel]] <b>Number cancelled</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Refunded · <b>{price}</b></blockquote>",
        "tk": "[[cancel]] <b>Belgi ýatyryldy</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] Gaýtaryldy · <b>{price}</b></blockquote>",
    },
    "order_timeout": {
        "ru": "[[wait]] <b>Время ожидания истекло</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code> · {service}\n"
              "[[sms]] СМС не пришло\n"
              "[[money]] Возвращено · <b>{price}</b></blockquote>\n\n"
              "[[info]] <i>Попробуйте другую страну</i>",
        "en": "[[wait]] <b>Time is up</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code> · {service}\n"
              "[[sms]] No SMS arrived\n"
              "[[money]] Refunded · <b>{price}</b></blockquote>\n\n"
              "[[info]] <i>Try another country</i>",
        "tk": "[[wait]] <b>Garaşmak wagty gutardy</b>\n\n"
              "<blockquote>[[phone]] <code>+{phone}</code> · {service}\n"
              "[[sms]] SMS gelmedi\n"
              "[[money]] Gaýtaryldy · <b>{price}</b></blockquote>\n\n"
              "[[info]] <i>Başga ýurt synap görüň</i>",
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
    "btn_cancel_order": {"ru": "Отменить номер", "en": "Cancel number", "tk": "Belgini ýatyr"},
    "btn_another_sms": {"ru": "Ещё СМС", "en": "Another SMS", "tk": "Ýene SMS"},
    "btn_finish": {"ru": "Завершить", "en": "Finish", "tk": "Tamamla"},
    "btn_copy_phone": {"ru": "Скопировать номер", "en": "Copy number", "tk": "Belgini göçür"},
    "btn_copy_code": {"ru": "Скопировать код", "en": "Copy code", "tk": "Kody göçür"},
    "btn_buy_more": {"ru": "Купить ещё", "en": "Buy more", "tk": "Ýene al"},

    "orders_title": {
        "ru": "[[orders]] <b>Мои номера</b>\n<i>Последние 10 заказов</i>",
        "en": "[[orders]] <b>My numbers</b>\n<i>Last 10 orders</i>",
        "tk": "[[orders]] <b>Meniň belgilerim</b>\n<i>Soňky 10 sargyt</i>",
    },
    "orders_empty": {
        "ru": "[[orders]] <b>Мои номера</b>\n\n<blockquote>[[box]] У вас пока нет номеров.\n"
              "Купите первый — это займёт пару секунд [[rocket]]</blockquote>",
        "en": "[[orders]] <b>My numbers</b>\n\n<blockquote>[[box]] You have no numbers yet.\n"
              "Buy your first one — it takes seconds [[rocket]]</blockquote>",
        "tk": "[[orders]] <b>Meniň belgilerim</b>\n\n<blockquote>[[box]] Entek belgiňiz ýok.\n"
              "Ilkinjisini alyň — bary-ýogy birnäçe sekunt [[rocket]]</blockquote>",
    },
    "orders_active_hint": {
        "ru": "[[down]] <b>Активные номера</b> — нажмите, чтобы открыть",
        "en": "[[down]] <b>Active numbers</b> — tap to open",
        "tk": "[[down]] <b>Işjeň belgiler</b> — açmak üçin basyň",
    },
    "status_waiting": {"ru": "ожидает СМС", "en": "waiting for SMS", "tk": "SMS garaşylýar"},
    "status_got_code": {"ru": "код получен", "en": "code received", "tk": "kod geldi"},
    "status_done": {"ru": "завершён", "en": "completed", "tk": "tamamlandy"},
    "status_cancelled": {"ru": "отменён, деньги возвращены", "en": "cancelled, refunded", "tk": "ýatyryldy, pul gaýtaryldy"},

    "topup": {
        "ru": "[[wallet]] <b>Пополнение баланса</b>\n\n"
              "<blockquote>[[money]] Текущий баланс · <b>{balance}</b></blockquote>\n\n"
              "<blockquote>[[crypto]] <b>Крипта</b> — USDT, TON, BTC и др.\n"
              "[[star]] <b>Telegram Stars</b> — прямо в Telegram\n"
              "[[card]] <b>Карта</b> — оплата в рублях</blockquote>\n\n"
              "[[down]] <b>Выберите способ оплаты</b>",
        "en": "[[wallet]] <b>Top up balance</b>\n\n"
              "<blockquote>[[money]] Current balance · <b>{balance}</b></blockquote>\n\n"
              "<blockquote>[[crypto]] <b>Crypto</b> — USDT, TON, BTC, etc.\n"
              "[[star]] <b>Telegram Stars</b> — right inside Telegram\n"
              "[[card]] <b>Card</b> — pay in rubles</blockquote>\n\n"
              "[[down]] <b>Choose a payment method</b>",
        "tk": "[[wallet]] <b>Balansy doldurmak</b>\n\n"
              "<blockquote>[[money]] Häzirki balans · <b>{balance}</b></blockquote>\n\n"
              "<blockquote>[[crypto]] <b>Kripto</b> — USDT, TON, BTC we ş.m.\n"
              "[[star]] <b>Telegram Stars</b> — göni Telegramda\n"
              "[[card]] <b>Karta</b> — rubl bilen tölemek</blockquote>\n\n"
              "[[down]] <b>Töleg usulyny saýlaň</b>",
    },
    "btn_pay_crypto": {"ru": "Криптовалюта", "en": "Cryptocurrency", "tk": "Kriptowalýuta"},
    "btn_pay_stars": {"ru": "Telegram Stars", "en": "Telegram Stars", "tk": "Telegram Stars"},
    "btn_pay_card": {"ru": "Банковская карта", "en": "Bank card", "tk": "Bank kartasy"},
    "choose_amount": {
        "ru": "[[money]] <b>{method}</b>\n\n"
              "<blockquote>[[info]] Выберите сумму ниже\nили отправьте свою числом\n"
              "[[check]] Минимум · <b>{min} ₽</b></blockquote>",
        "en": "[[money]] <b>{method}</b>\n\n"
              "<blockquote>[[info]] Choose an amount below\nor send your own as a number\n"
              "[[check]] Minimum · <b>{min} ₽</b></blockquote>",
        "tk": "[[money]] <b>{method}</b>\n\n"
              "<blockquote>[[info]] Aşakdan mukdary saýlaň\nýa-da öz mukdaryňyzy san bilen iberiň\n"
              "[[check]] Iň az · <b>{min} ₽</b></blockquote>",
    },
    "bad_amount": {
        "ru": "[[warning]] <b>Неверная сумма</b>\n<blockquote>Введите число от {min} до 100 000 ₽</blockquote>",
        "en": "[[warning]] <b>Invalid amount</b>\n<blockquote>Enter a number from {min} to 100 000 ₽</blockquote>",
        "tk": "[[warning]] <b>Nädogry mukdar</b>\n<blockquote>{min} we 100 000 ₽ aralygynda san giriziň</blockquote>",
    },
    "crypto_invoice": {
        "ru": "[[crypto]] <b>Счёт создан</b>\n\n"
              "<blockquote>[[money]] Сумма · <b>{amount}</b>\n"
              "[[diamond]] Оплата · USDT, TON, BTC, ETH и др.\n"
              "[[clock]] Счёт действует · <b>1 час</b></blockquote>\n\n"
              "[[check]] <i>Баланс пополнится автоматически после оплаты</i>",
        "en": "[[crypto]] <b>Invoice created</b>\n\n"
              "<blockquote>[[money]] Amount · <b>{amount}</b>\n"
              "[[diamond]] Pay with · USDT, TON, BTC, ETH, etc.\n"
              "[[clock]] Valid for · <b>1 hour</b></blockquote>\n\n"
              "[[check]] <i>Your balance is topped up automatically after payment</i>",
        "tk": "[[crypto]] <b>Hasap döredildi</b>\n\n"
              "<blockquote>[[money]] Mukdar · <b>{amount}</b>\n"
              "[[diamond]] Töleg · USDT, TON, BTC, ETH we ş.m.\n"
              "[[clock]] Hereket edýär · <b>1 sagat</b></blockquote>\n\n"
              "[[check]] <i>Tölegden soň balans awtomatik doldurylýar</i>",
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
        "ru": "[[ok]] <b>Оплата получена!</b> [[sparkle]]\n\n"
              "<blockquote>[[gift]] Зачислено · <b>+{amount}</b>\n"
              "[[wallet]] Баланс · <b>{balance}</b></blockquote>\n\n"
              "[[rocket]] <i>Можно покупать номера</i>",
        "en": "[[ok]] <b>Payment received!</b> [[sparkle]]\n\n"
              "<blockquote>[[gift]] Credited · <b>+{amount}</b>\n"
              "[[wallet]] Balance · <b>{balance}</b></blockquote>\n\n"
              "[[rocket]] <i>You can buy numbers now</i>",
        "tk": "[[ok]] <b>Töleg kabul edildi!</b> [[sparkle]]\n\n"
              "<blockquote>[[gift]] Goşuldy · <b>+{amount}</b>\n"
              "[[wallet]] Balans · <b>{balance}</b></blockquote>\n\n"
              "[[rocket]] <i>Indi belgi satyn alyp bilersiňiz</i>",
    },
    "pay_unavailable": {
        "ru": "[[warning]] <b>Способ оплаты недоступен</b>\n<blockquote>Выберите другой способ или попробуйте позже.</blockquote>",
        "en": "[[warning]] <b>Payment method unavailable</b>\n<blockquote>Choose another method or try later.</blockquote>",
        "tk": "[[warning]] <b>Töleg usuly elýeterli däl</b>\n<blockquote>Başga usul saýlaň ýa-da soňrak synanyşyň.</blockquote>",
    },
    "banned": {
        "ru": "[[cancel]] <b>Доступ ограничен</b>\n<blockquote>Обратитесь в поддержку.</blockquote>",
        "en": "[[cancel]] <b>Access restricted</b>\n<blockquote>Please contact support.</blockquote>",
        "tk": "[[cancel]] <b>Giriş çäklendirildi</b>\n<blockquote>Goldaw bilen habarlaşyň.</blockquote>",
    },
    "banned_short": {"ru": "Доступ ограничен", "en": "Access restricted", "tk": "Giriş çäklendirildi"},
    "support": {
        "ru": "[[support]] <b>Поддержка</b>\n\n"
              "<blockquote>[[sms]] Ответим на любые вопросы\n[[clock]] Обычно в течение нескольких минут</blockquote>\n\n"
              "[[down]] Пишите: {contact}",
        "en": "[[support]] <b>Support</b>\n\n"
              "<blockquote>[[sms]] We answer any questions\n[[clock]] Usually within a few minutes</blockquote>\n\n"
              "[[down]] Write to: {contact}",
        "tk": "[[support]] <b>Goldaw</b>\n\n"
              "<blockquote>[[sms]] Islendik soraga jogap berýäris\n[[clock]] Adatça birnäçe minudyň içinde</blockquote>\n\n"
              "[[down]] Ýazyň: {contact}",
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


def progress_bar(done: float, width: int = 10) -> str:
    filled = max(0, min(width, round(done * width)))
    return "▰" * filled + "▱" * (width - filled)


def fmt_money(kopecks: int) -> str:
    if kopecks % 100 == 0:
        return f"{kopecks // 100:,} ₽".replace(",", " ")
    return f"{kopecks / 100:,.2f} ₽".replace(",", " ")
