from money_management.shared.daily import Daily
from money_management.shared.models.base_model import BaseModel


class MonthReport(BaseModel):
    total: int
    daily_list: list[Daily]

    def __init__(self, dict):
        super().__init__(dict)
        self.daily_list = [Daily(daily) for daily in dict["daily_list"]]

    def __str__(self):
        super_str = super().__str__()
