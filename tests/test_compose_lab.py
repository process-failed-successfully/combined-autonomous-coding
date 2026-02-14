import unittest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import sys
from pathlib import Path

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from shared.compose_lab import run_compose_lab_logic, ComposeLabManager

class TestComposeLab(unittest.TestCase):

    @patch('shared.compose_lab.subprocess.run')
    def test_up_action(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        args = Namespace(
            action="up",
            detach=True,
            build=False,
            services=None,
            project_dir="."
        )

        run_compose_lab_logic(args)

        # Verify the command call
        # docker compose up -d
        mock_run.assert_called_with(
            ["docker", "compose", "up", "-d"],
            cwd=".",
            capture_output=False,
            text=True
        )

    @patch('shared.compose_lab.subprocess.run')
    def test_up_action_attached(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        args = Namespace(
            action="up",
            detach=False,
            build=False,
            services=None,
            project_dir="."
        )

        run_compose_lab_logic(args)

        # Verify the command call (no -d)
        mock_run.assert_called_with(
            ["docker", "compose", "up"],
            cwd=".",
            capture_output=False,
            text=True
        )

    @patch('shared.compose_lab.subprocess.run')
    def test_up_action_with_build_and_services(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        args = Namespace(
            action="up",
            detach=False,
            build=True,
            services=["web", "db"],
            project_dir="./myproject"
        )

        run_compose_lab_logic(args)

        # docker compose up --build web db
        # Note: detached is False, so no -d
        mock_run.assert_called_with(
            ["docker", "compose", "up", "--build", "web", "db"],
            cwd="./myproject",
            capture_output=False,
            text=True
        )

    @patch('shared.compose_lab.subprocess.run')
    def test_down_action(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        args = Namespace(
            action="down",
            volumes=True,
            remove_orphans=False,
            project_dir="."
        )

        run_compose_lab_logic(args)

        mock_run.assert_called_with(
            ["docker", "compose", "down", "-v"],
            cwd=".",
            capture_output=False,
            text=True
        )

    @patch('shared.compose_lab.subprocess.run')
    def test_ps_action_json_lines(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"Name":"foo", "Service":"bar", "State":"running", "Status":"Up"}'
        )
        args = Namespace(
            action="ps",
            all=False,
            project_dir="."
        )

        run_compose_lab_logic(args)

        mock_run.assert_called_with(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=".",
            capture_output=True,
            text=True
        )

    @patch('shared.compose_lab.subprocess.run')
    def test_ps_action_json_array(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"Name":"foo", "Service":"bar", "State":"running", "Status":"Up"}]'
        )
        args = Namespace(
            action="ps",
            all=False,
            project_dir="."
        )

        run_compose_lab_logic(args)

        mock_run.assert_called_with(
            ["docker", "compose", "ps", "--format", "json"],
            cwd=".",
            capture_output=True,
            text=True
        )

    @patch('shared.compose_lab.subprocess.run')
    def test_exec_action(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        args = Namespace(
            action="exec",
            service="web",
            command_args=["ls", "-la"],
            project_dir="."
        )

        run_compose_lab_logic(args)

        mock_run.assert_called_with(
            ["docker", "compose", "exec", "web", "ls", "-la"],
            cwd=".",
            check=True
        )

if __name__ == '__main__':
    unittest.main()
