import logging
from typing import Optional
from trading_system.portfolio import Portfolio, PositionRequest, Position
from trading_system.matching_engine import MatchingEngine
from trading_system.managers import OrderBookManager, PortfolioManager
from trading_system.order_book import Order


class PortfolioService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def can_afford_position(self, portfolio: Portfolio, quantity: float, price: float):
        """
        Check if there is enough cash available in portfolio.
        Makes sure portfolio value is no zero.
        """
        if quantity < 0 or price < 0:
            return False

        position_value = quantity * price
        commission = position_value * portfolio.commission_rate
        total_cost = position_value + commission

        # Check cash availability
        if total_cost > portfolio.buying_power:
            return False

        # IMPLEMENT PROPERTIES LATER!

        # if portfolio.total_portfolio_value == 0:
        #     return False
        #
        # # Check position size limits
        # position_pct = position_value / portfolio.total_portfolio_value
        # if position_pct > portfolio.max_position_size:
        #     return False

        return True

    def open_position(self, portfolio: Portfolio, position_trade: PositionRequest):
        """
        Check if portfolio has enough cash to open position.
        Updates portfolio cash.
        Updates position if there already exists one else a new one is added.
        Position is deleted if new position cancels out and existing position.
        """
        delete_position = False  # For when a short and long position cancel out
        position_type = "long" if position_trade.side == "bid" else "short"

        if not self.can_afford_position(portfolio,
                                       quantity=position_trade.quantity,
                                       price=position_trade.price):
            self.logger.error(f"INVALID POSITION REQUEST FOR {position_trade.trade_id}")
            return False

        position_value = position_trade.quantity * position_trade.price

        # Create or update position
        try:
            if position_trade.ticker in portfolio.positions:
                existing = portfolio.positions[position_trade.ticker]

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
                portfolio.positions[position_trade.ticker] = new_position
        except Exception as e:
            self.logger.error(f"FAILED TO UPDATE POSITIONS: {e}")
            return False

        # Update cash
        if position_type == "long":
            portfolio.cash -= (position_value + position_trade.commission)
        else:  # short position
            portfolio.cash += (position_value - position_trade.commission)

        if delete_position:
            del portfolio.positions[position_trade.ticker]

        self.logger.info(f"POSITION REQUEST {position_trade.trade_id} COMPLETED")
        return True

    def close_position(self, portfolio: Portfolio,
                       ticker: str,
                       current_price: float,
                       quantity: Optional[float] = None,
                       ):
        """
        Gets a position if it exists.
        Checks if the close quantity is less than position quantity.
        Updates portfolio cash and position quantity
        """
        if ticker not in portfolio.positions:
            return False

        position = portfolio.positions[ticker]
        close_quantity = quantity or position.quantity

        # Check if quantity is valid
        if close_quantity > position.quantity:
            return False

        proceeds = close_quantity * current_price
        commission = proceeds * portfolio.commission_rate

        # Update position
        try:
            if close_quantity == position.quantity:
                del portfolio.positions[ticker]
            else:
                position.quantity -= close_quantity
        except Exception as e:
            self.logger.error(f"FAILED TO UPDATE POSITION {ticker}: {e}")
            return False

        # Update cash
        if position.position_type == "long":
            portfolio.cash += (proceeds - commission)
        else:
            portfolio.cash -= (proceeds + commission)

        self.logger.info(f"POSITION {ticker} UPDATED SUCCESSFULLY")
        return True


class TradeService:
    def __init__(self,
                 order_book_manager: OrderBookManager,
                 portfolio_manager: PortfolioManager,
                 ):

        self.book_manager = order_book_manager
        self.portfolio_manager = portfolio_manager
        self.portfolio_service = PortfolioService()
        self.matching_engine = MatchingEngine()
        self.logger = logging.getLogger(__name__)

    def get_current_market_price(self, ticker: str):
        """
        Returns the current price of a stock.
        To be implemented properly
        """
        return 100

    def match_order(self, order, order_book):
        """
        Matches an order.
        Returns the quantity traded
        """
        original_quantity = order.quantity
        self.matching_engine.process_order(order=order, order_book=order_book)
        quantity_traded = original_quantity - order.quantity

        return quantity_traded

    def update_portfolio(self, ticker: str,  portfolio: Portfolio, position_request: PositionRequest):
        """
        Updates a portfolio based on a position request.
        """
        if position_request.close_open == "open":
            self.portfolio_service.open_position(portfolio=portfolio, position_trade=position_request)
        else:
            current_price = self.get_current_market_price(ticker=ticker)
            self.portfolio_service.close_position(ticker=ticker, portfolio=portfolio, current_price=current_price)
        self.logger.info(f"TRADE {portfolio.portfolio_id}_{position_request.trade_id} EXECUTED")

    def process_trade_request(self, portfolio_id: str):
        """
        Goes through all trade requests in the portfolio.
        An order is made based on the position of the trade request.
        Matching engine matches with another order in the order book.
        If a match is found, a position is closed or open in the portfolio.
        """
        try:
            # Load portfolio
            portfolio = self.portfolio_manager.load_portfolio(portfolio_id=portfolio_id)

            # Process trade requests in portfolio
            for i in range(len(portfolio.trade_requests)):
                position_request = portfolio.trade_requests.popleft()
                ticker = position_request.ticker
                order_book = self.book_manager.load_order_book(ticker=ticker)

                # Get the side of the trade request
                side = position_request.side

                # Create new order
                order = Order(order_id=f"{portfolio.portfolio_id}_{len(order_book.order_id_map)}",
                              order_kind="limit",
                              order_price=position_request.price,
                              side=side,
                              portfolio_id=portfolio.portfolio_id,
                              quantity=position_request.quantity,
                              ticker=position_request.ticker
                              )

                # Match order
                quantity_traded = self.match_order(order=order, order_book=order_book)

                # Check if trade occurred in order book, then update portfolio
                if quantity_traded > 0:
                    self.update_portfolio(ticker=ticker, portfolio=portfolio, position_request=position_request)
                else:
                    self.logger.error(f"FAILED TO EXECUTE TRADE {portfolio.portfolio_id}_{position_request.trade_id}.\n"
                                      f"MATCH NOT FOUND")
        except Exception as e:
            logging.error(f"FAILED TO PROCESS TRADE REQUESTS FOR PORTFOLIO {portfolio_id}: {e}")
class OrderService:
    pass