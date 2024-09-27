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


def create_logger(name: str):
    logger = logging.getLogger(name)
    consoleLog = logging.StreamHandler(stream=sys.stdout)

    logLevel = os.environ.get('LOG_LEVEL', 'warning').lower()

    logger.setLevel(levels[logLevel])
    consoleLog.setLevel(levels[logLevel])

    formatter = NewRelicContextFormatter('%(asctime)s | %(name)s | %(levelname)s: %(message)s')  # noqa: E501
    consoleLog.setFormatter(formatter)

    logger.addHandler(consoleLog)

    return logger


stage = os.getenv('STAGE', 'qa')

logger = create_logger(f'drb-etl-pipeline-{stage}')
