import time
from typing import Literal
class Trade:
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
