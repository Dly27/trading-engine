import logging
from trading_system.order_book_simulator import OrderBookSimulator
from trading_system.redis import RedisRepository
from trading_system.managers import OrderBookManager, PortfolioManager
from trading_system.services import TradeService


class TradingSystem:
    """
    Main system that coordinates managers and simulators
    """

    def __init__(self):
        self.repository = RedisRepository()
        self.order_book_manager = OrderBookManager(self.repository)
        self.portfolio_manager = PortfolioManager(self.repository)

        self.trade_processor = TradeService(
            self.order_book_manager,
            self.portfolio_manager,
        )

        self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.save_all()

    def create_order_book_simulator(self, ticker: str):
        """
        Creates and returns an order book simulator of a given ticker.
        """
        return OrderBookSimulator(order_book=self.order_book_manager.load_order_book(ticker=ticker))

    def save_all(self):
        """
        Save all order books and portfolios from memory into redis
        """
        for ticker in self.order_book_manager.order_books:
            self.order_book_manager.save_order_book(ticker=ticker)

        for portfolio_id in self.portfolio_manager.portfolios:
            self.portfolio_manager.save_portfolio(portfolio_id=portfolio_id)


class OrderBookError(Exception):
    pass
