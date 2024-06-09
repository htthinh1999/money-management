from money_management.database import database
from money_management.shared.enums.category import Category
from money_management.shared.models.receipt import Receipt


def store_daily_money(receipt: Receipt):
    daily = {
        "amount": receipt.amount,
        "beneficiary": receipt.beneficiary_name,
        "description": receipt.details_of_payment,
        "category": Category.Other.name,
        "date": receipt.trans_date,
        "time": receipt.trans_time,
    }
    result = database.daily.insert_one(daily)
    return result.inserted_id


def update_category(daily_id, category):
    return database.daily.find_one_and_update(
        {"_id": daily_id}, {"$set": {"category": category}}
    )


def get_total_amount_and_list_daily_by_date_range(date_from, date_to):
    total_amount = list(
        database.daily.aggregate(
            [
                {
                    "$match": {
                        "date": {
                            "$gte": date_from,
                            "$lte": date_to,
                        }
                    }
                },
                {
                    "$addFields": {
                        "amount": {
                            "$convert": {
                                "input": {
                                    "$replaceAll": {
                                        "input": "$amount",
                                        "find": ",",
                                        "replacement": "",
                                    }
                                },
                                "to": "int",
                            }
                        }
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total": {"$sum": "$amount"},
                        "daily": {"$push": "$$ROOT"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "total": 1,
                        "daily_list": {
                            "$map": {
                                "input": "$daily",
                                "as": "daily",
                                "in": {
                                    "amount": "$$daily.amount",
                                    "beneficiary": "$$daily.beneficiary",
                                    "description": "$$daily.description",
                                    "category": "$$daily.category",
                                    "date": "$$daily.date",
                                    "time": "$$daily.time",
                                },
                            }
                        },
                    }
                },
            ]
        )
    )
    return total_amount[0] if total_amount else {"total": 0, "daily_list": []}
