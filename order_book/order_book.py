import time
from collections import OrderedDict
from typing import Literal


class Node:
    def __init__(self, price, parent=None, left=None, right=None):
        """
        :param price: The price of the node
        values: OrderedDict storing Order objects in the form "order_id" : Order
        """
        self.parent = parent
        self.left = left
        self.right = right
        self.price = price
        self.values = OrderedDict()
        self.colour = None


class RedBlackTree:
    def __init__(self, type):
        self.nodes = []
        self.current_colour = "black"
        self.root = None
        self.type = type

    def add_price(self, price):
        """
        Adds a price node to the tree
        Sets the new node as a leaf
        Re-balances tree so node is in correct position
        """
        if self.root is None:
            self.root = Node(price=price)
            self.root.colour = "black"
            return self.root

        current = self.root
        parent = None

        while current is not None:
            parent = current

            if price == current.price:
                return current
            elif price < current.price:
                current = current.left
            else:
                current = current.right

        new_node = Node(price=price, parent=parent)
        new_node.colour = "red"

        if price < parent.price:
            parent.left = new_node
        else:
            parent.right = new_node

        self.rebalance_red_black(new_node)
        return new_node

    def rotate_left(self, node):
        right_child = node.right
        node.right = right_child.left

        if right_child.left is not None:
            right_child.left.parent = node

        right_child.parent = node.parent

        if node.parent is None:
            self.root = right_child
        elif node == node.parent.left:
            node.parent.left = right_child
        else:
            node.parent.right = right_child

        right_child.left = node
        node.parent = right_child

    def rotate_right(self, node):
        left_child = node.left
        node.left = left_child.right

        if left_child.right is not None:
            left_child.right.parent = node

        left_child.parent = node.parent

        if node.parent is None:
            self.root = left_child
        elif node == node.parent.right:
            node.parent.right = left_child
        else:
            node.parent.left = left_child

        left_child.right = node
        node.parent = left_child

    def rebalance_red_black(self, node):
        """
        Re-balances tree
        :param node: Node to move to the correct position
        """
        while node != self.root and node.parent.colour == "red":
            if node.parent == node.parent.parent.left:
                uncle = node.parent.parent.right

                if uncle and uncle.colour == "red":
                    node.parent.colour = "black"
                    uncle.colour = "black"
                    node.parent.parent.colour = "red"
                    node = node.parent.parent
                else:
                    # Node is a right child
                    if node == node.parent.right:
                        node = node.parent
                        self.rotate_left(node)

                    # Node is a left child
                    node.parent.colour = "black"
                    node.parent.parent.colour = "red"
                    self.rotate_right(node.parent.parent)
            else:
                uncle = node.parent.parent.left

                if uncle and uncle.colour == "red":
                    node.parent.colour = "black"
                    uncle.colour = "black"
                    node.parent.parent.colour = "red"
                    node = node.parent.parent
                else:
                    # Node is a left child
                    if node == node.parent.left:
                        node = node.parent
                        self.rotate_right(node)

                    # Node is a right child
                    node.parent.colour = "black"
                    node.parent.parent.colour = "red"
                    self.rotate_left(node.parent.parent)

        self.root.colour = "black"

    def search_price(self, price):
        """
        Search for a price node of a given price
        :param price: Price of price node to find
        :return:
        """
        current_price_node = self.root

        while current_price_node is not None:
            if current_price_node.price == price:
                return current_price_node

            if price < current_price_node.price:
                current_price_node = current_price_node.left
            else:
                current_price_node = current_price_node.right

        return current_price_node

    def get_best_bid(self):
        """
        Return the order with the best bid
        :return: Order
        """
        if self.type != "bids":
            raise ValueError("INVALID: THIS IS FOR BIDS")

        if self.root is None:
            raise EmptyBookError("CURRENTLY NO BIDS IN BOOK")

        current_price_node = self.root

        # Find node furthest to the right
        while current_price_node.right is not None:
            current_price_node = current_price_node.right

        # Traverse backwards
        while current_price_node is not None:
            if len(current_price_node.values) > 0:
                first_order_id = next(iter(current_price_node.values))
                return current_price_node.values[first_order_id]

            if current_price_node.left is not None:
                current_price_node = current_price_node.left
                while current_price_node.right is not None:
                    current_price_node = current_price_node.right
            else:
                parent = current_price_node.parent
                while parent is not None and current_price_node == parent.left:
                    current_price_node = parent
                    parent = parent.parent
                current_price_node = parent

        return None

    def get_best_ask(self):
        """
        Return the order with the best ask
        :return: Order
        """
        if self.type != "asks":
            raise ValueError("INVALID: THIS IS FOR ASKS")

        if self.root is None:
            raise EmptyBookError("CURRENTLY NO ASKS IN BOOK")

        current_price_node = self.root

        # Find node furthest to the left
        while current_price_node.left is not None:
            current_price_node = current_price_node.left

        # Traverse forwards until we find orders
        while current_price_node is not None:
            if len(current_price_node.values) > 0:
                first_order_id = next(iter(current_price_node.values))
                return current_price_node.values[first_order_id]

            if current_price_node.right is not None:
                current_price_node = current_price_node.right
                while current_price_node.left is not None:
                    current_price_node = current_price_node.left
            else:
                parent = current_price_node.parent
                while parent is not None and current_price_node == parent.right:
                    current_price_node = parent
                    parent = parent.parent
                current_price_node = parent

        return None

