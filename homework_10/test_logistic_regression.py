import numpy as np
import pytest
from logistic_regression import LogisticRegression


def test_train():
    # Создаем модель
    model = LogisticRegression()
    
    # Генерируем искусственные данные
    np.random.seed(0)  # Для воспроизводимости
    X = np.random.rand(100, 2)  # 100 примеров, 2 признака
    y = np.random.randint(0, 2, size=100)  # Бинарные метки (0 или 1)

    # Обучаем модель
    model.train(X, y, learning_rate=1e-2, num_iters=1000, verbose=False)

    # Проверяем, что веса обновились
    assert model.w is not None, "Weights should be initialized and updated"
    assert model.w.shape == (X.shape[1] + 1,), "Weights shape should match input features plus bias"

    # Проверяем, что история потерь не пустая
    assert model.loss_history is not None, "Loss history should not be None"
    assert len(model.loss_history) == 1000, "Loss history should have the same length as num_iters"

    # Проверяем, что потери не NaN
    assert not np.isnan(model.loss_history).any(), "Loss history should not contain NaN values"


def test_append_biases():
    X = np.array([[1, 2], [3, 4]])
    expected_output = np.array([[1, 1, 2], [1, 3, 4]])
    result = LogisticRegression.append_biases(X).toarray()  # Преобразуем разреженную матрицу в обычную
    assert np.array_equal(result, expected_output), f"Expected {expected_output}, but got {result}"


def test_predict_proba():
    model = LogisticRegression()
    model.w = np.array([0.0, 0.0, 0.0])  # Устанавливаем веса в ноль для простоты
    X = np.array([[1, 2], [1, 3]])
    X_with_bias = LogisticRegression.append_biases(X).toarray()
    probabilities = model.predict_proba(X_with_bias, append_bias=False)
    
    # Проверяем, что вероятности суммируются до 1
    assert np.allclose(np.sum(probabilities, axis=1), 1), "Probabilities do not sum to 1"


def test_loss():
    model = LogisticRegression()
    model.w = np.array([0.0, 0.0, 0.0])  # Устанавливаем веса в ноль для простоты
    X_batch = np.array([[1, 2], [1, 3]])
    y_batch = np.array([0, 1])
    X_batch_with_bias = LogisticRegression.append_biases(X_batch).toarray()  # Добавляем смещение
    loss, grad = model.loss(X_batch_with_bias, y_batch, reg=0.1)
    
    # Проверяем, что потери не NaN
    assert not np.isnan(loss), "Loss is NaN"
    assert grad.shape == model.w.shape, "Gradient shape does not match weights shape"


if __name__ == "__main__":
    pytest.main()