"""Тексты бота на трёх языках. [[имя]] — место для (премиум-)эмодзи из emoji.py."""
import re

from .emoji import e

LANGS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English", "tk": "🇹🇲 Türkmençe"}
DEFAULT_LANG = "ru"
LINE = "━━━━━━━━━━━━━━━"

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
        "ru": "[[logo]] <b>{bot_name}</b>\n" + LINE + "\n"
              "Виртуальные номера для приёма СМС\nна любые сервисы и страны [[globe]]\n\n"
              "[[user]] <b>{name}</b>\n"
              "[[id]] ID: <code>{user_id}</code>\n"
              "[[wallet]] Баланс: <b>{balance}</b>\n" + LINE + "\n"
              "[[fire]] Выберите действие:",
        "en": "[[logo]] <b>{bot_name}</b>\n" + LINE + "\n"
              "Virtual numbers to receive SMS\nfor any service and country [[globe]]\n\n"
              "[[user]] <b>{name}</b>\n"
              "[[id]] ID: <code>{user_id}</code>\n"
              "[[wallet]] Balance: <b>{balance}</b>\n" + LINE + "\n"
              "[[fire]] Choose an action:",
        "tk": "[[logo]] <b>{bot_name}</b>\n" + LINE + "\n"
              "Islendik hyzmat we ýurt üçin\nSMS kabul etmek üçin wirtual belgiler [[globe]]\n\n"
              "[[user]] <b>{name}</b>\n"
              "[[id]] ID: <code>{user_id}</code>\n"
              "[[wallet]] Balans: <b>{balance}</b>\n" + LINE + "\n"
              "[[fire]] Hereketi saýlaň:",
    },
    "btn_buy": {"ru": "Купить номер", "en": "Buy number", "tk": "Belgi satyn al"},
    "btn_topup": {"ru": "Пополнить баланс", "en": "Top up balance", "tk": "Balansy doldur"},
    "btn_orders": {"ru": "Мои номера", "en": "My numbers", "tk": "Meniň belgilerim"},
    "btn_lang": {"ru": "Язык", "en": "Language", "tk": "Dil"},
    "btn_support": {"ru": "Поддержка", "en": "Support", "tk": "Goldaw"},
    "btn_channel": {"ru": "Наш канал", "en": "Our channel", "tk": "Kanalymyz"},
    "btn_back": {"ru": "Назад", "en": "Back", "tk": "Yza"},
    "btn_home": {"ru": "Главное меню", "en": "Main menu", "tk": "Baş menýu"},
    "btn_search": {"ru": "Поиск сервиса", "en": "Search service", "tk": "Hyzmat gözle"},
    "btn_all_services": {"ru": "Все сервисы", "en": "All services", "tk": "Ähli hyzmatlar"},

    "choose_service": {
        "ru": "[[phone]] <b>Покупка номера</b>\n" + LINE + "\n"
              "[[fire]] Популярные сервисы ниже.\n[[search]] Не нашли нужный? Нажмите «Поиск» "
              "или просто отправьте название сервиса сообщением.",
        "en": "[[phone]] <b>Buy a number</b>\n" + LINE + "\n"
              "[[fire]] Popular services are below.\n[[search]] Can't find yours? Tap «Search» "
              "or just send the service name as a message.",
        "tk": "[[phone]] <b>Belgi satyn almak</b>\n" + LINE + "\n"
              "[[fire]] Meşhur hyzmatlar aşakda.\n[[search]] Gerekli hyzmaty tapmadyňyzmy? «Gözle» "
              "basyň ýa-da hyzmatyň adyny hat bilen iberiň.",
    },
    "all_services": {
        "ru": "[[phone]] <b>Все сервисы</b> · стр. {page}/{pages}",
        "en": "[[phone]] <b>All services</b> · page {page}/{pages}",
        "tk": "[[phone]] <b>Ähli hyzmatlar</b> · sahypa {page}/{pages}",
    },
    "search_prompt": {
        "ru": "[[search]] Отправьте название сервиса, например: <i>Telegram</i>, <i>WhatsApp</i>, <i>Google</i>",
        "en": "[[search]] Send the service name, e.g. <i>Telegram</i>, <i>WhatsApp</i>, <i>Google</i>",
        "tk": "[[search]] Hyzmatyň adyny iberiň, mysal üçin: <i>Telegram</i>, <i>WhatsApp</i>, <i>Google</i>",
    },
    "search_results": {
        "ru": "[[search]] Результаты по запросу «<b>{query}</b>»:",
        "en": "[[search]] Results for «<b>{query}</b>»:",
        "tk": "[[search]] «<b>{query}</b>» boýunça netijeler:",
    },
    "search_empty": {
        "ru": "[[warning]] По запросу «<b>{query}</b>» ничего не найдено. Попробуйте другое название.",
        "en": "[[warning]] Nothing found for «<b>{query}</b>». Try another name.",
        "tk": "[[warning]] «<b>{query}</b>» boýunça hiç zat tapylmady. Başga at synap görüň.",
    },
    "choose_country": {
        "ru": "[[globe]] <b>{service}</b>\n" + LINE + "\nВыберите страну (сначала самые дешёвые)\n"
              "Стр. {page}/{pages}",
        "en": "[[globe]] <b>{service}</b>\n" + LINE + "\nChoose a country (cheapest first)\n"
              "Page {page}/{pages}",
        "tk": "[[globe]] <b>{service}</b>\n" + LINE + "\nÝurdy saýlaň (iň arzanlary ilki)\n"
              "Sahypa {page}/{pages}",
    },
    "no_countries": {
        "ru": "[[warning]] Сейчас для <b>{service}</b> нет свободных номеров. Попробуйте позже.",
        "en": "[[warning]] No numbers available for <b>{service}</b> right now. Try later.",
        "tk": "[[warning]] Häzir <b>{service}</b> üçin boş belgi ýok. Soňrak synanyşyň.",
    },
    "confirm": {
        "ru": "[[buy]] <b>Подтверждение покупки</b>\n" + LINE + "\n"
              "[[phone]] Сервис: <b>{service}</b>\n"
              "[[globe]] Страна: <b>{country}</b>\n"
              "[[money]] Цена: <b>{price}</b>\n"
              "[[box]] В наличии: <b>{count}</b> шт.\n" + LINE + "\n"
              "[[wallet]] Ваш баланс: <b>{balance}</b>\n\n"
              "[[check]] Если СМС не придёт, деньги вернутся на баланс автоматически.",
        "en": "[[buy]] <b>Confirm purchase</b>\n" + LINE + "\n"
              "[[phone]] Service: <b>{service}</b>\n"
              "[[globe]] Country: <b>{country}</b>\n"
              "[[money]] Price: <b>{price}</b>\n"
              "[[box]] In stock: <b>{count}</b>\n" + LINE + "\n"
              "[[wallet]] Your balance: <b>{balance}</b>\n\n"
              "[[check]] If no SMS arrives, the money is returned to your balance automatically.",
        "tk": "[[buy]] <b>Satyn almagy tassyklaň</b>\n" + LINE + "\n"
              "[[phone]] Hyzmat: <b>{service}</b>\n"
              "[[globe]] Ýurt: <b>{country}</b>\n"
              "[[money]] Bahasy: <b>{price}</b>\n"
              "[[box]] Elýeterli: <b>{count}</b> sany\n" + LINE + "\n"
              "[[wallet]] Balansyňyz: <b>{balance}</b>\n\n"
              "[[check]] SMS gelmese, pul balansyňyza awtomatik yzyna gaýtarylýar.",
    },
    "btn_confirm_buy": {"ru": "Купить за {price}", "en": "Buy for {price}", "tk": "{price} bahasyna al"},
    "not_enough": {
        "ru": "[[warning]] <b>Недостаточно средств</b>\nЦена: <b>{price}</b>\nВаш баланс: <b>{balance}</b>",
        "en": "[[warning]] <b>Insufficient funds</b>\nPrice: <b>{price}</b>\nYour balance: <b>{balance}</b>",
        "tk": "[[warning]] <b>Balans ýeterlik däl</b>\nBahasy: <b>{price}</b>\nBalansyňyz: <b>{balance}</b>",
    },
    "buying": {
        "ru": "[[wait]] Получаем номер…",
        "en": "[[wait]] Getting a number…",
        "tk": "[[wait]] Belgi alynýar…",
    },
    "no_numbers": {
        "ru": "[[warning]] Номера закончились или цена изменилась. Выберите другую страну.",
        "en": "[[warning]] Numbers ran out or the price changed. Choose another country.",
        "tk": "[[warning]] Belgiler gutardy ýa-da baha üýtgedi. Başga ýurt saýlaň.",
    },
    "buy_error": {
        "ru": "[[warning]] Не удалось получить номер, деньги не списаны. Попробуйте позже.",
        "en": "[[warning]] Couldn't get a number, you were not charged. Try later.",
        "tk": "[[warning]] Belgi alyp bolmady, pul alynmady. Soňrak synanyşyň.",
    },
    "order_waiting": {
        "ru": "[[phone]] <b>Номер получен!</b>\n" + LINE + "\n"
              "[[phone]] Номер: <code>+{phone}</code>\n"
              "[[globe]] {service} · {country}\n"
              "[[money]] Цена: <b>{price}</b>\n" + LINE + "\n"
              "[[wait]] Ожидаем СМС… (до {minutes} мин)\n"
              "Код придёт сюда автоматически.",
        "en": "[[phone]] <b>Number received!</b>\n" + LINE + "\n"
              "[[phone]] Number: <code>+{phone}</code>\n"
              "[[globe]] {service} · {country}\n"
              "[[money]] Price: <b>{price}</b>\n" + LINE + "\n"
              "[[wait]] Waiting for SMS… (up to {minutes} min)\n"
              "The code will appear here automatically.",
        "tk": "[[phone]] <b>Belgi alyndy!</b>\n" + LINE + "\n"
              "[[phone]] Belgi: <code>+{phone}</code>\n"
              "[[globe]] {service} · {country}\n"
              "[[money]] Bahasy: <b>{price}</b>\n" + LINE + "\n"
              "[[wait]] SMS garaşylýar… ({minutes} min çenli)\n"
              "Kod şu ýere awtomatik geler.",
    },
    "order_code": {
        "ru": "[[ok]] <b>СМС получено!</b>\n" + LINE + "\n"
              "[[phone]] Номер: <code>+{phone}</code>\n"
              "[[globe]] {service} · {country}\n\n"
              "[[code]] Код: <code>{code}</code>\n" + LINE + "\n"
              "[[sms]] Нужен ещё код на этот же номер? Нажмите «Ещё СМС».",
        "en": "[[ok]] <b>SMS received!</b>\n" + LINE + "\n"
              "[[phone]] Number: <code>+{phone}</code>\n"
              "[[globe]] {service} · {country}\n\n"
              "[[code]] Code: <code>{code}</code>\n" + LINE + "\n"
              "[[sms]] Need another code on this number? Tap «Another SMS».",
        "tk": "[[ok]] <b>SMS geldi!</b>\n" + LINE + "\n"
              "[[phone]] Belgi: <code>+{phone}</code>\n"
              "[[globe]] {service} · {country}\n\n"
              "[[code]] Kod: <code>{code}</code>\n" + LINE + "\n"
              "[[sms]] Şu belgä ýene kod gerekmi? «Ýene SMS» basyň.",
    },
    "order_done": {
        "ru": "[[done]] <b>Активация завершена</b>\n[[phone]] <code>+{phone}</code> · {service}\n[[code]] Код: <code>{code}</code>",
        "en": "[[done]] <b>Activation completed</b>\n[[phone]] <code>+{phone}</code> · {service}\n[[code]] Code: <code>{code}</code>",
        "tk": "[[done]] <b>Aktiwasiýa tamamlandy</b>\n[[phone]] <code>+{phone}</code> · {service}\n[[code]] Kod: <code>{code}</code>",
    },
    "order_cancelled": {
        "ru": "[[cancel]] <b>Номер отменён</b>\n[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] <b>{price}</b> возвращено на баланс.",
        "en": "[[cancel]] <b>Number cancelled</b>\n[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] <b>{price}</b> returned to your balance.",
        "tk": "[[cancel]] <b>Belgi ýatyryldy</b>\n[[phone]] <code>+{phone}</code> · {service}\n"
              "[[money]] <b>{price}</b> balansyňyza gaýtaryldy.",
    },
    "order_timeout": {
        "ru": "[[wait]] <b>Время ожидания истекло</b>\n[[phone]] <code>+{phone}</code> · {service}\n"
              "СМС не пришло. [[money]] <b>{price}</b> возвращено на баланс.",
        "en": "[[wait]] <b>Time is up</b>\n[[phone]] <code>+{phone}</code> · {service}\n"
              "No SMS arrived. [[money]] <b>{price}</b> returned to your balance.",
        "tk": "[[wait]] <b>Garaşmak wagty gutardy</b>\n[[phone]] <code>+{phone}</code> · {service}\n"
              "SMS gelmedi. [[money]] <b>{price}</b> balansyňyza gaýtaryldy.",
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
    "btn_copy_phone": {"ru": "Копировать номер", "en": "Copy number", "tk": "Belgini göçür"},
    "btn_copy_code": {"ru": "Копировать код", "en": "Copy code", "tk": "Kody göçür"},
    "btn_buy_more": {"ru": "Купить ещё", "en": "Buy more", "tk": "Ýene al"},

    "orders_title": {
        "ru": "[[orders]] <b>Мои номера</b> (последние 10)\n" + LINE,
        "en": "[[orders]] <b>My numbers</b> (last 10)\n" + LINE,
        "tk": "[[orders]] <b>Meniň belgilerim</b> (soňky 10)\n" + LINE,
    },
    "orders_empty": {
        "ru": "[[box]] У вас пока нет номеров.",
        "en": "[[box]] You have no numbers yet.",
        "tk": "[[box]] Entek belgiňiz ýok.",
    },
    "status_waiting": {"ru": "ожидает СМС", "en": "waiting for SMS", "tk": "SMS garaşylýar"},
    "status_got_code": {"ru": "код получен", "en": "code received", "tk": "kod geldi"},
    "status_done": {"ru": "завершён", "en": "completed", "tk": "tamamlandy"},
    "status_cancelled": {"ru": "отменён", "en": "cancelled", "tk": "ýatyryldy"},

    "topup": {
        "ru": "[[wallet]] <b>Пополнение баланса</b>\n" + LINE + "\n"
              "[[money]] Текущий баланс: <b>{balance}</b>\n\n"
              "Выберите способ оплаты:",
        "en": "[[wallet]] <b>Top up balance</b>\n" + LINE + "\n"
              "[[money]] Current balance: <b>{balance}</b>\n\n"
              "Choose a payment method:",
        "tk": "[[wallet]] <b>Balansy doldurmak</b>\n" + LINE + "\n"
              "[[money]] Häzirki balans: <b>{balance}</b>\n\n"
              "Töleg usulyny saýlaň:",
    },
    "btn_pay_crypto": {"ru": "Криптовалюта (CryptoBot)", "en": "Crypto (CryptoBot)", "tk": "Kriptowalýuta (CryptoBot)"},
    "btn_pay_stars": {"ru": "Telegram Stars", "en": "Telegram Stars", "tk": "Telegram Stars"},
    "btn_pay_card": {"ru": "Банковская карта (₽)", "en": "Bank card (₽)", "tk": "Bank kartasy (₽)"},
    "choose_amount": {
        "ru": "[[money]] <b>{method}</b>\n" + LINE + "\nВыберите сумму пополнения или отправьте свою "
              "числом (минимум {min} ₽):",
        "en": "[[money]] <b>{method}</b>\n" + LINE + "\nChoose an amount or send your own "
              "as a number (minimum {min} ₽):",
        "tk": "[[money]] <b>{method}</b>\n" + LINE + "\nMukdary saýlaň ýa-da öz mukdaryňyzy "
              "san bilen iberiň (iň az {min} ₽):",
    },
    "bad_amount": {
        "ru": "[[warning]] Введите сумму числом от {min} до 100000 ₽",
        "en": "[[warning]] Enter an amount between {min} and 100000 ₽",
        "tk": "[[warning]] {min} we 100000 ₽ aralygynda mukdar giriziň",
    },
    "crypto_invoice": {
        "ru": "[[crypto]] <b>Счёт на {amount}</b>\n" + LINE + "\n"
              "Оплатите в @CryptoBot любой криптовалютой (USDT, TON, BTC и др.).\n"
              "[[check]] Баланс пополнится автоматически, либо нажмите «Проверить оплату».\n"
              "[[wait]] Счёт действует 1 час.",
        "en": "[[crypto]] <b>Invoice for {amount}</b>\n" + LINE + "\n"
              "Pay in @CryptoBot with any crypto (USDT, TON, BTC, etc.).\n"
              "[[check]] Your balance is topped up automatically, or tap «Check payment».\n"
              "[[wait]] The invoice is valid for 1 hour.",
        "tk": "[[crypto]] <b>{amount} möçberinde hasap</b>\n" + LINE + "\n"
              "@CryptoBot-da islendik kriptowalýuta bilen töläň (USDT, TON, BTC we ş.m.).\n"
              "[[check]] Balans awtomatik dolar ýa-da «Tölegi barla» basyň.\n"
              "[[wait]] Hasap 1 sagat hereket edýär.",
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
        "ru": "[[ok]] <b>Баланс пополнен на {amount}</b>\n[[wallet]] Текущий баланс: <b>{balance}</b>",
        "en": "[[ok]] <b>Balance topped up by {amount}</b>\n[[wallet]] Current balance: <b>{balance}</b>",
        "tk": "[[ok]] <b>Balans {amount} dolduryldy</b>\n[[wallet]] Häzirki balans: <b>{balance}</b>",
    },
    "pay_unavailable": {
        "ru": "[[warning]] Этот способ оплаты сейчас недоступен.",
        "en": "[[warning]] This payment method is unavailable right now.",
        "tk": "[[warning]] Bu töleg usuly häzir elýeterli däl.",
    },
    "banned": {
        "ru": "[[cancel]] Ваш доступ к боту ограничен. Обратитесь в поддержку.",
        "en": "[[cancel]] Your access to the bot is restricted. Contact support.",
        "tk": "[[cancel]] Bota girişiňiz çäklendirildi. Goldaw bilen habarlaşyň.",
    },
    "support": {
        "ru": "[[support]] <b>Поддержка</b>\n" + LINE + "\nПо любым вопросам пишите: {contact}",
        "en": "[[support]] <b>Support</b>\n" + LINE + "\nFor any questions write to: {contact}",
        "tk": "[[support]] <b>Goldaw</b>\n" + LINE + "\nIslendik sorag boýunça ýazyň: {contact}",
    },
}

_marker = re.compile(r"\[\[([a-z_]+)\]\]")


def t(lang: str | None, key: str, **kwargs) -> str:
    variants = TEXTS[key]
    text = variants.get(lang or DEFAULT_LANG) or variants[DEFAULT_LANG]
    if kwargs:
        text = text.format(**kwargs)
    return _marker.sub(lambda m: e(m.group(1)), text)


def fmt_money(kopecks: int) -> str:
    if kopecks % 100 == 0:
        return f"{kopecks // 100:,} ₽".replace(",", " ")
    return f"{kopecks / 100:,.2f} ₽".replace(",", " ")
