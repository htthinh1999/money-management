import os
import base64
import pickle
import datetime
import json
import requests
import logging
from flask import Flask, request
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

app = Flask(__name__)
# Configure logging
logging.basicConfig(level=logging.INFO,format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S')

# Load environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
GOOGLE_CREDENTIALS_FILE = os.environ.get('GOOGLE_CREDENTIALS_FILE')
GOOGLE_TOKEN_FILE = os.environ.get('GOOGLE_TOKEN_FILE')
GOOGLE_PUBSUB_TOPIC = os.environ.get('GOOGLE_PUBSUB_TOPIC') # projects/myproject/topics/mytopic

MAX_MESSAGE_LENGTH = 4000
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

@app.route('/healthz', methods=['GET'])
def health_check():
    return 'Healthy', 200

def build_gmail_service():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        with open(GOOGLE_TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    gmail = build('gmail', 'v1', credentials=creds)
    return gmail

@app.route('/watch', methods=['GET'])
def watch():
    request = {
        'labelIds': ['INBOX'],
        'topicName': GOOGLE_PUBSUB_TOPIC,
        'labelFilterBehavior': 'INCLUDE'
    }
    gmail = build_gmail_service()
    watch = gmail.users().watch(userId='me', body=request).execute()
    history_id = watch['historyId']
    app.logger.info(f"Watch started with history ID: {history_id}")

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
    # Extract relevant information from Gmail Pub/Sub data
    email_address = gmail_data.get('emailAddress', '')
    history_id = gmail_data.get('historyId', '')
    app.logger.info(f"Received email from {email_address} with history ID: {history_id}")

    # Fetch the email details
    gmail = build_gmail_service()

    histories = gmail.users().history().list(userId='me', startHistoryId=history_id).execute()
    
    for history in histories['history']:
        message_added = history['messagesAdded']
        for message in message_added:
            message_id = message['message']['id']
            email = gmail.users().messages().get(userId='me', id=message_id).execute()
            snippet = email['snippet']
            subject = ''
            for header in email['payload']['headers']:
                if header['name'] == 'Subject':
                    subject = header['value']
                    break
            message = f"Subject: {subject}\nSnippet: {snippet}"
            app.logger.info(message)
            send_telegram_message(message)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.post(url, json=params)
    if response.status_code != 200:
        app.logger.error(f"Failed to send Telegram message: {response.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
