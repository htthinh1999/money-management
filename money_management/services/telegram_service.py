from datetime import datetime
import time
from money_management import app
from money_management.repositories import (
    daily_repository,
    telegram_poll_message_repository,
)
from money_management.shared.daily import Daily
from money_management.shared.enums.category import (
    get_category_by_index,
    get_category_by_string,
)
from money_management.shared.models.month_report import MonthReport
from money_management.utils import telegram
from money_management.utils.common import valid_year_month


def process_telegram_update(update_data):
    app.logger.info(f"Processing Telegram update: {update_data}")
    if "poll_answer" in update_data:
        poll_answer = update_data["poll_answer"]
        process_poll_answer(poll_answer)
    elif "message" in update_data:
        message = update_data["message"]
        process_message(message)


def process_poll_answer(poll_answer):
    poll_id = poll_answer["poll_id"]
    category_position = poll_answer["option_ids"][0]
    category = get_category_by_index(category_position)
    poll_message = telegram_poll_message_repository.find_by_poll_id(poll_id)
    if poll_message is None:
        return
    daily_id = poll_message["daily_id"]
    daily_data = daily_repository.update_category(daily_id, category.name)
    telegram.delete_message(poll_message["message_id"])
    message = f"💵{daily_data['amount']} chi cho `{category.value}`\n{daily_data['beneficiary']} - {daily_data['description']}"
    telegram.send_message(message)
    telegram_poll_message_repository.delete_by_poll_id(poll_id)


def process_message(message):
    text: str = message["text"]
    if text == "/start":
        telegram.send_message("Chào bạn, mình là bot quản lý chi tiêu")
    elif text.startswith("/report_detail"):
        month = text.split(" ")[1] if len(text.split(" ")) > 1 else None
        month_report_detail(month)
    elif text.startswith("/report"):
        month = text.split(" ")[1] if len(text.split(" ")) > 1 else None
        month_report(month)
    else:
        telegram.send_message("Mình không hiểu bạn muốn gì, hãy thử lại")


def month_report(month: str):
    if month is None or not valid_year_month(month):
        month = datetime.now().strftime("%Y-%m")

    report = daily_repository.get_total_amount_and_list_daily_by_date_range(
        f"{month}-01", f"{month}-31"
    )
    month_report = MonthReport(report)
    total = month_report.total
    message = f"Tổng chi tiêu tháng `{month}`: <b>{total:,}</b>\n"
    message = f"{message}{prepare_month_report_message(month_report.daily_list)}"
    telegram.send_message(message)


def prepare_month_report_message(daily_list: list[Daily]):
    message = f"Chi tiêu từng ngày:\n"
    message = f"{message}{'-' * 41}\n"
    daily_list = daily_list or []
    # sort daily by date
    daily_list.sort(key=lambda x: x.date)
    # group daily by date
    daily_group_by_date = {}
    for daily in daily_list:
        if daily.date not in daily_group_by_date:
            daily_group_by_date[daily.date] = []
        daily_group_by_date[daily.date].append(daily)
    for daily_date, daily_group in daily_group_by_date.items():
        total_amount = sum([daily.amount for daily in daily_group])
        message = f"{message}{daily_date}{' ' * 20}{total_amount:,}\n"
    message = f"{message}{'-' * 41}"
    return message


def month_report_detail(month: str):
    if month is None or not valid_year_month(month):
        month = datetime.now().strftime("%Y-%m")

    report = daily_repository.get_total_amount_and_list_daily_by_date_range(
        f"{month}-01", f"{month}-31"
    )
    month_report = MonthReport(report)
    total = month_report.total
    message = f"Tổng chi tiêu tháng `{month}`: <b>{total:,}</b>\n"
    telegram.send_message(message)
    daily_list = month_report.daily_list
    daily_list.sort(key=lambda x: x.date)
    # group daily by date
    daily_group_by_date = {}
    for daily in daily_list:
        if daily.date not in daily_group_by_date:
            daily_group_by_date[daily.date] = []
        daily_group_by_date[daily.date].append(daily)
    for daily_date, daily_group in daily_group_by_date.items():
        message = {prepare_month_report_detail_message(daily_date, daily_group)}
        app.logger.info(f"message: {message}")
        # telegram.send_message(message)
        # delay 1s to send next message
        # time.sleep(1)


def prepare_month_report_detail_message(daily_date: str, daily_group: list[Daily]):
    daily_group = daily_group or []
    daily_group.sort(key=lambda x: x.time)
    total_amount = sum([daily.amount for daily in daily_group])
    message = f"{'-' * 41}\n"
    message = f"Chi tiêu ngày `{daily_date}`: <b>{total_amount:,}</b>\n"
    message = f"{message}{'-' * 41}\n"
    for daily in daily_group:
        message = f"{message}{daily.time[-8:][:5]}{' ' * 5}{daily.amount:<15,}{daily.category}\n"
    message = f"{message}{'-' * 41}"
    return message
