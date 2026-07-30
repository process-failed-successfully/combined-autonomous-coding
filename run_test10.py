import unittest
import sys

# Try loading everything from test_qr_lab
suite = unittest.defaultTestLoader.discover('tests', pattern='*qr_lab*.py')
unittest.TextTestRunner(verbosity=2).run(suite)
