import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from shared.cheatsheet_lab import CheatsheetManager

class TestCheatsheetLab(unittest.TestCase):
    def test_list_topics(self):
        manager = CheatsheetManager()
        topics = manager.list_topics()
        self.assertIn("git", topics)
        self.assertIn("python", topics)

    def test_get_content(self):
        manager = CheatsheetManager()
        content = manager.get_content("git")
        self.assertIsNotNone(content)
        self.assertIn("git init", content)

    def test_search(self):
        manager = CheatsheetManager()
        results = manager.search("py")
        self.assertIn("python", results)

    def test_user_cheatsheet(self):
        with TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            user_dir = project_dir / ".cheatsheets"
            user_dir.mkdir()
            (user_dir / "custom.md").write_text("# Custom\nContent", encoding="utf-8")

            manager = CheatsheetManager(project_dir)
            topics = manager.list_topics()
            self.assertIn("custom", topics)

            content = manager.get_content("custom")
            self.assertEqual(content, "# Custom\nContent")
