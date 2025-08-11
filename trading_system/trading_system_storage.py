import pathlib
from pathlib import Path
import pickle
from trading_system.matching_engine import MatchingEngine
from trading_system.order_book import OrderBook, Order
from trading_system.portfolio import Portfolio


class TradingSystem:
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.order_books = {}  # ticker: OrderBook
        self.portfolios = {}  # id : Portfolio
        self.portfolio_count = 0
        self.matching_engine = MatchingEngine()

    def __del__(self):
        """
        Save portfolios and order books when TradingSystem is deleted
        :return:
        """
        self.save_all()

    def load_order_book(self, ticker: str):
        """
        Load an order book object from a pickle file.
        :param ticker:
        :return:
        """
        path = self.base_dir / "order_books" / f"{ticker}.pkl"

        # Create a new order book if it does not exist
        if not pathlib.Path.exists(path):
            order_book = OrderBook(ticker=ticker)

            with open(path, "wb") as f:
                pickle.dump(order_book, f)
        # Convert pickle file into order_book object if it exists
        with open(path, "rb") as f:
            order_book = pickle.load(f)

        # Store order book in a map
        self.order_books[order_book.ticker] = order_book

    def save_order_book(self, ticker: str):
        """
        Save an order book object into a pickle file.
        :param ticker:
        :return:
        """
        path = self.base_dir / "order_books" / f"{ticker}.pkl"
        order_book = self.order_books[ticker]

        with open(path, "wb") as f:
            pickle.dump(order_book, f)

    def save_all(self):
        """
        Saves all portfolios and order books in the trading system.
        """
        for ticker in self.order_books.keys():
            self.save_order_book(ticker=ticker)

        for portfolio_id, portfolio in self.portfolios.items():
            self.save_portfolio(portfolio)

    def remove_order_book(self, ticker):
        """
        Removes an order book from the trading system memory.
        :param ticker:
        :return:
        """
        self.save_order_book(ticker=ticker)
        order_book = self.order_books[ticker]

        # Remove order_book from memory
        del self.order_books[ticker]

    def load_portfolio(self, portfolio_id):
        """
        Loads a pickle file into a portfolio object
        """
        # Check if portfolio in portfolio store
        if portfolio_id in self.portfolios:
            return self.portfolios[portfolio_id]

        path = self.base_dir / "portfolios" / f"{portfolio_id}.pkl"

        # Create a new portfolio if it does not exist
        if not pathlib.Path.exists(path):
            portfolio = Portfolio(portfolio_id)

            with open(path, "wb") as f:
                pickle.dump(portfolio, f)
        else:
            # Convert pickle file into portfolio object if it exists
            with open(path, "rb") as f:
                portfolio = pickle.load(f)

        self.portfolios[portfolio_id] = portfolio
        return portfolio

    def save_portfolio(self, portfolio):
        """
        Saves a portfolio object into a pickle file
        """
        path = self.base_dir / "portfolios" / f"{portfolio.portfolio_id}.pkl"

        with open(path, "wb") as f:
            pickle.dump(portfolio, f)

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
