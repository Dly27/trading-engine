import pytest
from trading_system.order_book import OrderBook, Order


def test_add_order():
    order_book = OrderBook(ticker="TEST_ORDERBOOK")
    order = Order(portfolio_id="test_orderbook",
                  side="bid",
                  order_kind="limit",
                  order_id="0",
                  order_price=100,
                  quantity=2,
                  ticker="TEST_ORDERBOOK")

    print("=" * 10)
    print("TEST ADD ORDER")
    old_order_book_size = len(order_book.order_id_map)
    order_book.add_order(order=order)
    new_order_book_size = len(order_book.order_id_map)
    assert old_order_book_size != new_order_book_size


def test_cancel_order():
    order_book = OrderBook(ticker="TEST_ORDERBOOK")
    order = Order(portfolio_id="test_orderbook",
                  side="bid",
                  order_kind="limit",
                  order_id="0",
                  order_price=100,
                  quantity=2,
                  ticker="TEST_ORDERBOOK")

    print("=" * 10)
    print("TEST CANCEL ORDER")

    # Add order
    order_book.add_order(order=order)
    old_order_book_size = len(order_book.order_id_map)

    # Cancel order
    order_book.cancel_order(order_id="0")
    new_order_book_size = len(order_book.order_id_map)

    assert new_order_book_size == old_order_book_size - 1
    assert len(order_book.order_id_map) == 0


def test_best_bid_ask_spread():
    order_book = OrderBook(ticker="TEST_ORDERBOOK")

    order1 = Order(portfolio_id="test_orderbook",
                   side="bid",
                   order_kind="limit",
                   order_id="1",
                   order_price=99,
                   quantity=2,
                   ticker="TEST_ORDERBOOK")

    order2 = Order(portfolio_id="test_orderbook",
                   side="ask",
                   order_kind="limit",
                   order_id="2",
                   order_price=101,
                   quantity=2,
                   ticker="TEST_ORDERBOOK")

    print("=" * 10)
    print("TEST BEST ASK, BID, SPREAD")

    order_book.add_order(order=order1)
    order_book.add_order(order=order2)

    best_bid = order_book.get_best_bid().order_price
    best_ask = order_book.get_best_ask().order_price
    spread = order_book.get_spread()

    assert best_bid == 99
    assert best_ask == 101
    assert spread == 2


def test_multiple_orders_same_side():
    order_book = OrderBook(ticker="TEST_ORDERBOOK")

    bid1 = Order(portfolio_id="test_orderbook",
                 side="bid",
                 order_kind="limit",
                 order_id="bid1",
                 order_price=100,
                 quantity=2,
                 ticker="TEST_ORDERBOOK")

    bid2 = Order(portfolio_id="test_orderbook",
                 side="bid",
                 order_kind="limit",
                 order_id="bid2",
                 order_price=101,
                 quantity=3,
                 ticker="TEST_ORDERBOOK")

    order_book.add_order(order=bid1)
    order_book.add_order(order=bid2)

    best_bid = order_book.get_best_bid().order_price
    assert best_bid == 101


def test_empty_order_book():
    order_book = OrderBook(ticker="TEST_ORDERBOOK")

    # Should return None for empty book
    best_bid = order_book.get_best_bid()
    best_ask = order_book.get_best_ask()  # order_price attribute cant be returned if the price_node is none
    spread = order_book.get_spread()

    assert best_bid is None
    assert best_ask is None
    assert spread is None


if __name__ == "__main__":
    test_add_order()
    test_cancel_order()
    test_best_bid_ask_spread()
    test_multiple_orders_same_side()
    test_empty_order_book()