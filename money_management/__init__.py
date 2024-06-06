from flask import Flask
import logging

app = Flask(__name__)
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S",
)

from money_management import database
from money_management import routes
