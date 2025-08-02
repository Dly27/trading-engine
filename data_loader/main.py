import time
import numpy as np
import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor
from queue import Queue
from threading import Thread
from collections import deque


class DataSet:
    def __init__(self, data, target):
        self.data = data
        self.target = target
        self.y = None
        self.x = None

        self.load_data()

    def load_data(self):
        if isinstance(self.data, str) and os.path.isfile(self.data):
            self.load_csv()
        elif isinstance(self.data, pd.DataFrame):
            self.load_pandas_dataframe()
        elif isinstance(self.data, tuple) and len(self.data) == 2:
            self.load_numpy_array()

    def load_csv(self):
        df = pd.read_csv(self.data)
        self.y = df[self.target].values
        self.x = df.drop(columns=[self.target]).values

    def load_pandas_dataframe(self):

        self.y = self.data[self.target].values
        self.x = self.data.drop(columns=[self.target]).values

    def load_numpy_array(self):
        self.x, self.y = self.data

    def __len__(self):
        return len(self.x)

    def __getitem__(self, item):
        return self.x[item], self.y[item]


def load_single_batch(data, batch_indices):
    x_batch = []
    y_batch = []

    for i in batch_indices:
        x, y = data[i]
        x_batch.append(x)
        y_batch.append(y)

    return np.array(x_batch), np.array(y_batch)


class Pipeline:
    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, x, y):
        for transform in self.transforms:
            x, y = transform(x, y)

        return x, y


class Profiler:
    def __init__(self, history_size=50, tune_freq=10):
        self.history_size = history_size
        self.tune_freq = tune_freq
        self.batch_times = deque(maxlen=self.history_size)
        self.last_tune_counter = 0

    def log(self, time):
        self.batch_times.append(time)

    def check_to_tune(self, current_batch_index):
        return current_batch_index - self.last_tune_counter >= self.tune_freq

    def update_tune_counter(self, current_batch_index):
        self.last_tune_counter = current_batch_index

    def mean_time(self):
        return sum(self.batch_times) / len(self.batch_times)


class DataLoader:
    def __init__(self,
                 data,
                 transforms=[],
                 shuffle=False,
                 batch_size=32,
                 workers=4,
                 max_prefetch=3,
                 ):

        self.data = data
        self.shuffle = shuffle
        self.batch_size = batch_size
        self.workers = workers
        self.x_batches = []
        self.y_batches = []
        self.indices = list(range(len(self.data)))
        self.max_prefetch = max_prefetch
        self.batch_queue = Queue(self.max_prefetch)
        self.worker_thread = None
        self.profiler = Profiler()

        if transforms is None:
            self.transforms = []
        else:
            self.transforms = transforms

    def __iter__(self):
        self.current_batch_index = 0

        if self.shuffle:
            np.random.shuffle(self.indices)

        # Creates thread if it is not alive or does not exist
        if not self.worker_thread or self.worker_thread is None:
            self.worker_thread = Thread(target=self.load_batches)
            self.worker_thread.start()

        return self

    def __next__(self):
        batch = self.batch_queue.get()

        if batch is None:
            raise StopIteration

        return batch

    def process_sample(self, sample):
        x, y = sample

        pipeline = Pipeline(self.transforms)
        pipeline(x, y)

        return x, y

    def load_batches(self):
        with ProcessPoolExecutor(max_workers=self.workers) as executor:
            while self.current_batch_index < len(self.indices):

                start_time = time.time()
                end = min(self.current_batch_index + self.batch_size, len(self.indices))
                batch_indices = self.indices[self.current_batch_index:end]

                samples = [self.data[i] for i in batch_indices]
                processed_samples = list(executor.map(self.process_sample, samples))

                x_batch = [s[0] for s in processed_samples]
                y_batch = [s[1] for s in processed_samples]

                self.batch_queue.put((np.array(x_batch), np.array(y_batch)))
                self.current_batch_index = end

                end_time = time.time()
                self.profiler.log(end_time - start_time)

                if self.profiler.check_to_tune(self.current_batch_index):
                    avg_time = self.profiler.mean_time()
                    if avg_time > 0.2 and self.batch_size > 4:
                        self.batch_size = max(4, self.batch_size // 2)
                    elif avg_time < 0.05 and self.batch_size < 1024:
                        self.batch_size = self.batch_size * 2

                    self.profiler.update_tune_counter(self.current_batch_index)

        self.batch_queue.put(None)
