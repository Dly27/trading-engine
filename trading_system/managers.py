import logging
from trading_system.redis import RedisRepository
from trading_system.order_book import OrderBook
from trading_system.portfolio import Portfolio
from trading_system.market_data_fetcher import MarketDataFetcher


class OrderBookManager:
    def __init__(self, redis_repository: RedisRepository):
        self.repository = redis_repository
        self.order_books = {}
        self.logger = logging.getLogger(__name__)

    def load_order_book(self, ticker: str):
        """
        Loads order book from redis
        """
        if ticker in self.order_books:
            return self.order_books[ticker]

        # Load order book from Redis
        order_book = self.repository.load(key=f"orderbook:{ticker}")

        # Create new order book if not loaded from redis
        if order_book is None:
            order_book = OrderBook(ticker=ticker)
            self.logger.info(f"NEW {ticker} ORDER BOOK CREATED")
        else:
            self.logger.info(f"LOADED {ticker} ORDER BOOK FROM REDIS")

        # Add to order book storage
        self.order_books[ticker] = order_book

        return order_book

    def save_order_book(self, ticker: str):
        """
        Save an order book to redis
        """
        if ticker not in self.order_books:
            self.logger.warning(f"{ticker} ORDER BOOK DOES NOT EXIST")
            return

        order_book = self.order_books[ticker]

        # Save order book to redis
        self.repository.save(key=f"orderbook:{ticker}", data=order_book)

    def remove_order_book(self, ticker: str):
        """
        Remove an order book from memory
        """
        self.save_order_book(ticker=ticker)
        del self.order_books[ticker]


class PortfolioManager:
    def __init__(self, redis_repository: RedisRepository):
        self.repository = redis_repository
        self.logger = logging.getLogger(__name__)
        self.portfolios = {}

    def load_portfolio(self, portfolio_id: str):
        """
        Load a portfolio to redis
        """
        if portfolio_id in self.portfolios:
            return self.portfolios[portfolio_id]

        # Load portfolio from redis
        portfolio = self.repository.load(key=f"portfolio:{portfolio_id}")

        # Create new portfolio if not in redis
        if portfolio is None:
            portfolio = Portfolio(portfolio_id=portfolio_id)
            self.logger.info(f"CREATED PORTFOLIO {portfolio_id}")
        else:
            self.logger.info(f"LOADED PORTFOLIO {portfolio_id} FROM REDIS")

        self.portfolios[portfolio_id] = portfolio
        return portfolio

    def save_portfolio(self, portfolio_id: str):
        """
        Save a portfolio to redis
        """
        # Check if portfolio in redis
        if portfolio_id not in self.portfolios:
            self.logger.warning(f"PORTFOLIO {portfolio_id} DOES NOT EXIST")
            return

        portfolio = self.portfolios[portfolio_id]

        # Save portfolio to redis
        self.repository.save(key=f"portfolio:{portfolio_id}", data=portfolio)


class MarketDataManager:
    def __init__(self):
        self.data_fetchers = {}
        self.logger = logging.getLogger(__name__)

    def add_data_fetcher(self, ticker: str):
        """
        Add a new  market data fetcher
        """
        if ticker not in self.data_fetchers:
            self.data_fetchers[ticker] = MarketDataFetcher(ticker)
            self.logger.info(f"ADDED MARKET DATA FETCHER FOR {ticker}")

    def update_all_data(self):
        """
        Update all data in market data fetchers
        """
        for ticker, fetcher in self.data_fetchers.items():
            try:
                fetcher.update()
            except Exception as e:
                self.logger.error(f"MARKET DATA UPDATE FAILED FOR {ticker}: {e}")

    def get_current_data(self, ticker: str):
        """
        Get the current price and estimated spread of a ticker
        """
        if ticker not in self.data_fetchers:
            self.add_data_fetcher(ticker)
        return self.data_fetchers[ticker].get_data()
