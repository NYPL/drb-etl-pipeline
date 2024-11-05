import logging
from newrelic.agent import NewRelicContextFormatter
import os
import sys


levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def create_logger(module: str) -> logging.Logger:
    logger = logging.getLogger(module)
    console_log = logging.StreamHandler(stream=sys.stdout)

    log_level = os.environ.get('LOG_LEVEL', 'warning').lower()
    environment = os.environ.get('ENVIRONMENT', 'local')

    logger.setLevel(levels.get(log_level, logging.WARNING))
    console_log.setLevel(levels.get(log_level, logging.WARNING))

    formatter = NewRelicContextFormatter('%(asctime)s | %(name)s | %(levelname)s: %(message)s')  # noqa: E501
    console_log.setFormatter(formatter)

    if environment == 'local':
        logger.addHandler(console_log)

    return logger
