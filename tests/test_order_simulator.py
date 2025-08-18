import asyncio
import trading_system.trading_system as ts
import pytest
import psutil
import os

async def main():
    trading_system = ts.TradingSystem()
    simulator = trading_system.create_order_book_simulator(ticker="AAPL")
    simulator.start()

if __name__ == "__main__":
    asyncio.run(main())







