
import logging

global app

# Configure logging
logging.basicConfig(level=logging.INFO,format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S')

def init(app_instance):
    global app
    app = app_instance

def info(message):
    app.logger.info(message)

def error(message):
    app.logger.error(message)

def warning(message):
    app.logger.warning(message)