"""
Logging Configuration
=====================
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "agent", log_file: Optional[Path] = None, verbose: bool = False, console_output: bool = True
) -> logging.Logger:
    """Configure and return a logger instance."""

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all, filter in handlers

    # Check if handlers already exist to avoid duplicates
    if logger.hasHandlers():
        return logger

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

    return logger
