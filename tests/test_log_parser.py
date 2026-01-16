
import unittest
from shared.log_parser import parse_log_file

class TestLogParser(unittest.TestCase):
    def test_parse_log_file(self):
        log_content = """2024-07-15 10:00:00,123 - INFO - Thinking:
        This is a thought.
        It has multiple lines.
2024-07-15 10:00:01,456 - INFO - Tool Call:
        tool_name --arg1 value1
2024-07-15 10:00:02,789 - INFO - Tool Output:
        Some output from the tool.
"""
        steps = parse_log_file(log_content)
        self.assertEqual(len(steps), 3)

        self.assertEqual(steps[0]['type'], 'Thinking')
        self.assertEqual(steps[0]['content'], 'This is a thought.\n        It has multiple lines.')

        self.assertEqual(steps[1]['type'], 'Tool Call')
        self.assertEqual(steps[1]['content'], 'tool_name --arg1 value1')

        self.assertEqual(steps[2]['type'], 'Tool Output')
        self.assertEqual(steps[2]['content'], 'Some output from the tool.')

if __name__ == '__main__':
    unittest.main()
