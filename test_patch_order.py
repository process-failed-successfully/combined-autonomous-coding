import unittest
from unittest.mock import patch

class TestOrder(unittest.TestCase):
    @patch('sys.exit')
    @patch('os.getcwd')
    def test_order(self, mock_getcwd, mock_exit):
        print(f"Arg 1: {mock_getcwd._mock_name if hasattr(mock_getcwd, '_mock_name') else 'unknown'}")
        # Note: MagicMock doesn't always have _mock_name set by patch unless configured.
        # But we can check equality.
        pass

if __name__ == '__main__':
    # unittest.main()
    pass
