from money_management.database import database


def set_current_history_id(current_history_id):
    database.history.update_one(
        {"id": 1}, {"$set": {"current_history_id": current_history_id}}, upsert=True
    )


def get_current_history_id():
    current_history_id = database.history.find_one()["current_history_id"]
    return current_history_id
