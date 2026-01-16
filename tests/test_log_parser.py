import unittest
from shared.log_parser import parse_log_file, LogStep

class TestLogParser(unittest.TestCase):

    def test_parse_log_file_with_single_step(self):
        log_content = """
13:42:12 - INFO - Sending prompt to Gemini...
13:42:12 - DEBUG - Sending Augmented Prompt:
## YOUR ROLE - CODING AGENT
This is the thought process.
---
13:42:12 - DEBUG - Starting gemini subprocess...
This is the action part.
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 1)
        self.assertIsInstance(steps[0], LogStep)
        self.assertIn("This is the thought process.", steps[0].thought)
        self.assertIn("This is the action part.", steps[0].action)
        self.assertNotIn("This is the thought process.", steps[0].action)

    def test_parse_log_file_with_multiple_steps(self):
        log_content = """
13:42:12 - INFO - Sending prompt to Gemini...
13:42:12 - DEBUG - Sending Augmented Prompt:
Thought 1
---
Action 1
13:42:12 - INFO - Sending prompt to Gemini...
13:42:12 - DEBUG - Sending Augmented Prompt:
Thought 2
---
Action 2
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 2)
        self.assertIn("Thought 1", steps[0].thought)
        self.assertIn("Action 1", steps[0].action)
        self.assertNotIn("Thought 1", steps[0].action)
        self.assertIn("Thought 2", steps[1].thought)
        self.assertIn("Action 2", steps[1].action)
        self.assertNotIn("Thought 2", steps[1].action)

    def test_parse_log_file_with_no_steps(self):
        log_content = "Just some random log content without any steps."
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 0)

    def test_parse_log_file_with_empty_content(self):
        log_content = ""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 0)

if __name__ == '__main__':
    unittest.main()
