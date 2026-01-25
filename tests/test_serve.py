import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import sys
import os
from shared.serve import ServeManager

class TestServeManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.manager = ServeManager(self.project_dir)

    @patch("pathlib.Path.exists", autospec=True)
    @patch("shared.serve.shutil.which")
    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data='{"scripts": {"dev": "vite"}}')
    def test_detect_node(self, mock_open, mock_which, mock_exists):
        # Simulate package.json existing
        def side_effect(self):
            return self.name == "package.json"
        mock_exists.side_effect = side_effect

        mock_which.return_value = "/usr/bin/npm"

        cmd, port = self.manager.detect_config()
        self.assertEqual(cmd, ["npm", "run", "dev"])
        self.assertEqual(port, 3000)

    @patch("pathlib.Path.exists", autospec=True)
    def test_detect_python_fastapi(self, mock_exists):
        # Simulate requirements.txt and main.py
        def side_effect(self):
            if self.name == "requirements.txt": return True
            if self.name == "main.py": return True
            return False
        mock_exists.side_effect = side_effect

        with patch("pathlib.Path.read_text", return_value="fastapi\nuvicorn"):
            cmd, port = self.manager.detect_config()
            self.assertEqual(cmd, ["uvicorn", "main:app", "--reload"])
            self.assertEqual(port, 8000)

    @patch("pathlib.Path.exists", autospec=True)
    def test_detect_python_django(self, mock_exists):
        # Simulate manage.py
        def side_effect(self):
            return self.name == "manage.py"
        mock_exists.side_effect = side_effect

        cmd, port = self.manager.detect_config()
        self.assertEqual(cmd, [sys.executable, "manage.py", "runserver"])
        self.assertEqual(port, 8000)

    @patch("pathlib.Path.exists", autospec=True)
    def test_detect_static(self, mock_exists):
        # Simulate index.html
        def side_effect(self):
            return self.name == "index.html"
        mock_exists.side_effect = side_effect

        cmd, port = self.manager.detect_config()
        self.assertEqual(cmd, [sys.executable, "-m", "http.server"])
        self.assertEqual(port, 8000)

    @patch("shared.serve.subprocess.Popen")
    @patch("shared.serve.ServeManager.detect_config")
    def test_start(self, mock_detect, mock_popen):
        mock_detect.return_value = (["npm", "start"], 3000)

        # Test dry run
        success = self.manager.start(dry_run=True)
        self.assertTrue(success)
        mock_popen.assert_not_called()

        # Test actual run
        process_mock = MagicMock()
        mock_popen.return_value = process_mock

        success = self.manager.start()
        self.assertTrue(success)

        # Check env vars
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0], ["npm", "start"])
        self.assertEqual(kwargs['env']['PORT'], '3000')
        self.assertEqual(kwargs['env']['HOST'], '127.0.0.1')

    @patch("shared.serve.subprocess.Popen")
    def test_start_manual_command(self, mock_popen):
        process_mock = MagicMock()
        mock_popen.return_value = process_mock

        success = self.manager.start(command="python custom.py", port=9999)
        self.assertTrue(success)

        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0], ["python", "custom.py"])
        # Port might not be injected in custom command logic unless we parsed it,
        # but the ServeManager sets env vars regardless.
        self.assertEqual(kwargs['env']['PORT'], '9999')

if __name__ == "__main__":
    unittest.main()
