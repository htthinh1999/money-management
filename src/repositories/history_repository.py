import database.database as database

def set_current_history_id(current_history_id):
    mongo_client = database.get_mongo_client()
    db = mongo_client['money-management']
    db.history.update_one({'id': 1},{'$set': {'current_history_id': current_history_id}}, upsert=True)

def get_current_history_id():
    mongo_client = database.get_mongo_client()
    db = mongo_client['money-management']
    history = db.history.find_one()
    current_history_id = history.current_history_id
    return current_history_id