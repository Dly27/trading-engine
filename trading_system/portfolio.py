from typing import Literal, Optional
from trading_system.trade import PositionRequest
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


class Portfolio:

    def __init__(self, portfolio_id):
        self.portfolio_id = portfolio_id
        self.cash = 0
        self.commission_rate = 0.001
        self.positions = {}  # ticker : Position
        self.position_trade_history = []
        self.max_position_size = 0.9
        self.trade_requests = deque([])  # Stores positions needed to be fulfilled by trading system
        self.logger = logging.getLogger(__name__)

    @property
    def total_market_value(self):
        total = 0
        for position in self.positions.values():
            total += position.current_price * position.quantity

        return total

    @property
    def total_portfolio_value(self):
        return self.cash + self.total_market_value

    @property
    def buying_power(self):
        return max(0, self.cash)

    def can_afford_position(self, quantity: float, price: float):
        """
        Check if there is enough cash available in portfolio.
        Makes sure portfolio value is no zero.
        """
        if quantity < 0 or price < 0:
            return False

        position_value = quantity * price
        commission = position_value * self.commission_rate
        total_cost = position_value + commission

        # Check cash availability
        if total_cost > self.buying_power:
            return False

        if self.total_portfolio_value == 0:
            return False

        # Check position size limits
        position_pct = position_value / self.total_portfolio_value
        if position_pct > self.max_position_size:
            return False

        return True

    def open_position(self, position_trade: PositionRequest):
        """
        Check if portfolio has enough cash to open position.
        Updates portfolio cash.
        Updates position if there already exists one else a new one is added.
        Position is deleted if new position cancels out and existing position.
        """
        delete_position = False  # For when a short and long position cancel out
        position_type = "long" if position_trade.side == "bid" else "short"

        if not self.can_afford_position(quantity=position_trade.quantity,
                                        price=position_trade.price,
                                        ):
            self.logger.error(f"INVALID POSITION REQUEST FOR {position_trade.trade_id}")
            return False

        position_value = position_trade.quantity * position_trade.price

        # Create or update position
        try:
            if position_trade.ticker in self.positions:
                existing = self.positions[position_trade.ticker]

                # Average out positions if position types are the same
                if existing.position_type == position_type:
                    total_quantity = existing.quantity + position_trade.quantity
                    weighted_price = (
                            (existing.entry_price * existing.quantity + position_trade.price * position_trade.quantity)
                            / total_quantity
                    )
                    existing.quantity = total_quantity
                    existing.entry_price = weighted_price
                else:
                    # Net out or reverse
                    total_quantity = existing.quantity - position_trade.quantity
                    if total_quantity > 0:
                        existing.quantity = total_quantity
                    elif total_quantity < 0:
                        existing.quantity = abs(total_quantity)
                        existing.position_type = position_type  # Change position type
                        existing.entry_price = position_trade.price  # New entry price for reversed position
                    else:
                        delete_position = True
            else:
                # Create new position
                new_position = Position(
                    ticker=position_trade.ticker,
                    position_type=position_type,
                    entry_price=position_trade.price,
                    quantity=position_trade.quantity,
                    take_profit=0
                )
                self.positions[position_trade.ticker] = new_position
        except Exception as e:
            self.logger.error(f"FAILED TO UPDATE POSTIONS: {e}")
            return

        # Update cash
        if position_type == "long":
            self.cash -= (position_value + position_trade.commission)
        else:  # short position
            self.cash += (position_value - position_trade.commission)

        if delete_position:
            del self.positions[position_trade.ticker]

        self.logger.info(f"POSITION REQUEST {position_trade.trade_id} COMPLETED")
        return True

    def close_position(self, ticker: str, quantity: Optional[float] = None):
        """
        Gets a position if it exists.
        Checks if the close quantity is less than position quantity.
        Updates portfolio cash and position quantity
        """
        if ticker not in self.positions:
            return False

        position = self.positions[ticker]
        close_quantity = quantity or position.quantity

        # Check if quantity is valid
        if close_quantity > position.quantity:
            return False

        proceeds = close_quantity * position.current_price # ADD LATER: GET CURRENT PRICE OF STOCK
        commission = proceeds * self.commission_rate       # USING MARKET DATA

        # Update position
        try:
            if close_quantity == position.quantity:
                del self.positions[ticker]
            else:
                position.quantity -= close_quantity
        except Exception as e:
            self.logger.error(f"FAILED TO UPDATE POSITION {ticker}: {e}")
            return False

        # Update cash
        if position.position_type == "long":
            self.cash += (proceeds - commission)
        else:
            self.cash -= (proceeds + commission)

        self.logger.info(f"POSITION {ticker} UPDATED SUCCESSFULLY")
        return True

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
