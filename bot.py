import os
import requests

from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]

API = f"https://api.telegram.org/bot{TOKEN}"


def telegram(method, data=None):
    try:
        response = requests.post(
            f"{API}/{method}",
            json=data or {},
            timeout=8
        )

        result = response.json()

        if not result.get("ok"):
            print(f"Telegram {method}: {result}")

        return result

    except Exception as e:
        print(f"Telegram {method} error: {e}")
        return None


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


def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

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

    # Сначала убираем загрузку на кнопке.
    answer_callback(callback_id)

    message = callback.get("message")

    if not message:
        return

    chat_id = message["chat"]["id"]
    message_id = message["message_id"]

    data = callback.get("data")

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

    elif data == "free":

        text = (
            "🆓 <b>LukirbyVPN Free</b>\n\n"
            "Бесплатная подписка.\n\n"
            "Серверов будет меньше, чем в VIP."
        )

        keyboard = back_keyboard()

    elif data == "subscription":

        text = (
            "👤 <b>Моя подписка</b>\n\n"
            "У вас пока нет активной подписки."
        )

        keyboard = back_keyboard()

    elif data == "devices":

        text = (
            "📱 <b>Устройства</b>\n\n"
            "Активные устройства: 0\n"
            "Лимит: 0\n\n"
            "После покупки подписки "
            "здесь появится управление устройствами."
        )

        keyboard = back_keyboard()

    elif data == "help":

        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "Если возникли проблемы с "
            "подпиской или подключением — "
            "обратитесь в поддержку."
        )

        keyboard = back_keyboard()

    elif data == "back":

        text = (
            "🔥 <b>LukirbyVPN</b>\n\n"
            "Выберите нужный раздел:"
        )

        keyboard = main_keyboard()

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
    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port
    )
