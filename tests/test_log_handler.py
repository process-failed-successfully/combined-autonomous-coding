import unittest
import logging
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from shared.log_handler import MemoryLogHandler

class TestMemoryLogHandler(unittest.TestCase):
    def test_log_capturing(self):
        handler = MemoryLogHandler(capacity=10)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info('message 1')
        logger.info('message 2')

        logs = handler.get_logs()
        self.assertEqual(len(logs), 2)
        self.assertIn('message 1', logs[0])
        self.assertIn('message 2', logs[1])

    def test_log_truncation(self):
        handler = MemoryLogHandler(capacity=2)
        logger = logging.getLogger('test_logger_2')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        logger.info('message 1')
        logger.info('message 2')
        logger.info('message 3')

        logs = handler.get_logs()
        self.assertEqual(len(logs), 2)
        self.assertIn('message 2', logs[0])
        self.assertIn('message 3', logs[1])

if __name__ == '__main__':
    unittest.main()
