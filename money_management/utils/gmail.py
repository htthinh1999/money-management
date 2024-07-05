import os
from money_management import app
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


# Load environment variables
env_vars = os.environ
GOOGLE_OAUTH_STATE = env_vars.get("GOOGLE_OAUTH_STATE")
GOOGLE_OAUTH_CODE_VERIFIER = env_vars.get("GOOGLE_OAUTH_CODE_VERIFIER")
GOOGLE_OAUTH_REDIRECT_URI = env_vars.get("GOOGLE_OAUTH_REDIRECT_URI")
GOOGLE_CREDENTIALS_FILE = env_vars.get("GOOGLE_CREDENTIALS_FILE")
GOOGLE_TOKEN_FILE: str = env_vars.get("GOOGLE_TOKEN_FILE") or "user-token/token.json"
GOOGLE_PUBSUB_TOPIC = env_vars.get("GOOGLE_PUBSUB_TOPIC")

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def init():
    # Generate a random state for CSRF protection
    # state = secrets.token_urlsafe(16)
    state = GOOGLE_OAUTH_STATE
    # Generate code verifier and challenge for PKCE
    # code_verifier = secrets.token_urlsafe(64)
    code_verifier = GOOGLE_OAUTH_CODE_VERIFIER
    code_challenge = code_verifier

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
                GOOGLE_CREDENTIALS_FILE,
                scopes=GMAIL_SCOPES,
                redirect_uri=GOOGLE_OAUTH_REDIRECT_URI,
            )
            authorization_url, _ = flow.authorization_url(
                state=state,
                code_challenge=code_challenge,
                code_challenge_method="plain",
                access_type="offline",
                prompt="consent",
            )
            # Redirect the user to the authorization URL
            return (None, authorization_url)

        with open(GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    global gmail
    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return (gmail, None)


def valid_state(state: str | None):
    return state == GOOGLE_OAUTH_STATE


def process_callback(args):
    flow = InstalledAppFlow.from_client_secrets_file(
        GOOGLE_CREDENTIALS_FILE,
        scopes=GMAIL_SCOPES,
        redirect_uri=GOOGLE_OAUTH_REDIRECT_URI,
    )
    code_verifier = GOOGLE_OAUTH_CODE_VERIFIER
    flow.fetch_token(code=args["code"], code_verifier=code_verifier)
    creds = flow.credentials
    with open(GOOGLE_TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    app.logger.info("Google OAuth token saved")


def watch() -> str:
    (gmail, authorization_url) = init()
    if gmail is None:
        return authorization_url or ""
    request = {
        "labelIds": ["INBOX"],
        "topicName": GOOGLE_PUBSUB_TOPIC,
        "labelFilterBehavior": "INCLUDE",
    }
    watch = gmail.users().watch(userId="me", body=request).execute()
    return watch["historyId"]


def get_histories(history_id):
    (gmail, authorization_url) = init()
    if gmail is None:
        app.logger.error("Gmail service is not initialized")
        return {"history": []}

    histories = (
        gmail.users().history().list(userId="me", startHistoryId=history_id).execute()
    )
    return histories


def get_message(message_id):
    (gmail, authorization_url) = init()
    if gmail is None:
        app.logger.error("Gmail service is not initialized")
        return []
    message = gmail.users().messages().get(userId="me", id=message_id).execute()
    return message
