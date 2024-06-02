import database.database as database

def store_daily_money(amount, beneficiary, description, trans_date, trans_time):
    mongo_client = database.get_mongo_client()
    db = mongo_client['money-management']
    daily = {
        'amount': amount,
        'beneficiary': beneficiary,
        'description': description,
        'date': trans_date,
        'time': trans_time
    }
    db.daily.insert_one(daily)
