import os
import json

def find_latest_log(log_dir):
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not log_files:
        return None
    latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    return os.path.join(log_dir, latest_log)

def parse_log(log_file):
    url_stats = {}
    with open(log_file, 'r') as f:
        for line in f:
            # Предполагается, что лог имеет формат: <time> <url>
            parts = line.strip().split()
            if len(parts) < 2:
                continue
            time = float(parts[0])  # Время ответа
            url = parts[1]          # URL
            if url not in url_stats:
                url_stats[url] = []
            url_stats[url].append(time)
    return url_stats