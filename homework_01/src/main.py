import argparse
import os
import json
import structlog
from logger import setup_logging
from parser import find_latest_log, parse_log
from report_generator import generate_report
from datetime import datetime

def main(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    setup_logging(config.get('LOG_FILE'))
    
    # Находим последний лог
    latest_log = find_latest_log(config['LOG_DIR'])
    if not latest_log:
        structlog.get_logger().info("No logs to process.")
        return

    # Форматируем дату для имени файла отчета
    report_date = datetime.now().strftime('%Y.%m.%d')
    report_file_json = os.path.join(config['REPORT_DIR'], f"report-{report_date}.json")

    # Проверяем, существует ли отчет за текущую дату
    if os.path.exists(report_file_json):
        structlog.get_logger().info(f"Report for {report_date} already exists. Skipping report generation.")
        return

    # Если отчета нет, продолжаем обработку
    url_stats = parse_log(latest_log)
    generate_report(url_stats, config['REPORT_DIR'])
    structlog.get_logger().info("Report generated successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config.json', help='Path to config file')
    args = parser.parse_args()
    main(args.config)