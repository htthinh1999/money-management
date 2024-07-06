from flask import Flask
from cloud_detect import provider
import logging

app = Flask(__name__)


def is_cloud_handler(handler: logging.Handler) -> bool:
    """
    is_cloud_handler

    Returns True or False depending on whether the input is a
    google-cloud-logging handler class

    """
    accepted_handlers = (
        google.cloud.logging.handlers.StructuredLogHandler,
        google.cloud.logging.handlers.CloudLoggingHandler,
        google.cloud.logging.handlers.ContainerEngineHandler,
        google.cloud.logging.handlers.AppEngineHandler,
    )
    return isinstance(handler, accepted_handlers)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
)

if provider() == "gcp":
    # Set up the Google Cloud Logging python client library
    import google.cloud.logging

    client = google.cloud.logging.Client()
    root_logger = logging.getLogger()
    root_logger.handlers = [h for h in root_logger.handlers if is_cloud_handler(h)]
    client.setup_logging()

from money_management import database
from money_management import routes
