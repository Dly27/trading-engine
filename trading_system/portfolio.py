from typing import Literal
from trading_system.order_book import OrderBook, Order

class Position:
    def __init__(self,
                 ticker: str,
                 position_type: Literal["short", "long"],
                 entry_price: int,
                 current_price: int,
                 position_size: int,
                 order_kind: Literal["limit", "market"],
                 take_profit: int):

        self.ticker = ticker
        self.position_type = position_type
        self.entry_price = entry_price
        self.current_price = current_price
        self.position_size = position_size
        self.take_profit = take_profit
        self.order_kind = order_kind



class Portfolio:
    def __init__(self, trader_id):
        self.trader_id = trader_id
        self.open_positions = {}
        self.closed_trades = []

        self.metrics = {"balance": 0,
                        "unrealised_pl": 0,
                        "realised_pl": 0,
                        "sharpe_ratio": 0,
                        }


