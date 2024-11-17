import pytest
from unittest.mock import patch
from store import Store
from scoring import get_score, get_interests

@pytest.fixture
def store():
    # Создаем временную базу данных SQLite
    store = Store()
    yield store
    store.close()

@pytest.mark.parametrize("first_name, last_name, phone, email, birthday, gender, expected_score", [
    ("John", "Doe", "71234567890", "john.doe@example.com", None, None, 3.5),  # 1.5 + 1.5
    (None, None, "71234567890", "jane.doe@example.com", None, None, 3.0),  # 1.5 + 1.5
    ("John", "Doe", "71234567890", "john.doe@example.com", "2000-01-01", 1, 5.0),  # 0.5 + 1.5 + 1.5 + 1.5
    (None, None, None, None, None, None, 0.0),
])
def test_get_score(store, first_name, last_name, phone, email, birthday, gender, expected_score):
    score = get_score(store, phone=phone, first_name=first_name, last_name=last_name, email=email, birthday=birthday, gender=gender)
    assert score == expected_score

def test_get_interests(store):
    with patch('random.sample', return_value=["interest_1", "interest_2"]):
        interests = get_interests(store, "client_id")
        assert interests == ["interest_1", "interest_2"]

def test_store_get_success(store):
    store.cache_set('key', 'value')
    result = store.get('key')
    
    assert result == 'value'

def test_store_get_nonexistent(store):
    result = store.get('nonexistent_key')
    
    assert result is None

def test_store_cache_set_success(store):
    store.cache_set('key', 'value')
    result = store.get('key')
    
    assert result == 'value'

def test_store_cache_set_update(store):
    store.cache_set('key', 'value1')
    store.cache_set('key', 'value2')
    result = store.get('key')
    
    assert result == 'value2'

@pytest.fixture(scope='module')
def sqlite_store():
    # Создаем временную базу данных SQLite
    store = Store()
    yield store
    store.close()

def test_integration_cache_set_and_get(sqlite_store):
    sqlite_store.cache_set('test_key', 'test_value')
    result = sqlite_store.get('test_key')
    
    assert result == 'test_value'

def test_integration_cache_get_nonexistent(sqlite_store):
    result = sqlite_store.get('nonexistent_key')
    
    assert result is None    

