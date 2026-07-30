import unittest
import sys

# discover loads all tests matching pattern and runs them
suite = unittest.defaultTestLoader.discover('tests', pattern='test_*.py')
print(f"Total tests discovered: {suite.countTestCases()}")
