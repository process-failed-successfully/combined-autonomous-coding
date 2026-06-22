import unittest
from unittest.mock import patch, MagicMock
from main import parse_args

class TestMainTypeIDLab(unittest.TestCase):

    @patch('shared.typeid_lab.run_typeid_lab_logic')
    @patch('main.sys.exit')
    def test_typeid_lab_generate_command(self, mock_exit, mock_logic):
        mock_logic.return_value = True

        args = parse_args(['typeid-lab', 'generate', 'user', '--count', '5'])

        self.assertEqual(args.command, 'typeid-lab')
        self.assertEqual(args.action, 'generate')
        self.assertEqual(args.prefix, 'user')
        self.assertEqual(args.count, 5)

    @patch('shared.typeid_lab.run_typeid_lab_logic')
    @patch('main.sys.exit')
    def test_typeid_lab_parse_command(self, mock_exit, mock_logic):
        mock_logic.return_value = True

        args = parse_args(['typeid-lab', 'parse', 'user_01h455vb4pex5vsknk084sn02q'])

        self.assertEqual(args.command, 'typeid-lab')
        self.assertEqual(args.action, 'parse')
        self.assertEqual(args.typeid, 'user_01h455vb4pex5vsknk084sn02q')

    @patch('shared.typeid_lab.run_typeid_lab_logic')
    @patch('main.sys.exit')
    def test_typeid_lab_tui_command(self, mock_exit, mock_logic):
        mock_logic.return_value = True

        args = parse_args(['typeid-lab', 'tui'])

        self.assertEqual(args.command, 'typeid-lab')
        self.assertEqual(args.action, 'tui')

if __name__ == '__main__':
    unittest.main()
