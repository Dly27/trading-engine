from trading_system.trading_system import *

if __name__ == "__main__":
    ts = TradingSystem()
    simulator = ts.create_order_book_simulator(ticker="MSFT")
    simulator.run()