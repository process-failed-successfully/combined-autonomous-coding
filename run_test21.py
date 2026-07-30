import unittest

def test_everything():
    suite = unittest.defaultTestLoader.discover('tests', pattern='test_qr*.py')
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        sys.exit(1)

test_everything()
