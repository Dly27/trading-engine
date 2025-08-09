from typing import Literal, Optional
from trade import PositionTrade
from datetime import datetime

class Position:
    def __init__(self,
                 ticker: str,
                 position_type: Literal["short", "long"],
                 entry_price: float,
                 current_price: float,
                 quantity: int,
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
        self.positions = {} # ticker : Position # ticker : Position
        self.trade_history = []
        self.max_position_size = 0.9

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

    def can_afford_position(self, ticker: str, quantity: int, price: float) -> bool:
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

    def open_position(self,
                      ticker: str,
                      position_type: Literal["short", "long"],
                      current_price: float,
                      quantity: int,
                      take_profit: float
                      ):

        delete_position = False  # For when a short and long position cancel out

        if not self.can_afford_position(ticker=ticker,
                                        quantity=quantity,
                                        price=current_price):

            raise InvalidPosition("INVALID POSITION")

        position_value = quantity * current_price
        commission = position_value * self.commission_rate

        # Update cash
        if position_type == "long":
            self.cash -= (position_value + commission)
        else:  # short position
            self.cash += (position_value - commission)

        # Create or update position
        if ticker in self.positions:

            existing = self.positions[ticker]
            # Average out positions if position types are the same
            if existing.position_type == position_type:

                total_quantity = existing.quantity + quantity
                weighted_price = (
                    (existing.entry_price * existing.quantity + current_price * quantity)
                    / total_quantity
                )
                existing.quantity = total_quantity
                existing.entry_price = weighted_price

            else:
                # Net out or reverse
                total_quantity = existing.quantity - quantity

                if total_quantity > 0:
                    existing.quantity = total_quantity
                elif total_quantity < 0:
                    existing.quantity = abs(total_quantity)
                    existing.position_type = position_type  # Change position to short, quantity being less
                    existing.entry_price = current_price    # then 0 means new position has to be a short
                else:
                    delete_position = True
        else:
            # Add new position
            self.positions[ticker] = Position(
                ticker=ticker,
                position_type=position_type,
                entry_price=current_price,
                quantity=quantity,
                current_price=current_price,
                take_profit=take_profit
            )

        self.create_trade(ticker=ticker,
                          position_type=position_type,
                          close_open="open",
                          quantity=quantity,
                          price=current_price,
                          commission=commission,
                          )

        if delete_position:
            del self.positions[ticker]


    def close_position(self, ticker: str, quantity: Optional[int] = None):
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

        self.create_trade(ticker=ticker,
                          position_type=position.position_type,
                          close_open="close",
                          quantity=close_quantity,
                          price=position.current_price,
                          commission=commission,
                          )

        # Update position
        if close_quantity == position.quantity:
            del self.positions[ticker]
        else:
            position.quantity -= close_quantity

        return True

    def create_trade(self,
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

        trade = PositionTrade(
            trade_id=f"T{len(self.trade_history) + 1}",
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
            close_open=close_open,
            commission=commission
        )
        self.trade_history.append(trade)

    def update(self):
        pass


class InvalidPosition(Exception):
    pass