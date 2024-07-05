from flask import Flask
from cloud_detect import provider
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
)

if provider() == "gcp":
    # Set up the Google Cloud Logging python client library
    import google.cloud.logging

    client = google.cloud.logging.Client()
    client.get_default_handler()
    client.setup_logging()

from money_management import database
from money_management import routes
