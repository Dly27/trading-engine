from trading_system.trading_system import OrderSimulator
from trading_system.trading_system import OrderBookManager
from trading_system.trading_system import RedisRepository
import pytest
import psutil
import os

def test_simulate_orders():
    print("=" * 50)
    print("TEST: Orderbook simulation")
    print("=" * 50)

    repository = RedisRepository()
    book_manager = OrderBookManager(redis_repository=repository)
    simulator = OrderSimulator(order_book_manager=book_manager)

    order_book = book_manager.load_order_book(ticker="AAPL")

    old_orderbook_size = len(order_book.order_id_map)
    simulator.simulate_orders(ticker="AAPL", batch_size=10, quantity_range=100)

    # Check order counts
    new_orderbook_size = len(order_book.order_id_map)
    orders_added = new_orderbook_size - old_orderbook_size
    expected_orders = 2 * 10

    print(f"OLD ORDER BOOK SIZE: {old_orderbook_size}")
    print(f"NEW ORDER BOOK SIZE: {new_orderbook_size}")

    assert old_orderbook_size < new_orderbook_size
    assert orders_added == expected_orders

    # Check best ask and best bids

    best_ask = order_book.get_best_ask()
    best_bid = order_book.get_best_bid()
    spread = order_book.get_spread()

    if best_bid:
        print(f"Best bid: {best_bid.order_price}")
        assert best_bid.order_price != 0

    if best_ask:
        print(f"Best ask: {best_ask.order_price}")
        assert best_ask.order_price != 0

    if spread:
        print(f"Spread: {spread}")
        assert spread != 0





