import os
import base64
import json
import requests
import logging
from flask import Flask, request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

app = Flask(__name__)
# Configure logging
logging.basicConfig(level=logging.INFO,format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %I:%M:%S')

# Load environment variables
env_vars = os.environ
TELEGRAM_BOT_TOKEN = env_vars.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = env_vars.get('TELEGRAM_CHAT_ID')
GOOGLE_CREDENTIALS_FILE = env_vars.get('GOOGLE_CREDENTIALS_FILE')
GOOGLE_TOKEN_FILE = env_vars.get('GOOGLE_TOKEN_FILE')
GOOGLE_PUBSUB_TOPIC = env_vars.get('GOOGLE_PUBSUB_TOPIC')

MAX_MESSAGE_LENGTH = 4000
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
CURRENT_HISTORY_ID = 0

@app.route('/healthz', methods=['GET'])
def health_check():
    return 'Healthy', 200

def build_gmail_service():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        with open(GOOGLE_TOKEN_FILE, 'rb') as token:
            creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE, GMAIL_SCOPES)
            creds = flow.run_local_server(port=8081,open_browser=False)
        with open(GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    gmail = build('gmail', 'v1', credentials=creds, cache_discovery=False)
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
    global CURRENT_HISTORY_ID
    CURRENT_HISTORY_ID = history_id
    app.logger.info(f"Watch started with history ID: {history_id}")
    return f"Watch started with history ID: {history_id}", 200

@app.route('/webhook', methods=['POST'])
def receive_pubsub_message():
    if request.method == 'POST':
        envelope = request.get_json()
        if envelope and 'message' in envelope:
            pubsub_message = envelope['message']
            data = base64.b64decode(pubsub_message['data']).decode("utf-8")
            app.logger.info(f"Data from Pub/Sub: {data}")
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

    global CURRENT_HISTORY_ID
    if CURRENT_HISTORY_ID == 0:
        watch()

    histories = gmail.users().history().list(userId='me', startHistoryId=CURRENT_HISTORY_ID).execute()
    CURRENT_HISTORY_ID = history_id

    app.logger.info(f"Processing histories: {histories} with history ID: {CURRENT_HISTORY_ID}")
    if 'history' not in histories:
        # no new messages
        return
    
    for history in histories['history']:
        if 'messagesAdded' not in history:
            continue
        message_added = history['messagesAdded']
        for message in message_added:
            if 'message' not in message:
                continue
            if 'id' not in message['message']:
                continue
            message_id = message['message']['id']
            email = gmail.users().messages().get(userId='me', id=message_id).execute()
            app.logger.info(f"Processing email: {email}")
            if 'snippet' not in email:
                continue
            snippet = email['snippet']
            subject = ''
            if 'headers' not in email['payload']:
                continue
            if 'headers' not in email['payload']:
                continue
            for header in email['payload']['headers']:
                if 'name' not in header:
                    continue
                if 'value' not in header:
                    continue
                if header['name'] == 'Subject':
                    subject = header['value']
                    break
            # message = f"Subject: {subject}; Snippet: {snippet}"
            app.logger.info(message)
            if len(message) > 4096:
                for x in range(0, len(message), 4096):
                    send_telegram_message(message[x:x+4096])
                else:
                    send_telegram_message(message)
            else:
                send_telegram_message(message)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=params)
    if response.status_code != 200:
        app.logger.error(f"Failed to send Telegram message: {response.text}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
