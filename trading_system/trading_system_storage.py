import pathlib
from pathlib import Path
import pickle
from .matching_engine import MatchingEngine
from .order_book import OrderBook


class TradingSystem:
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.order_books = {} # ticker : OrderBook

    def __del__(self):
        self.save_all()

    def load_order_book(self, ticker: str):
        path = self.base_dir / "order_books" / f"{ticker}.pkl"

        # Create a new order book if it does not exist
        if not pathlib.Path.exists(path):
            order_book = OrderBook(ticker=ticker)

            with open(path, "wb") as f:
                pickle.dump(order_book, f)
        # Convert pickle file into order_book object if it exists
        else:
            with open(path, "rb") as f:
                order_book = pickle.load(f)

        # Store order book in a map
        self.order_books[order_book.ticker] = order_book

    def save_order_book(self, ticker: str):
        path = self.base_dir / "order_books" / f"{ticker}.pkl"
        order_book = self.order_books[ticker]

        with open(path, "wb") as f:
            pickle.dump(order_book, f)

    def save_all(self):
        for ticker in self.order_books.keys():
            self.save_order_book(ticker=ticker)

    def remove_order_book(self, ticker):
        self.save_order_book(ticker=ticker)
        order_book = self.order_books[ticker]

        # Remove order_book from memory
        del order_book[ticker]


    def load_portfolio(self, portfolio_id):
        pass

    def execute_trade(self, portfolio, trade):
        pass



