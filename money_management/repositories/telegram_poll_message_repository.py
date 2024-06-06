from money_management.database import database


def store_poll_message(message_id, poll_id, daily_id):
    poll_message = {"daily_id": daily_id, "message_id": message_id, "poll_id": poll_id}
    database.telegram_poll_message.insert_one(poll_message)


def find_by_poll_id(poll_id):
    return database.telegram_poll_message.find_one({"poll_id": poll_id})


def delete_by_poll_id(poll_id):
    return database.telegram_poll_message.delete_one({"poll_id": poll_id})
