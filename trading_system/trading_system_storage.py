import logging
import pickle
import redis
from trading_system.matching_engine import MatchingEngine
from trading_system.order_book import OrderBook, Order
from trading_system.portfolio import Portfolio

logger = logging.getLogger(__name__)


class TradingSystem:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=False)

        try:
            self.redis.ping()
            logger.info("CONNECTED TO REDIS")
        except:
            raise Exception("REDIS CONNECTION FAILED")

        self.order_books = {}  # ticker: OrderBook
        self.portfolios = {}  # id : Portfolio
        self.matching_engine = MatchingEngine()

    def __del__(self):
        """
        Save portfolios and order books when TradingSystem is deleted
        :return:
        """
        self.save_all()

    def load_order_book(self, ticker: str):
        """
        Load an order book from redis
        """
        if ticker in self.order_books:
            return self.order_books[ticker]

        data = self.redis.get(f"orderbook:{ticker}")

        if data:
            # Load order book from redis
            order_book = pickle.loads(data)
            logger.info(f"LOADED {ticker} ORDER BOOK FROM REDIS")
        else:
            # Create new order book if it does not exist in redis
            order_book = OrderBook(ticker=ticker)
            logger.info(f"NEW {ticker} ORDER BOOK CREATED")

        self.order_books[ticker] = order_book
        return order_book

    def save_order_book(self, ticker: str):
        """
        Serialise and order book then save to redis
        :param ticker:
        :return:
        """
        if ticker not in self.order_books:
            return

        order_book = self.order_books[ticker]
        data = pickle.dumps(order_book)

        try:
            # Save order book to redis
            self.redis.set(f"orderbook:{ticker}", data)
            logger.info(f"SAVED {ticker} ORDER BOOK TO REDIS")
        except Exception as e:
            logger.error(f"FAILED TO SAVE {ticker} ORDER BOOK TO REDIS: {e}")

    def save_all(self):
        """
        Saves all portfolios and order books in the trading system.
        """
        for ticker in self.order_books.keys():
            self.save_order_book(ticker=ticker)

        for portfolio_id, portfolio in self.portfolios.items():
            self.save_portfolio(portfolio)

        logger.info("SAVED ALL TO REDIS")

    def remove_order_book(self, ticker):
        """
        Removes an order book from the trading system memory.
        """
        self.save_order_book(ticker=ticker)

        # Remove order_book from memory
        del self.order_books[ticker]

    def load_portfolio(self, portfolio_id):
        """
        Loads portfolio object from redis
        """
        # Check if portfolio in portfolio store
        if portfolio_id in self.portfolios:
            return self.portfolios[portfolio_id]

        data = self.redis.get(f"portfolio:{portfolio_id}")

        if data:
            # Load portfolio from redis
            try:
                portfolio = pickle.loads(data)
                logger.info(f"LOADED PORTFOLIO {portfolio_id} FROM REDIS")
            except Exception as e:
                logger.error(f"FAILED TO LOAD PORTFOLIO {portfolio_id} FROM REDIS: {e}")
                raise Exception("PORTFOLIO FAILED TO LOAD")
        else:
            # Create new portfolio
            portfolio = Portfolio(portfolio_id=portfolio_id)
            logger.info(f"CREATED PORTFOLIO {portfolio_id}")

        self.portfolios[portfolio_id] = portfolio
        return portfolio

    def save_portfolio(self, portfolio):
        """
        Serialises portfolio then saves to redis
        """
        data = pickle.dumps(portfolio)
        try:
            self.redis.set(f"portfolio:{portfolio.portfolio_id}", data)
            logger.info(f"SAVED PORTFOLIO {portfolio.portfolio_id} TO REDIS")
        except Exception as e:
            logger.error(f"FAILED TO SAVE PORTFOLIO {portfolio.portfolio_id} TO REDIS: {e}")

    def process_trade_request(self, portfolio):
        """
        Goes through all trade requests in the portfolio.
        An order is made based on the position of the trade request.
        Matching engine matches with another order in the order book.
        If a match is found, a position is closed or open in the portfolio.
        """
        for i in range(len(portfolio.trade_requests)):
            position_request = portfolio.trade_requests.popleft()
            ticker = position_request.ticker
            order_book = self.order_books[ticker]

            if order_book is None:
                raise OrderBookError("ORDER BOOK NOT FOUND. PLEASE LOAD ORDER BOOK FIRST")

            side = position_request.side

            order = Order(order_id=f"{portfolio.portfolio_id}_{len(order_book.order_id_map)}",
                          order_kind="limit",
                          order_price=position_request.price,
                          side=side,
                          portfolio_id=portfolio.portfolio_id,
                          quantity=position_request.quantity,
                          ticker=position_request.ticker
                          )

            original_quantity = order.quantity
            self.matching_engine.process_order(order=order, order_book=order_book)
            quantity_traded = original_quantity - order.quantity

            # Check if trade occurred in order book, then update portfolio
            if quantity_traded > 0:
                if position_request.close_open == "open":
                    portfolio.open_position(position_trade=position_request)
                else:
                    portfolio.close_position(ticker=ticker, quantity=quantity_traded)
            else:
                raise OrderBookError(f"{portfolio.portfolio_id}_{position_request.trade_id} DID NOT EXECUTE. \n"
                                     f"MATCH NOT FOUND.")


class OrderBookError(Exception):
    pass
