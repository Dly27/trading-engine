import time
import threading
from trading_system import TradingSystem
from trading_system.order_book import Order, OrderBook

class Benchmark:
    def __init__(self):
        self.ts = TradingSystem()
        self.order_book = OrderBook(ticker="BENCHMARK")

    def benchmark_processing(self, total_orders = 2000000):
        """
        Return the throughput and latency
        """

        ticker = self.order_book.ticker
        start_time = time.time()

        for i in range(total_orders):
            order = Order(
                order_id=f"benchmark_{i}",
                portfolio_id="benchmark",
                side="bid" if i % 2 == 0 else "ask",
                order_kind="limit",
                order_price=100 + (i % 10),
                quantity=100,
                ticker=ticker
            )
            self.order_book.add_order(order)

        end_time = time.time()

        mean_latency = (end_time - start_time) / total_orders
        throughput = total_orders / (end_time - start_time)

        return {
            "mean_latency": mean_latency,
            "throughput": throughput,
            "total_time": end_time - start_time,
            "total_orders": total_orders
        }

    def benchmark_matching(self, total_orders=2000000):

        ticker =self.order_book.ticker
        start_time = time.time()

        for i in range(total_orders):
            order = Order(
                order_id=f"benchmark_{i}",
                portfolio_id="benchmark",
                side="bid" if i % 2 == 0 else "ask",
                order_kind="limit",
                order_price=100 + (i % 10),
                quantity=100,
                ticker=ticker
            )
            self.ts.trade_processor.match_order(order, order_book=self.order_book)

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
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX",
            "JPM", "JNJ", "WMT", "PG", "UNH", "HD", "MA", "BAC", "PLTR", "DIS",
            "PYPL", "PEP", "INTC", "CSCO", "VZ", "T", "CVX", "XOM", "KO", "MCD",
            "IBM", "ADBE", "CRM", "ORCL", "AMD", "UBER", "LYFT", "RR",
            "ROKU", "SNAP", "PINS", "SPOT",
            "QCOM", "AVGO", "TXN", "AMAT", "MU", "LRCX", "KLAC", "MCHP", "ADI", "MRVL",
            "COST", "AMGN", "GILD", "BIIB", "REGN", "VRTX", "ILMN", "INCY", "ALXN", "CELG",
            "GS", "C", "AXP", "BLK", "SPGI", "ICE", "CME", "NDAQ", "MCO", "MSCI",
            "LMT", "RTX", "NOC", "GD", "BA", "HON", "MMM", "CAT", "DE", "EMR",
            "NKE", "SBUX", "LULU", "TJX", "LOW", "TGT", "EBAY", "ETSY", "W", "CHWY",
            "F", "GM", "TSLA", "NIO", "RIVN", "LCID", "XPEV", "LI", "RIDE", "NKLA"
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



if __name__ == "__main__":
    benchmark = Benchmark()
    benchmark.test_concurrent_simulators()

