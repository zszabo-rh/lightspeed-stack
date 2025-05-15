import logging
from rich.logging import RichHandler


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers = [RichHandler()]
    logger.propagate = False
    return logger
