import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import shutil
import tempfile
import sys
import json

# Ensure shared module is available
sys.path.append(str(Path(__file__).parent.parent))

from shared.scaffold import ScaffoldManager

class TestScaffoldAI(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.manager = ScaffoldManager(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("agents.gemini.GeminiAgent")
    async def test_generate_ai_scaffold(self, mock_agent_cls):
        # Mock agent response
        mock_agent = mock_agent_cls.return_value
        expected_json = {
            "main.py": "print('hello')",
            "test.py": "assert True"
        }
        mock_response = "```json\n" + json.dumps(expected_json) + "\n```"
        mock_agent.run_agent_session = AsyncMock(return_value=(True, mock_response, []))

        result = await self.manager.generate_ai_scaffold("Test app")

        self.assertEqual(result, expected_json)
        mock_agent.run_agent_session.assert_awaited()

    def test_create_from_plan(self):
        plan = {
            "app/main.py": "print('hello')",
            "requirements.txt": "flask"
        }

        success = self.manager.create_from_plan(plan)

        self.assertTrue(success)
        self.assertTrue((self.test_dir / "app/main.py").exists())
        self.assertTrue((self.test_dir / "requirements.txt").exists())

        self.assertEqual((self.test_dir / "app/main.py").read_text(encoding="utf-8").strip(), "print('hello')")

    def test_create_from_plan_security(self):
        # Test that writing outside project dir is prevented
        plan = {
            "../outside.txt": "evil content",
            "/tmp/evil.txt": "evil content",
            "safe.txt": "good content"
        }

        success = self.manager.create_from_plan(plan)

        self.assertTrue(success) # It should still return True if it processed the safe file
        self.assertFalse((self.test_dir.parent / "outside.txt").exists())
        self.assertTrue((self.test_dir / "safe.txt").exists())

if __name__ == "__main__":
    unittest.main()
