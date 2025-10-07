from loguru import logger

def setup_logger() -> None:
    logger.add("../logs/log_{time}.log")
    logger.info("Logger was configured")