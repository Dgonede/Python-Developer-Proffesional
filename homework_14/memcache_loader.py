from pymemcache.client import base
from concurrent.futures import ThreadPoolExecutor

# Загрузка данных в Memcache
def load_data_to_memcache(data_chunk):
    client = base.Client(('localhost', 11211))
    for key, value in data_chunk.items():
        client.set(key, value)
    client.close()

def chunk_data(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield dict(list(data.items())[i:i + chunk_size])

def load_all_data(data, chunk_size=2, max_workers=4):
    data_chunks = list(chunk_data(data, chunk_size))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        executor.map(load_data_to_memcache, data_chunks)