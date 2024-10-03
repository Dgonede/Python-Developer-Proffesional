import structlog
import logging

def setup_logging(log_file=None):
    processors = [
        structlog.processors.TimeStamper(fmt='iso'),
        structlog.processors.JSONRenderer(),
    ]
    
    if log_file:
        logging.basicConfig(filename=log_file, level=logging.INFO)
    else:
        logging.basicConfig(level=logging.INFO)

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

# Пример использования
if __name__ == "__main__":
    setup_logging('logfile.json')  # Убедитесь, что вы передаете имя файла
    logger = structlog.get_logger()
    logger.info("Report generated successfully.")