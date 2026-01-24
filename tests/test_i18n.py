import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import json
import tempfile
import shutil
import os

from shared.i18n import I18nManager

class TestI18nManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.project_dir = Path(self.test_dir)
        self.locales_dir = self.project_dir / "locales"
        self.locales_dir.mkdir()
        self.manager = I18nManager(self.project_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("shared.i18n.GeminiAgent")
    async def test_translate_generates_file(self, MockAgent):
        # Setup source file
        source_file = self.locales_dir / "en.json"
        source_content = {"greeting": "Hello", "goodbye": "Goodbye"}
        source_file.write_text(json.dumps(source_content), encoding="utf-8")

        # Setup Mock Agent
        mock_agent_instance = MockAgent.return_value
        # run_agent_session returns (status, response, actions)
        # Mock response to be valid JSON
        mock_response = json.dumps({"greeting": "Hola", "goodbye": "Adios"})
        mock_agent_instance.run_agent_session = AsyncMock(return_value=("success", mock_response, []))

        # Run translation
        success = await self.manager.translate(
            source_file=source_file,
            target_langs=["es"],
            agent_type="gemini"
        )

        self.assertTrue(success)

        # Verify output file
        target_file = self.locales_dir / "es.json"
        self.assertTrue(target_file.exists())
        content = json.loads(target_file.read_text(encoding="utf-8"))
        self.assertEqual(content["greeting"], "Hola")
        self.assertEqual(content["goodbye"], "Adios")

    def test_verify_no_issues(self):
        source_file = self.locales_dir / "en.json"
        target_file = self.locales_dir / "es.json"

        source_file.write_text(json.dumps({"a": 1, "b": {"c": 2}}), encoding="utf-8")
        target_file.write_text(json.dumps({"a": "uno", "b": {"c": "dos"}}), encoding="utf-8")

        report = self.manager.verify(source_file, ["es"])
        self.assertEqual(report, {})

    def test_verify_missing_keys(self):
        source_file = self.locales_dir / "en.json"
        target_file = self.locales_dir / "es.json"

        source_file.write_text(json.dumps({"a": 1, "b": 2}), encoding="utf-8")
        target_file.write_text(json.dumps({"a": "uno"}), encoding="utf-8")

        report = self.manager.verify(source_file, ["es"])
        self.assertIn("es", report)
        self.assertTrue(any("Missing keys" in issue for issue in report["es"]))
        self.assertTrue(any("b" in issue for issue in report["es"]))

    def test_verify_extra_keys(self):
        source_file = self.locales_dir / "en.json"
        target_file = self.locales_dir / "es.json"

        source_file.write_text(json.dumps({"a": 1}), encoding="utf-8")
        target_file.write_text(json.dumps({"a": "uno", "b": "dos"}), encoding="utf-8")

        report = self.manager.verify(source_file, ["es"])
        self.assertIn("es", report)
        self.assertTrue(any("Extra keys" in issue for issue in report["es"]))
        self.assertTrue(any("b" in issue for issue in report["es"]))

if __name__ == "__main__":
    unittest.main()
