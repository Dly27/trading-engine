import yfinance as yf
import numpy as np
from collections import deque
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[{asctime}] {levelname:<8} {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class MarketDataFetcher:
    def __init__(self, ticker: str):
        self.symbol = ticker
        self.ticker = yf.Ticker(ticker)
        self.current_price = None
        self.previous_price = None
        self.price_history = deque(maxlen=10)
        self.base_spread = self.estimate_base_spread()
        self.current_spread = self.base_spread
        self.fetch_initial_data()
        self.DEFAULT_PRICE = 100

    def estimate_base_spread(self):
        """
        Calculate a base spread based on market data.
        Return different spread depending on stock price.
        """
        try:
            data = self.ticker.history(period="1d", interval="1m")

            if not data.empty:
                mean_price = data["Close"].mean()

                if mean_price < 10:
                    return 0.01
                elif mean_price < 100:
                    return 0.03
                else:
                    return 0.05
            else:
                return 0.01

        except Exception as e:
            logging.error(f"COULD NOT CALCULATE BASE SPREAD. DEFAULT ESTIMATE USED: {e}")
            return 0.01

    def fetch_initial_data(self):
        """
        Get the most recent price and add it to history.
        If data is not fetched set the initial price to 100.
        """
        try:
            self.current_price = float(self.ticker.fast_info["last_price"])
            self.price_history.append(self.current_price)
        except Exception as e:
            logging.error(f"FAILED TO FETCH INITIAL DATA: {e}")
            self.price_history.append(self.DEFAULT_PRICE)

    def update(self):
        try:
            self.update_price()
        except Exception as e:
            logging.error(f"COULD NOT UPDATE {self.symbol} DATA: {e}")


    def update_price(self):
        """
        Updates to the most recent price and changes the price history
        """
        try:
            # Update the prices
            new_price = float(self.ticker.fast_info["last_price"])
            self.previous_price = self.current_price
            self.current_price = new_price

            # Add new price to price history
            self.price_history.append(new_price)

            # Update spread
            self.update_spread()

            logging.info(f"UPDATED CURRENT PRICE TO {new_price}")
            return True
        except Exception as e:
            logging.error(f"PRICE UPDATE FAILED: {e}")
            return False

    def update_spread(self):
        """
        Update the spread by calculating volatility of recent prices
        """
        if len(self.price_history) < 5:
            self.current_spread = self.base_spread
            return

        recent_prices = self.price_history
        price_changes = []

        for i in range(1, len(recent_prices)):
            change_pct = abs((recent_prices[i] - recent_prices[i - 1]) / recent_prices[i - 1])
            price_changes.append(change_pct)

        if price_changes:
            volatility = np.std(price_changes)

            # Change spread based on volatility
            if volatility > 0.005:
                self.current_spread = self.base_spread * 2.0
            elif volatility > 0.002:
                self.current_spread = self.base_spread * 1.5
            else:
                self.current_spread = self.base_spread

    def get_data(self):
        """
        Returns current stock price and current estimated spread
        """
        if self.current_price is None:
            logging.warning(f"NO CURRENT PRICE AVAILABLE FOR {self.ticker}")
            return None

        return {
            "price": self.current_price,
            "spread": self.current_spread,
        }
