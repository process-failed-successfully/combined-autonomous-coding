import unittest
import sys
from tests.test_tui_qr import TestQRLabTUI
from tests.test_qr_lab import TestQRLabManager

suite = unittest.TestSuite()
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestQRLabTUI))
suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestQRLabManager))
unittest.TextTestRunner(verbosity=2).run(suite)
