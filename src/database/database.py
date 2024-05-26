import os
import utils.logger as logger
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Load the MongoDB URI from the environment variables
env_vars = os.environ
db_host = env_vars.get('MONGO_DB_HOST')
db_user = env_vars.get('MONGO_DB_USER')
db_password = env_vars.get('MONGO_DB_PASSWORD')
uri = f"mongodb+srv://{db_user}:{db_password}@{db_host}/?retryWrites=true&w=majority&appName=money-management"

MONGO_CLIENT = None

def init():
    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi('1'))
    global MONGO_CLIENT
    MONGO_CLIENT = client

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB!")
    except Exception as e:
        logger.error(e)

def get_mongo_client():
    return MONGO_CLIENT