import numpy as np
import pandas as pd
import yfinance as yf
from main import DataSet, DataLoader, Profiler


class FinancialPreprocessor:
    def __init__(self, symbols, start_date, end_date, target_type='returns'):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.target_type = target_type

    def load_prepare_data(self):
        if len(self.symbols) == 1:
            data_raw = yf.download(self.symbols[0], start=self.start_date, end=self.end_date)
        else:
            data_raw = yf.download(self.symbols, start=self.start_date, end=self.end_date)

        if len(self.symbols) == 1:
            df = self.prepare_single_symbol(data=data_raw, symbol=self.symbols[0])
        else:
            df = self.prepare_multiple_symbols(data=data_raw)

        return df

    def prepare_single_symbol(self, data, symbol):
        df = data.copy()
        features_df = self.create_features(df=df, symbol=symbol)

        if self.target_type == "returns":
            features_df["target"] = df["Close"].pct_change()
        elif self.target_type == 'next_close':
            features_df['target'] = df['Close'].shift(-1)
        elif self.target_type == 'price_direction':
            features_df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        else:
            raise ValueError(f"Unknown target_type: {self.target_type}")

        features_df = features_df.dropna()

        return features_df

    def prepare_multiple_symbols(self, data):
        all_features = []

        for symbol in self.symbols:
            if isinstance(data.columns, pd.MultiIndex):
                symbol_data = data.xs(symbol, level=1, axis=1)
            else:
                symbol_data = data

            symbol_features = self.create_features(symbol_data, symbol)
            symbol_features['symbol'] = symbol
            all_features.append(symbol_features)

        combined_df = pd.concat(all_features, ignore_index=True)

        if self.target_type == 'returns':
            combined_df['target'] = combined_df.groupby('symbol')['Close'].pct_change()
        elif self.target_type == 'next_close':
            combined_df['target'] = combined_df.groupby('symbol')['Close'].shift(-1)
        elif self.target_type == 'price_direction':
            combined_df['target'] = (combined_df.groupby('symbol')['Close'].shift(-1) >
                                     combined_df['Close']).astype(int)

        combined_df = combined_df.dropna()
        return combined_df

    def create_features(self, df, symbol):
        features = pd.DataFrame(index=df.index)

        # Price features
        features[f"open_{symbol}"] = df["Open"]
        features[f"high_{symbol}"] = df["High"]
        features[f"close_{symbol}"] = df["Close"]
        features[f"low_{symbol}"] = df["Low"]
        features[f"volume_{symbol}"] = df["Volume"]

        # Technical indicatiors
        features[f"sma_5_{symbol}"] = df["Close"].rolling(window=5).mean()
        features[f"sma_20_{symbol}"] = df["Close"].rolling(window=20).mean()
        features[f"volatility_20_{symbol}"] = df["Close"].rolling(window=20).std()
        features[f"rsi_{symbol}"] = self.calculate_rsi(prices=df["Close"], window=14)

        # Lag features
        for lag in [1, 7, 14, 30]:
            features[f'close_lag_{lag}_{symbol}'] = df['Close'].shift(lag)
            features[f'volume_lag_{lag}_{symbol}'] = df['Volume'].shift(lag)

        return features

    def calculate_rsi(self, prices, window=14):
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class FinancialDataSet(DataSet):
    def __init__(self, symbols, start_date, end_date, target_type='returns', **kwargs):
        self.start_date = start_date
        self.end_date = end_date
        self.target_type = target_type
        self.symbols = symbols

        preprocessor = FinancialPreprocessor(symbols, start_date, end_date, target_type)
        processed_data = preprocessor.load_prepare_data()

        super().__init__(data=processed_data, target='target')

    def fetch_data(self, symbol, start_date, end_date):
        return yf.download(symbol, start=start_date, end=end_date)

    def get_point_in_time_data(self, as_of_date, lookback=None):
        as_of_date = pd.to_datetime(as_of_date)
        df = self.data.copy()

        mask = df.index <= as_of_date
        pit_data = df[mask]

        if lookback and len(pit_data) > lookback:
            pit_data = pit_data.tail(lookback)

        return pit_data


class FinancialDataLoader(DataLoader):
    def __init__(self, data, lookback_window=10, **kwargs):
        self.lookback_window = lookback_window
        super().__init__(data=data, **kwargs)

    def create_time_series_batches(self):
        pass


if __name__ == "__main__":

    data = FinancialDataSet(symbols=["AAPL"],
                            start_date="2024-01-01",
                            end_date="2025-08-01",
                            target_type="returns")


    print(f"Dataset length: {len(data)}")
    print(f"Feature columns: {data.data.columns.tolist()}")
    print(f"Target stats: min={data.y.min():.4f}, max={data.y.max():.4f}, mean={data.y.mean():.4f}")

    data = data.get_point_in_time_data(as_of_date="2025-03-01", lookback=30)


    loader = FinancialDataLoader(data=data,
                                 batch_size=16,
                                 lookback_window=10,
                                 shuffle=False,
                                 workers=4)

    for i, (x_batch, y_batch) in enumerate(loader):
        print(f"Batch shape: X={x_batch.shape}, Y={y_batch.shape}")
        print(f"Sample target: {y_batch[0]}")