import time
import threading
import yfinance as yf
import numpy as np
from trading_system import TradingSystem
from trading_system.order_book import Order, OrderBook

class Benchmark:
    def __init__(self):
        self.ts = TradingSystem()

    def benchmark_processing(self, total_orders=200000):
        """
        Return the throughput and latency
        """
        order_book = OrderBook("BENCHMARK")
        ticker = order_book.ticker
        start_time = time.time()

        for i in range(total_orders):
            order = Order(
                order_id=f"benchmark_{i}",
                portfolio_id="benchmark",
                side="bid" if i % 2 == 0 else "ask",
                order_kind="limit",
                order_price=100 + np.random.uniform(-0.25, 0.25),
                quantity=100,
                ticker=ticker
            )
            order_book.add_order(order)

        end_time = time.time()

        mean_latency = (end_time - start_time) / total_orders
        throughput = total_orders / (end_time - start_time)

        return {
            "mean_latency": mean_latency,
            "throughput": throughput,
            "total_time": end_time - start_time,
            "total_orders": total_orders
        }

    def test_concurrent_simulators(self):
        simulators = []
        threads = []
        tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"
        ]

        success_count = 0

        for ticker in tickers:
            sim = self.ts.create_order_book_simulator(ticker)
            thread = threading.Thread(target=sim.run, daemon=True)
            thread.start()

            if thread.is_alive():
                simulators.append(sim)
                threads.append(thread)
                success_count += 1
                print(f"Simulator {success_count} ({ticker}) working")
            else:
                break

        print(f"RESULT: {success_count} simulators successfully running")
        time.sleep(300)

    def benchmark_matching(self, total_orders=50000):
        order_book = OrderBook(ticker="BENCHMARK")
        base_price = 100

        for i in range(1000):
            # Add some initial orders
            bid = Order(
                order_id=f"initial_bid_{i}",
                portfolio_id="market_maker",
                side="bid",
                order_kind="limit",
                order_price=base_price - 0.5 - np.random.uniform(0, 1.0),
                quantity=np.random.randint(50, 200),
                ticker="BENCHMARK"
            )
            order_book.add_order(bid)

            ask = Order(
                order_id=f"initial_ask_{i}",
                portfolio_id="market_maker",
                side="ask",
                order_kind="limit",
                order_price=base_price + 0.5 + np.random.uniform(0, 1.0),
                quantity=np.random.randint(50, 200),
                ticker="BENCHMARK"
            )
            order_book.add_order(ask)

        start_time = time.time()
        matched_orders = 0

        for i in range(total_orders):

            # Split orders into passive and aggressive orders
            if np.random.random() < 0.3:
                if i % 2 == 0:
                    price = base_price + np.random.uniform(0.5, 1.5)
                    side = "bid"
                else:
                    price = base_price - np.random.uniform(0.5, 1.5)
                    side = "ask"
            else:
                if i % 2 == 0:
                    price = base_price - np.random.uniform(0.5, 2.0)
                    side = "bid"
                else:
                    price = base_price + np.random.uniform(0.5, 2.0)
                    side = "ask"

            order = Order(
                order_id=f"test_{i}",
                portfolio_id="trader",
                side=side,
                order_kind="limit",
                order_price=price,
                quantity=100,
                ticker="BENCHMARK"
            )

            initial_quantity = order.quantity
            self.ts.trade_processor.match_order(order, order_book=order_book)

            if order.quantity < initial_quantity:
                matched_orders += 1

        end_time = time.time()

        return {
            "mean_latency": (end_time - start_time) / total_orders,
            "throughput": total_orders / (end_time - start_time),
            "total_time": end_time - start_time,
            "total_orders": total_orders,
            "matched_orders": matched_orders,
            "match_rate": matched_orders / total_orders
        }

def check_if_blocked():
    ticker = yf.Ticker("AAPL")
    try:
        price1 = ticker.fast_info["last_price"]
        print(f"First request: {price1}")

        time.sleep(5)

        price2 = ticker.fast_info["last_price"]
        print(f"Second request: {price2}")

        if price1 == price2:
            print("RATE LIMITED")
        else:
            print("GETTING DATA")

    except Exception as e:
        print(f"BLOCKED OR ERROR: {e}")

if __name__ == "__main__":
    # benchmark = Benchmark()
    # print(f"PROCESSING: {benchmark.benchmark_processing()}")
    # print(f"MATCHING: {benchmark.benchmark_matching()}")
    # check_if_blocked()