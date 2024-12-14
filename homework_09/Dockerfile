# используем официальный образ питона
FROM python:3.12

#устанавливаем рабочую директорию в контейнере
WORKDIR /app

#копируем файл зависимостей
COPY pyproject.toml .

#устанавливаем зависимости из этого файла
RUN pip install "poetry==1.8.3" setuptools wheel

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

RUN poetry install 

#копируем все содержимое папки в контейнер
COPY . .

#указываем команду для запуска сервера unicorn

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]