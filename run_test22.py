import unittest

def test_everything():
    suite = unittest.defaultTestLoader.discover('tests', pattern='*qr*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        import sys
        sys.exit(1)

test_everything()
