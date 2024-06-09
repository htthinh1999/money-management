from money_management.shared.models.base_model import BaseModel


class Daily(BaseModel):
    amount: int
    beneficiary: str
    description: str
    category: str
    date: str
    time: str

    def __init__(self, dict):
        super().__init__(dict)

    def __str__(self):
        super_str = super().__str__()
