import pickle
import redis
import logging

class RedisRepository:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=False)
        self.logger = logging.getLogger(__name__)

        try:
            self.redis.ping()
            self.logger.info("CONNECTED TO REDIS")
        except Exception as e:
            self.logger.error(f"FAILED TO CONNECT TO REDIS: {e}")
            raise

    def save(self, key: str, data: any):
        """
        Serialises object then saves data to redis
        """
        try:
            serialized = pickle.dumps(data)
            self.redis.set(key, serialized)
            self.logger.info(f"SAVED {key} TO REDIS")
        except Exception as e:
            self.logger.error(f"FAILED TO SAVE {key} TO REDIS: {e}")

    def load(self, key: str):
        """
        Load data from redis then serialise into an object
        """
        try:
            data = self.redis.get(key)
            if data:
                result = pickle.loads(data)
                self.logger.info(f"LOADED {key} FROM REDIS")
                return result
        except Exception as e:
            self.logger.warning(f"CORRUPTED DATA FOR {key}, RETURNING NONE: {e}")
