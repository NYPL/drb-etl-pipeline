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


def create_log(module):
    logger = logging.getLogger(module)
    console_log_handler = logging.StreamHandler(stream=sys.stdout)

    logLevel = os.environ.get('LOG_LEVEL', 'warning').lower()

    logger.setLevel(levels[logLevel])
    console_log_handler.setLevel(levels[logLevel])

    formatter = NewRelicContextFormatter('%(asctime)s | %(name)s | %(levelname)s: %(message)s')  # noqa: E501
    console_log_handler.setFormatter(formatter)

    logger.addHandler(console_log_handler)

    return logger
