import os
import requests

from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"
BACKEND = "https://lukirby-backend.onrender.com"


def telegram(method, data=None):
    try:
        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data or {},
            timeout=10
        )

        result = response.json()

        if not result.get("ok"):
            print(f"[Telegram {method}] {result}")

        return result

    except Exception as e:
        print(f"[Telegram {method}] error: {e}")
        return None


def backend(method, path, data=None):
    try:
        response = requests.request(
            method,
            f"{BACKEND}{path}",
            json=data,
            timeout=10
        )

        try:
            return response.json()
        except Exception:
            return {
                "ok": False,
                "error": f"Backend returned HTTP {response.status_code}"
            }

    except Exception as e:
        print(f"[Backend {method} {path}] error: {e}")

        return {
            "ok": False,
            "error": str(e)
        }


def main_keyboard():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "⭐ Купить VIP",
                    "callback_data": "buy_vip"
                }
            ],
            [
                {
                    "text": "🆓 Free",
                    "callback_data": "free"
                },
                {
                    "text": "👤 Моя подписка",
                    "callback_data": "subscription"
                }
            ],
            [
                {
                    "text": "📱 Устройства",
                    "callback_data": "devices"
                }
            ],
            [
                {
                    "text": "ℹ️ Помощь",
                    "callback_data": "help"
                }
            ]
        ]
    }


def back_keyboard():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "◀️ Назад",
                    "callback_data": "back"
                }
            ]
        ]
    }


def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if keyboard:
        data["reply_markup"] = keyboard

    return telegram("sendMessage", data)


def edit_message(chat_id, message_id, text, keyboard):
    return telegram(
        "editMessageText",
        {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": keyboard
        }
    )


def answer_callback(callback_id):
    return telegram(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_id
        }
    )


def get_user(chat_id):
    return backend(
        "POST",
        "/api/users",
        {
            "user_id": str(chat_id)
        }
    )


def get_devices(chat_id):
    return backend(
        "GET",
        f"/api/devices/{chat_id}"
    )


def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # Регистрируем пользователя в backend
    user = get_user(chat_id)

    if not user.get("ok"):
        print("Failed to create/get user:", user)

    if text == "/start":

        send_message(
            chat_id,
            (
                "🔥 <b>LukirbyVPN</b>\n\n"
                "Добро пожаловать!\n\n"
                "Выберите нужный раздел:"
            ),
            main_keyboard()
        )


def handle_callback(callback):

    callback_id = callback["id"]

    # Telegram callback должен подтверждаться сразу
    answer_callback(callback_id)

    message = callback.get("message")

    if not message:
        return

    chat_id = message["chat"]["id"]
    message_id = message["message_id"]

    data = callback.get("data")

    # --------------------------------
    # BUY VIP
    # --------------------------------

    if data == "buy_vip":

        text = (
            "⭐ <b>LukirbyVPN VIP</b>\n\n"
            "Выберите срок подписки:"
        )

        keyboard = {
            "inline_keyboard": [
                [
                    {
                        "text": "⭐ 1 месяц",
                        "callback_data": "vip_1"
                    }
                ],
                [
                    {
                        "text": "⭐ 3 месяца",
                        "callback_data": "vip_3"
                    }
                ],
                [
                    {
                        "text": "⭐ 6 месяцев",
                        "callback_data": "vip_6"
                    }
                ],
                [
                    {
                        "text": "◀️ Назад",
                        "callback_data": "back"
                    }
                ]
            ]
        }

    # --------------------------------
    # FREE
    # --------------------------------

    elif data == "free":

        user = get_user(chat_id)

        plan = user.get("plan", "free")

        text = (
            "🆓 <b>LukirbyVPN Free</b>\n\n"
            "Тариф: <b>Free</b>\n"
            "Устройств: <b>1</b>\n\n"
            "Бесплатная подписка."
        )

        if plan == "vip":
            text = (
                "⭐ <b>У вас уже VIP</b>\n\n"
                "Ваш текущий тариф: <b>VIP</b>\n"
                "Лимит устройств: <b>5</b>"
            )

        keyboard = back_keyboard()

    # --------------------------------
    # SUBSCRIPTION
    # --------------------------------

    elif data == "subscription":

        user = get_user(chat_id)

        if not user.get("ok"):
            text = (
                "❌ <b>Ошибка</b>\n\n"
                "Не удалось получить данные подписки."
            )
        else:

            plan = user.get("plan", "free")

            if plan == "vip":
                text = (
                    "⭐ <b>Моя подписка</b>\n\n"
                    "Тариф: <b>VIP</b>\n"
                    "Лимит устройств: <b>5</b>\n\n"
                    "Спасибо за поддержку LukirbyVPN ❤️"
                )
            else:
                text = (
                    "🆓 <b>Моя подписка</b>\n\n"
                    "Тариф: <b>Free</b>\n"
                    "Лимит устройств: <b>1</b>\n\n"
                    "Хотите больше возможностей? "
                    "Оформите VIP ⭐"
                )

        keyboard = back_keyboard()

    # --------------------------------
    # DEVICES
    # --------------------------------

    elif data == "devices":

        user = get_user(chat_id)
        devices = get_devices(chat_id)

        plan = user.get("plan", "free")

        limit = 5 if plan == "vip" else 1

        if not devices.get("ok"):

            text = (
                "❌ <b>Ошибка</b>\n\n"
                "Не удалось получить список устройств."
            )

        else:

            device_list = devices.get("devices", [])

            if device_list:

                lines = []

                for i, device in enumerate(device_list, 1):

                    name = device.get(
                        "name",
                        "Неизвестное устройство"
                    )

                    lines.append(
                        f"{i}. 📱 {name}"
                    )

                devices_text = "\n".join(lines)

            else:

                devices_text = "Нет активных устройств."

            text = (
                "📱 <b>Устройства</b>\n\n"
                f"{devices_text}\n\n"
                f"Использовано: <b>{len(device_list)}/{limit}</b>\n"
                f"Тариф: <b>{plan.upper()}</b>"
            )

        keyboard = back_keyboard()

    # --------------------------------
    # HELP
    # --------------------------------

    elif data == "help":

        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "Если возникли проблемы с "
            "подпиской или подключением — "
            "обратитесь в поддержку."
        )

        keyboard = back_keyboard()

    # --------------------------------
    # BACK
    # --------------------------------

    elif data == "back":

        text = (
            "🔥 <b>LukirbyVPN</b>\n\n"
            "Выберите нужный раздел:"
        )

        keyboard = main_keyboard()

    # --------------------------------
    # VIP PERIOD
    # --------------------------------

    elif data in ("vip_1", "vip_3", "vip_6"):

        months = {
            "vip_1": "1 месяц",
            "vip_3": "3 месяца",
            "vip_6": "6 месяцев"
        }

        text = (
            f"⭐ <b>VIP — {months[data]}</b>\n\n"
            "Оплата через Telegram Stars "
            "будет подключена следующим этапом."
        )

        keyboard = back_keyboard()

    else:
        return

    edit_message(
        chat_id,
        message_id,
        text,
        keyboard
    )


@app.get("/")
def index():
    return "LukirbyVPN Bot is alive 🔥", 200


@app.post("/webhook")
def webhook():

    update = request.get_json(silent=True)

    if not update:
        return "OK", 200

    try:

        if "message" in update:
            handle_message(update["message"])

        elif "callback_query" in update:
            handle_callback(update["callback_query"])

    except Exception as e:
        print("Update error:", e)

    return "OK", 200


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
        )
