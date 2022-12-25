import config
import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd


def simulate_fee(transaction_size):
    min_fee = config.min_transaction_fee
    max_fee = config.max_transaction_fee
    variable_fee = config.transaction_fee

    return min(
        max(min_fee, transaction_size*variable_fee),
        max_fee
    )


class Rating:
    def __init__(self, rating_name):
        quarter, year = rating_name.split("_")
        self.rating_name = rating_name
        self.quarter = int(quarter[1])
        self.year = int(year[:-4])
        self.start_date = datetime.datetime(year=self.year, month=[1, 4, 7, 10][self.quarter-1], day=1)
        self.end_date = self.start_date + relativedelta(months=+3)
        self.rating_df = pd.read_csv("ratings/"+rating_name)
