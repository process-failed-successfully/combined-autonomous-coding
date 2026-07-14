import unittest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import sys
from pathlib import Path

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from shared.docker_lab import run_docker_lab_logic

class TestDockerLabCLI(unittest.TestCase):

    @patch('shared.docker_lab.DockerLabManager')
    def test_ps_action(self, mock_manager_cls):
        mock_lab = mock_manager_cls.return_value
        args = Namespace(action="ps")

        run_docker_lab_logic(args)

        mock_lab.list_containers.assert_called_once()

    @patch('shared.docker_lab.DockerLabManager')
    def test_images_action(self, mock_manager_cls):
        mock_lab = mock_manager_cls.return_value
        args = Namespace(action="images")

        run_docker_lab_logic(args)

        mock_lab.list_images.assert_called_once()

    @patch('shared.docker_lab.DockerLabManager')
    def test_start_action(self, mock_manager_cls):
        mock_lab = mock_manager_cls.return_value
        mock_lab.manager.start_container.return_value = True
        args = Namespace(action="start", container="123")

        run_docker_lab_logic(args)

        mock_lab.manager.start_container.assert_called_once_with("123")

    @patch('shared.docker_lab.DockerLabManager')
    def test_rm_action(self, mock_manager_cls):
        mock_lab = mock_manager_cls.return_value
        mock_lab.manager.remove_container.return_value = True
        args = Namespace(action="rm", container="123", force=True)

        run_docker_lab_logic(args)

        mock_lab.manager.remove_container.assert_called_once_with("123", force=True)

    @patch('shared.docker_lab.DockerLabManager')
    @patch('builtins.input', return_value='y')
    def test_prune_action(self, mock_input, mock_manager_cls):
        mock_lab = mock_manager_cls.return_value
        mock_lab.manager.prune_containers.return_value = True
        mock_lab.manager.prune_images.return_value = True

        args = Namespace(action="prune", what="all", force=False)

        run_docker_lab_logic(args)

        mock_lab.manager.prune_containers.assert_called_once()
        mock_lab.manager.prune_images.assert_called_once()

    @patch('shared.docker_lab.DockerLabManager')
    def test_inspect_action(self, mock_manager_cls):
        mock_lab = mock_manager_cls.return_value
        args = Namespace(action="inspect", container="123")

        run_docker_lab_logic(args)

        mock_lab.inspect.assert_called_once_with("123")

    @patch('shared.docker_lab.DockerLabManager')
    def test_stats_action(self, mock_manager_cls):
        mock_lab = mock_manager_cls.return_value
        args = Namespace(action="stats", container="123")

        run_docker_lab_logic(args)

        mock_lab.stats.assert_called_once_with("123")

    @patch('main.run_tui')
    def test_tui_action(self, mock_run_tui):
        args = Namespace(action="tui")

        run_docker_lab_logic(args)

        mock_run_tui.assert_called_once_with(args, start_tab="tab-docker")

if __name__ == '__main__':
    unittest.main()
