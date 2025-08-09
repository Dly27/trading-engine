import pathlib
from pathlib import Path
import pickle
from .matching_engine import MatchingEngine
from .order_book import OrderBook, Order
from .portfolio import Portfolio


class TradingSystem:
    def __init__(self, base_dir: Path = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.order_books = {} # ticker: OrderBook
        self.portfolio_count = 0
        self.matching_engine = MatchingEngine()

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
        path = self.base_dir / "portfolios" / f"{portfolio_id}.pkl"

        # Create a new portfolio if it does not exist
        if not pathlib.Path.exists(path):
            portfolio = Portfolio(self.portfolio_count)

            with open(path, "wb") as f:
                pickle.dump(portfolio, f)

            self.portfolio_count += 1

        # Convert pickle file into portfolio object if it exists
        with open(path, "rb") as f:
            portfolio = pickle.load(f)

        return portfolio


    def request_trade(self, portfolio, trade):
        ticker = trade.ticker
        order_book = self.order_books[ticker]

        if order_book is None:
            raise OrderBookError("ORDER BOOK NOT FOUND. PLEASE LOAD ORDER BOOK FIRST")

        order = Order(order_id=str(len(order_book.order_map_id)),
                      order_kind="market",
                      order_price=trade.price,
                      side=trade.side,
                      portfolio_id=portfolio.portfolio_id,
                      quantity=trade.quantity,
                      ticker= ticker
        )

        original_quantity = order.quantity
        self.matching_engine.process_order(order=order, order_book=order_book)
        quantity_traded = original_quantity - order.quantity

        # Check if trade occurred, then update portfolio
        if quantity_traded > 0:
            portfolio.update()

class OrderBookError(Exception):
    pass
