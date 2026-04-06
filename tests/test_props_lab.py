import pytest
import argparse
import sys
import io
import json
from unittest.mock import patch, MagicMock
from pathlib import Path
from shared.props_lab import PropsLabManager, run_props_lab_logic

class TestPropsLabManager:
    def setup_method(self):
        self.manager = PropsLabManager()

    def test_props_to_dict(self):
        props_content = """
        # This is a comment
        key1=value1
        key2:value2
        key3=value=with=equals
        """
        result = self.manager.props_to_dict(props_content)
        assert result == {"key1": "value1", "key2": "value2", "key3": "value=with=equals"}

    def test_dict_to_props(self):
        data = {"key1": "value1", "key2": "value2", "nested": {"key3": "value3"}}
        result = self.manager.dict_to_props(data)
        assert "key1=value1" in result
        assert "key2=value2" in result
        assert "nested.key3=value3" in result

    def test_props2json(self):
        props_content = "key1=value1\nkey2=value2"
        result = self.manager.props2json(props_content)
        data = json.loads(result)
        assert data == {"key1": "value1", "key2": "value2"}

    def test_json2props(self):
        json_content = '{"key1": "value1", "key2": "value2"}'
        result = self.manager.json2props(json_content)
        assert "key1=value1" in result
        assert "key2=value2" in result

    def test_props2yaml(self):
        props_content = "key1=value1\nkey2=value2"
        result = self.manager.props2yaml(props_content)
        assert "key1: value1" in result
        assert "key2: value2" in result

    def test_yaml2props(self):
        yaml_content = "key1: value1\nkey2: value2"
        result = self.manager.yaml2props(yaml_content)
        assert "key1=value1" in result
        assert "key2=value2" in result

@patch('sys.stdout', new_callable=io.StringIO)
def test_run_props_lab_logic_text(mock_stdout):
    args = argparse.Namespace(
        action="props2json",
        text="key=value",
        file=None,
        output=None,
        tui=False
    )
    assert run_props_lab_logic(args) is True
    output = mock_stdout.getvalue()
    data = json.loads(output)
    assert data == {"key": "value"}

@patch('sys.stderr', new_callable=io.StringIO)
def test_run_props_lab_logic_no_input(mock_stderr):
    args = argparse.Namespace(
        action="props2json",
        text=None,
        file=None,
        output=None,
        tui=False
    )
    assert run_props_lab_logic(args) is False
    assert "Either --file or --text must be provided" in mock_stderr.getvalue()

@pytest.mark.asyncio
async def test_tui_props_lab():
    pytest.importorskip("textual")
    from textual.app import App
    from shared.tui_props import PropsLabTab

    class TestApp(App):
        def compose(self):
            yield PropsLabTab()

    app = TestApp()
    async with app.run_test() as pilot:
        # Wait for app to be ready
        await pilot.pause()

        # Test input and output interactions
        input_widget = app.query_one("#props-input")
        input_widget.text = "key=value"

        btn = app.query_one("#btn-convert")
        await pilot.click("#btn-convert")
        await pilot.pause()

        output_widget = app.query_one("#props-output")
        data = json.loads(output_widget.text)
        assert data == {"key": "value"}
