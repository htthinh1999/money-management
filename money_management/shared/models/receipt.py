class Receipt:

    def __init__(
        self, amount, beneficiary_name, details_of_payment, trans_date, trans_time
    ):
        self.amount = amount
        self.beneficiary_name = beneficiary_name
        self.details_of_payment = details_of_payment
        self.trans_date = trans_date
        self.trans_time = trans_time

    def __str__(self):
        return f"{self.beneficiary_name}: {self.amount} VND\n{self.details_of_payment}"
