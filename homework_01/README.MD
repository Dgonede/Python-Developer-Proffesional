Для запуска приложения: 

poetry run python src/log_parser.py <path_to_nginx_log>

Запуск тестов: 

poetry run pytest tests/

Docker:

Сборка образа 
docker build -t log-analyzer .

Запуск 
docker run -v "path-to-logs with analyzer app" log-analyzer python /app/log_analyzer.py /app/test_nginx_log.txt
