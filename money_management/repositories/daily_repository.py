from money_management.database import database
from money_management.shared.category import Category


def store_daily_money(amount, beneficiary, description, trans_date, trans_time):
    daily = {
        "amount": amount,
        "beneficiary": beneficiary,
        "description": description,
        "category": Category.Other.value,
        "date": trans_date,
        "time": trans_time,
    }
    result = database.daily.insert_one(daily)
    return result.inserted_id


def update_category(daily_id, category):
    return database.daily.find_one_and_update(
        {"_id": daily_id}, {"$set": {"category": category}}
    )
