# Проверка загруженных данных в Memcache

from pymemcache.client import base

def check_data_in_memcache(keys):
    client = base.Client(('localhost', 11211))
    for key in keys:
        value = client.get(key)
        print(f"{key}: {value}")
    client.close()

if __name__ == "__main__":
    keys_to_check = ['key1', 'key2', 'key3', 'key4', 'key5', 'key6', 'key7', 'key8']
    check_data_in_memcache(keys_to_check)