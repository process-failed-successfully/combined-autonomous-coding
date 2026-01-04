
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
from pathlib import Path
from agents.shared.sprint import SprintManager, Task
from shared.config import Config
import tempfile
import shutil
import os

class TestSprintGuardrail(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_sprint_guardrail_")
        self.project_dir = Path(self.tmp_dir)
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.feature_list = self.project_dir / "feature_list.json"
        self.feature_list.write_text("[]")
        self.config = Config(project_dir=self.project_dir)
        with patch("agents.shared.sprint.WorktreeManager") as MockWT:
            self.manager = SprintManager(self.config)
            self.manager.worktree_manager = MockWT.return_value
            self.manager.worktree_manager.create_worktree.return_value = self.project_dir # Mock returning project dir as worktree path

    def tearDown(self):
        if hasattr(self, "tmp_dir") and os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    @patch("agents.shared.sprint.shutil.copy")
    @patch("agents.shared.sprint.get_sprint_coding_prompt")
    @patch("agents.shared.sprint.SprintManager._get_agent_runner")
    def test_worker_loop_detection(self, mock_get_runner, mock_prompt, mock_copy):
        # Setup
        mock_client = MagicMock()
        mock_runner = AsyncMock()
        mock_get_runner.return_value = (mock_client, mock_runner)
        mock_prompt.return_value = "prompt"

        # Mock runner to return same action repeatedly
        # 1st call: action A
        # 2nd call: action A
        # 3rd call: action A -> Should trigger 3rd repetition count?
        # definition: if actions == last_actions.
        # 1. actions=A. last=[], update last=A
        # 2. actions=A. last=A. rep=1.
        # 3. actions=A. last=A. rep=2.
        # 4. actions=A. last=A. rep=3. -> trigger.
        # So we need 4 calls to trigger ">=3" if we start count at 0?
        # Logic implemented:
        # if actions == last_actions: rep += 1. if rep >=3: break.
        # Initial: rep=0, last=[]
        # Turn 1: actions=['a']. last=[]. match=False. rep=0. last=['a']
        # Turn 2: actions=['a']. last=['a']. match=True. rep=1.
        # Turn 3: actions=['a']. last=['a']. match=True. rep=2.
        # Turn 4: actions=['a']. last=['a']. match=True. rep=3. -> Break.

        mock_runner.return_value = ("continue", "response", ["view_file('foo.py')"])

        task = Task(id="t1", title="Test Task", description="desc")
        self.manager.running_tasks.add(task.id)

        # Run worker
        asyncio.run(self.manager.run_worker(task))

        # Assertions
        self.assertEqual(task.status, "FAILED")
        self.assertIn("t1", self.manager.failed_tasks)
        # Verify mocked runner was called 4 times
        self.assertEqual(mock_runner.call_count, 4)
        
        # Verify Context Copy (feature_list.json was created in setUp)
        self.assertTrue(mock_copy.called)

    @patch("agents.shared.sprint.shutil.copy")
    @patch("agents.shared.sprint.get_sprint_coding_prompt")
    @patch("agents.shared.sprint.SprintManager._get_agent_runner")
    def test_worker_no_loop_with_variation(self, mock_get_runner, mock_prompt, mock_copy):
        mock_client = MagicMock()
        mock_runner = AsyncMock()
        mock_get_runner.return_value = (mock_client, mock_runner)
        mock_prompt.return_value = "prompt"

        # Alternating actions
        mock_runner.side_effect = [
            ("continue", "r1", ["a"]),
            ("continue", "r2", ["b"]),
            ("continue", "r3", ["a"]),
            ("continue", "r4", ["b"]),
            ("done", "SPRINT_TASK_COMPLETE", ["c"]),
        ]

        task = Task(id="t2", title="Test Task 2", description="desc")
        self.manager.running_tasks.add(task.id)

        asyncio.run(self.manager.run_worker(task))

        self.assertEqual(task.status, "COMPLETED")
        self.assertEqual(mock_runner.call_count, 5)

    @patch("agents.shared.sprint.shutil.copy")
    @patch("agents.shared.sprint.get_sprint_coding_prompt")
    @patch("agents.shared.sprint.SprintManager._get_agent_runner")
    def test_runaway_output(self, mock_get_runner, mock_prompt, mock_copy):
        mock_client = MagicMock()
        mock_runner = AsyncMock()
        mock_get_runner.return_value = (mock_client, mock_runner)
        mock_prompt.return_value = "prompt"
        
        # Runaway output: "foo" repeated 30 times
        runaway_text = "foo " * 30
        mock_runner.return_value = ("continue", runaway_text, [])
        
        task = Task(id="t_runaway", title="Runaway Task", description="desc")
        self.manager.running_tasks.add(task.id)
        
        asyncio.run(self.manager.run_worker(task))
        
        self.assertEqual(task.status, "FAILED")
        self.assertIn("t_runaway", self.manager.failed_tasks)
        # Should detect immediately
        self.assertEqual(mock_runner.call_count, 1)

    @patch("agents.shared.sprint.shutil.copy")
    @patch("agents.shared.sprint.get_sprint_coding_prompt")
    @patch("agents.shared.sprint.SprintManager._get_agent_runner")
    def test_text_loop(self, mock_get_runner, mock_prompt, mock_copy):
        mock_client = MagicMock()
        mock_runner = AsyncMock()
        mock_get_runner.return_value = (mock_client, mock_runner)
        mock_prompt.return_value = "prompt"
        
        # Repetitive text with no actions
        # 4 identical calls
        mock_runner.return_value = ("continue", "I am thinking.", [])
        
        task = Task(id="t_text_loop", title="Text Loop Task", description="desc")
        self.manager.running_tasks.add(task.id)
        
        asyncio.run(self.manager.run_worker(task))
        
        self.assertEqual(task.status, "FAILED")
        self.assertIn("t_text_loop", self.manager.failed_tasks)
        self.assertEqual(mock_runner.call_count, 4) # 3 repetitions + initial = 4 calls? Actually logic:
        # Turn 1: rep=0. last="I am thinking."
        # Turn 2: rep=1.
        # Turn 3: rep=2.
        # Turn 4: rep=3 -> Break.
        
if __name__ == "__main__":
    unittest.main()
