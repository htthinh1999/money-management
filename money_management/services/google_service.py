import base64
from money_management.shared.enums.category import Category
from money_management.shared.models.receipt import Receipt
from money_management.utils.common import (
    cost_convert,
    date_from_trans_date_time,
    get_value_from_mail_html_with_i_tag,
)
from money_management.utils import gmail
from money_management.utils import telegram
from money_management.repositories import daily_repository
from money_management.repositories import history_repository
from money_management.repositories import telegram_poll_message_repository


def valid_state(state: str | None):
    return gmail.valid_state(state)


def process_callback(args):
    gmail.process_callback(args)


def gmail_watch():
    data = gmail.watch()
    # validate data is digit
    if not data.isdigit():
        # this is authorization url
        return data

    # this is history id
    handle_gmail_histories()
    history_id = data
    history_repository.set_current_history_id(history_id)
    return history_id


def process_pubsub(pubsub_message):
    handle_gmail_histories()
    new_history_id = pubsub_message.get("historyId", "")
    history_repository.set_current_history_id(new_history_id)


def handle_gmail_histories():
    current_history_id = history_repository.get_current_history_id()
    histories = gmail.get_histories(current_history_id)

    if "history" not in histories:
        # no new messages
        return

    for history in histories["history"]:
        if "messagesAdded" not in history:
            # no new messages
            continue
        message_added = history["messagesAdded"]
        for message in message_added:
            if "message" not in message:
                continue
            if "id" not in message["message"]:
                continue
            message_id = message["message"]["id"]
            message = gmail.get_message(message_id)
            process_gmail_message(message)


def process_gmail_message(message):
    valid_message = validate_gmail_message(message)
    if not valid_message:
        return

    mail_body = message["payload"]["body"]["data"]
    mail_html = base64.urlsafe_b64decode(mail_body).decode("utf-8")
    # get receipt from mail html
    receipt = get_receipt_from_mail_html(mail_html)

    # store daily money
    daily_id = daily_repository.store_daily_money(receipt)

    # send telegram poll
    question = f"💵{receipt.amount} chi cho?"
    options = [category.value for category in Category]
    poll = telegram.send_poll(question, options)
    telegram_poll_message_repository.store_poll_message(
        poll["message_id"], poll["poll"]["id"], daily_id
    )


def get_receipt_from_mail_html(mail_html: str):
    amount = cost_convert(get_value_from_mail_html_with_i_tag(mail_html, "Amount"))
    details_of_payment = get_value_from_mail_html_with_i_tag(
        mail_html, "Details of Payment"
    )
    beneficiary_name = get_value_from_mail_html_with_i_tag(
        mail_html, "Beneficiary Name"
    )
    trans_date_time = get_value_from_mail_html_with_i_tag(
        mail_html, "Trans. Date, Time"
    )
    trans_date = date_from_trans_date_time(trans_date_time)
    trans_time = date_from_trans_date_time(trans_date_time, trans_time=True)

    return Receipt(amount, beneficiary_name, details_of_payment, trans_date, trans_time)


def validate_gmail_message(message):
    subject = ""
    from_email = ""
    validate_success = True
    if "payload" not in message:
        validate_success = False
    if "headers" not in message["payload"]:
        validate_success = False
    for header in message["payload"]["headers"]:
        if "name" not in header:
            continue
        if "value" not in header:
            continue
        if header["name"] == "Subject":
            subject = header["value"]
        if header["name"] == "From":
            from_email = header["value"]
    if from_email != "VCBDigibank@info.vietcombank.com.vn" or "Biên lai" not in subject:
        validate_success = False
    if "body" not in message["payload"]:
        validate_success = False
    if "data" not in message["payload"]["body"]:
        validate_success = False
    return validate_success
