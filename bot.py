import os
import requests

from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ["BOT_TOKEN"]

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

BACKEND = os.environ.get(
    "BACKEND_URL",
    "https://lukirby-backend.onrender.com"
)

MAINTENANCE = True


def telegram(method, data=None):

    try:

        response = requests.post(
            f"{TELEGRAM_API}/{method}",
            json=data or {},
            timeout=15
        )

        result = response.json()

        if not result.get("ok"):

            print(
                f"[Telegram {method}] "
                f"{result}"
            )

        return result

    except Exception as e:

        print(
            f"[Telegram {method}] "
            f"error: {e}"
        )

        return None


def backend(method, path, data=None):

    try:

        response = requests.request(
            method,
            f"{BACKEND}{path}",
            json=data,
            timeout=15
        )

        try:

            return response.json()

        except Exception:

            return {
                "ok": False,
                "error":
                    f"Backend returned HTTP "
                    f"{response.status_code}"
            }

    except Exception as e:

        print(
            f"[Backend {method} {path}] "
            f"error: {e}"
        )

        return {
            "ok": False,
            "error": str(e)
        }


def main_keyboard():

    return {
        "inline_keyboard": [

            [
                {
                    "text": "⭐ VIP",
                    "callback_data":
                        "vip_info"
                }
            ],

            [
                {
                    "text": "🆓 Free",
                    "callback_data":
                        "free"
                },

                {
                    "text": "👤 Моя подписка",
                    "callback_data":
                        "subscription"
                }
            ],

            [
                {
                    "text": "📱 Устройства",
                    "callback_data":
                        "devices"
                }
            ],

            [
                {
                    "text": "ℹ️ Помощь",
                    "callback_data":
                        "help"
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
                    "callback_data":
                        "back"
                }
            ]
        ]
    }


def subscription_keyboard(
    subscription_url
):

    return {
        "inline_keyboard": [

            [
                {
                    "text":
                        "📋 Скопировать подписку",

                    "copy_text": {
                        "text":
                            subscription_url
                    }
                }
            ],

            [
                {
                    "text":
                        "📱 Устройства",
                    "callback_data":
                        "devices"
                }
            ],

            [
                {
                    "text":
                        "◀️ Назад",
                    "callback_data":
                        "back"
                }
            ]
        ]
    }


def escape_html(text):

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def device_delete_keyboard(devices):

    keyboard = []

    for device in devices:

        device_id = device.get(
            "device_id"
        )

        name = device.get(
            "name",
            "Неизвестное устройство"
        )

        keyboard.append([
            {
                "text":
                    f"❌ {name}",
                "callback_data":
                    f"delete_device:{device_id}"
            }
        ])

    keyboard.append([
        {
            "text":
                "◀️ Назад",
            "callback_data":
                "devices"
        }
    ])

    return {
        "inline_keyboard":
            keyboard
    }


def device_restore_keyboard(devices):

    keyboard = []

    for device in devices:

        device_id = device.get(
            "device_id"
        )

        name = device.get(
            "name",
            "Неизвестное устройство"
        )

        keyboard.append([
            {
                "text":
                    f"♻️ {name}",
                "callback_data":
                    f"restore_device:{device_id}"
            }
        ])

    keyboard.append([
        {
            "text":
                "◀️ Назад",
            "callback_data":
                "devices"
        }
    ])

    return {
        "inline_keyboard":
            keyboard
    }


def send_message(
    chat_id,
    text,
    keyboard=None
):

    data = {
        "chat_id":
            chat_id,

        "text":
            text,

        "parse_mode":
            "HTML"
    }

    if keyboard:

        data["reply_markup"] = keyboard

    return telegram(
        "sendMessage",
        data
    )


def edit_message(
    chat_id,
    message_id,
    text,
    keyboard
):

    return telegram(
        "editMessageText",
        {
            "chat_id":
                chat_id,

            "message_id":
                message_id,

            "text":
                text,

            "parse_mode":
                "HTML",

            "reply_markup":
                keyboard
        }
    )


def answer_callback(
    callback_id,
    text=None
):

    data = {
        "callback_query_id":
            callback_id
    }

    if text:

        data["text"] = text

    return telegram(
        "answerCallbackQuery",
        data
    )


