import time
from typing import Literal
import datetime


class OrderBookTrade:
    def __init__(self, trade_id: str,
                 buyer_order_id: str,
                 seller_order_id: str,
                 price: float,
                 quantity: int,
                 instrument: Literal["option", "future", "stock", "swap"]):
        self.trade_id = trade_id
        self.buyer_order_id = buyer_order_id
        self.seller_order_id = seller_order_id
        self.quantity = quantity
        self.price = price
        self.instrument = instrument
        self.timestamp = time.time()


class PositionRequest:
    def __init__(self,
                 trade_id: str,
                 ticker: str,
                 side: Literal["bid", "ask"],
                 quantity: float,
                 price: float,
                 timestamp: datetime,
                 commission: float,
                 close_open: Literal["close", "open"]
                 ):
        self.trade_id = trade_id
        self.ticker = ticker
        self.side = side
        self.quantity = quantity
        self.price = price
        self.timestamp = timestamp
        self.commission = commission
        self.close_open = close_open
