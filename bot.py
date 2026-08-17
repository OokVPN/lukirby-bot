import os
import requests

from flask import Flask, request

app = Flask(__name__)

# =========================================================
# CONFIG
# =========================================================

TOKEN = os.environ["BOT_TOKEN"]

TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

BACKEND = os.environ.get(
    "BACKEND_URL",
    "https://lukirby-backend.onrender.com"
)

# Endpoint Happ Crypto5 / URL encryption.
#
# Официальный endpoint из документации Happ:
# https://www.happ.su/main/dev-docs/crypto-link
#
# POST {"url": "..."} -> {"url": "happ://crypt5/..."}
#
# Можно переопределить через env, если Happ
# поменяет адрес API.
HAPP_CRYPTO_API = os.environ.get(
    "HAPP_CRYPTO_API",
    "https://crypto.happ.su/api-v2.php"
)


# =========================================================
# TELEGRAM API
# =========================================================

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


# =========================================================
# BACKEND API
# =========================================================

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


# =========================================================
# HAPP CRYPTO5
# =========================================================

def encrypt_happ_url(subscription_url):

    if not HAPP_CRYPTO_API:

        return {
            "ok": False,
            "error":
                "HAPP_CRYPTO_API is not configured"
        }

    try:

        response = requests.post(
            HAPP_CRYPTO_API,
            json={
                "url": subscription_url
            },
            timeout=20
        )

        try:

            result = response.json()

        except Exception:

            return {
                "ok": False,
                "error":
                    "Happ API returned invalid JSON"
            }

        if not response.ok:

            print(
                "[Happ] HTTP error:",
                response.status_code,
                result
            )

            return {
                "ok": False,
                "error":
                    f"Happ API HTTP "
                    f"{response.status_code}"
            }

        print(
            "[Happ] encryption response:",
            result
        )

        # -------------------------------------------------
        # Поддерживаем несколько распространённых
        # вариантов ответа API.
        # -------------------------------------------------

        happ_link = (
            result.get("url")
            or result.get("link")
            or result.get("subscription")
            or result.get("result")
        )

        if isinstance(happ_link, dict):

            happ_link = (
                happ_link.get("url")
                or happ_link.get("link")
            )

        if not happ_link:

            return {
                "ok": False,
                "error":
                    "Happ API did not return encrypted URL"
            }

        return {
            "ok": True,
            "url": str(happ_link)
        }

    except Exception as e:

        print(
            "[Happ] encryption error:",
            e
        )

        return {
            "ok": False,
            "error": str(e)
        }


# =========================================================
# MAIN KEYBOARD
# =========================================================

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


# =========================================================
# BACK BUTTON
# =========================================================

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


# =========================================================
# SUBSCRIPTION KEYBOARD
# =========================================================

