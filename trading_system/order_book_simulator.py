import asyncio
import logging
import numpy as np
from trading_system.market_data_fetcher import MarketDataFetcher
from trading_system.order_book import Order, OrderBook


class OrderGenerator:
    def __init__(self, order_book: OrderBook):
        self.order_book = order_book
        self.fetcher = MarketDataFetcher(ticker=order_book.ticker)

    def generate_orders(self, ticker: str, batch_size: int, quantity_range: int):
        """
        Uses estimated spreads and current prices from current market data to create synthetic orders.
        batch_size: The amount of orders to add for bid and ask
        quantity_range: The range of quantities per order
        """
        base_price, spread = self.fetcher.get_data()

        for i in range(batch_size):
            bid_order = Order(ticker=ticker,
                              side="bid",
                              portfolio_id="synthetic",
                              order_id=f"synthetic_bid_{ticker}_{len(self.order_book.order_id_map)}_{i}",
                              order_kind="limit",
                              quantity=np.random.randint(1, quantity_range),
                              order_price=base_price - np.random.uniform(0, spread / 2)
                              )

            self.order_book.add_order(order=bid_order)

        for i in range(batch_size):
            ask_order = Order(ticker=ticker,
                              side="ask",
                              portfolio_id="synthetic",
                              order_id=f"synthetic_ask_{ticker}_{len(self.order_book.order_id_map)}_{i}",
                              order_kind="limit",
                              quantity=np.random.randint(1, quantity_range),
                              order_price=base_price + np.random.uniform(0, spread / 2)
                              )

            self.order_book.add_order(order=ask_order)


class OrderBookSimulator:
    def __init__(self, order_book: OrderBook):
        self.order_generator = OrderGenerator(order_book=order_book)
        self.order_book = order_book
        self.ticker = order_book.ticker
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.simulation_task = None
        self.batch_size = 5
        self.quantity_range = 100
        self.intervals = 1

    def run(self):
        """
        Start the simulation.
        Used by user.
        """
        try:
            asyncio.run(self.start_simulation_loop())
        except KeyboardInterrupt:
            self.logger.info("SIMULATION STOPPED BY USER")

    async def start_simulation_loop(self):
        """
        Start the order book simulation loop.
        """
        if self.running:
            self.logger.warning("SIMULATION ALREADY RUNNING.")
            return

        # Create main simulation loop
        self.simulation_task = asyncio.create_task(self.simulation_loop())
        self.running = True
        self.logger.info("SIMULATION STARTED")

        try:
            await self.simulation_task
        except asyncio.CancelledError:
            self.logger.info("SIMULATION CANCELLED")
        except Exception as e:
            self.logger.error(f"SIMULATION ERROR: {e}")
        finally:
            self.running = False

    async def simulation_loop(self):
        """
        Run the main simulation loop.
        """
        while self.running:
            try:
                await self.add_orders()
                self.print_orderbook_info()
                await asyncio.sleep(self.intervals)
            except Exception as e:
                self.logger.error(f"SIMULATION LOOP ERROR: {e}")
                await asyncio.sleep(self.intervals)

    async def add_orders(self, ):
        """
        Add simulated orders to order book
        """
        try:
            # Generate and add orders to order book
            self.order_generator.generate_orders(self.ticker,
                                                 batch_size=self.batch_size,
                                                 quantity_range=self.quantity_range)
            self.logger.info("ORDERS ADDED TO ORDER BOOK")
        except Exception as e:
            self.logger.error(f"FAILED TO ADD ORDERS TO  ORDER BOOK: {e}")

    def print_orderbook_info(self):
        """
        Print out bid, ask, spread of the orderbook.
        """
        try:
            # Print info
            best_bid = self.order_book.get_best_bid()
            best_ask = self.order_book.get_best_ask()
            spread = self.order_book.get_spread()

            print({"ticker": self.ticker,
                   "best_ask": best_ask.order_price,
                   "best_bid": best_bid.order_price,
                   "spread": spread})

        except Exception as e:
            self.logger.error(f"FAILED TO PRINT ORDERBOOK INFO: {e}")

    async def stop(self):
        """
        Stop the simulation.
        """
        if not self.running:
            self.logger.warning("SIMULATION ALREADY STOPPED")
            return

        # Stop the simulation
        if self.simulation_task:
            self.simulation_task.cancel()
            self.running = False
