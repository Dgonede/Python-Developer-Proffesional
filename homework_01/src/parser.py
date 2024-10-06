import gzip
import os
import json

import structlog

def find_latest_log(log_dir):
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not log_files:
        return None
    latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    return os.path.join(log_dir, latest_log)

def parse_log(log_file):
    url_stats = {}
    open_func = gzip.open if log_file.endswith('.gz') else open
    
    try:
        with open_func(log_file, 'rt') as f:  # 'rt' для текстового режима
            for line in f:
                # Предполагается, что лог имеет формат: <time> <url>
                parts = line.strip().split()
                if len(parts) < 2:
                    continue
                
                try:
                    time = float(parts[0])  # Время ответа
                except ValueError:
                    structlog.get_logger().warning(f"Invalid time value: '{parts[0]}' in line: '{line.strip()}'")
                    continue  # Пропускаем строку, если значение времени некорректно
                
                url = parts[1]  # URL
                if url not in url_stats:
                    url_stats[url] = []
                url_stats[url].append(time)
    except FileNotFoundError:
        structlog.get_logger().error(f"Log file not found: {log_file}")
    except PermissionError:
        structlog.get_logger().error(f"Permission denied when accessing log file: {log_file}")
    except Exception as e:
        structlog.get_logger().error(f"An unexpected error occurred while parsing the log file: {e}")
    
    return url_stats