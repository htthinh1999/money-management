import os
import base64
import json
import time
import requests
import utils.logger as logger
import database.database as database
import repositories.history_repository as history_repository
from flask import Flask, request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

app = Flask(__name__)
logger.init(app)
database.init()

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
    set_current_history_id(history_id)
    logger.info(f"Watch started with history ID: {history_id}")
    return f"Watch started with history ID: {history_id}", 200

@app.route('/webhook', methods=['POST'])
def receive_pubsub_message():
    if request.method == 'POST':
        envelope = request.get_json()
        if envelope and 'message' in envelope:
            pubsub_message = envelope['message']
            data = base64.b64decode(pubsub_message['data']).decode("utf-8")
            logger.info(f"Data from Pub/Sub: {data}")
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
    logger.info(f"Received email from {email_address} with history ID: {history_id}")

    # Fetch the email details
    gmail = build_gmail_service()

    global CURRENT_HISTORY_ID
    CURRENT_HISTORY_ID = history_repository.get_current_history_id()
    if CURRENT_HISTORY_ID == 0:
        watch()

    histories = gmail.users().history().list(userId='me', startHistoryId=CURRENT_HISTORY_ID).execute()
    set_current_history_id(history_id)

    logger.info(f"Processing histories: {histories} with history ID: {CURRENT_HISTORY_ID}")
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
            # logger.info(f"Processing email: {email}")
            subject = ''
            from_email = ''
            if 'payload' not in email:
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
                if header['name'] == 'From':
                    from_email = header['value']
            if from_email != "VCBDigibank@info.vietcombank.com.vn" or 'Biên lai' not in subject:
                continue
            
            if 'body' not in email['payload']:
                continue
            if 'data' not in email['payload']['body']:
                continue
            mail_body = email['payload']['body']['data']
            mail_html = base64.urlsafe_b64decode(mail_body).decode('utf-8')

            # find first text match 'VND' in html
            cost_end_pos = mail_html.find('VND')
            # find last text match '>' in html end with 'VND'
            cost_start_pos = mail_html.rfind('>', 0, cost_end_pos)
            # get cost value
            cost = mail_html[cost_start_pos+1:cost_end_pos]
            # convert cost to number
            cost = int(cost.replace(',', ''))
            # convert cost to string with dot separator
            cost = "{:,}".format(cost)
            message = f"{subject}: <b>{cost}</b> VND"
            logger.info(message)
            if len(message) > 4096:
                for x in range(0, len(message), 4096):
                    send_telegram_message(message[x:x+4096])
                    # delay 1 second to avoid telegram rate limit
                    time.sleep(1)
                else:
                    send_telegram_message(message)
            else:
                send_telegram_message(message)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?parse_mode=HTML"
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    response = requests.post(url, json=params)
    if response.status_code != 200:
        logger.error(f"Failed to send Telegram message: {response.text}")

def set_current_history_id(history_id):
    global CURRENT_HISTORY_ID
    CURRENT_HISTORY_ID = history_id
    history_repository.set_current_history_id(history_id)
    return CURRENT_HISTORY_ID

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)