"""Получение токена ЮMoney для проверки платежей.

Запуск: sudo smsbot yoomoney   (или из папки бота: venv/bin/python -m bot.yoomoney_auth)

Перед запуском зарегистрируйте приложение: https://yoomoney.ru/myservices/new
  - Название: любое, например «SMS бот»
  - Адрес сайта и Redirect URI: https://t.me
  - Галочку «Проверять подлинность приложения (OAuth2 client_secret)» не ставьте
"""
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

REDIRECT_URI = "https://t.me"
SCOPE = "account-info operation-history operation-details"


def _set_env(key: str, value: str, path: Path = Path(".env")) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    line = f"{key}={value}"
    if re.search(rf"^{key}=.*$", text, flags=re.M):
        text = re.sub(rf"^{key}=.*$", lambda _: line, text, flags=re.M)
    else:
        text = text.rstrip("\n") + f"\n{line}\n"
    path.write_text(text, encoding="utf-8")


def main() -> None:
    print(__doc__)
    client_id = input("client_id вашего приложения: ").strip()
    redirect = input(f"Redirect URI, который вы указали [{REDIRECT_URI}]: ").strip() or REDIRECT_URI
    auth_url = "https://yoomoney.ru/oauth/authorize?" + urlencode({
        "client_id": client_id, "response_type": "code", "redirect_uri": redirect, "scope": SCOPE,
    })
    print("\n1) Откройте ссылку в браузере, войдите в ЮMoney и нажмите «Разрешить»:\n")
    print(auth_url)
    print("\n2) Браузер перейдёт на адрес вида https://t.me/?code=XXXX — скопируйте его целиком.\n")
    answer = input("Вставьте адрес (или только code): ").strip()
    code = parse_qs(urlparse(answer).query).get("code", [answer])[0]

    data = urlencode({"code": code, "client_id": client_id, "grant_type": "authorization_code",
                      "redirect_uri": redirect}).encode()
    with urllib.request.urlopen(urllib.request.Request("https://yoomoney.ru/oauth/token", data=data)) as resp:
        result = json.loads(resp.read().decode())
    token = result.get("access_token")
    if not token:
        raise SystemExit(f"Не удалось получить токен: {result}")

    req = urllib.request.Request("https://yoomoney.ru/api/account-info", data=b"",
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        wallet = json.loads(resp.read().decode()).get("account", "")

    _set_env("YOOMONEY_TOKEN", token)
    if wallet:
        _set_env("YOOMONEY_WALLET", wallet)
    print(f"\n✔ Готово. Кошелёк {wallet} подключён, токен сохранён в .env")


if __name__ == "__main__":
    main()
