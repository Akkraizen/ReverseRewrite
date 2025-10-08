import logging
from logging import DEBUG, INFO, WARN, ERROR, CRITICAL

from loguru import logger

def setup_logger() -> None:
    logging.disable(DEBUG)
    logging.disable(INFO)
    logging.disable(WARN)
    logging.disable(ERROR)
    logging.disable(CRITICAL)

    logger.add("../logs/log_{time}.log")
    logger.info("Logger was configured")