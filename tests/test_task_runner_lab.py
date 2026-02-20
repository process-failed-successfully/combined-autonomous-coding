import unittest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from shared.task_runner_lab import TaskRunnerManager, Task

class TestTaskRunnerManager(unittest.TestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/mock_project")
        self.manager = TaskRunnerManager(self.project_dir)

    def test_scan_makefile(self):
        makefile_content = """
target1:
\techo hello

target2: dependency
\techo world

.PHONY: clean
clean:
\trm -rf *
"""
        with patch.object(Path, "exists") as mock_exists:
            with patch.object(Path, "read_text") as mock_read:
                mock_exists.return_value = True
                mock_read.return_value = makefile_content

                tasks = self.manager._scan_makefile()

                self.assertEqual(len(tasks), 3)
                self.assertEqual(tasks[0].name, "target1")
                self.assertEqual(tasks[0].script_key, "target1")
                self.assertEqual(tasks[0].command, "make target1")
                self.assertEqual(tasks[1].name, "target2")
                self.assertEqual(tasks[2].name, "clean")

    def test_scan_package_json(self):
        package_json_content = '{"scripts": {"start": "node index.js", "test:unit": "jest"}}'

        def exists_side_effect(self):
            path_str = str(self)
            if path_str.endswith("package.json"):
                return True
            return False

        with patch("builtins.open", mock_open(read_data=package_json_content)):
            with patch.object(Path, "exists", autospec=True, side_effect=exists_side_effect):

                tasks = self.manager._scan_package_json()

                # We expect package.json and ui/package.json to exist
                self.assertEqual(len(tasks), 4)

                # Check first file (root)
                self.assertEqual(tasks[0].name, "start")
                self.assertEqual(tasks[0].script_key, "start")
                self.assertEqual(tasks[0].command, "node index.js")
                self.assertTrue("npm" in tasks[0].source)

                # Check complex name
                self.assertEqual(tasks[1].name, "test:unit")
                self.assertEqual(tasks[1].script_key, "test:unit")

    def test_scan_pyproject_toml(self):
        toml_content = {
            "tool": {
                "poetry": {
                    "scripts": {
                        "run-server": "python server.py",
                        "lint": "flake8"
                    }
                }
            }
        }

        with patch("shared.task_runner_lab.tomlkit.load") as mock_toml_load:
            # We also need to mock open because _scan_pyproject_toml opens the file
            with patch("builtins.open", mock_open(read_data="")):
                with patch.object(Path, "exists", return_value=True):
                    mock_toml_load.return_value = toml_content

                    tasks = self.manager._scan_pyproject_toml()

                    self.assertEqual(len(tasks), 2)
                    self.assertEqual(tasks[0].name, "run-server")
                    self.assertEqual(tasks[0].script_key, "run-server")
                    self.assertEqual(tasks[0].command, "poetry run run-server")
                    self.assertEqual(tasks[0].source, "poetry")

    def test_list_tasks(self):
        # Mock individual scan methods
        with patch.object(self.manager, "_scan_makefile", return_value=[Task("Make", "clean", "make clean", "", "clean")]), \
             patch.object(self.manager, "_scan_package_json", return_value=[Task("npm", "test", "npm test", "", "test")]), \
             patch.object(self.manager, "_scan_pyproject_toml", return_value=[]):

             tasks = self.manager.list_tasks()
             self.assertEqual(len(tasks), 2)

    def test_run_task_command_construction(self):
        # Test npm command construction with script_key
        task = Task(source="npm (root)", name="ui:test:unit", command="jest", file_path="/tmp/package.json", script_key="test:unit")

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = ["output"]
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            self.manager.run_task(task)

            # Check args
            args, kwargs = mock_popen.call_args
            cmd = args[0]
            # Should use script_key "test:unit", not try to split name "ui:test:unit"
            self.assertEqual(cmd, "npm run test:unit")
            self.assertEqual(kwargs["cwd"], Path("/tmp"))

    def test_run_task_makefile(self):
        task = Task(source="Makefile", name="build", command="make build", file_path="/tmp/Makefile", script_key="build")

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.stdout = []
            mock_process.returncode = 0
            mock_popen.return_value = mock_process

            self.manager.run_task(task)

            args, kwargs = mock_popen.call_args
            self.assertEqual(args[0], "make build")
