# tests/test_log_parser.py

import unittest
from shared.log_parser import parse_log_file, CodeBlock, LogStep

class TestLogParser(unittest.TestCase):
    def test_parse_log_file_with_multiple_turns(self):
        log_content = """
2024-07-22 10:00:00,123 - INFO - Sending prompt to Gemini...
2024-07-22 10:00:05,457 - DEBUG - Response:
This is the first thought.
```bash
echo "hello"
```
2024-07-22 10:00:05,458 - INFO - Processing response blocks...
2024-07-22 10:00:10,123 - INFO - Sending prompt to Gemini...
2024-07-22 10:00:15,457 - DEBUG - Response:
This is the second thought.
```write:hello.txt
hello world
```
2024-07-22 10:00:15,458 - INFO - Processing response blocks...
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 2)

        self.assertEqual(steps[0].thought, "This is the first thought.")
        self.assertEqual(len(steps[0].actions), 1)
        self.assertEqual(steps[0].actions[0].type, "bash")
        self.assertEqual(steps[0].actions[0].content, 'echo "hello"')

        self.assertEqual(steps[1].thought, "This is the second thought.")
        self.assertEqual(len(steps[1].actions), 1)
        self.assertEqual(steps[1].actions[0].type, "write:hello.txt")
        self.assertEqual(steps[1].actions[0].content, "hello world")

    def test_parse_log_file_with_no_actions(self):
        log_content = """
2024-07-22 10:00:00,123 - INFO - Sending prompt to Gemini...
2024-07-22 10:00:05,457 - DEBUG - Response:
This is a thought with no actions.
2024-07-22 10:00:05,458 - INFO - Processing response blocks...
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].thought, "This is a thought with no actions.")
        self.assertEqual(len(steps[0].actions), 0)

    def test_parse_log_file_with_multiple_actions(self):
        log_content = """
2024-07-22 10:00:00,123 - INFO - Sending prompt to Gemini...
2024-07-22 10:00:05,457 - DEBUG - Response:
This is a thought with multiple actions.
```bash
echo "action 1"
```
```write:file.txt
action 2
```
2024-07-22 10:00:05,458 - INFO - Processing response blocks...
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].thought, "This is a thought with multiple actions.")
        self.assertEqual(len(steps[0].actions), 2)
        self.assertEqual(steps[0].actions[0].type, "bash")
        self.assertEqual(steps[0].actions[0].content, 'echo "action 1"')
        self.assertEqual(steps[0].actions[1].type, "write:file.txt")
        self.assertEqual(steps[0].actions[1].content, "action 2")

    def test_empty_log_file(self):
        steps = parse_log_file("")
        self.assertEqual(len(steps), 0)

if __name__ == '__main__':
    unittest.main()
