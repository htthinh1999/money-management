from money_management import app


def process_telegram_update(update_data):
    app.logger.info(f"Processing Telegram update: {update_data}")
