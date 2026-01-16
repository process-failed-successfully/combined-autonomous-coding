import unittest
import shutil
from pathlib import Path
from shared.log_parser import parse_log_file

class TestLogParser(unittest.TestCase):
    def setUp(self):
        self.log_dir = Path("agents/logs")
        self.log_dir.mkdir(exist_ok=True)
        self.addCleanup(shutil.rmtree, self.log_dir, ignore_errors=True)

    def test_parse_log_file(self):
        # Create a mock log file
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
        log_dir = Path("agents/logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "test_log.log"
        log_file.write_text(log_content)

        # Parse the log file
        steps = parse_log_file("test_log", Path("."))

        # Check the results
        self.assertEqual(len(steps), 5)
        self.assertEqual(steps[0].timestamp, "2023-10-27 10:00:00")
        self.assertIn("I need to create a simple Flask application.", steps[0].thoughts)
        self.assertIn("write_file", steps[0].command)
        self.assertEqual(steps[0].files, ["/app/app.py"])
        self.assertEqual(steps[4].command, "finish()")

if __name__ == '__main__':
    unittest.main()
