import pytest
import io
import argparse
from pathlib import Path
from unittest.mock import patch

from shared.toml2py_lab import Toml2PyManager, run_toml2py_lab_logic

def test_flat_dataclass():
    manager = Toml2PyManager()
    toml_str = 'name = "test"\nage = 30\nis_active = true'
    result = manager.generate(toml_str, framework="dataclass", root_name="User")

    assert "@dataclass" in result
    assert "class User:" in result
    assert "name: Optional[str] = None" in result
    assert "age: Optional[int] = None" in result
    assert "is_active: Optional[bool] = None" in result

def test_flat_pydantic():
    manager = Toml2PyManager()
    toml_str = "id = 123\nbalance = 99.99"
    result = manager.generate(toml_str, framework="pydantic", root_name="Account")

    assert "class Account(BaseModel):" in result
    assert "id: Optional[int] = None" in result
    assert "balance: Optional[float] = None" in result

def test_nested_objects():
    manager = Toml2PyManager()
    toml_str = '[user]\nname = "Alice"\n\n[status]\nstate = "ok"'
    result = manager.generate(toml_str, framework="dataclass", root_name="Response")

    assert "class User:" in result
    assert "name: Optional[str] = None" in result
    assert "class Response:" in result
    assert "user: Optional[User] = None" in result

    # Check order: nested class should appear before root class
    assert result.index("class User:") < result.index("class Response:")

def test_lists():
    manager = Toml2PyManager()
    toml_str = 'tags = ["a", "b"]\nscores = [1, 2]'
    result = manager.generate(toml_str)

    assert "tags: Optional[List[str]] = None" in result
    assert "scores: Optional[List[int]] = None" in result

def test_nested_lists():
    manager = Toml2PyManager()
    toml_str = '[[items]]\nid = 1\nname = "item1"\n[[items]]\nid = 2\nname = "item2"'
    result = manager.generate(toml_str, framework="dataclass", root_name="Cart")

    assert "class ItemsItem:" in result
    assert "id: Optional[int] = None" in result
    assert "name: Optional[str] = None" in result
    assert "class Cart:" in result
    assert "items: Optional[List[ItemsItem]] = None" in result

def test_invalid_toml():
    manager = Toml2PyManager()
    with pytest.raises(ValueError):
        manager.generate("invalid: toml: :")

def test_sanitize_identifier():
    manager = Toml2PyManager()
    toml_str = '"1st_item" = "value"\nclass = "keyword"\n"a-b" = 1'
    result = manager.generate(toml_str)

    assert "_1st_item: Optional[str] = None" in result
    assert "class_: Optional[str] = None" in result
    assert "a_b: Optional[int] = None" in result

@patch('sys.stdout', new_callable=io.StringIO)
def test_cli_logic_text(mock_stdout):
    args = argparse.Namespace(
        text='name = "Charlie"\nage = 40',
        file=None,
        output=None,
        framework="dataclass",
        name="TestClass",
        tui=False
    )
    result = run_toml2py_lab_logic(args)
    assert result is True

    output = mock_stdout.getvalue()
    assert "class TestClass:" in output
    assert "name: Optional[str] = None" in output

def test_cli_logic_file(tmp_path):
    toml_file = tmp_path / "input.toml"
    toml_file.write_text('name = "David"\n', encoding="utf-8")

    py_file = tmp_path / "output.py"

    args = argparse.Namespace(
        text=None,
        file=str(toml_file),
        output=str(py_file),
        framework="pydantic",
        name="Person",
        tui=False
    )

    with patch('sys.stdout', new_callable=io.StringIO):
        result = run_toml2py_lab_logic(args)
        assert result is True

    assert py_file.exists()
    assert "class Person(BaseModel):" in py_file.read_text()
    assert "name: Optional[str] = None" in py_file.read_text()

@patch('sys.stderr', new_callable=io.StringIO)
def test_cli_logic_missing_input(mock_stderr):
    args = argparse.Namespace(
        text=None,
        file=None,
        output=None,
        framework="dataclass",
        name="RootModel",
        tui=False
    )
    with patch('sys.stdin.isatty', return_value=True):
        result = run_toml2py_lab_logic(args)
        assert result is False

    assert "No TOML input provided" in mock_stderr.getvalue()

@pytest.mark.asyncio
async def test_tui_toml2py():
    """Test the Textual TUI interface."""
    pytest.importorskip("textual")
    from textual.app import App, ComposeResult
    from shared.tui_toml2py import Toml2PyLabTab
    from textual.widgets import TextArea, Select, Input
    from textual.widgets import TabbedContent

    class MockApp(App):
        def compose(self) -> ComposeResult:
            with TabbedContent():
                yield Toml2PyLabTab()

    app = MockApp()
    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.pause(0.1)

        input_ta = app.query_one("#editor-toml2py-in", TextArea)
        output_ta = app.query_one("#editor-toml2py-out", TextArea)
        name_input = app.query_one("#input-toml2py-root", Input)
        fw_select = app.query_one("#select-toml2py-framework", Select)

        # Test valid conversion
        toml_data = '[user]\nid = 123\nrole = "admin"'
        input_ta.load_text(toml_data)

        # Test change input
        name_input.value = "MyApp"

        from textual.widgets import Button
        btn = app.query_one("#btn-generate-toml2py", Button)
        await app.query_one("Toml2PyLabTab").on_button_pressed(Button.Pressed(btn))
        await pilot.pause(0.1)

        assert "class User:" in output_ta.text
        assert "class MyApp:" in output_ta.text
        assert "user: Optional[User] = None" in output_ta.text