def get_user(chat_id):

    return backend(
        "POST",
        "/api/users",
        {
            "user_id":
                str(chat_id)
        }
    )


def get_devices(chat_id):

    return backend(
        "GET",
        f"/api/devices/{chat_id}"
    )


def get_subscription(token):

    return backend(
        "GET",
        f"/api/subscriptions/{token}"
    )


def get_subscription_url(
    chat_id
):

    user = get_user(
        chat_id
    )

    if not user.get("ok"):

        return {
            "ok": False,
            "error":
                "Unable to get user"
        }

    subscription = user.get(
        "subscription"
    )

    if not subscription:

        return {
            "ok": False,
            "error":
                "Subscription not found"
        }

    token = subscription.get(
        "token"
    )

    if not token:

        return {
            "ok": False,
            "error":
                "Subscription token not found"
        }

    subscription_base = os.environ.get(
        "SUBSCRIPTION_URL",
        "https://ook-vpn.vercel.app/sub.txt"
    )

    if not subscription_base:

        return {
            "ok": False,
            "error":
                "SUBSCRIPTION_URL is not configured"
        }

    separator = (
        "&"
        if "?" in subscription_base
        else "?"
    )

    subscription_url = (
        f"{subscription_base}"
        f"{separator}"
        f"token={token}"
    )

    return {
        "ok": True,

        "token":
            token,

        "subscription_url":
            subscription_url
    }


def handle_message(message):

    chat_id = message["chat"]["id"]

    if MAINTENANCE:

        send_message(
            chat_id,
            (
                "🛠 <b>OokVPN временно закрыт</b>\n\n"
                "Мы делаем масштабную переработку VPN.\n\n"
                "Текущая подписка продолжает работать "
                "до выхода новой версии.\n\n"
                "Следите за новостями в канале."
            )
        )

        return

    text = message.get(
        "text",
        ""
    )

    user = get_user(
        chat_id
    )

    if not user.get("ok"):

        print(
            "Failed to create/get user:",
            user
        )

    if text == "/start":

        send_message(
            chat_id,

            (
                "🔥 <b>OokVPN</b>\n\n"
                "Добро пожаловать!\n\n"
                "Выберите нужный раздел:"
            ),

            main_keyboard()
        )


