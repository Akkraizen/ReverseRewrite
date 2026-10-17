import logging
import sys
from pathlib import Path
from typing import override

from loguru import logger


class _InterceptHandler(logging.Handler):
    @override
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 0
        while frame is not None and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(log_dir: Path, level: str = "INFO") -> None:
    logger.remove()
    logger.add(sys.stderr, level=level, diagnose=False)
    logger.add(log_dir / "log_{time}.log", level=level, rotation="1 day", retention="14 days", diagnose=False)
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    logger.info("Logging configured, files in {}", log_dir.resolve())
