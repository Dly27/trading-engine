from typing import Literal, Optional
from trade import PositionRequest
from datetime import datetime
from collections import deque


class Position:
    def __init__(self,
                 ticker: str,
                 position_type: Literal["short", "long"],
                 entry_price: float,
                 current_price: float,
                 quantity: float,
                 take_profit: float):
        self.ticker = ticker
        self.position_type = position_type
        self.entry_price = entry_price
        self.quantity = quantity
        self.current_price = current_price
        self.take_profit = take_profit


class Portfolio:

    def __init__(self, portfolio_id):
        self.portfolio_id = portfolio_id
        self.cash = 0
        self.commission_rate = 0.001
        self.positions = {}  # ticker : Position # ticker : Position
        self.position_trade_history = []
        self.max_position_size = 0.9
        self.trade_requests = deque([])  # Stores positions needed to be fulfilled by trading system

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

    def can_afford_position(self, quantity: float, price: float) -> bool:
        """Check if portfolio can afford a new position"""
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
        """Open a position using a PositionTrade object"""
        delete_position = False  # For when a short and long position cancel out

        position_type = "long" if position_trade.side == "bid" else "short"

        if not self.can_afford_position(quantity=position_trade.quantity,
                                        price=position_trade.price):
            raise InvalidPosition("INVALID POSITION")

        position_value = position_trade.quantity * position_trade.price

        # Update cash
        if position_type == "long":
            self.cash -= (position_value + position_trade.commission)
        else:  # short position
            self.cash += (position_value - position_trade.commission)

        # Create or update position
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
                current_price=position_trade.price,
                quantity=position_trade.quantity,
                take_profit=0
            )
            self.positions[position_trade.ticker] = new_position

        if delete_position:
            del self.positions[position_trade.ticker]

    def close_position(self, ticker: str, quantity: Optional[float] = None):
        if ticker not in self.positions:
            return False

        position = self.positions[ticker]
        close_quantity = quantity or position.quantity

        # Check if quantity is valid
        if close_quantity > position.quantity:
            return False

        proceeds = close_quantity * position.current_price
        commission = proceeds * self.commission_rate

        # Update cash
        if position.position_type == "long":
            self.cash += (proceeds - commission)
        else:
            self.cash -= (proceeds + commission)

        # Update position
        if close_quantity == position.quantity:
            del self.positions[ticker]
        else:
            position.quantity -= close_quantity

        return True

    def create_position_request(self,
                                ticker: str,
                                position_type: Literal["long", "short"],
                                close_open: Literal["open", "close"],
                                quantity: float,
                                price: float,
                                commission: float):

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

        position_trade = self.create_position_request(self,
                                                      ticker=ticker,
                                                      position_type=position_type,
                                                      close_open=close_open,
                                                      quantity=quantity,
                                                      price=price,
                                                      commission=commission)

        self.trade_requests.append(position_trade)


class InvalidPosition(Exception):
    pass
