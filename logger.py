"""
AI Turkish Video Translator Bot - Logging Module
Professional logging with file rotation and colored console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import config


class ColoredFormatter(logging.Formatter):
    """Custom formatter with ANSI colors for console output."""

    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{self.BOLD}{record.levelname:<8}{self.RESET}"
        record.name = f"\033[34m{record.name}{self.RESET}"
        return super().format(record)


def setup_logger(name: str = "turkish_bot") -> logging.Logger:
    """
    Set up and return a configured logger instance.

    Args:
        name: Logger name (usually __name__ of the calling module).

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, config.LOG_LEVEL.upper(), logging.INFO))

    # ─── Console Handler ────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_fmt = ColoredFormatter(
        "%(asctime)s │ %(levelname)s │ %(name)-20s │ %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # ─── File Handler (Rotating) ────────────────────────────────────
    log_path = Path(config.LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename=str(log_path),
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s │ %(levelname)-8s │ %(name)-25s │ %(funcName)-20s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    # ─── Error-only File Handler ────────────────────────────────────
    error_log_path = log_path.parent / "errors.log"
    error_handler = RotatingFileHandler(
        filename=str(error_log_path),
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_fmt)
    logger.addHandler(error_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the main bot logger."""
    main_logger = setup_logger("turkish_bot")
    return main_logger.getChild(name)
