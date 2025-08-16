from trading_system.matching_engine import MatchingEngine
from trading_system.order_book import OrderBook, Order
import pytest


def test_single_buy_sell_match():
    print("\n" + "=" * 50)
    print("TEST: Single Buy/Sell Match")
    print("=" * 50)

    engine = MatchingEngine()
    order_book = OrderBook(ticker="TEST")

    buy = Order(ticker="TEST",
                order_id="buy",
                order_price=100,
                quantity=1,
                order_kind="limit",
                side="bid",
                portfolio_id="TEST")

    sell = Order(ticker="TEST",
                 order_id="sell",
                 order_price=100,
                 quantity=1,
                 order_kind="limit",
                 side="ask",
                 portfolio_id="TEST")

    print(f"Adding sell order")
    order_book.add_order(sell)
    print(f"Order book size after adding sell: {len(order_book.order_id_map)}")
    assert len(order_book.order_id_map) == 1

    print(f"Processing buy order")
    engine.process_order(buy, order_book)
    print(f"Order book size after matching: {len(order_book.order_id_map)}")
    print(f"Number of trades executed: {len(order_book.trades)}")

    assert len(order_book.order_id_map) == 0
    print("PASS")


def test_partial_fill():
    print("\n" + "=" * 50)
    print("TEST: Partial Fill")
    print("=" * 50)
    engine = MatchingEngine()
    order_book = OrderBook(ticker="TEST")

    sell = Order(ticker="TEST",
                 order_id="sell_partial",
                 order_price=100,
                 quantity=5,
                 order_kind="limit",
                 side="ask",
                 portfolio_id="SELLER")

    buy = Order(ticker="TEST",
                order_id="buy_partial",
                order_price=100,
                quantity=10,
                order_kind="limit",
                side="bid",
                portfolio_id="BUYER")

    print(f"Adding sell order")
    order_book.add_order(sell)
    print(f"Order book size after adding sell: {len(order_book.order_id_map)}")
    assert len(order_book.order_id_map) == 1

    print(f"Processing buy order")
    engine.process_order(buy, order_book)
    print(f"Order book size after matching: {len(order_book.order_id_map)}")
    print(f"Number of trades executed: {len(order_book.trades)}")
    print(f"Buy order remaining quantity: {buy.quantity}")
    print(f"Sell order remaining quantity: {sell.quantity}")

    assert buy.quantity == 5
    assert sell.quantity == 0
    assert len(order_book.trades) == 1
    print("PASS")


if __name__ == "__main__":

    test_single_buy_sell_match()
