import logging
from collections import deque
from typing import Deque

class MemoryLogHandler(logging.Handler):
    def __init__(self, capacity: int = 50):
        super().__init__()
        self.log_deque: Deque[str] = deque(maxlen=capacity)

    def emit(self, record: logging.LogRecord) -> None:
        self.log_deque.append(self.format(record))

    def get_logs(self) -> list[str]:
        return list(self.log_deque)
