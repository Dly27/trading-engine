from collections import OrderedDict
from typing import Literal


class Node:
    def __init__(self, price, parent=None, left=None, right=None):
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
        current = self.root

        while current is not None:
            if current.price == price:
                return current

            if price < current.price:
                current = current.left
            else:
                current = current.right

        return None

    def get_best_bid(self):
        if self.type != "bids":
            raise ValueError("INVALID: THIS IS FOR BIDS")

        if self.root is None:
            return None

        current = self.root

        while current.right is not None:
            current = current.right

        first_order_id = next(iter(current.values))
        return current.values[first_order_id]

    def get_best_ask(self):
        if self.type != "asks":
            raise ValueError("INVALID: THIS IS FOR ASKS")

        if self.root is None:
            return None

        current = self.root

        while current.left is not None:
            current = current.left

        first_order_id = next(iter(current.values))
        return current.values[first_order_id]


class Order:
    def __init__(self, order_id: str, order_type: Literal["ask", "bid"], order_price: int):
        self.order_id = order_id
        self.order_price = order_price

        if order_type != "ask" and order_type != "bid":
            raise ValueError("INVALID ORDER TYPE")
        else:
            self.order_type = order_type


class OrderBook:
    def __init__(self):
        self.asks = RedBlackTree(type="asks")
        self.bids = RedBlackTree(type="bids")
        self.order_id_map = {}

    def add_order(self, order):
        if order.order_type == "ask":
            price_node = self.asks.add_price(order.order_price)  # Create new price level
            price_node.values[order.order_id] = order
            self.order_id_map[order.order_id] = price_node

        elif order.order_type == "bid":
            price_node = self.bids.add_price(order.order_price)  # Create new price level
            price_node.values[order.order_id] = order
            self.order_id_map[order.order_id] = price_node

    def cancel_order(self, order_id):
        price_node = self.order_id_map.get(order_id)

        if price_node is None:
            raise  ValueError(f"ORDER {order_id} NOT FOUND")

        if order_id not in price_node.values:
            raise ValueError(f"ORDER {order_id} NOT FOUND")
        else:
            del price_node.values[order_id]
            del self.order_id_map[order_id]

    def get_best_bid(self):
        return self.bids.get_best_bid()

    def get_best_ask(self):
        return self.asks.get_best_ask()

    def get_spread(self):
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()

        if best_bid is None or best_ask is None:
            return None

        return best_ask.order_price - best_bid.order_price


if __name__ == "__main__":
    book = OrderBook()

    # Add bids and asks
    counter = 0
    for price in [10, 10, 20, 30, 40, 40]:
        order = Order(order_id=str(counter), order_type="bid", order_price=price)
        book.add_order(order=order)
        counter += 1

    for price in [50, 51, 52, 60, 70, 80]:
        order = Order(order_id=str(counter), order_type="ask", order_price=price)
        book.add_order(order=order)
        counter += 1

    print(f"Spread: {book.get_spread()}")
    print(f"Best bid: {book.get_best_bid().order_price}")
    print(f"Best ask: {book.get_best_ask().order_price}")
