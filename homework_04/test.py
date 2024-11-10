import pytest
from unittest.mock import MagicMock, patch
from scoring import get_score, get_interests

@pytest.fixture
def mock_store():
    store = MagicMock()
    return store

@pytest.mark.parametrize("first_name, last_name, phone, email, birthday, gender, expected_score", [
    ("John", "Doe", "71234567890", "john.doe@example.com", None, None, 3.5),  # 1.5 + 1.5
    (None, None, "71234567890", "jane.doe@example.com", None, None, 3.0),  # 1.5 + 1.5
    ("John", "Doe", "71234567890", "john.doe@example.com", "2000-01-01", 1, 5.0),  # 0.5 + 1.5 + 1.5 + 1.5
    (None, None, None, None, None, None, 0.0),  # Ничего не передаем
])
def test_get_score(mock_store, first_name, last_name, phone, email, birthday, gender, expected_score):
    score = get_score(mock_store, phone=phone, first_name=first_name, last_name=last_name, email=email, birthday=birthday, gender=gender)
    assert score == expected_score

def test_get_interests(mock_store):
    with patch('random.sample', return_value=["interest_1", "interest_2"]):
        interests = get_interests(mock_store, "client_id")
        assert interests == ["interest_1", "interest_2"]