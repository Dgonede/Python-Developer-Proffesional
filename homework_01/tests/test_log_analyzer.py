import os
import json
import pytest
from src.report_generator import generate_report  # Замените на фактический путь
import datetime

@pytest.fixture
def setup_report_dir():
    report_dir = "test_reports"
    os.makedirs(report_dir, exist_ok=True)
    yield report_dir
    for file in os.listdir(report_dir):
        os.remove(os.path.join(report_dir, file))
    os.rmdir(report_dir)

def test_generate_report(setup_report_dir):
    url_stats = {
        "http://example.com": [1.2, 2.3, 3.1],
        "http://another-example.com": [0.5, 1.5, 2.0]
    }
    generate_report(url_stats, setup_report_dir)

    # Получаем текущую дату для имени файла
    report_date = datetime.datetime.now().strftime('%Y.%m.%d')
    json_file = os.path.join(setup_report_dir, f"report-{report_date}.json")

    # Проверяем, что JSON-файл был создан
    assert os.path.exists(json_file)

    # Проверяем содержимое JSON-файла
    with open(json_file, 'r') as f:
        data = json.load(f)