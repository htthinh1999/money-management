from money_management import app
from money_management.repositories import (
    daily_repository,
    telegram_poll_message_repository,
)
from money_management.shared.category import get_category_by_index
from money_management.utils import telegram


def process_telegram_update(update_data):
    app.logger.info(f"Processing Telegram update: {update_data}")
    if "poll_answer" in update_data:
        poll_answer = update_data["poll_answer"]
        poll_id = poll_answer["poll_id"]
        category_position = poll_answer["option_ids"][0]
        category = get_category_by_index(category_position)
        poll_message = telegram_poll_message_repository.find_by_poll_id(poll_id)
        if poll_message is None:
            return
        daily_id = poll_message["daily_id"]
        daily_data = daily_repository.update_category(daily_id, category.value)
        telegram.delete_message(poll_message["message_id"])
        message = f"💵{daily_data['amount']} chi cho `{category.value}`\n{daily_data['beneficiary']} - {daily_data['description']}"
        telegram.send_message(message)
        telegram_poll_message_repository.delete_by_poll_id(poll_id)
