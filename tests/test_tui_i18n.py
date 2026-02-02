import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
import json
import io
import contextlib

from textual.widgets import Label, Button, DataTable, RichLog, Input, Select
from shared.tui_i18n import I18nTab

class TestI18nTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.project_dir = Path("/tmp/test_project")
        self.project_dir.mkdir(parents=True, exist_ok=True)

        # Mock I18nManager
        self.patcher_manager = patch("shared.tui_i18n.I18nManager")
        self.MockManager = self.patcher_manager.start()
        self.manager = self.MockManager.return_value

        self.tab = I18nTab(self.project_dir)

        # Mock query_one
        self.mock_source_input = MagicMock(spec=Input)
        self.mock_langs_input = MagicMock(spec=Input)
        self.mock_log = MagicMock(spec=RichLog)
        self.mock_table = MagicMock(spec=DataTable)
        self.mock_agent_select = MagicMock(spec=Select)
        self.mock_verify_btn = MagicMock(spec=Button)
        self.mock_translate_btn = MagicMock(spec=Button)

        self.tab.query_one = MagicMock(side_effect=lambda selector, type=None: {
            "#i18n-source-input": self.mock_source_input,
            "#i18n-langs-input": self.mock_langs_input,
            "#i18n-log": self.mock_log,
            "#i18n-table": self.mock_table,
            "#i18n-agent-select": self.mock_agent_select,
            "#btn-i18n-verify": self.mock_verify_btn,
            "#btn-i18n-translate": self.mock_translate_btn
        }.get(selector))

        # Mock notify
        self.tab.notify = MagicMock()

    def tearDown(self):
        self.patcher_manager.stop()

    def test_load_data_success(self):
        # Setup source file
        source_file = self.project_dir / "locales" / "en.json"
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_content = {"hello": "Hello", "world": "World"}
        source_file.write_text(json.dumps(source_content), encoding="utf-8")

        # Setup inputs
        self.mock_source_input.value = "locales/en.json"
        self.mock_langs_input.value = "es, fr"

        # Mock Manager behavior
        self.manager.flatten_keys.return_value = ["hello", "world"]

        self.tab.load_data()

        # Checks
        self.mock_table.clear.assert_called_with(columns=True)
        self.mock_table.add_columns.assert_called_with("Key", "Source", "es", "fr")
        self.assertEqual(self.mock_table.add_row.call_count, 2) # 2 keys
        self.mock_verify_btn.disabled = False
        self.mock_translate_btn.disabled = False
        self.mock_log.write.assert_called()

    def test_load_data_file_not_found(self):
        self.mock_source_input.value = "missing.json"
        self.tab.load_data()
        self.tab.notify.assert_called_with(f"File not found: {self.project_dir / 'missing.json'}", severity="error")

    def test_verify_translations(self):
        self.tab.source_file = self.project_dir / "locales/en.json"
        self.tab.target_langs = ["es"]

        self.manager.verify.return_value = {"es": ["Missing key: hello"]}

        self.tab.verify_translations()

        self.manager.verify.assert_called_with(self.tab.source_file, ["es"])
        self.mock_log.write.assert_any_call("Verifying translations...")
        self.mock_log.write.assert_any_call("[yellow]Issues found:[/yellow]")

    async def test_translate_missing(self):
        self.tab.source_file = self.project_dir / "locales/en.json"
        self.tab.target_langs = ["es"]
        self.mock_agent_select.value = "cursor"

        self.manager.translate = AsyncMock(return_value=True)

        # Mock load_data to avoid re-running logic
        with patch.object(self.tab, "load_data") as mock_load:
            await self.tab.translate_missing()

            self.manager.translate.assert_called_with(
                self.tab.source_file,
                ["es"],
                agent_type="cursor"
            )
            self.mock_log.write.assert_any_call("[green]Translation complete.[/green]")
            mock_load.assert_called_once()

if __name__ == "__main__":
    unittest.main()
