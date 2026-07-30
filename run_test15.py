import unittest
import sys

from tests.test_tui import TestTUI
from tests.test_qr_lab import TestQRLabManager

suite = unittest.TestSuite()
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestTUI))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestQRLabManager))
unittest.TextTestRunner(verbosity=2).run(suite)
