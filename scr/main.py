from trading_system.trading_system_storage import TradingSystem
from trading_system.order_book import Order
import random
import time
import psutil
import os

if __name__ == "__main__":
    trade_system = TradingSystem()
    trade_system.load_order_book(ticker="TEST")
    portfolio = trade_system.load_portfolio(portfolio_id="test")
    TEST = trade_system.order_books["TEST"]
    portfolio.cash = 100000


