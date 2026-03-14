import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import sys
import shutil
import io
from main import parse_args, main

class TestImageLabFaviconCLI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.tmp_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    @patch('shared.image_lab.ImageLabManager.generate_favicon')
    @patch('sys.stdout', new_callable=io.StringIO)
    @patch('sys.argv', ['main.py', 'image-lab', 'favicon', 'input.png', 'output_dir'])
    async def test_image_lab_favicon_cli(self, mock_stdout, mock_generate_favicon):
        mock_generate_favicon.return_value = [Path('output_dir/favicon.ico')]

        try:
            await main()
        except SystemExit as e:
            self.assertEqual(e.code, 0)

        mock_generate_favicon.assert_called_once()
        args, kwargs = mock_generate_favicon.call_args
        self.assertEqual(args[0].name, 'input.png')
        self.assertEqual(args[1].name, 'output_dir')

if __name__ == '__main__':
    unittest.main()
