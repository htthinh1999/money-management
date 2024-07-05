from flask import Flask
from cloud_detect import provider
import logging

app = Flask(__name__)

if provider() == "gcp":
    # Set up the Google Cloud Logging python client library
    import google.cloud.logging

    client = google.cloud.logging.Client()
    client.setup_logging()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S",
)

from money_management import database
from money_management import routes
