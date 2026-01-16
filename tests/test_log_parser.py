import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from shared.log_parser import parse_log_file

class TestLogParser(unittest.TestCase):
    @patch('shared.log_parser.Path')
    def test_parse_log_file(self, MockPath):
        # 1. Define the mock log content
        log_content = """2023-10-27 10:00:00 - INFO -
THOUGHTS:
I need to create a simple Flask application.
First, I will create a file named `app.py`.
Then, I will write the basic Flask "Hello, World!" code into it.
Finally, I will create a `requirements.txt` file and add `Flask` to it.

COMMAND:
write_file(filepath="app.py", content="from flask import Flask\\n\\napp = Flask(__name__)\\n\\n@app.route('/')\\ndef hello_world():\\n    return 'Hello, World!'\\n\\nif __name__ == '__main__':\\n    app.run(debug=True)\\n")

FILES:
/app/app.py

2023-10-27 10:00:05 - INFO -
THOUGHTS:
Now that I have the main application file, I need to create the `requirements.txt` file so that the user can install the necessary dependencies.

COMMAND:
write_file(filepath="requirements.txt", content="Flask")

FILES:
/app/requirements.txt

2023-10-27 10:00:10 - INFO -
THOUGHTS:
I have created both files. I should now install the dependencies and then run the application to verify it works.

COMMAND:
run_in_bash_session(command="pip install -r requirements.txt")

2023-10-27 10:00:15 - INFO -
COMMAND:
run_in_bash_session(command="python app.py &")

2023-10-27 10:00:20 - INFO -
THOUGHTS:
The application should be running now. I will mark the task as complete.
COMMAND:
finish()
"""
        # 2. Configure the mock to simulate the file existing and having content
        mock_log_path = MagicMock()
        mock_log_path.exists.return_value = True
        mock_log_path.read_text.return_value = log_content

        # This complex line mocks the expression `Path(__file__).parent.parent / f"agents/logs/{run_id}.log"`
        # It ensures that when the code builds this path, the final object is our mock_log_path
        MockPath.return_value.parent.parent.__truediv__.return_value = mock_log_path

        # 3. Parse the log file using the mocked Path object
        steps = parse_log_file("test_log", Path("."))

        # 4. Check the results
        self.assertEqual(len(steps), 5)
        self.assertEqual(steps[0].timestamp, "2023-10-27 10:00:00")
        self.assertIn("I need to create a simple Flask application.", steps[0].thoughts)
        self.assertIn("write_file", steps[0].command)
        self.assertEqual(steps[0].files, ["/app/app.py"])
        self.assertEqual(steps[4].command, "finish()")

if __name__ == '__main__':
    unittest.main()
