"""Central logging with in-memory buffer for GUI."""

from __future__ import annotations

import logging
from collections import deque
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Deque

from config_tool.paths import get_app_data_dir

LOG_BUFFER: Deque[str] = deque(maxlen=2000)
_CONFIGURED = False


class MemoryLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        LOG_BUFFER.append(self.format(record))


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger("config_tool")
    if _CONFIGURED:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    logger.addHandler(console)

    memory = MemoryLogHandler()
    memory.setLevel(logging.DEBUG)
    memory.setFormatter(formatter)
    logger.addHandler(memory)

    log_dir = get_app_data_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "config_tool.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    _CONFIGURED = True
    return logger


def get_log_lines() -> list[str]:
    return list(LOG_BUFFER)
