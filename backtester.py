import os

import pandas as pd
import yfinance as yf

from utils import *


class Backtester:
    def __init__(self):
        self.cash = config.start_money
        self.fees = 0.0
        self.rating_list = []
        for rating_name in os.listdir("ratings"):
            self.rating_list.append(Rating(rating_name))
        self.rating_list.sort(key=lambda x: (x.year, x.quarter))
        self.results = {
            'portfolio_val': [],
            'cash': [],
            'fees': [],
            'taxes': []
        }

    def simulate(self):
        curr_portfolio = {}
        new_port = {}
        taxpool = TaxPool()
        first_rating = True
        for rating in self.rating_list:
            rating_symbols = pd.read_csv("ratings/"+rating.rating_name)['Symbol'].to_list()
            new_symbols = get_symbols_for_new_portfolio(curr_portfolio, rating_symbols)
            data = pd.read_csv("data/"+rating.rating_name, header=[0, 1], index_col=0)

            for date, prices in data.iterrows():
                if first_rating:
                    new_port = build_new_portfolio(curr_portfolio, new_symbols, prices, self.cash)
                    first_rating = False
                if date == data.index[0]:
                    self.cash, self.fees = do_rebalancing(curr_portfolio, new_port, prices, self.cash, taxpool, self.fees)

                portfolio_value = 0.0
                for symbol, position in curr_portfolio.items():
                    portfolio_value += position.qty * prices[symbol]

                self.results['portfolio_val'].append(portfolio_value)
                self.results['cash'].append(self.cash)
                self.results['fees'].append(self.fees)
                self.results['taxes'].append(taxpool.paid_balance)

                if date == data.index[-1]:
                    new_port = build_new_portfolio(curr_portfolio, new_symbols, prices, self.cash)







