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


def test_run_logic_missing_args(capsys):
    # Missing target
    args = MagicMock(action="apply", target=None, patch="[]", tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 1
    assert "Error: --target is required." in capsys.readouterr().err


def test_run_logic_valid_args(capsys):
    # Valid arguments string literals
    target = '{"a": 1}'
    patch_str = '[{"op": "replace", "path": "/a", "value": 2}]'
    args = MagicMock(action="apply", target=target, patch=patch_str, tui=False)
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

    args = MagicMock(action="apply", target=str(target_file), patch=str(patch_file), tui=False)
    with pytest.raises(SystemExit) as e:
        run_jsonpatch_lab_logic(args)
    assert e.value.code == 0
    output = capsys.readouterr().out
    assert '"a": 2' in output


@pytest.mark.asyncio
async def test_tui_jsonpatch():
    pytest.importorskip("textual")
    from shared.tui_jsonpatch import JsonPatchLabTab
    from shared.tui import AgentTUI

    from shared.database import init_db
    import tempfile

    # Initialize a temporary DB to avoid "no such table" errors in other tabs
    with tempfile.NamedTemporaryFile() as tmp:
        init_db(tmp.name)
        app = AgentTUI(project_dir=Path("."), start_tab="tab-jsonpatch")
        async with app.run_test() as pilot:
            # We don't have to navigate to the tab if we start with it, but just in case
            await pilot.pause()

            # The TUI component should be JsonPatchLabTab
            # Find text areas
            target_ta = app.query_one("#input-target")
            patch_ta = app.query_one("#input-patch")
            output_ta = app.query_one("#output-result")

            target_ta.load_text('{"a": 1}')
            patch_ta.load_text('[{"op": "replace", "path": "/a", "value": 2}]')

            # Give textual time to react to the change events
            await pilot.pause()

            # Output should now contain the valid result
            assert '"a": 2' in output_ta.text

            # Test invalid patch handling
            patch_ta.load_text('[{"op": "invalid", "path": "/a", "value": 2}]')
            await pilot.pause()
            assert 'Error' in output_ta.text