def handle_callback(callback):

    callback_id = callback["id"]

    answer_callback(
        callback_id
    )

    message = callback.get(
        "message"
    )

    if not message:
        return

    chat_id = message["chat"]["id"]

    message_id = message["message_id"]

    data = callback.get(
        "data",
        ""
    )

    if data == "vip_info":

        text = (
            "⭐ <b>OokVPN VIP</b>\n\n"
            "VIP — навсегда, лимит "
            "устройств: <b>10</b>.\n\n"
            "Оплата пока не подключена. "
        )

        keyboard = back_keyboard()

    elif data == "free":

        user = get_user(
            chat_id
        )

        plan = user.get(
            "plan",
            "free"
        )

        if plan == "vip":

            text = (
                "⭐ <b>У вас уже VIP</b>\n\n"
                "Тариф: <b>VIP</b>\n"
                "Лимит устройств: <b>10</b>\n\n"
                "VIP действует навсегда."
            )

        else:

            text = (
                "🆓 <b>OokVPN Free</b>\n\n"
                "Тариф: <b>Free</b>\n"
                "Устройств: <b>5</b>\n\n"
                "Бесплатная подписка."
            )

        keyboard = back_keyboard()

    elif data == "subscription":

        result = get_subscription_url(
            chat_id
        )

        if not result.get("ok"):

            text = (
                "❌ <b>Ошибка</b>\n\n"
                f"{result.get('error', 'Unknown error')}"
            )

            keyboard = back_keyboard()

        else:

            text = (
                "🔐 <b>Ваша подписка</b>\n\n"
                "Нажмите кнопку ниже, "
                "чтобы скопировать ссылку "
                "в буфер обмена."
            )

            keyboard = subscription_keyboard(
                result["subscription_url"]
            )

    elif data == "devices":

        user = get_user(
            chat_id
        )

        devices = get_devices(
            chat_id
        )

        plan = user.get(
            "plan",
            "free"
        )

        limit = user.get(
            "device_limit"
        )

        if limit is None:

            subscription = user.get(
                "subscription",
                {}
            )

            subscription_plan = subscription.get(
                "plan",
                plan
            )

            limit = (
                999999
                if subscription_plan == "dev"
                else 10
                if subscription_plan == "vip"
                else 5
            )

        if not devices.get("ok"):

            text = (
                "❌ <b>Ошибка</b>\n\n"
                "Не удалось получить "
                "список устройств."
            )

            keyboard = back_keyboard()

        else:

            device_list = devices.get(
                "devices",
                []
            )

            active_devices = [
                d
                for d in device_list
                if d.get("status")
                == "active"
            ]

            removed_devices = [
                d
                for d in device_list
                if d.get("status")
                == "removed"
            ]

            if active_devices:

                lines = []

                for device in active_devices:

                    name = device.get(
                        "name",
                        "Неизвестное устройство"
                    )

                    lines.append(
                        f"📱 {name}"
                    )

                devices_text = (
                    "\n".join(lines)
                )

            else:

                devices_text = (
                    "Нет активных устройств."
                )

            text = (
                "📱 <b>Устройства</b>\n\n"
                f"{devices_text}\n\n"
                f"Использовано: "
                f"<b>{len(active_devices)}/{limit}</b>\n"
                f"Тариф: "
                f"<b>{plan.upper()}</b>"
            )

            keyboard_rows = [

                [
                    {
                        "text":
                            "❌ Удалить устройство",
                        "callback_data":
                            "delete_menu"
                    }
                ]
            ]

            if removed_devices:

                keyboard_rows.append([
                    {
                        "text":
                            "♻️ Восстановить устройство",
                        "callback_data":
                            "restore_menu"
                    }
                ])

            keyboard_rows.append([
                {
                    "text":
                        "◀️ Назад",
                    "callback_data":
                        "back"
                }
            ])

            keyboard = {
                "inline_keyboard":
                    keyboard_rows
            }

    elif data == "delete_menu":

        devices = get_devices(
            chat_id
        )

        if not devices.get("ok"):

            text = (
                "❌ <b>Ошибка</b>\n\n"
                "Не удалось получить "
                "список устройств."
            )

            keyboard = back_keyboard()

        else:

            device_list = devices.get(
                "devices",
                []
            )

            active_devices = [
                d
                for d in device_list
                if d.get("status")
                == "active"
            ]

            if not active_devices:

                text = (
                    "📱 <b>Удаление устройства</b>\n\n"
                    "Нет активных устройств "
                    "для удаления."
                )

                keyboard = back_keyboard()

            else:

                text = (
                    "❌ <b>Выберите какое "
                    "устройство удалить:</b>\n\n"
                    "После удаления оно "
                    "перестанет считаться "
                    "активным.\n\n"
                    "При необходимости его "
                    "можно восстановить "
                    "через меню устройств."
                )

                keyboard = device_delete_keyboard(
                    active_devices
                )

    elif data.startswith(
        "delete_device:"
    ):

        device_id = data.split(
            ":",
            1
        )[1]

        result = backend(
            "DELETE",
            f"/api/devices/"
            f"{chat_id}/"
            f"{device_id}"
        )

        if not result.get("ok"):

            text = (
                "❌ <b>Ошибка</b>\n\n"
                f"{result.get('error', 'Не удалось удалить устройство.')}"
            )

            keyboard = back_keyboard()

        else:

            text = (
                "✅ <b>Устройство удалено</b>\n\n"
                "Оно больше не считается "
                "активным.\n\n"
                "Восстановить его можно "
                "через меню устройств."
            )

            keyboard = {
                "inline_keyboard": [

                    [
                        {
                            "text":
                                "📱 Устройства",
                            "callback_data":
                                "devices"
                        }
                    ],

                    [
                        {
                            "text":
                                "◀️ Назад",
                            "callback_data":
                                "back"
                        }
                    ]
                ]
            }

    elif data == "restore_menu":

        devices = get_devices(
            chat_id
        )

        if not devices.get("ok"):

            text = (
                "❌ <b>Ошибка</b>\n\n"
                "Не удалось получить "
                "список устройств."
            )

            keyboard = back_keyboard()

        else:

            device_list = devices.get(
                "devices",
                []
            )

            removed_devices = [
                d
                for d in device_list
                if d.get("status")
                == "removed"
            ]

            if not removed_devices:

                text = (
                    "♻️ <b>Восстановление "
                    "устройства</b>\n\n"
                    "Нет удалённых устройств "
                    "для восстановления."
                )

                keyboard = back_keyboard()

            else:

                text = (
                    "♻️ <b>Восстановление "
                    "устройства</b>\n\n"
                    "Выберите устройство, "
                    "которое хотите восстановить."
                )

                keyboard = device_restore_keyboard(
                    removed_devices
                )

    elif data.startswith(
        "restore_device:"
    ):

        device_id = data.split(
            ":",
            1
        )[1]

        result = backend(
            "POST",
            f"/api/devices/"
            f"{chat_id}/"
            f"{device_id}/restore"
        )

        if not result.get("ok"):

            error = result.get(
                "error",
                "Не удалось восстановить устройство."
            )

            if error == "device limit reached":

                text = (
                    "❌ <b>Лимит устройств "
                    "достигнут</b>\n\n"
                    f"Активных устройств: "
                    f"<b>{result.get('active_devices', '?')}"
                    f"/{result.get('device_limit', '?')}</b>\n\n"
                    "Освободите место или "
                    "используйте тариф с большим "
                    "лимитом устройств."
                )

            else:

                text = (
                    "❌ <b>Ошибка</b>\n\n"
                    f"{error}"
                )

            keyboard = {
                "inline_keyboard": [

                    [
                        {
                            "text":
                                "♻️ Восстановление",
                            "callback_data":
                                "restore_menu"
                        }
                    ],

                    [
                        {
                            "text":
                                "📱 Устройства",
                            "callback_data":
                                "devices"
                        }
                    ],

                    [
                        {
                            "text":
                                "◀️ Назад",
                            "callback_data":
                                "back"
                        }
                    ]
                ]
            }

        else:

            text = (
                "♻️ <b>Устройство восстановлено</b>\n\n"
                "Оно снова считается активным.\n\n"
                f"Активных устройств: "
                f"<b>{result.get('active_devices', '?')}"
                f"/{result.get('device_limit', '?')}</b>"
            )

            keyboard = {
                "inline_keyboard": [

                    [
                        {
                            "text":
                                "📱 Устройства",
                            "callback_data":
                                "devices"
                        }
                    ],

                    [
                        {
                            "text":
                                "◀️ Назад",
                            "callback_data":
                                "back"
                        }
                    ]
                ]
            }

    elif data == "help":

        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "Если возникли проблемы "
            "с подпиской, подключением "
            "или устройствами — "
            "обратитесь в поддержку.\n\n"
            "👤 Поддержка: "
            "<b>@OokVPNHelp</b>"
        )

        keyboard = back_keyboard()

    elif data == "back":

        text = (
            "🔥 <b>OokVPN</b>\n\n"
            "Выберите нужный раздел:"
        )

        keyboard = main_keyboard()

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

    return (
        "Ook Bot is alive 🔥",
        200
    )


@app.post("/webhook")
def webhook():

    update = request.get_json(
        silent=True
    )

    if not update:

        return "OK", 200

    try:

        if MAINTENANCE:

            if "message" in update:

                chat_id = update["message"]["chat"]["id"]

                send_message(
                    chat_id,
                    (
                        "🛠 <b>OokVPN временно закрыт</b>\n\n"
                        "Мы делаем масштабную переработку VPN.\n\n"
                        "Текущая подписка продолжает работать "
                        "до выхода новой версии.\n\n"
                        "Следите за новостями в канале."
                    )
                )

            elif "callback_query" in update:

                callback = update["callback_query"]

                answer_callback(
                    callback["id"],
                    "🛠 Бот временно отключён"
                )

            return "OK", 200

        if "message" in update:

            handle_message(
                update["message"]
            )

        elif "callback_query" in update:

            handle_callback(
                update["callback_query"]
            )

    except Exception as e:

        print(
            "Update error:",
            e
        )

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
