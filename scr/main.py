from trading_system.trading_system_storage import TradingSystem

if __name__ == "__main__":
    trade_system = TradingSystem()
    trade_system.load_order_book(ticker="TEST")
    portfolio = trade_system.load_portfolio(portfolio_id="test")
    TEST = trade_system.order_books["TEST"]

    print(f"Best bid:{TEST.get_best_bid().order_price}")
    print(f"Best ask:{TEST.get_best_ask().order_price}")
    print(len(TEST.order_id_map))
    print(portfolio.cash)

    portfolio.request_trade(ticker="TEST",
                            position_type="long",
                            close_open="open",
                            quantity=1,
                            price=100.05,
                            commission=portfolio.commission_rate * (1 * 100.05))

    trade_system.process_trade_request(portfolio=portfolio)

    print(len(TEST.order_id_map))
    print(portfolio.cash)