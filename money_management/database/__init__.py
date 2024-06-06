import os
from money_management import app
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Load the MongoDB URI from the environment variables
env_vars = os.environ
DB_HOST = env_vars.get("MONGO_DB_HOST")
DB_USER = env_vars.get("MONGO_DB_USER")
DB_PASSWORD = env_vars.get("MONGO_DB_PASSWORD")
uri = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/?retryWrites=true&w=majority&appName=money-management"

# Create a new client and connect to the server
mongo_client = MongoClient(uri, server_api=ServerApi("1"))
database = None

# Send a ping to confirm a successful connection
try:
    mongo_client.admin.command("ping")
    app.logger.info(f"Successfully connected to MongoDB!")
    database = mongo_client["money-management"]
except Exception as e:
    app.logger.error(e)
