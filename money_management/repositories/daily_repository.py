from money_management.database import database


def store_daily_money(amount, beneficiary, description, trans_date, trans_time):
    daily = {
        "amount": amount,
        "beneficiary": beneficiary,
        "description": description,
        "date": trans_date,
        "time": trans_time,
    }
    database.daily.insert_one(daily)
