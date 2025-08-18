from typing import Literal
from datetime import datetime
from collections import deque
import logging


class Position:
    def __init__(self,
                 ticker: str,
                 position_type: Literal["short", "long"],
                 entry_price: float,
                 quantity: float,
                 take_profit: float):
        self.ticker = ticker
        self.position_type = position_type
        self.entry_price = entry_price
        self.quantity = quantity
        self.take_profit = take_profit


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


class Portfolio:

    def __init__(self, portfolio_id):
        self.portfolio_id = portfolio_id
        self.cash = 0
        self.commission_rate = 0.001
        self.positions = {}  # ticker : Position
        self.position_trade_history = []  # Stores past executed trades
        self.max_position_size = 0.9
        self.trade_requests = deque([])  # Stores positions needed to be fulfilled by trading system
        self.logger = logging.getLogger(__name__)

    @property
    def buying_power(self):
        return max(0, self.cash)

    def create_position_request(self,
                                ticker: str,
                                position_type: Literal["long", "short"],
                                close_open: Literal["open", "close"],
                                quantity: float,
                                price: float,
                                commission: float):
        """
        Creates a position request
        """

        if close_open == "open":
            side = "bid" if position_type == "long" else "ask"
        else:
            side = "ask" if position_type == "long" else "bid"

        request = PositionRequest(
            trade_id=f"T{len(self.position_trade_history) + 1}",
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            close_open=close_open,
            commission=commission
        )
        self.position_trade_history.append(request)

        return request

    def request_trade(self,
                      ticker: str,
                      position_type: Literal["long", "short"],
                      close_open: Literal["open", "close"],
                      quantity: float,
                      price: float,
                      commission: float):
        """
        Create a position request then add it to the request queue.
        """
        position_request = self.create_position_request(
            ticker=ticker,
            position_type=position_type,
            close_open=close_open,
            quantity=quantity,
            price=price,
            commission=commission)

        self.trade_requests.append(position_request)


class InvalidPosition(Exception):
    pass
