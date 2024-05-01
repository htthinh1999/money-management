import os
import base64
import json
import requests
import logging
from flask import Flask, request

app = Flask(__name__)
# Configure logging
logging.basicConfig(level=logging.INFO,format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S')

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

@app.route('/webhook', methods=['POST'])
def receive_pubsub_message():
    if request.method == 'POST':
        envelope = request.get_json()
        if envelope and 'message' in envelope:
            pubsub_message = envelope['message']
            data = base64.b64decode(pubsub_message['data']).decode('utf-8')
            message = f"Data from Pub/Sub:\n{data}"
            app.logger.info(message)
            # Assuming the data is JSON
            gmail_data = json.loads(data)
            # Process the Gmail data here
            process_gmail_data(gmail_data)
            return 'Message received', 200
        else:
            return 'Bad request: missing message', 400
    else:
        return 'Method not allowed', 405

def process_gmail_data(gmail_data):
    # Extract relevant information from Gmail data
    sender = gmail_data.get('sender', '')
    subject = gmail_data.get('subject', '')
    message_body = gmail_data.get('message_body', '')
    # Perform actions based on the extracted information
    message = f"\nNew email from: {sender}\nSubject: {subject}\nMessage Body:\n{message_body}"
    app.logger.info(message)
    # Send message to Telegram
    send_telegram_message(message)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message
    }
    response = requests.post(url, json=params)
    if response.status_code != 200:
        app.logger.error(f"Failed to send Telegram message: {response.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
