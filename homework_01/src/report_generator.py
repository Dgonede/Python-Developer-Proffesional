import json
import datetime
import os

def generate_report(url_stats, report_dir):
    report_data = {}
    
    # Вычисление статистики для каждого URL
    for url, times in url_stats.items():
        if times:  # Проверка на наличие данных
            report_data[url] = {
                "count": len(times),
                "average": sum(times) / len(times),
                "max": max(times),
                "median": sorted(times)[len(times) // 2],
                "time_sum": sum(times)
            }
        else:
            print(f"No data for URL: {url}")  # Отладочный вывод

    # Добавление новых полей для отчета
    total_count = sum(item["count"] for item in report_data.values())
    total_time_sum = sum(item["time_sum"] for item in report_data.values())

    for url, stats in report_data.items():
        stats["count_perc"] = (stats["count"] / total_count) * 100 if total_count > 0 else 0
        stats["time_perc"] = (stats["time_sum"] / total_time_sum) * 100 if total_time_sum > 0 else 0

    # Проверка на наличие данных для сохранения
    if not report_data:
        print("No data to save in report.")
        return  # Выход из функции, если нет данных

    # Форматирование даты для имени файла
    report_date = datetime.datetime.now().strftime('%Y.%m.%d')
    
    # Путь для сохранения JSON-отчета
    report_file_json = os.path.join(report_dir, f"report-{report_date}.json")
    
    # Сохранение JSON-отчета
    with open(report_file_json, 'w') as f:
        json.dump(report_data, f, indent=4)
    print(f"JSON report saved to: {report_file_json}")  # Отладочный вывод

    # Генерация HTML-отчета
    report_file_html = os.path.join(report_dir, f"report-{report_date}.html")
    
    # Убедитесь, что файл шаблона report.html существует
    template_path = os.path.join(os.path.dirname(__file__), '..', 'report.html')
    try:
        with open(template_path, 'r') as template_file:
            template = template_file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Template file 'report.html' not found at {template_path}")

    # Подготовка данных для HTML
    table_data = json.dumps(report_data)
    report_content = template.replace('$table_json', table_data)
    
    # Сохранение HTML-отчета
    with open(report_file_html, 'w') as f:
        f.write(report_content)
    print(f"HTML report saved to: {report_file_html}")  # Отладочный вывод

# Пример вызова функции
if __name__ == "__main__":
    url_stats = {
        "http://example.com": [1.2, 2.3, 3.1],
        "http://another-example.com": [0.5, 1.5, 2.0]
    }
    report_dir = "reports"  # Убедитесь, что эта директория существует
    os.makedirs(report_dir, exist_ok=True)  # Создание директории, если она не существует
    generate_report(url_stats, report_dir)