import pandas as pd
import backtester
import os


def main():
    bt = backtester.Backtester()
    bt.simulate()
    bt.plot_results()
    """
    for rating in os.listdir("ratings"):
        symbols = pd.read_csv("ratings/" + rating)['Symbol'][:200]
        data = pd.read_csv("data/" + rating, header=[0, 1])
        adj_cl = data['Adj Close'].columns
        div = data['Dividends'].columns
        not_in_div = [x for x in adj_cl if x not in div]
        print(not_in_div)   
    """


if __name__ == "__main__":
    main()
