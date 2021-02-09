import logging
import os


levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}


def createLog(module):
    logger = logging.getLogger(module)
    consoleLog = logging.StreamHandler()

    logLevel = os.environ.get('LOG_LEVEL', 'warning').lower()

    logger.setLevel(levels[logLevel])
    consoleLog.setLevel(levels[logLevel])

    formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s: %(message)s')  # noqa: E501
    consoleLog.setFormatter(formatter)

    logger.addHandler(consoleLog)

    return logger
