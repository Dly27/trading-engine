import time
import numpy as np
import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor
from queue import Queue
from threading import Thread
from collections import deque
from pathlib import Path
from transforms import *
from functools import partial


class DataSet:
    def __init__(self, data, target):
        self.data = data
        self.target = target
        self.y = None
        self.x = None
        self.load_data()

    def __len__(self):
        return len(self.x)

    def __getitem__(self, item):
        return self.x[item], self.y[item]

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
                 transforms=None,
                 shuffle=False,
                 batch_size=32,
                 workers=4,
                 max_prefetch=3,
                 cache_type=None
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

        self.cache_type = cache_type
        self.cache = {}

        if cache_type == "disk":
            self.cache_dir = Path(".batch_cache")
            self.cache_dir.mkdir(exist_ok=True)

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

    def cache_batch(self, key, x_batch, y_batch):
        if self.cache_type == 'memory':
            self.cache[key] = (x_batch, y_batch)

    def get_batch_cache_path(self, batch_indices):
        id = "".join(map(str, batch_indices))
        return os.path.join(self.cache_dir, f"{id}.npz")

    def save_batch_to_disk(self, x_batch, y_batch, batch_indices):
        path = self.get_batch_cache_path(batch_indices=batch_indices)
        np.savez(path, x=x_batch, y=y_batch)

    def batch_exists_in_disk(self, batch_indices):
        path = self.get_batch_cache_path(batch_indices=batch_indices)
        return os.path.exists(path)

    def load_batch_from_disk(self, batch_indices):
        path = self.get_batch_cache_path(batch_indices=batch_indices)
        data = np.load(path)
        return data['x'], data['y']

    def get_or_process_batch(self, key, batch_indices, executor):
        if self.cache_type == "memory" and key in self.cache:
            return self.cache[key]

        if self.cache_type == "disk" and self.batch_exists_in_disk(batch_indices=batch_indices):
            return self.load_batch_from_disk(batch_indices=batch_indices)

        samples = [self.data[i] for i in batch_indices]
        func = partial(process_sample, transforms=self.transforms)
        processed_samples = list(executor.map(func, samples))

        x_batch = [s[0] for s in processed_samples]
        y_batch = [s[1] for s in processed_samples]
        x_batch = np.array(x_batch)
        y_batch = np.array(y_batch)

        if self.cache_type == "memory":
            self.cache_batch(key, x_batch, y_batch)
        elif self.cache_type == "disk":
            self.save_batch_to_disk(x_batch=x_batch, y_batch=y_batch, batch_indices=batch_indices)

        return x_batch, y_batch

    def load_batches(self):
        with ProcessPoolExecutor(max_workers=self.workers) as executor:

            while self.current_batch_index < len(self.indices):
                start_time = time.time()
                end = min(self.current_batch_index + self.batch_size, len(self.indices))
                current_batch_indices = self.indices[self.current_batch_index:end]
                key = tuple(current_batch_indices)

                x_batch, y_batch = self.get_or_process_batch(key=key,
                                                             batch_indices=current_batch_indices,
                                                             executor=executor)

                self.batch_queue.put((np.array(x_batch), np.array(y_batch)))
                self.current_batch_index = end

                end_time = time.time()
                self.profiler.log(end_time - start_time)

                # Auto tune batching
                if self.profiler.check_to_tune(self.current_batch_index):
                    avg_time = self.profiler.mean_time()
                    if avg_time > 0.2 and self.batch_size > 4:
                        self.batch_size = max(4, self.batch_size // 2)
                    elif avg_time < 0.05 and self.batch_size < 1024:
                        self.batch_size = self.batch_size * 2

                    self.profiler.update_tune_counter(self.current_batch_index)

        self.batch_queue.put(None)


def process_sample(sample, transforms):
    x, y = sample
    pipeline = Pipeline(transforms)
    x, y = pipeline(x, y)
    return x, y


if __name__ == "__main__":

    df = pd.DataFrame({
        'feature1': np.random.randn(100),
        'feature2': np.random.randn(100),
        'feature3': np.random.randn(100),
        'target': np.random.randint(0, 2, size=100)
    })

    data = DataSet(data=df, target='target')

    loader = DataLoader(data=data,
                        transforms=[Normalize(mean=0.5, std=0.2)],
                        batch_size=16,
                        workers=2,
                        shuffle=True
                        )

    for x_batch, y_batch in loader:
        print(x_batch, y_batch)
