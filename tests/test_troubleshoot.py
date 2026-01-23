import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from shared.troubleshoot import TroubleshootManager, run_troubleshoot_logic

class TestTroubleshootManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test")

        # Patch verify checks
        self.patcher_lint = patch("shared.troubleshoot.run_lint")
        self.mock_lint = self.patcher_lint.start()

        self.patcher_tests = patch("shared.troubleshoot.run_tests")
        self.mock_tests = self.patcher_tests.start()

        self.patcher_type = patch("shared.troubleshoot.run_type_check")
        self.mock_type = self.patcher_type.start()

        # Patch KnowledgeManager
        self.patcher_km = patch("shared.troubleshoot.KnowledgeManager")
        self.mock_km_cls = self.patcher_km.start()
        self.mock_km = self.mock_km_cls.return_value

        # Patch Agent config to avoid real API calls init
        self.patcher_config = patch("shared.troubleshoot.Config")
        self.patcher_config.start()

        # We need to patch GeminiAgent to mock run_agent_session
        self.patcher_agent = patch("shared.troubleshoot.GeminiAgent")
        self.mock_agent_cls = self.patcher_agent.start()
        self.mock_agent = self.mock_agent_cls.return_value
        self.mock_agent.run_agent_session = AsyncMock(return_value=("done", "Diagnosis: It's broken.\nFix: Fix it.", []))

    def tearDown(self):
        patch.stopall()

    def test_detect_issues_clean(self):
        self.mock_lint.return_value = {"success": True}
        self.mock_tests.return_value = {"success": True}
        self.mock_type.return_value = {"success": True}

        manager = TroubleshootManager(self.project_dir)
        issues = manager.detect_issues()
        self.assertEqual(len(issues), 0)

    def test_detect_issues_fail(self):
        self.mock_lint.return_value = {"success": False, "stdout": "Lint Error", "stderr": ""}
        self.mock_tests.return_value = {"success": True}
        self.mock_type.return_value = {"success": False, "stdout": "Type Error", "stderr": ""}

        manager = TroubleshootManager(self.project_dir)
        issues = manager.detect_issues()
        self.assertEqual(len(issues), 2)
        self.assertIn("lint", issues)
        self.assertIn("type", issues)

    async def test_diagnose(self):
        manager = TroubleshootManager(self.project_dir)

        issues = {"lint": {"stdout": "some_error_string", "stderr": ""}}
        self.mock_km.list_knowledge.return_value = []

        response = await manager.diagnose(issues)

        self.mock_agent.run_agent_session.assert_called_once()
        args = self.mock_agent.run_agent_session.call_args[0][0]
        self.assertIn("some_error_string", args)
        self.assertEqual(response, "Diagnosis: It's broken.\nFix: Fix it.")

    async def test_apply_fix(self):
        manager = TroubleshootManager(self.project_dir)
        await manager.apply_fix()
        self.mock_agent.run_agent_session.assert_called()
        args = self.mock_agent.run_agent_session.call_args[0][0]
        self.assertIn("apply the fix", args)

    def test_learn(self):
        manager = TroubleshootManager(self.project_dir)
        manager.learn("Issue A", "Fix B")
        self.mock_km.add_knowledge.assert_called_once()

    @patch("builtins.input", side_effect=["y", "y"]) # Apply fix? Yes. Learn? Yes.
    async def test_run_logic_interactive(self, mock_input):
        # Initial detection fails
        self.mock_lint.side_effect = [
            {"success": False, "stdout": "Lint Error"}, # First call
            {"success": True}                           # Second call (Verify)
        ]
        self.mock_tests.return_value = {"success": True}
        self.mock_type.return_value = {"success": True}

        await run_troubleshoot_logic(self.project_dir)

        # Verify call count
        # 1. Detect (fails)
        # 2. Diagnose
        # 3. Apply
        # 4. Detect (passes)
        # 5. Learn
        self.assertEqual(self.mock_lint.call_count, 2)
        self.mock_km.add_knowledge.assert_called()

if __name__ == "__main__":
    unittest.main()
