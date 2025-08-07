import time
from typing import Literal
from red_black_tree import RedBlackTree
from matching_engine import MatchingEngine


class Order:
    def __init__(self, order_id: str,
                 side: Literal["ask", "bid"],
                 order_kind: Literal["market", "limit"],
                 order_price: float,
                 quantity: int):

        self.order_id = order_id
        self.order_price = order_price
        self.quantity = quantity
        self.timestamp = time.time()

        if side != "ask" and side != "bid":
            raise ValueError("INVALID ORDER TYPE")
        else:
            self.side = side

        if order_kind != "market" and order_kind != "limit":
            raise ValueError("INVALID ORDER KIND")
        else:
            self.order_kind = order_kind


class OrderBook:
    def __init__(self):
        self.asks = RedBlackTree(type="asks")
        self.bids = RedBlackTree(type="bids")
        self.order_id_map = {}  # order_id: price_node

    def add_order(self, order):
        """
        Adds order to either bids or asks
        Adds order to order_id_map
        :param order:
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
        return self.bids.get_best_bid()

    def get_best_ask(self):
        """
        Get the worst bid
        :return:
        """
        return self.asks.get_best_ask()

    def get_spread(self):
        """
        Get the spread
        """
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid is None or best_ask is None:
            return None

        return best_ask.order_price - best_bid.order_price


if __name__ == "__main__":
    book = OrderBook()
    match = MatchingEngine(order_book=book)

    # Add bids and asks
    counter = 0
    for price in [10, 10, 20, 30, 40, 40, 50, 100, 30, 20, 10, 500, 240, 210, 32]:
        order = Order(order_id=str(counter), side="bid", order_kind="limit", order_price=price, quantity=100)
        book.add_order(order=order)
        counter += 1

    for price in [50, 51, 52, 60, 70, 80, 130, 403, 5034, 3053, 232, 424, 3434]:
        order = Order(order_id=str(counter), side="ask", order_kind="limit", order_price=price, quantity=100)
        book.add_order(order=order)
        counter += 1

    best_bid = book.get_best_bid()
    book.cancel_order(order_id=best_bid.order_id)

    second_best_bid = book.get_best_bid()
    book.cancel_order(order_id=second_best_bid.order_id)

    match.process_order(
        order=Order(order_id=str(counter), side="ask", order_kind="market", order_price=1000, quantity=1000))

    print(f"Spread: {book.get_spread()}")
    print(f"Best bid: {book.get_best_bid().order_price}")
    print(f"Best ask: {book.get_best_ask().order_price}")

