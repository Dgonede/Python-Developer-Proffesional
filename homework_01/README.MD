Для запуска приложения: 

poetry run 
python src/main.py --config config.json

Запуск тестов: 

poetry run pytest tests/

Docker:

Сборка образа 
docker build -t my-python-app .

Запуск 
docker run 
--rm my-python-app
