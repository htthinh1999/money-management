import os
import time
import requests
from money_management import app


# Load environment variables
env_vars = os.environ
TELEGRAM_BOT_TOKEN = env_vars.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = env_vars.get("TELEGRAM_CHAT_ID")


def send_telegram_long_message(message):
    if len(message) > 4096:
        for x in range(0, len(message), 4096):
            send_telegram_message(message[x : x + 4096])
            # delay 1 second to avoid telegram rate limit
            time.sleep(1)
        else:
            send_telegram_message(message)
    else:
        send_telegram_message(message)


def send_telegram_message(message):
    url = (
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?parse_mode=HTML"
    )
    params = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    response = requests.post(url, json=params)
    if response.status_code != 200:
        app.logger.error(f"Failed to send Telegram message: {response.text}")


def send_telegram_poll(question, options):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPoll"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "question": question,
        "options": options,
        "is_anonymous": "false",
        "allows_multiple_answers": "false",
    }
    response = requests.post(url, json=params)
    if response.status_code != 200:
        app.logger.error(f"Failed to send Telegram poll: {response.text}")


def delete_telegram(message_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
    params = {"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id}
    response = requests.post(url, json=params)
    if response.status_code != 200:
        app.logger.error(f"Failed to delete Telegram message: {response.text}")
