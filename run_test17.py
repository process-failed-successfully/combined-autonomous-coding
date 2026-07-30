import unittest
import sys

# discover loads all tests matching pattern and runs them
suite = unittest.defaultTestLoader.discover('tests', pattern='test_qr_lab.py')
print(f"Total tests discovered: {suite.countTestCases()}")
for t in suite:
    for t2 in t:
        print(t2)
