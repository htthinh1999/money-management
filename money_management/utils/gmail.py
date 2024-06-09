import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


# Load environment variables
env_vars = os.environ
GOOGLE_CREDENTIALS_FILE = env_vars.get("GOOGLE_CREDENTIALS_FILE")
GOOGLE_TOKEN_FILE = env_vars.get("GOOGLE_TOKEN_FILE")
GOOGLE_PUBSUB_TOPIC = env_vars.get("GOOGLE_PUBSUB_TOPIC")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def init():
    creds = None
    if os.path.exists(GOOGLE_TOKEN_FILE):
        with open(GOOGLE_TOKEN_FILE, "rb") as token:
            creds = Credentials.from_authorized_user_file(
                GOOGLE_TOKEN_FILE, GMAIL_SCOPES
            )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CREDENTIALS_FILE, GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=8081, open_browser=False)
        with open(GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    global gmail
    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return gmail


def watch():
    gmail = init()
    request = {
        "labelIds": ["INBOX"],
        "topicName": GOOGLE_PUBSUB_TOPIC,
        "labelFilterBehavior": "INCLUDE",
    }
    watch = gmail.users().watch(userId="me", body=request).execute()
    return watch["historyId"]


def get_histories(history_id):
    gmail = init()
    histories = (
        gmail.users().history().list(userId="me", startHistoryId=history_id).execute()
    )
    return histories


def get_message(message_id):
    gmail = init()
    message = gmail.users().messages().get(userId="me", id=message_id).execute()
    return message
