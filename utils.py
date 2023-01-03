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

    def add_dividend_tax(self, profit):
        tax = profit * config.taxes
        self.balance += tax
        self.paid_balance += tax
        return tax

    def add_sell_tax(self, profit):
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
    new_symbols = new_symbols[:config.kickout_threshold]
    res = [symbol for symbol in current_portfolio.keys() if symbol in new_symbols]
    not_in_res = [symbol for symbol in new_symbols if symbol not in res]
    while len(res) < 100:
        res.append(not_in_res[0])
        not_in_res = not_in_res[1:]
    return res


def build_new_portfolio(current_portfolio, new_symbols, prices, cash):
    total_available_assets = cash
    for symbol, position in current_portfolio.items():
        total_available_assets += prices[symbol] * position.qty

    new_portfolio = {}
    pos_size = total_available_assets/len(new_symbols)
    if config.portfolio_strat == "floor":
        for symbol in new_symbols:
            new_portfolio[symbol] = max(math.floor(pos_size/prices[symbol]), 1)
    elif config.portfolio_strat == "floor_no_adj":
        # TODO fix
        not_adjusted = 0.0
        for symbol in new_symbols:
            qty = max(math.floor(pos_size / prices[symbol]), 1)
            if symbol in current_portfolio:
                not_adjusted += (qty - current_portfolio[symbol].qty) * prices[symbol]
                new_portfolio[symbol] = current_portfolio[symbol].qty
            else:
                new_portfolio[symbol] = max(math.floor(pos_size / prices[symbol]), 1)

        while cash < not_adjusted:
            for symbol in new_symbols:
                if symbol not in current_portfolio:
                    not_adjusted -= prices[symbol]
                    new_portfolio[symbol] -= 1
    elif config.portfolio_strat == "no_adj_opt":
        # TODO fix
        dead_cash = 0.0
        for symbol in current_portfolio:
            qty = max(math.floor(pos_size / prices[symbol]), 1)
            if symbol in new_symbols:
                dead_cash += (qty - current_portfolio[symbol].qty) * prices[symbol]

        for symbol in new_symbols:
            qty = max(math.floor(pos_size / prices[symbol]), 1)
            if symbol in current_portfolio:
                new_portfolio[symbol] = current_portfolio[symbol].qty
            else:
                new_portfolio[symbol] = qty

        improved = False
        while dead_cash > 0 and improved:
            improved = False
            for symbol in [s for s in new_symbols if s not in current_portfolio]:
                if 0 < dead_cash < prices[symbol]:
                    improved = True
                    dead_cash -= prices[symbol]
                    new_portfolio[symbol] += 1
    elif config.portfolio_strat == "optimal":
        for symbol in [x for x in current_portfolio if x not in new_symbols]:
            cash += (current_portfolio[symbol].qty*prices[symbol])
            cash -= simulate_fee(current_portfolio[symbol].qty*prices[symbol])
            profit = (prices[symbol]-current_portfolio[symbol].price) * current_portfolio[symbol].qty
            if profit > 0:
                cash -= profit * config.taxes

        new_buys = []
        for symbol in new_symbols:
            qty = max(math.floor(pos_size / prices[symbol]), 1)
            if symbol in current_portfolio:
                if (1+config.adj_threshold)*current_portfolio[symbol].qty < qty or qty < (1-config.adj_threshold)*current_portfolio[symbol].qty:
                    new_portfolio[symbol] = qty
                    diff = abs(current_portfolio[symbol].qty - qty)
                    sell = current_portfolio[symbol].qty > qty
                    trans_size = diff * prices[symbol]
                    cash -= simulate_fee(trans_size)
                    if sell:
                        cash += trans_size
                        profit = (prices[symbol] - current_portfolio[symbol].price) * diff
                        if profit > 0:
                            cash -= profit * config.taxes
                    else:
                        cash -= trans_size
                else:  # do nothing
                    new_portfolio[symbol] = current_portfolio[symbol].qty
            else:
                new_buys.append(symbol)
                cash -= simulate_fee(qty*prices[symbol])
                cash -= qty*prices[symbol]
                new_portfolio[symbol] = qty

        # due to not adjusting cash could be below zero
        improved = True
        safety_threshold = 0
        while cash < safety_threshold and improved:
            improved = False
            for symbol in new_buys:
                if prices[symbol] == 1:
                    continue
                improved = True
                cash += prices[symbol]
                new_portfolio[symbol] -= 1
                if cash >= safety_threshold:
                    break

    return new_portfolio


def do_rebalancing(current_portfolio, new_portfolio, prices, cash, taxpool: TaxPool):
    """
    :param current_portfolio: being altered
    :param new_portfolio: contains symbol + qty, only used for rebalancing/taking orders
    :param prices: prices of stock
    :param cash: free cash that is available --> to return
    :param taxpool: being altered
    :return: cash, fees
    """
    num_buys = 0
    num_sells = 0
    num_adj = 0
    buy_vol = 0.0
    sell_vol = 0.0
    adj_vol = 0.0
    total_fees = 0.0

    for symbol, position in current_portfolio.copy().items():
        # first sell
        if symbol not in new_portfolio:
            num_sells += 1
            transaction_size = prices[symbol] * current_portfolio[symbol].qty
            sell_vol += transaction_size
            fee = simulate_fee(transaction_size)
            total_fees += fee
            cash += (transaction_size - fee)
            profit = (prices[symbol] - current_portfolio[symbol].price) * current_portfolio[symbol].qty
            taxpool.add_sell_tax(profit)
            current_portfolio.pop(symbol)
    # buy and adjust position size respectively
    for symbol, qty in new_portfolio.items():
        if symbol not in current_portfolio:
            # buy new
            num_buys += 1
            transaction_size = prices[symbol] * new_portfolio[symbol]
            buy_vol += transaction_size
            fee = simulate_fee(transaction_size)
            total_fees += fee
            cash -= new_portfolio[symbol]*prices[symbol]
            cash -= fee
            current_portfolio[symbol] = Position(new_portfolio[symbol], prices[symbol])
        else:
            # alter number of shares being held
            if current_portfolio[symbol].qty < new_portfolio[symbol]:
                # buy more
                num_adj += 1
                to_buy = new_portfolio[symbol] - current_portfolio[symbol].qty
                transaction_size = to_buy * prices[symbol]
                adj_vol += transaction_size
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
                num_adj += 1
                to_sell = current_portfolio[symbol].qty - new_portfolio[symbol]
                transaction_size = to_sell * prices[symbol]
                adj_vol += transaction_size
                fee = simulate_fee(transaction_size)
                total_fees += fee
                cash += transaction_size - fee
                profit = (prices[symbol] - current_portfolio[symbol].price) * to_sell
                taxpool.add_sell_tax(profit)
                current_portfolio[symbol] = Position(new_portfolio[symbol], current_portfolio[symbol].price)

    cash -= taxpool.process_rebalancing()
    return cash, total_fees, num_buys, num_sells, num_adj, buy_vol, sell_vol, adj_vol