class EmptyBookError(Exception):
    pass


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
        self.order_id_map = {} # order_id: price_node

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

class MatchingEngine:
    def __init__(self, order_book):
        self.order_book = order_book
        self.trades = []

    def process_order(self, order):
        if order.side == "ask":
            self.process_sell_order(order=order)
        else:
            self.process_buy_order(order=order)

    def process_buy_order(self, order):

        while order.quantity > 0:
            best_ask = self.order_book.get_best_ask()

            if best_ask is None:
                break

            if not self.match_possible(buy_order=order, sell_order=best_ask):
                break

            trade = self.execute_trade(buy_order=order, sell_order=best_ask)

            if trade:
                self.trades.append(trade)

        if order.quantity > 0:
            self.order_book.add_order(order)

    def process_sell_order(self, order):
        while order.quantity > 0:
            best_bid = self.order_book.get_best_bid()

            if best_bid is None:
                break

            if not self.match_possible(buy_order=best_bid, sell_order=order):
                break

            trade = self.execute_trade(buy_order=best_bid, sell_order=order)

            if trade:
                self.trades.append(trade)

        if order.quantity > 0:
            self.order_book.add_order(order)

    def match_possible(self, buy_order=None, sell_order=None):
        if sell_order is None or buy_order is None:
            raise ValueError("BUY OR SELL ORDER NOT SPECIFIED")

        if sell_order.order_kind == "market" or buy_order == "market":
            return True

        return buy_order.order_price >= sell_order.order_price

    def execute_trade(self, buy_order, sell_order):
        trade_quantity = min(buy_order.quantity, sell_order.quantity)

        if trade_quantity <= 0:
            return None

        trade_price = self.get_trade_price(buy_order=buy_order, sell_order=sell_order)

        buy_order.quantity -= trade_quantity
        sell_order.quantity -= trade_quantity

        if buy_order.quantity == 0 and buy_order.order_id in self.order_book.order_id_map:
            self.order_book.cancel_order(order_id=buy_order.order_id)
        if sell_order.quantity == 0 and buy_order.order_id in self.order_book.order_id_map:
            self.order_book.cancel_order(order_id=sell_order.order_id)

        trade = Trade(trade_id=str(len(self.trades)),
                      buyer_order_id=buy_order.order_id,
                      seller_order_id=sell_order.order_id,
                      price=trade_price,
                      quantity=trade_quantity,
                      instrument="stock")

        self.trades.append(trade)

        return trade

    def get_trade_price(self, buy_order, sell_order):
        if buy_order.order_kind == "market":
            return sell_order.order_price
        if sell_order.order_kind == "market":
            return buy_order.order_price

        if buy_order.timestamp > sell_order.timestamp:
            return sell_order.order_price
        else:
            return buy_order.order_price


class Trade:
    def __init__(self, trade_id: str,
                 buyer_order_id: str,
                 seller_order_id: str,
                 price: float,
                 quantity: int,
                 instrument: Literal["option", "future", "stock", "swap"]):

        self.trade_id = trade_id
        self.buyer_order_id = buyer_order_id
        self.seller_order_id = seller_order_id
        self.quantity = quantity
        self.price = price
        self.instrument = instrument
        self.timestamp = time.time()



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

    match.process_order(order=Order(order_id=str(counter), side="ask", order_kind="market", order_price=1000, quantity=1000))

    print(f"Spread: {book.get_spread()}")
    print(f"Best bid: {book.get_best_bid().order_price}")
    print(f"Best ask: {book.get_best_ask().order_price}")
