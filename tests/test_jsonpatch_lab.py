import pytest
import json
import sys
from unittest.mock import patch, MagicMock
from io import StringIO
from pathlib import Path
from shared.jsonpatch_lab import JsonPatchLabManager, run_jsonpatch_lab_logic


def test_jsonpatch_manager_apply_strings():
    manager = JsonPatchLabManager()
    target = '{"foo": "bar"}'
    patch_str = '[{"op": "replace", "path": "/foo", "value": "baz"}]'
    result = manager.apply_patch(target, patch_str)
    assert result == {"foo": "baz"}


def test_jsonpatch_manager_apply_dicts():
    manager = JsonPatchLabManager()
    target = {"foo": "bar"}
    patch_data = [{"op": "add", "path": "/baz", "value": "qux"}]
    result = manager.apply_patch(target, patch_data)
    assert result == {"foo": "bar", "baz": "qux"}


def test_jsonpatch_manager_apply_invalid_patch():
    manager = JsonPatchLabManager()
    target = {"foo": "bar"}
    patch_data = [{"op": "invalid_op", "path": "/foo", "value": "baz"}]
    with pytest.raises(ValueError, match="Patch error"):
        manager.apply_patch(target, patch_data)


def test_jsonpatch_manager_diff_strings():
    manager = JsonPatchLabManager()
    source = '{"foo": "bar"}'
    target = '{"foo": "baz"}'
    result = manager.diff(source, target)
    assert len(result) == 1
    assert result[0] == {"op": "replace", "path": "/foo", "value": "baz"}

def test_jsonpatch_manager_diff_dicts():
    manager = JsonPatchLabManager()
    source = {"foo": "bar"}
    target = {"foo": "bar", "baz": "qux"}
    result = manager.diff(source, target)
    assert len(result) == 1
    assert result[0] == {"op": "add", "path": "/baz", "value": "qux"}

def test_run_logic_diff_missing_args(capsys):
    args = MagicMock(jsonpatch_action="diff", source=None, target="{}", tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 1
    assert "Error: --source is required." in capsys.readouterr().err

def test_run_logic_diff_valid_args(capsys):
    source = '{"a": 1}'
    target = '{"a": 2}'
    args = MagicMock(jsonpatch_action="diff", source=source, target=target, tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 0
    output = capsys.readouterr().out
    assert '"op": "replace"' in output
    assert '"value": 2' in output

def test_run_logic_diff_make_alias(capsys):
    source = '{"a": 1}'
    target = '{"a": 2}'
    args = MagicMock(jsonpatch_action="make", source=source, target=target, tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 0
    output = capsys.readouterr().out
    assert '"op": "replace"' in output
    assert '"value": 2' in output

def test_run_logic_missing_args(capsys):
    # Missing target
    args = MagicMock(jsonpatch_action="apply", action="apply", target=None, patch="[]", tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 1
    assert "Error: --target is required." in capsys.readouterr().err


def test_run_logic_valid_args(capsys):
    # Valid arguments string literals
    target = '{"a": 1}'
    patch_str = '[{"op": "replace", "path": "/a", "value": 2}]'
    args = MagicMock(jsonpatch_action="apply", action="apply", target=target, patch=patch_str, tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 0
    output = capsys.readouterr().out
    assert '"a": 2' in output


def test_run_logic_file_read(tmp_path, capsys):
    target_file = tmp_path / "target.json"
    patch_file = tmp_path / "patch.json"
    target_file.write_text('{"a": 1}')
    patch_file.write_text('[{"op": "replace", "path": "/a", "value": 2}]')

    args = MagicMock(jsonpatch_action="apply", action="apply", target=str(target_file), patch=str(patch_file), tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 0
    output = capsys.readouterr().out
    assert '"a": 2' in output


@pytest.mark.asyncio
async def test_tui_jsonpatch():
    pytest.importorskip("textual")
    from shared.tui_jsonpatch import JsonPatchLabTab
    from textual.app import App

    class DummyApp(App):
        def compose(self):
            yield JsonPatchLabTab()

    app = DummyApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        target_ta = app.query_one("#input-target")
        patch_ta = app.query_one("#input-patch")
        output_ta = app.query_one("#output-result")

        target_ta.load_text('{"a": 1}')
        patch_ta.load_text('[{"op": "replace", "path": "/a", "value": 2}]')

        await pilot.pause()
        assert '"a": 2' in output_ta.text

        # Test invalid patch handling
        patch_ta.load_text('[{"op": "invalid", "path": "/a", "value": 2}]')
        await pilot.pause()
        assert 'Error' in output_ta.text
