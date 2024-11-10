import redis
import time

class Store:
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.StrictRedis(host=host, port=port, db=db)
        self.max_retries = 5
        self.retry_delay = 1

    def get(self, key):
        for _ in range(self.max_retries):
            try:
                return self.client.get(key)
            except redis.ConnectionError:
                time.sleep(self.retry_delay)
        raise Exception("Could not connect to the store")

    def cache_get(self, key):
        return self.get(key)

    def cache_set(self, key, value, timeout):
        for _ in range(self.max_retries):
            try:
                self.client.setex(key, timeout, value)
                return
            except redis.ConnectionError:
                time.sleep(self.retry_delay)
        raise Exception("Could not connect to the store")