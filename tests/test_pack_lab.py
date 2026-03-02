import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.pack_lab import PackManager, run_pack_logic

class TestPackLab(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/mock/project")
        self.manager = PackManager(self.project_dir)

    @patch("shared.pack_lab.subprocess.run")
    @patch("shared.pack_lab.Path.is_file")
    def test_get_files(self, mock_is_file, mock_run):
        # Mock git output
        mock_run.side_effect = [
            MagicMock(stdout="file1.py\ndir/file2.md\n", returncode=0),
            MagicMock(stdout="untracked.txt\n", returncode=0)
        ]
        mock_is_file.return_value = True

        # Mock binary check to be False for text files
        with patch.object(self.manager, '_is_binary', return_value=False):
            files = self.manager.get_files()

        self.assertEqual(len(files), 3)
        self.assertEqual(files[0], self.project_dir / "dir/file2.md")
        self.assertEqual(files[1], self.project_dir / "file1.py")
        self.assertEqual(files[2], self.project_dir / "untracked.txt")

    @patch("shared.pack_lab.subprocess.run")
    @patch("shared.pack_lab.Path.is_file")
    def test_get_files_with_patterns(self, mock_is_file, mock_run):
        mock_run.side_effect = [
            MagicMock(stdout="file1.py\ndir/file2.md\ntests/test1.py\n", returncode=0),
            MagicMock(stdout="untracked.txt\n", returncode=0)
        ]
        mock_is_file.return_value = True

        with patch.object(self.manager, '_is_binary', return_value=False):
            files = self.manager.get_files(include_patterns=["*.py"], exclude_patterns=["tests/*"])

        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], self.project_dir / "file1.py")

    def test_pack_markdown(self):
        mock_file1 = MagicMock()
        mock_file1.relative_to.return_value = "file1.py"
        mock_file1.read_text.return_value = "print('hello')"
        mock_file1.suffix = ".py"

        result = self.manager._pack_markdown([mock_file1])
        expected = "### File: file1.py\n```py\nprint('hello')\n```\n"
        self.assertEqual(result, expected)

    def test_pack_xml(self):
        mock_file1 = MagicMock()
        mock_file1.relative_to.return_value = "file1.py"
        mock_file1.read_text.return_value = "print('<hello>')"

        result = self.manager._pack_xml([mock_file1])
        self.assertIn('<file path="file1.py">', result)
        self.assertIn("<![CDATA[\nprint('<hello>')\n]]>", result)
        self.assertIn("</repository>", result)

    @patch("shared.pack_lab.PackManager.get_files")
    @patch("shared.pack_lab.PackManager.pack")
    def test_run_pack_logic_stdout(self, mock_pack, mock_get_files):
        mock_args = MagicMock()
        mock_args.project_dir = self.project_dir
        mock_args.include = "*.py"
        mock_args.exclude = None
        mock_args.format = "markdown"
        mock_args.output = None

        mock_get_files.return_value = [self.project_dir / "file1.py"]
        mock_pack.return_value = "mock_output"

        with patch("sys.stdout") as mock_stdout:
            result = run_pack_logic(mock_args)
            self.assertTrue(result)
            mock_pack.assert_called_once_with([self.project_dir / "file1.py"], format="markdown")

    @patch("shared.pack_lab.PackManager.get_files")
    @patch("shared.pack_lab.PackManager.pack")
    @patch("shared.pack_lab.Path.write_text")
    def test_run_pack_logic_file(self, mock_write_text, mock_pack, mock_get_files):
        mock_args = MagicMock()
        mock_args.project_dir = self.project_dir
        mock_args.include = None
        mock_args.exclude = None
        mock_args.format = "xml"
        mock_args.output = "output.xml"

        mock_get_files.return_value = [self.project_dir / "file1.py"]
        mock_pack.return_value = "mock_xml_output"

        result = run_pack_logic(mock_args)
        self.assertTrue(result)
        mock_write_text.assert_called_once_with("mock_xml_output", encoding='utf-8')

if __name__ == '__main__':
    unittest.main()
