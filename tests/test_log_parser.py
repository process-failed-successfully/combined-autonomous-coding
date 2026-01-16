
import unittest
from pathlib import Path
import tempfile
import shutil
from shared.log_parser import LogParser

class TestLogParser(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.log_file = Path(self.test_dir) / "test.log"
        self.log_content = """21:26:32 - INFO - ==================================================
21:26:32 - INFO -   SESSION 1 (INITIALIZATION)
21:26:32 - INFO - ==================================================

21:26:32 - INFO - Starting Gemini Agent on .
21:26:33 - INFO - Generated Agent ID: test-agent-123
21:26:35 - INFO - THOUGHT: I need to initialize the project.
21:26:35 - INFO - PLAN: 1. Check git status.
2. Create app_spec.txt
21:26:35 - INFO - COMMAND: git status
"""
        with open(self.log_file, "w") as f:
            f.write(self.log_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parse(self):
        parser = LogParser(self.log_file)
        steps = parser.parse()
        self.assertEqual(len(steps), 8)
        self.assertEqual(steps[0]["timestamp"], "21:26:32")
        self.assertTrue("SESSION 1" in steps[1]["message"])
        self.assertEqual(steps[7]["message"], "COMMAND: git status")

    def test_extract_turns(self):
        parser = LogParser(self.log_file)
        steps = parser.parse()
        turns = parser.extract_agent_turns(steps)

        # Depending on implementation, the first few logs might be part of turn 0 or pre-turn
        # Our implementation creates a new turn on "SESSION"

        self.assertTrue(len(turns) >= 1)

        # Find the turn with thoughts and commands
        turn = None
        for t in turns:
            for log in t["logs"]:
                if "THOUGHT:" in log["message"]:
                    turn = t
                    break

        self.assertIsNotNone(turn)
        self.assertIn("thought", turn)
        self.assertIn("plan", turn)
        self.assertIn("command", turn)

if __name__ == '__main__':
    unittest.main()
