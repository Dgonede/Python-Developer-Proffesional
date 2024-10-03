FROM python:3.12-slim

WORKDIR /app

# Установите Poetry
RUN pip install poetry

# Копируем файлы проекта
COPY pyproject.toml poetry.lock ./
COPY . .

# Устанавливаем зависимости
RUN poetry install --no-dev
RUN pip install pandas
RUN pip install structlog
# Копируем код
COPY ./src ./src
COPY ./config.json .
COPY ./report.html .

# Указываем команду для запуска приложения
CMD ["python", "src/main.py", "--config", "config.json"]