import pandas as pd

def parse_nginx_logs(log_file):
    data = []
    with open(log_file, 'r') as file:
        for line in file:
            line = line.strip()  # Удаляем пробелы в начале и конце строки
            if not line:  # Игнорируем пустые строки
                continue
            print(f"Читаем строку: '{line}'")  # Выводим строку для отладки
            parts = line.split()  # Разделяем строку по пробелам
            print(f"Количество элементов: {len(parts)}")  # Выводим количество элементов          
            # Проверяем, что в строке достаточно элементов
            if len(parts) == 10:
                try:
                    response_time = float(parts[9])  # Убедитесь, что индекс 10 соответствует времени отклика
                    data.append(response_time)
                except ValueError:
                    print(f"Не удалось преобразовать время отклика: {parts[9]}")
            else:
                print(f"Пропущена строка из-за недостатка элементов: {line}")
    return pd.Series(data)

def analyze_response_times(response_times):
    return {
        'mean': response_times.mean(),
        'median': response_times.median(),
        'max': response_times.max(),
        'min': response_times.min(),
    }

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python log_analyzer.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]
    response_times = parse_nginx_logs(log_file)
    analysis_results = analyze_response_times(response_times)

    print("Response Time Analysis:")
    print(f"Mean: {analysis_results['mean']}")
    print(f"Median: {analysis_results['median']}")
    print(f"Max: {analysis_results['max']}")
    print(f"Min: {analysis_results['min']}")