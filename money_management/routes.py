import base64
import json
import logging
from flask import redirect, request
from money_management import app
from money_management.services import telegram_service
from money_management.services import google_service
from money_management.services import report_service
from money_management.utils.common import valid_year_month


@app.route("/healthz", methods=["GET"])
def health_check():
    return "Healthy", 200


@app.route("/watch", methods=["GET"])
def watch():
    data = google_service.gmail_watch()
    # validate data is digit
    if not data.isdigit():
        # this is authorization url
        logging.warning(
            f"Watch started but we didn't authenticate, redirect to Google OAuth: {data}"
        )
        return redirect(data)
    # this is history id
    history_id = data
    logging.info(f"Watch started with history ID: {history_id}")
    return f"Watch started with history ID: {history_id}", 200


@app.route("/google-callback", methods=["GET"])
def callback():
    # Verify state to prevent CSRF attacks
    if not google_service.valid_state(request.args.get("state")):
        return "Invalid state parameter", 400
    # Process Google OAuth callback
    google_service.process_callback(request.args)
    logging.info("Google OAuth callback processed")
    # Redirect to watch
    return redirect("/watch")


@app.route("/webhook", methods=["POST"])
def receive_pubsub_message():
    if request.method == "POST":
        envelope = request.get_json()
        if envelope and "message" in envelope:
            pubsub_message = envelope["message"]
            data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
            logging.info(f"Data from Pub/Sub: {data}")
            # Assuming the data is JSON
            gmail_data = json.loads(data)
            # Process the Gmail data here
            google_service.process_pubsub(gmail_data)
            return "Message received", 200
        else:
            return "Bad request: missing message", 400
    else:
        return "Method not allowed", 405


@app.route("/telegram-update", methods=["POST"])
def receive_telegram_update():
    if request.method == "POST":
        update_data = request.get_json()
        telegram_service.process_telegram_update(update_data)
        return "Telegram update received", 200
    else:
        return "Method not allowed", 405


@app.route("/month-report/<month>", methods=["GET"])
def month_report(month):
    if request.method == "GET":
        # check month format is yyyy-MM
        if not valid_year_month(month):
            return "Invalid month format", 400
        # process month report
        result = report_service.process_month(month)
        return str(result), 200
    else:
        return "Method not allowed", 405
