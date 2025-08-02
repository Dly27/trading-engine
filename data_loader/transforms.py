import numpy as np


class Normalize:
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std

    def __call__(self, x, y):
        return (x - self.mean) / self.std, y

class AddNoise:
    def __init__(self, std=0.01):
        self.std = std

    def __call__(self, x, y):
        noise = np.random.normal(0, self.std, size=x.shape)
        return x + noise, y