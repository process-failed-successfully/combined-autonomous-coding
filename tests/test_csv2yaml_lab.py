import pytest
import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

from shared.csv2yaml_lab import Csv2YamlManager, run_csv2yaml_lab_logic


def test_convert_valid_csv():
    manager = Csv2YamlManager()
    csv_input = "name,age\nAlice,30\nBob,25"
    result = manager.convert(csv_input)
    assert "- name: Alice\n  age: '30'" in result
    assert "- name: Bob\n  age: '25'" in result


def test_convert_empty_csv():
    manager = Csv2YamlManager()
    result = manager.convert("")
    assert result.strip() == "[]"


def test_process_file(tmp_path):
    manager = Csv2YamlManager()
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.yaml"

    input_file.write_text("fruit,color\napple,red\nbanana,yellow")

    success = manager.process_file(input_file, output_file)
    assert success is True
    assert output_file.exists()
    yaml_content = output_file.read_text()
    assert "- fruit: apple" in yaml_content
    assert "color: red" in yaml_content


def test_process_file_missing():
    manager = Csv2YamlManager()
    success = manager.process_file(Path("nonexistent_file.csv"))
    assert success is False


@patch("sys.stdout")
def test_run_logic_text(mock_stdout):
    args = argparse.Namespace(tui=False, file=None, text="a,b\n1,2", output=None, delimiter=",")
    success = run_csv2yaml_lab_logic(args)
    assert success is True


def test_run_logic_no_args():
    args = argparse.Namespace(tui=False, file=None, text=None)
    success = run_csv2yaml_lab_logic(args)
    assert success is False


def test_tui_component():
    pytest.importorskip("textual")
    from textual.app import App
    from shared.tui_csv2yaml import Csv2YamlTab

    class TestApp(App):
        def compose(self):
            yield Csv2YamlTab()

    async def run_tui_test():
        app = TestApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            tab = app.query_one(Csv2YamlTab)

            input_area = tab.query_one("#csv2yaml_input")
            input_area.text = "name,val\ntest,123"

            # Click convert
            await pilot.click("#btn_convert")
            await pilot.pause()

            output_area = tab.query_one("#csv2yaml_output")
            assert "- name: test" in output_area.text

            # Click clear
            await pilot.click("#btn_clear")
            await pilot.pause()

            assert input_area.text == ""
            assert output_area.text == ""

    import asyncio
    asyncio.run(run_tui_test())
