import numpy as np
import pandas as pd
import yfinance as yf
from base import DataSet, DataLoader, Profiler


class FinancialPreprocessor:
    def __init__(self, symbols, start_date, end_date, target_type='returns'):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.target_type = target_type

    def load_prepare_data(self):
        """
        Load and prepare data based on whether there is a single or multiple
        stocks
        :return: Pandas DataFrame
        """
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
        """
        Prepare a single stock dataset
        Create target based on user input
        :param data: Non-prepared data from yfinance
        :param symbol: Ticker of stock
        :return: Pandas DataFrame
        """
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
        """
        Prepare multiple stock datasets
        :param data: Non-prepared data from yfinance
        :return: Pandas DataFrame
        """
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
    def __init__(self,
                 symbols,
                 start_date,
                 end_date,
                 target_type='returns',
                 data=None,
                 window=False,
                 lookback=None,
                 **kwargs):
        """
        Create object based on whether you will download new data or you are inputting already
        downloaded data
        :param symbols: Tickers for stocks
        """
        if data is not None:
            self.lookback = lookback
            super().__init__(data=data, target='target')
        else:
            self.start_date = start_date
            self.end_date = end_date
            self.target_type = target_type
            self.symbols = symbols
            self.window = window

            preprocessor = FinancialPreprocessor(symbols, start_date, end_date, target_type)
            processed_data = preprocessor.load_prepare_data()

            super().__init__(data=processed_data, target='target')

    def fetch_data(self, symbol, start_date, end_date):
        """
        Download single stock data from yfinance
        :param symbol: Ticker of stock
        :param start_date: Start date of data
        :param end_date: ENd date of data
        :return: Pandas Dataframe
        """
        return yf.download(symbol, start=start_date, end=end_date)

    def get_point_in_time_data(self, as_of_date, lookback=None):
        """
        Return a dataset of a given time range to remove need to download data from API
        :param as_of_date: Final date of the dataset
        :param lookback: How many days back from the as_of_date to include in the dataset
        :return: FinancialDataSet
        """
        as_of_date = pd.to_datetime(as_of_date)
        start_date = pd.to_datetime(self.start_date)
        df = self.data.copy()

        # If no lookback set, set lookback to days between as_of_date and start
        if lookback is None:
            lookback = (as_of_date - start_date).days

        mask = df.index <= as_of_date
        pit_data = df[mask]

        if lookback and len(pit_data) > lookback:
            pit_data = pit_data.tail(lookback)

        return FinancialDataSet(data=pit_data,
                                start_date=as_of_date-pd.Timedelta(days=lookback),
                                end_date=as_of_date,
                                symbols=self.symbols,
                                lookback=lookback)

    def create_windows(self, window_size, forecast_horizon):
        """
        Create windows from dataset
        :param window_size: Size of individual windows
        :param forecast_horizon: Range into the future to predict
        :return: DataSet
        """
        # Make sure window size is smaller than lookback
        if window_size > self.lookback:
            raise ValueError("Window size cannot be greater than the lookback")

        sequences = []
        targets = []

        for i in range(window_size, len(self.data) - forecast_horizon):
            sequence = self.data.iloc[i-window_size:i].values
            target = self.data.iloc[i+forecast_horizon]["target"]
            sequences.append(sequence)
            targets.append(target)

        return DataSet(data=(sequences, targets), target=None)  # DataSet.load_numpy_array doesn't need a target

class FinancialDataLoader(DataLoader):
    def __init__(self, data, **kwargs):
        super().__init__(data=data, **kwargs)

    def create_time_series_batches(self):
        pass


if __name__ == "__main__":

    data = FinancialDataSet(symbols=["AAPL", "MSFT"],
                            start_date="2024-01-01",
                            end_date="2025-08-01",
                            target_type="returns")


    print(f"Dataset length: {len(data)}")
    print(f"Feature columns: {data.data.columns.tolist()}")
    print(f"Target stats: min={data.y.min():.4f}, max={data.y.max():.4f}, mean={data.y.mean():.4f}")

    data = data.get_point_in_time_data(as_of_date="2025-03-01", lookback=None)
    data = data.create_windows(window_size=50, forecast_horizon=1)

    loader = FinancialDataLoader(data=data,
                                 batch_size=16,
                                 shuffle=False,
                                 workers=4)

    """
    for i, (x_batch, y_batch) in enumerate(loader):
        print(f"Batch shape: X={x_batch.shape}, Y={y_batch.shape}")
        print(f"Sample target: {y_batch[0]}")
    """

    for x_batch, y_batch in loader:
        print(x_batch, y_batch)