"""
Logging Configuration
=====================
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Tuple
from shared.log_handler import MemoryLogHandler


def setup_logger(
    name: str = "agent",
    log_file: Optional[Path] = None,
    verbose: bool = False,
    console_output: bool = True,
) -> Tuple[logging.Logger, MemoryLogHandler]:
    """Configure and return a logger instance and the memory handler."""

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all, filter in handlers

    # Check if handlers already exist to avoid duplicates
    if logger.hasHandlers():
        # Find the existing memory handler if it exists
        for handler in logger.handlers:
            if isinstance(handler, MemoryLogHandler):
                return logger, handler
        # If no memory handler is found, we clear existing handlers to re-configure
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
    )

    # Console Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File Handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Memory Handler
    memory_handler = MemoryLogHandler()
    memory_handler.setLevel(logging.DEBUG)
    memory_handler.setFormatter(formatter)
    logger.addHandler(memory_handler)

    return logger, memory_handler
