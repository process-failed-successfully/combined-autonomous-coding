import unittest
import sys

from tests.test_tui_qr import TestQrLabTab
from tests.test_qr_lab import TestQRLabManager
from tests.test_tui import TestAgentTUI

suite = unittest.TestSuite()
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestQrLabTab))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestQRLabManager))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAgentTUI))
unittest.TextTestRunner(verbosity=2).run(suite)
