import logging
import pickle
import redis
import numpy as np
from trading_system.matching_engine import MatchingEngine
from trading_system.order_book import OrderBook, Order
from trading_system.portfolio import Portfolio
from trading_system.market_data_fetcher import MarketDataFetcher


class RedisRepository:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.logger = logging.getLogger(__name__)

        try:
            self.redis.ping()
            self.logger.info("CONNECTED TO REDIS")
        except:
            raise Exception("REDIS CONNECTION FAILED")

    def save(self, key: str, data: any) -> None:
        """
        Serialised object then saves data to redis
        """
        try:
            serialized = pickle.dumps(data)
            self.redis.set(key, serialized)
            self.logger.info(f"SAVED {key} TO REDIS")
        except Exception as e:
            self.logger.error(f"FAILED TO SAVE {key} TO REDIS: {e}")
            raise

    def load(self, key: str) -> any:
        """
        Load data from redis then serialise into an object
        """
        try:
            data = self.redis.get(key)
            if data:
                result = pickle.loads(data)
                self.logger.info(f"LOADED {key} FROM REDIS")
                return result
            return None
        except Exception as e:
            self.logger.warning(f"CORRUPTED DATA FOR {key}, RETURNING NONE: {e}")
            return None


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

class OrderSimulator:
    def __init__(self, order_book_manager: OrderBookManager):
        self.book_manager = order_book_manager
        self.data_fetchers = {}

    def create_market_data_fetchers(self, ticker: str):
        if ticker not in self.data_fetchers:
            self.data_fetchers[ticker] = MarketDataFetcher(ticker=ticker)
        return self.data_fetchers[ticker]

    def simulate_orders(self, ticker: str, batch_size: int, quantity_range: int):
        """
        Uses estimated spreads and current prices from current market data to create synthetic orders.
        batch_size: The amount of orders to add for bid and ask
        quantity_range: The range of quantities per order
        """
        order_book = self.book_manager.load_order_book(ticker=ticker)
        fetcher = self.create_market_data_fetchers(ticker=ticker)

        base_price, spread = fetcher.get_data()

        for i in range(batch_size):
            bid_order = Order(ticker=ticker,
                              side="bid",
                              portfolio_id="synthetic",
                              order_id=f"synthetic_bid_{ticker}_{len(order_book.order_id_map)}_{i}",
                              order_kind="limit",
                              quantity=np.random.randint(1, quantity_range),
                              order_price=base_price - np.random.uniform(0, spread / 2)
                              )

            order_book.add_order(order=bid_order)

        for i in range(batch_size):
            ask_order = Order(ticker=ticker,
                              side="ask",
                              portfolio_id="synthetic",
                              order_id=f"synthetic_ask_{ticker}_{len(order_book.order_id_map)}_{i}",
                              order_kind="limit",
                              quantity=np.random.randint(1, quantity_range),
                              order_price=base_price + np.random.uniform(0, spread / 2)
                              )

            order_book.add_order(order=ask_order)

class TradeProcessor:
    def __init__(self,
                 order_book_manager: OrderBookManager,
                 portfolio_manager: PortfolioManager,
                 matching_engine: MatchingEngine):

        self.book_manager = order_book_manager
        self.portfolio_manager = portfolio_manager
        self.matching_engine = matching_engine
        self.logger = logging.getLogger(__name__)

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
                original_quantity = order.quantity
                self.matching_engine.process_order(order=order, order_book=order_book)
                quantity_traded = original_quantity - order.quantity

                # Check if trade occurred in order book, then update portfolio
                if quantity_traded > 0:
                    if position_request.close_open == "open":
                        portfolio.open_position(position_trade=position_request)
                    else:
                        portfolio.close_position(ticker=ticker, quantity=quantity_traded)

                    self.logger.info(f"TRADE {portfolio.portfolio_id}_{position_request.trade_id} EXECUTED")
                else:
                    self.logger.error(f"FAILED TO EXECUTE TRADE {portfolio.portfolio_id}_{position_request.trade_id}.\n"
                                      f"MATCH NOT FOUND")
        except Exception as e:
            logging.error(f"FAILED TO PROCESS TRADE REQUESTS FOR PORTFOLIO {portfolio_id}: {e}")



class TradingSystem:
    def __init__(self):
        self.repository = RedisRepository()
        self.order_book_manager = OrderBookManager(self.repository)
        self.portfolio_manager = PortfolioManager(self.repository)
        self.matching_engine = MatchingEngine()

        # The new focused services
        self.order_simulator = OrderSimulator(self.order_book_manager)
        self.trade_processor = TradeProcessor(
            self.order_book_manager,
            self.portfolio_manager,
            self.matching_engine
        )

    def submit_order(self, ticker: str, order_data: dict):
        """
        Submit order to an order book.
        Orders are not associated with any portfolio
        """
        order_book = self.order_book_manager.load_order_book(ticker)

        order = Order(**order_data)
        self.matching_engine.process_order(order, order_book)

        return {"status": "processed"}

    def simulate_orders(self, ticker: str, batch_size: int, quantity_range: int):
        """
        Add simulated orders to an order book using OrderSimulator.
        """
        return self.order_simulator.simulate_orders(ticker, batch_size, quantity_range)

    def process_trade_request(self, portfolio_id: str):
        """
        Process trade requests in a given portfolio.
        """
        return self.trade_processor.process_trade_request(portfolio_id)


class OrderBookError(Exception):
    pass