def subscription_keyboard():

    # Саму ссылку теперь не кладём в кнопку:
    # copy_text у Telegram ограничен 256 символами,
    # а Crypto5-ссылка обычно в 3+ раза длиннее.
    #
    # Вместо этого ссылка идёт прямо в тексте сообщения
    # внутри <blockquote expandable><code>...</code></blockquote> —
    # у такого блока нет ограничения длины, он сворачивается
    # сам, а тап по моноширинному тексту копирует его в буфер.

    return {
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


# =========================================================
# HTML ESCAPE (для parse_mode=HTML)
# =========================================================

def escape_html(text):

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# =========================================================
# DEVICE DELETE KEYBOARD
# =========================================================

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

        # Telegram callback_data имеет
        # ограничение 1-64 bytes.
        #
        # Поэтому ID устройства
        # отправляем в callback.
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


# =========================================================
# SEND MESSAGE
# =========================================================

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


# =========================================================
# EDIT MESSAGE
# =========================================================

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


# =========================================================
# ANSWER CALLBACK
# =========================================================

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


# =========================================================
# GET USER
# =========================================================

def get_user(chat_id):

    return backend(
        "POST",
        "/api/users",
        {
            "user_id":
                str(chat_id)
        }
    )


# =========================================================
# GET DEVICES
# =========================================================

def get_devices(chat_id):

    return backend(
        "GET",
        f"/api/devices/{chat_id}"
    )


# =========================================================
# GET SUBSCRIPTION
# =========================================================

def get_subscription(
    token
):

    return backend(
        "GET",
        f"/api/subscriptions/{token}"
    )


# =========================================================
# BUILD / GET HAPP SUBSCRIPTION
# =========================================================

def get_happ_subscription(chat_id):

    # -----------------------------------------------------
    # Backend /api/users уже возвращает
    # постоянный token пользователя.
    # -----------------------------------------------------

    user = get_user(chat_id)

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

    # -----------------------------------------------------
    # ОБЫЧНАЯ ССЫЛКА ПОДПИСКИ
    #
    # Здесь укажи свой реальный URL Worker/Netlify,
    # который принимает ?token=...
    # -----------------------------------------------------

    subscription_base = os.environ.get(
        "SUBSCRIPTION_URL",
        "https://lukirby-vpn.vercel.app/api/subscription"
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

    # -----------------------------------------------------
    # CRYPTO5
    # -----------------------------------------------------

    encrypted = encrypt_happ_url(
        subscription_url
    )

    if not encrypted.get("ok"):

        return encrypted

    return {
        "ok": True,

        "token":
            token,

        "subscription_url":
            subscription_url,

        "happ_url":
            encrypted["url"]
    }


# =========================================================
# /START
# =========================================================

def handle_message(message):

    chat_id = message["chat"]["id"]

    text = message.get(
        "text",
        ""
    )

    # Всегда регистрируем /
    # получаем существующего пользователя.
    user = get_user(chat_id)

    if not user.get("ok"):

        print(
            "Failed to create/get user:",
            user
        )

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


# =========================================================
# CALLBACK HANDLER
# =========================================================

def handle_callback(callback):

    callback_id = callback["id"]

    # Telegram callback подтверждаем сразу.
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

    # =====================================================
    # VIP INFO (без оплаты — Stars-оплата не реализована)
    # =====================================================

    if data == "vip_info":

        text = (
            "⭐ <b>LukirbyVPN VIP</b>\n\n"
            "VIP — навсегда, лимит "
            "устройств: <b>5</b>.\n\n"
            "Оплата пока не подключена. "
            "Если хочешь VIP — напиши "
            "в поддержку: <b>@LukirbyVPN</b>, "
            "тариф выдаётся вручную."
        )

        keyboard = back_keyboard()

    # =====================================================
    # FREE
    # =====================================================

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
                "Лимит устройств: <b>5</b>\n\n"
                "VIP действует навсегда."
            )

        else:

            text = (
                "🆓 <b>LukirbyVPN Free</b>\n\n"
                "Тариф: <b>Free</b>\n"
                "Устройств: <b>1</b>\n\n"
                "Бесплатная подписка."
            )

        keyboard = back_keyboard()

    # =====================================================
    # SUBSCRIPTION
    # =====================================================

    elif data == "subscription":

        result = get_happ_subscription(
            chat_id
        )

        if not result.get("ok"):

            text = (
                "❌ <b>Ошибка</b>\n\n"
                f"{result.get('error', 'Unknown error')}"
            )

            keyboard = back_keyboard()

        else:

            happ_link = escape_html(
                result["happ_url"]
            )

            text = (
                "🔐 <b>Ваша подписка</b>\n\n"
                "Нажми на ссылку ниже — "
                "она скопируется в буфер:\n\n"
                "<blockquote expandable>"
                f"<code>{happ_link}</code>"
                "</blockquote>"
            )

            keyboard = subscription_keyboard()

    # =====================================================
    # DEVICES
    # =====================================================

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

        limit = (
            5
            if plan == "vip"
            else 1
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

            # -------------------------------------------------
            # Показываем все устройства,
            # включая removed.
            #
            # Но active считаем отдельно.
            # -------------------------------------------------

            active_devices = [
                d
                for d in device_list
                if d.get("status")
                == "active"
            ]

            if device_list:

                lines = []

                for device in device_list:

                    name = device.get(
                        "name",
                        "Неизвестное устройство"
                    )

                    status = device.get(
                        "status",
                        "active"
                    )

                    if status == "active":

                        lines.append(
                            f"📱 {name}"
                        )

                devices_text = (
                    "\n".join(lines)
                    if lines
                    else
                    "Нет активных устройств."
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

            keyboard = {
                "inline_keyboard": [

                    [
                        {
                            "text":
                                "❌ Удалить устройство",
                            "callback_data":
                                "delete_menu"
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

    # =====================================================
    # DELETE MENU
    # =====================================================

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
                    "После удаления оно получит "
                    "ограниченный сервер.\n\n"
                    "При повторном подключении "
                    "с того же HWID устройство "
                    "снова станет активным."
                )

                keyboard = device_delete_keyboard(
                    active_devices
                )

    # =====================================================
    # DELETE SPECIFIC DEVICE
    # =====================================================

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
                "При повторном подключении "
                "с того же HWID оно снова "
                "станет активным."
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

    # =====================================================
    # HELP
    # =====================================================

    elif data == "help":

        text = (
            "ℹ️ <b>Помощь</b>\n\n"
            "Если возникли проблемы "
            "с подпиской, подключением "
            "или устройствами — "
            "обратитесь в поддержку.\n\n"
            "👤 Поддержка: "
            "<b>@LukirbyVPN</b>"
        )

        keyboard = back_keyboard()

    # =====================================================
    # BACK
    # =====================================================

    elif data == "back":

        text = (
            "🔥 <b>LukirbyVPN</b>\n\n"
            "Выберите нужный раздел:"
        )

        keyboard = main_keyboard()

    # =====================================================
    # UNKNOWN
    # =====================================================

    else:

        return

    edit_message(
        chat_id,
        message_id,
        text,
        keyboard
    )


# =========================================================
# WEB
# =========================================================

@app.get("/")
def index():

    return (
        "LukirbyVPN Bot is alive 🔥",
        200
    )


# =========================================================
# WEBHOOK
# =========================================================

@app.post("/webhook")
def webhook():

    update = request.get_json(
        silent=True
    )

    if not update:

        return "OK", 200

    try:

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


# =========================================================
# START
# =========================================================

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
