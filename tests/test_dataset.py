import unittest
import tempfile
import json
import shutil
from pathlib import Path
from shared.dataset import LogParser, DatasetGenerator

class TestLogParser(unittest.TestCase):
    def test_parse_log(self):
        log_content = """
10:00:00 - DEBUG - Sending Augmented Prompt:
User Prompt content here
10:00:01 - INFO - Received response from Gemini.
10:00:01 - DEBUG - Response:
Assistant Response here
10:00:02 - INFO - Some other log
"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tf:
            tf.write(log_content)
            tf_path = Path(tf.name)

        try:
            parser = LogParser()
            interactions = parser.parse(tf_path)
            self.assertEqual(len(interactions), 1)
            self.assertEqual(interactions[0]['prompt'], "User Prompt content here")
            self.assertEqual(interactions[0]['response'], "Assistant Response here")
        finally:
            tf_path.unlink()

class TestDatasetGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

        # Mock logs directory
        self.logs_dir = self.project_dir / "agents/logs"
        self.logs_dir.mkdir(parents=True)

        # Create a sample log file
        self.run_id = "run-123"
        self.log_file = self.logs_dir / f"{self.run_id}.log"
        self.log_file.write_text("""
10:00:00 - DEBUG - Sending Augmented Prompt:
Prompt 1
10:00:01 - DEBUG - Response:
Response 1
""")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_from_run_id(self):
        generator = DatasetGenerator(self.project_dir, logs_dir=self.logs_dir)
        output_file = self.project_dir / "dataset.jsonl"

        count = generator.generate(output_file, run_id=self.run_id)

        self.assertEqual(count, 1)
        self.assertTrue(output_file.exists())

        content = output_file.read_text()
        data = json.loads(content)
        self.assertEqual(data["messages"][0]["content"], "Prompt 1")
        self.assertEqual(data["messages"][1]["content"], "Response 1")

    def test_generate_all(self):
        # Add history file
        history_file = self.project_dir / ".agent_history"
        history_file.write_text(f"{self.run_id}\n")

        # Add another log not in history
        (self.logs_dir / "other.log").write_text("""
10:00:00 - DEBUG - Sending Augmented Prompt:
Prompt 2
10:00:01 - DEBUG - Response:
Response 2
""")

        generator = DatasetGenerator(self.project_dir, logs_dir=self.logs_dir)
        output_file = self.project_dir / "dataset_all.jsonl"

        # Should pick up both (one from history, one from glob because we check glob too in `all_runs` branch)
        count = generator.generate(output_file, all_runs=True)

        self.assertEqual(count, 2)
