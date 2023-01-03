import os

import pandas as pd
import matplotlib.pyplot as plt

import config
from utils import *


class Backtester:
    def __init__(self):
        self.cash = config.start_money
        self.rating_list = []
        for rating_name in os.listdir("ratings"):
            self.rating_list.append(Rating(rating_name))
        self.rating_list.sort(key=lambda x: (x.year, x.quarter))
        self.results = {
            'date': [],
            'portfolio_val': [],
            'cash': [],
            'paid_out_dividends': [],
            'fees': [],
            'taxes': [],
            'num_buys': [],
            'num_sells': [],
            'num_adj': [],
            'buy_vol': [],
            'sell_vol': [],
            'adj_vol': []
        }

    def simulate(self):
        curr_portfolio = {}
        taxpool = TaxPool()
        latest_prices = None
        curr_year = None
        taxes_paid = 0.0
        for rating in self.rating_list:
            new_year = False
            if curr_year is None:
                curr_year = rating.year
            elif rating.year > curr_year:
                new_year = True
                curr_year = rating.year
                taxes_paid += taxpool.paid_balance
                taxpool = TaxPool()
            rating_symbols = pd.read_csv("ratings/"+rating.rating_name)['Symbol'].to_list()
            new_symbols = get_symbols_for_new_portfolio(curr_portfolio, rating_symbols)
            data = pd.read_csv("data/"+rating.rating_name, header=[0, 1], index_col=0)

            for date, price_and_dividend in data.iterrows():
                assert self.cash >= 0
                assert taxpool.paid_balance >= 0
                prices = price_and_dividend['Adj Close']
                dividend = price_and_dividend['Dividends']
                if date == data.index[0]:
                    if latest_prices is None:
                        latest_prices = prices
                    not_in_latest_prices = [x for x in prices.index if x not in latest_prices.index]
                    latest_prices = pd.concat([latest_prices, prices[not_in_latest_prices]])
                    new_port = build_new_portfolio(curr_portfolio, new_symbols, latest_prices, self.cash)
                    self.cash, fees, num_buys, num_sells, num_adj, buy_vol, sell_vol, adj_vol = do_rebalancing(
                        curr_portfolio, new_port, latest_prices, self.cash, taxpool
                    )
                    self.results['fees'].append(fees)
                    self.results['num_buys'].append(num_buys)
                    self.results['num_sells'].append(num_sells)
                    self.results['num_adj'].append(num_adj)
                    self.results['buy_vol'].append(buy_vol)
                    self.results['sell_vol'].append(sell_vol)
                    self.results['adj_vol'].append(adj_vol)

                portfolio_value = 0.0
                dividends = 0.0
                for symbol, position in curr_portfolio.items():
                    portfolio_value += position.qty * prices[symbol]
                    if dividend[symbol] != 0:
                        tax = taxpool.add_dividend_tax(position.qty * dividend[symbol])
                        dividends += (position.qty * dividend[symbol] - tax)
                        self.cash += (position.qty * dividend[symbol] - tax)

                self.results['date'].append(date)
                self.results['portfolio_val'].append(portfolio_value)
                self.results['cash'].append(self.cash)
                self.results['paid_out_dividends'].append(dividends)
                if len(self.results['taxes']) == 0 or new_year:
                    new_year = False
                    self.results['taxes'].append(taxpool.paid_balance)
                else:
                    self.results['taxes'].append(taxpool.paid_balance+taxes_paid-sum(self.results['taxes']))
                if date != data.index[0]:
                    self.results['fees'].append(0)
                    self.results['num_buys'].append(0)
                    self.results['num_sells'].append(0)
                    self.results['num_adj'].append(0)
                    self.results['buy_vol'].append(0)
                    self.results['sell_vol'].append(0)
                    self.results['adj_vol'].append(0)

                if date == data.index[-1]:
                    latest_prices = prices

    def plot_results(self):
        df = pd.DataFrame(self.results)
        df = df.set_index('date')
        df.index = [x[:-9] for x in df.index]
        fig, ax = plt.subplots(nrows=1, ncols=1)
        ax.stackplot(
            df.index,
            [df['portfolio_val'], df['cash']],
            labels=['Portfolio', 'Cash']
        )
        ax.stackplot(
            df.index,
            [-1*df['fees'].cumsum(), -1*df['taxes'].cumsum()],
            labels=['Gebühren', 'Steuern']
        )
        ax.stackplot(
            df.index,
            df['paid_out_dividends'].cumsum(),
            labels=["Dividenden"]
        )
        ax.set_xlabel("Date")
        ax.set_ylabel("Worth")
        label_ten_ticks = round(len(df) / 15)
        plt.xticks(range(0, len(df), label_ten_ticks), df.index[::label_ten_ticks])
        fig.autofmt_xdate()
        plt.grid(True)
        plt.legend(loc="center", prop={'size': 8})
        plt.title(config.simulation_name)
        plt.tight_layout()
        plt.savefig('result.jpg', dpi=400)
        plt.show()
        df.to_csv("res.csv")

        # Print Indicators
        print(
            f"ROI Brutto: "
            f"{round((((df['portfolio_val'][-1]+df['cash'][-1]+df['fees'].sum()+df['taxes'].sum())/config.start_money)-1)*100, 2)}"
            f" %"
        )
        print(f"Gebühren: {df['fees'].sum()}")
        print(f"Steuern: {round(df['taxes'].sum(), 2)}")
        print(f"Dividenden: {round(df['paid_out_dividends'].sum(), 2)}")
        print(f"ROI Netto: {round((((df['portfolio_val'][-1] + df['cash'][-1])/config.start_money)-1)*100, 2)} %")
        print(f"Gewinn Netto: {round(df['portfolio_val'][-1]+df['cash'][-1]-config.start_money,2)}")
