from datetime import datetime
from typing import Literal
from trading_system.red_black_tree import RedBlackTree, EmptyBookError
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ORDER_BOOK_DIR = BASE_DIR / "order_books"


class Order:
    def __init__(self, order_id: str,
                 portfolio_id: str,
                 side: Literal["ask", "bid"],
                 order_kind: Literal["market", "limit"],
                 order_price: float,
                 quantity: int,
                 ticker: str):

        self.order_id = order_id
        self.order_price = order_price
        self.quantity = quantity
        self.timestamp = datetime.now()
        self.ticker = ticker
        self.portfolio_id = portfolio_id

        if side != "ask" and side != "bid":
            raise ValueError("INVALID ORDER TYPE")
        else:
            self.side = side

        if order_kind != "market" and order_kind != "limit":
            raise ValueError("INVALID ORDER KIND")
        else:
            self.order_kind = order_kind


class OrderBook:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.asks = RedBlackTree(type="asks")
        self.bids = RedBlackTree(type="bids")
        self.order_id_map = {}  # order_id: price_node
        self.trades = []

    def add_order(self, order):
        """
        Adds order to either bids or asks
        Adds order to order_id_map
        :param order
        :return:
        """
        if order.side == "ask":
            price_node = self.asks.add_price(order.order_price)  # Add new price node
            price_node.values[order.order_id] = order
            self.order_id_map[order.order_id] = price_node

        elif order.side == "bid":
            price_node = self.bids.add_price(order.order_price)  # Add new price node
            price_node.values[order.order_id] = order
            self.order_id_map[order.order_id] = price_node

    def cancel_order(self, order_id):
        """
        Deletes order from bids or asks
        Deletes order from order_id_map
        """
        price_node = self.order_id_map.get(order_id)

        if price_node is None:
            raise ValueError(f"ORDER {order_id} NOT FOUND")

        if order_id not in price_node.values:
            raise ValueError(f"ORDER {order_id} NOT FOUND")
        else:
            del price_node.values[order_id]
            del self.order_id_map[order_id]

    def get_best_bid(self):
        """
        Get the best bid
        """
        try:
            return self.bids.get_best_bid()
        except EmptyBookError:
            return None


    def get_best_ask(self):
        """
        Get the best ask
        """
        try:
            return self.asks.get_best_ask()
        except EmptyBookError:
            return None

    def get_spread(self):
        """
        Get the spread
        """
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid is None or best_ask is None:
            return None

        return best_ask.order_price - best_bid.order_price
