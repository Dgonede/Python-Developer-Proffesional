import sqlite3

class Store:
    def __init__(self, db_name=':memory:'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        self.connection.commit()

    def get(self, key):
        self.cursor.execute('SELECT value FROM cache WHERE key = ?', (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def cache_get(self, key):
        return self.get(key)

    def cache_set(self, key, value):
        self.cursor.execute('INSERT OR REPLACE INTO cache (key, value) VALUES (?, ?)', (key, value))
        self.connection.commit()

    def close(self):
        self.connection.close()