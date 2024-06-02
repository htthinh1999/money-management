import os
import base64
import json
import time
import requests
import utils.logger as logger
import database.database as database
import repositories.history_repository as history_repository
import repositories.daily_repository as daily_repository
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
            # process mail html
            cost = cost_convert(get_value_from_mail_html_with_i_tag(mail_html, "Amount"))
            details_of_payment = get_value_from_mail_html_with_i_tag(mail_html, "Details of Payment")
            beneficiary_name = get_value_from_mail_html_with_i_tag(mail_html, "Beneficiary Name")
            trans_date_time = get_value_from_mail_html_with_i_tag(mail_html, "Trans. Date, Time")
            trans_date = date_from_trans_date_time(trans_date_time)
            trans_time = date_from_trans_date_time(trans_date_time, trans_time=True)
            # store daily money
            daily_repository.store_daily_money(cost, beneficiary_name, details_of_payment, trans_date, trans_time)
            # send telegram message
            message = f"{subject} - {beneficiary_name}: <b>{cost}</b> VND\n{details_of_payment}"
            send_telegram(message)

def get_value_from_mail_html_with_i_tag(mail_html, tag_value):
    # find first text match '<i>{tag_value}</i>' in html
    tag_start_pos = mail_html.find(f'<i>{tag_value}</i>')
    # find first open td tag after tag_value
    tag_start_pos = mail_html.find('<td', tag_start_pos)
    # find first text match '>' after tag_value
    tag_start_pos = mail_html.find('>', tag_start_pos)
    # find first close td tag after tag_value
    tag_end_pos = mail_html.find('</td>', tag_start_pos)
    # get tag value
    tag_value = mail_html[tag_start_pos+1:tag_end_pos]
    # trim start and end space
    tag_value = tag_value.strip()
    return tag_value

def cost_convert(cost_text):
    cost = int(cost_text.replace(' VND', '').replace(',', ''))
    # convert cost to string with dot separator
    cost = "{:,}".format(cost)
    return cost

def date_from_trans_date_time(trans_date_time, trans_time: bool = False):
    # trans date time format: 14:31 Chủ Nhật 19/05/2024
    # get last 10 characters
    date = trans_date_time[-10:]
    # current format: 19/05/2024 -> new format: 2024-05-19
    date = date[-4:] + '-' + date[3:5] + '-' + date[:2]
    if trans_time:
        # get first 5 characters
        time = trans_date_time[:5]
        # current format: 14:31 -> new format: 14:31:00
        time = time + ':00'
        # combine date and time
        date = date + ' ' + time

def send_telegram(message):
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
