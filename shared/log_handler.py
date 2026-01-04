import logging
from collections import deque

class MemoryLogHandler(logging.Handler):
    def __init__(self, capacity=50):
        super().__init__()
        self.log_deque = deque(maxlen=capacity)

    def emit(self, record):
        self.log_deque.append(self.format(record))

    def get_logs(self):
        return list(self.log_deque)
