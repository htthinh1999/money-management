from money_management.repositories import daily_repository
from money_management.shared.models.month_report import MonthReport


def process_month(month):
    date_from = f"{month}-01"
    date_to = f"{month}-31"
    month_data = daily_repository.get_total_amount_and_list_daily_by_date_range(
        date_from, date_to
    )
    result = MonthReport(month_data)
    return result
