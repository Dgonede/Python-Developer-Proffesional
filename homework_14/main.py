from data import data
from memcache_loader import load_all_data

if __name__ == "__main__":
    print("Начинаем загрузку данных в Memcache...")
    load_all_data(data)
    print("Загрузка данных завершена.")