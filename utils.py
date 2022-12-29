import math

import config


class Rating:
    def __init__(self, rating_name):
        quarter, year = rating_name.split("_")
        self.rating_name = rating_name
        self.quarter = int(quarter[1])
        self.year = int(year[:-4])


class TaxPool:
    def __init__(self):
        self.balance = 0.0
        self.paid_balance = 0.0

    def add_tax(self, profit):
        tax = profit * config.taxes
        self.balance += tax

    def process_rebalancing(self):
        if self.balance < 0:
            to_get_back = self.balance
            if -1*to_get_back > self.paid_balance:
                to_get_back = -1*self.paid_balance

            self.paid_balance += to_get_back
            self.balance = 0
            return to_get_back
        else:
            self.paid_balance += self.balance
            to_pay = self.balance
            self.balance = 0
            return to_pay


class Position:
    def __init__(self, qty, price):
        self.qty = qty
        self.price = price


def simulate_fee(transaction_size):
    min_fee = config.min_transaction_fee
    max_fee = config.max_transaction_fee
    variable_fee = config.transaction_fee

    return min(
        max(min_fee, transaction_size*variable_fee),
        max_fee
    )


def get_symbols_for_new_portfolio(current_portfolio, new_symbols):
    # TODO do sth with current_portfolio --> threshold to kick out for example
    return new_symbols[:100]


def build_new_portfolio(current_portfolio, new_symbols, prices, cash):
    total_available_assets = cash
    for symbol, position in current_portfolio.items():
        total_available_assets += prices[symbol] * position.qty

    new_portfolio = {}
    pos_size = total_available_assets/len(new_symbols)
    if config.portfolio_strat == "floor":
        for symbol in new_symbols:
            new_portfolio[symbol] = min(math.floor(prices[symbol]/pos_size), 1)

    return new_portfolio


def do_rebalancing(current_portfolio, new_portfolio, prices, cash, taxpool: TaxPool, total_fees):
    """
    :param current_portfolio: being altered
    :param new_portfolio: contains symbol + qty, only used for rebalancing/taking orders
    :param prices: prices of stock
    :param cash: free cash that is available --> to return
    :param taxpool: being altered
    :param total_fees: total fees that have been paid --> to return
    :return: cash, total_fees
    """
    # first sell
    for symbol, position in current_portfolio.items():
        if symbol not in new_portfolio:
            transaction_size = prices[symbol] * current_portfolio[symbol].qty
            fee = simulate_fee(transaction_size)
            total_fees += fee
            cash += transaction_size - fee
            profit = (prices[symbol] - current_portfolio[symbol].price) * current_portfolio[symbol].qty
            taxpool.add_tax(profit)
            current_portfolio.pop(symbol)

    # buy and adjust position size respectively
    for symbol, qty in new_portfolio.items():
        if symbol not in current_portfolio:
            # buy new
            transaction_size = prices[symbol] * new_portfolio[symbol]
            fee = simulate_fee(transaction_size)
            total_fees += fee
            cash -= new_portfolio[symbol]*prices[symbol]
            cash -= fee
            current_portfolio[symbol] = Position(new_portfolio[symbol], prices[symbol])
        else:
            # alter number of shares being held
            if current_portfolio[symbol].qty < new_portfolio[symbol]:
                # buy more
                to_buy = new_portfolio[symbol] - current_portfolio[symbol].qty
                transaction_size = to_buy * prices[symbol]
                fee = simulate_fee(transaction_size)
                total_fees += fee
                cash -= transaction_size
                cash -= fee

                # calc new average price
                new_price = (
                                    current_portfolio[symbol].qty*current_portfolio[symbol].price
                                    +
                                    to_buy*prices[symbol]
                             )/new_portfolio[symbol]
                current_portfolio[symbol] = Position(new_portfolio[symbol], new_price)
            elif current_portfolio[symbol].qty > new_portfolio[symbol]:
                to_sell = current_portfolio[symbol].qty - new_portfolio[symbol]
                transaction_size = to_sell * prices[symbol]
                fee = simulate_fee(transaction_size)
                total_fees += fee
                cash += transaction_size - fee
                profit = (prices[symbol] - current_portfolio[symbol].price) * to_sell
                taxpool.add_tax(profit)
                current_portfolio[symbol] = Position(new_portfolio[symbol], current_portfolio[symbol].price)

    cash -= taxpool.process_rebalancing()
    return cash, total_fees
