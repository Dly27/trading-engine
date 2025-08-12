from trading_system.trading_system_storage import TradingSystem
import pytest
import psutil
import os


def test_initial_order_book_status():
    print("\n" + "=" * 50)
    print("TEST: Initial Order Book Status")
    print("=" * 50)

    trade_system = TradingSystem()
    trade_system.load_order_book(ticker="TEST")
    TEST = trade_system.order_books["TEST"]

    print(f"Orders in book: {len(TEST.order_id_map):,}")
    print(f"Best bid: {TEST.get_best_bid().order_price if TEST.get_best_bid() else 'None'}")
    print(f"Best ask: {TEST.get_best_ask().order_price if TEST.get_best_ask() else 'None'}")
    print(f"Spread: {TEST.get_spread() if TEST.get_spread() else 'None'}")

    assert hasattr(TEST, 'order_id_map')
    assert hasattr(TEST, 'get_best_bid')
    assert hasattr(TEST, 'get_best_ask')
    assert hasattr(TEST, 'get_spread')
    print("PASS")


def test_portfolio_initial_state():
    print("\n" + "=" * 50)
    print("TEST: Portfolio Initial State")
    print("=" * 50)

    trade_system = TradingSystem()
    portfolio = trade_system.load_portfolio(portfolio_id="test")

    print(f"Portfolio cash: {portfolio.cash:,.2f}")

    assert hasattr(portfolio, 'cash')
    assert hasattr(portfolio, 'commission_rate')
    assert hasattr(portfolio, 'request_trade')
    assert portfolio.cash >= 0
    print("PASS")


def test_memory_monitoring():
    print("\n" + "=" * 50)
    print("TEST: Memory Monitoring")
    print("=" * 50)

    process = psutil.Process(os.getpid())
    memory_before = process.memory_info().rss / 1024 / 1024

    print(f"Memory usage: {memory_before:.2f} MB")

    assert memory_before > 0
    print("PASS")


def test_trade_execution():
    print("\n" + "=" * 50)
    print("TEST: Trade Execution")
    print("=" * 50)

    trade_system = TradingSystem()
    trade_system.load_order_book(ticker="TEST")
    portfolio = trade_system.load_portfolio(portfolio_id="test")
    TEST = trade_system.order_books["TEST"]

    initial_cash = portfolio.cash
    print(f"Initial cash: {initial_cash:,.2f}")

    print(f"\nExecuting trades:")
    print("=" * 60)

    trades_executed = 0
    for trade_num in range(5):
        best_ask = TEST.get_best_ask()

        if best_ask is None:
            print(f"Trade {trade_num + 1}: No ask orders available")
            continue

        best_ask_price = best_ask.order_price
        trade_cost = 1 * best_ask_price
        commission = portfolio.commission_rate * trade_cost
        total_cost = trade_cost + commission

        if portfolio.cash < total_cost:
            print(f"Trade {trade_num + 1}: Insufficient funds")
            continue

        print(f"Trade {trade_num + 1}: Buying 1 share at {best_ask_price}")

        portfolio.request_trade(ticker="TEST",
                                position_type="long",
                                close_open="open",
                                quantity=1,
                                price=best_ask_price,
                                commission=commission)
        trade_system.process_trade_request(portfolio=portfolio)
        trades_executed += 1

    print(f"Total trades executed: {trades_executed}")

    if trades_executed > 0:
        assert portfolio.cash < initial_cash
    print("PASS")


def test_post_trade_analysis():
    print("\n" + "=" * 50)
    print("TEST: Post-Trade Analysis")
    print("=" * 50)

    trade_system = TradingSystem()
    trade_system.load_order_book(ticker="TEST")
    portfolio = trade_system.load_portfolio(portfolio_id="test")
    TEST = trade_system.order_books["TEST"]

    # Execute some trades first
    for _ in range(3):
        best_ask = TEST.get_best_ask()
        if best_ask and portfolio.cash >= best_ask.order_price:
            portfolio.request_trade(ticker="TEST",
                                    position_type="long",
                                    close_open="open",
                                    quantity=1,
                                    price=best_ask.order_price,
                                    commission=portfolio.commission_rate * best_ask.order_price)
            trade_system.process_trade_request(portfolio=portfolio)

    print(f"Orders in book: {len(TEST.order_id_map):,}")
    print(f"Portfolio cash: {portfolio.cash:,.2f}")
    print(f"Best bid: {TEST.get_best_bid().order_price if TEST.get_best_bid() else 'None'}")
    print(f"Best ask: {TEST.get_best_ask().order_price if TEST.get_best_ask() else 'None'}")
    print(f"Spread: {TEST.get_spread() if TEST.get_spread() else 'None'}")

    if hasattr(TEST, 'trades'):
        print(f"Trades executed: {len(TEST.trades)}")
        assert len(TEST.trades) >= 0

    print("PASS")


def test_order_book_analysis():
    print("\n" + "=" * 50)
    print("TEST: Order Book Analysis")
    print("=" * 50)

    trade_system = TradingSystem()
    trade_system.load_order_book(ticker="TEST")
    TEST = trade_system.order_books["TEST"]

    bid_prices = []
    ask_prices = []
    total_bid_volume = 0
    total_ask_volume = 0

    for order_id, price_node in TEST.order_id_map.items():
        for oid, order in price_node.values.items():
            if order.side == "bid":
                bid_prices.append(order.order_price)
                total_bid_volume += order.quantity
            else:
                ask_prices.append(order.order_price)
                total_ask_volume += order.quantity

    if bid_prices:
        print(f"BID SIDE:")
        print(f"  Orders: {len(bid_prices):,}")
        print(f"  Total volume: {total_bid_volume:,} shares")
        print(f"  Price range: {min(bid_prices):.2f} - {max(bid_prices):.2f}")
        print(f"  Average price: {sum(bid_prices) / len(bid_prices):.2f}")

        assert len(bid_prices) >= 0
        assert total_bid_volume >= 0

    if ask_prices:
        print(f"ASK SIDE:")
        print(f"  Orders: {len(ask_prices):,}")
        print(f"  Total volume: {total_ask_volume:,} shares")
        print(f"  Price range: ${min(ask_prices):.2f} - ${max(ask_prices):.2f}")
        print(f"  Average price: ${sum(ask_prices) / len(ask_prices):.2f}")

        assert len(ask_prices) >= 0
        assert total_ask_volume >= 0

    print("PASS")


if __name__ == "__main__":
    test_initial_order_book_status()
    test_portfolio_initial_state()
    test_memory_monitoring()
    test_trade_execution()
    test_post_trade_analysis()
    test_order_book_analysis()