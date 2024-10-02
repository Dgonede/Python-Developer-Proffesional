FROM python:3.12-slim

WORKDIR /app

# Установите Poetry
RUN pip install poetry

# Копируем файлы проекта
COPY pyproject.toml poetry.lock ./

# Устанавливаем зависимости
RUN poetry install --no-dev
RUN pip install pandas
# Копируем код
COPY src/ ./src
COPY tests/ ./tests

CMD ["poetry", "run", "python", "src/log_parser.py"]