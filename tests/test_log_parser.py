import unittest
import tempfile
import sys
from pathlib import Path

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.log_explorer import LogParser, AgentStep

class TestLogParser(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.test_dir.name) / "test.log"

        self.log_content = """10:00:01 - INFO - Start
10:00:02 - INFO - Sending prompt
Multi-line
Prompt content
10:00:03 - ERROR - Error occurred
Traceback (most recent call last):
  File "main.py", line 1, in <module>
10:00:04 - INFO - End
"""
        self.log_path.write_text(self.log_content)
        self.parser = LogParser()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_parse_entries(self):
        entries = self.parser._parse_entries(self.log_path)
        self.assertEqual(len(entries), 4)

        self.assertEqual(entries[0].message, "Start")
        self.assertEqual(entries[1].message, "Sending prompt\nMulti-line\nPrompt content")
        self.assertEqual(entries[2].level, "ERROR")
        self.assertIn("Traceback", entries[2].message)

    def test_group_steps(self):
        steps = self.parser.parse_run(self.log_path)
        self.assertEqual(len(steps), 4)

        self.assertEqual(steps[1].type, "THOUGHT") # "Sending prompt"
        self.assertEqual(steps[2].type, "ERROR")

    def test_empty_file(self):
        empty_log = Path(self.test_dir.name) / "empty.log"
        empty_log.touch()
        steps = self.parser.parse_run(empty_log)
        self.assertEqual(steps, [])

if __name__ == "__main__":
    unittest.main()
