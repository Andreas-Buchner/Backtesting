import os

import pandas as pd
import yfinance as yf

from utils import *


class Backtester:
    def __init__(self):
        self.starting_money = config.start_money
        self.rating_list = []
        for rating_name in os.listdir("ratings"):
            self.rating_list.append(Rating(rating_name))
        self.rating_list.sort(key=lambda x: (x.year, x.quarter))

    def simulate(self):
        for rating in self.rating_list:
            if os.path.exists("data/"+rating.rating_name):
                data = pd.read_csv("data/"+rating.rating_name, header=[0, 1], index_col=0)
            else:
                symbols = rating.rating_df['Symbol'].to_list()[:200]  # only look at the top ratings --> portfolio will be smaller anyways
                data = yf.download(symbols, start=rating.start_date.strftime("%Y-%m-%d"), end=rating.end_date.strftime("%Y-%m-%d"),
                                   actions=True)[['Adj Close', 'Dividends']]
                data.to_csv("data/"+rating.rating_name)


