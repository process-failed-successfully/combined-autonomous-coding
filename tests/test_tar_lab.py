import pytest
from pathlib import Path
import argparse
from unittest.mock import patch, mock_open
import tarfile

from shared.tar_lab import TarManager, run_tar_lab_logic


@pytest.fixture
def tar_manager(tmp_path):
    return TarManager(project_dir=tmp_path)


def test_tar_manager_init(tmp_path):
    manager = TarManager(project_dir=tmp_path)
    assert manager.project_dir == tmp_path

    manager_default = TarManager()
    assert manager_default.project_dir == Path(".")


def test_tar_manager_create(tar_manager, tmp_path):
    input_file1 = tmp_path / "file1.txt"
    input_file1.write_text("hello")

    output_tar = tmp_path / "out.tar.gz"

    result = tar_manager.create([input_file1], output_tar, "gz")
    assert result == output_tar
    assert output_tar.exists()

def test_tui_tar_lab_app_unsupported_action(tmp_path):
    from shared.tui_tar import TarLabApp
    from textual.widgets import Button

    class MockButton(Button):
        def __init__(self, id):
            super().__init__()
            self.id = id

    app = TarLabApp()

    class MockEvent:
        button = MockButton("btn-unknown")

    app.on_button_pressed(MockEvent()) # Should just do nothing


def test_tar_manager_create_no_inputs(tar_manager, tmp_path):
    with pytest.raises(ValueError, match="No input paths provided"):
        tar_manager.create([], tmp_path / "out.tar.gz")


def test_tar_manager_create_unsupported_compression(tar_manager, tmp_path):
    input_file1 = tmp_path / "file1.txt"
    input_file1.write_text("hello")
    with pytest.raises(ValueError, match="Unsupported compression type"):
        tar_manager.create([input_file1], tmp_path / "out.tar.gz", "unsupported")

def test_tar_manager_create_empty_compression(tar_manager, tmp_path):
    input_file1 = tmp_path / "file1.txt"
    input_file1.write_text("hello")
    output_tar = tmp_path / "out.tar"

    result = tar_manager.create([input_file1], output_tar, "")
    assert result == output_tar
    assert output_tar.exists()

def test_tar_manager_create_missing_input(tar_manager, tmp_path, capsys):
    input_file1 = tmp_path / "file1.txt"
    missing_file = tmp_path / "missing.txt"
    input_file1.write_text("hello")

    output_tar = tmp_path / "out.tar.gz"

    result = tar_manager.create([input_file1, missing_file], output_tar, "gz")
    assert result == output_tar
    assert output_tar.exists()

    captured = capsys.readouterr()
    assert "Warning: Path not found" in captured.err


def test_tar_manager_extract(tar_manager, tmp_path):
    # First create a tar
    input_file1 = tmp_path / "file1.txt"
    input_file1.write_text("hello")
    archive_tar = tmp_path / "out.tar.gz"
    tar_manager.create([input_file1], archive_tar, "gz")

    output_dir = tmp_path / "extracted"
    result = tar_manager.extract(archive_tar, output_dir)

    assert result == output_dir
    assert (output_dir / "file1.txt").exists()
    assert (output_dir / "file1.txt").read_text() == "hello"


def test_tar_manager_extract_missing_archive(tar_manager, tmp_path):
    missing_archive = tmp_path / "missing.tar.gz"
    with pytest.raises(FileNotFoundError, match="Archive not found"):
        tar_manager.extract(missing_archive, tmp_path / "out")


def test_tar_manager_extract_not_file(tar_manager, tmp_path):
    dir_archive = tmp_path / "dir_archive"
    dir_archive.mkdir()
    with pytest.raises(ValueError, match="Not a file"):
        tar_manager.extract(dir_archive, tmp_path / "out")


def test_tar_manager_list(tar_manager, tmp_path):
    input_file1 = tmp_path / "file1.txt"
    input_file1.write_text("hello")
    archive_tar = tmp_path / "out.tar.gz"
    tar_manager.create([input_file1], archive_tar, "gz")

    result = tar_manager.list(archive_tar)
    assert result == ["file1.txt"]

def test_tar_manager_list_missing_archive(tar_manager, tmp_path):
    missing_archive = tmp_path / "missing.tar.gz"
    with pytest.raises(FileNotFoundError, match="Archive not found"):
        tar_manager.list(missing_archive)

def test_tar_manager_list_not_file(tar_manager, tmp_path):
    dir_archive = tmp_path / "dir_archive"
    dir_archive.mkdir()
    with pytest.raises(ValueError, match="Not a file"):
        tar_manager.list(dir_archive)


# CLI Logic Tests
@patch("shared.tar_lab.TarManager.create")
def test_cli_create(mock_create, tmp_path, capsys):
    mock_create.return_value = tmp_path / "archive.tar.gz"

    args = argparse.Namespace(
        action="create",
        inputs=[str(tmp_path / "file1.txt")],
        output=str(tmp_path / "archive.tar.gz"),
        compression="gz"
    )

    with pytest.raises(SystemExit) as e:
        run_tar_lab_logic(args)

    assert e.value.code == 0
    mock_create.assert_called_once()

    captured = capsys.readouterr()
    assert "Archive created at" in captured.out

def test_cli_create_none_compression(tmp_path, capsys):
    args = argparse.Namespace(
        action="create",
        inputs=[str(tmp_path / "file1.txt")],
        output=str(tmp_path / "archive.tar"),
        compression="none"
    )
    with patch("shared.tar_lab.TarManager.create") as mock_create:
        mock_create.return_value = tmp_path / "archive.tar"
        with pytest.raises(SystemExit) as e:
            run_tar_lab_logic(args)
        assert e.value.code == 0
        mock_create.assert_called_once()
        args, kwargs = mock_create.call_args
        assert args[2] == "" # compression string

def test_cli_create_no_inputs(capsys):
    args = argparse.Namespace(
        action="create",
        inputs=[],
        output="out.tar.gz",
        compression="gz"
    )
    with pytest.raises(SystemExit) as e:
        run_tar_lab_logic(args)
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Input paths are required" in captured.err

@patch("shared.tar_lab.TarManager.extract")
def test_cli_extract(mock_extract, tmp_path, capsys):
    mock_extract.return_value = tmp_path / "outdir"

    args = argparse.Namespace(
        action="extract",
        input=str(tmp_path / "archive.tar.gz"),
        output=str(tmp_path / "outdir")
    )

    with pytest.raises(SystemExit) as e:
        run_tar_lab_logic(args)

    assert e.value.code == 0
    mock_extract.assert_called_once()

    captured = capsys.readouterr()
    assert "Archive extracted to" in captured.out

def test_cli_extract_no_input(capsys):
    args = argparse.Namespace(
        action="extract",
        input=None,
        output="outdir"
    )
    with pytest.raises(SystemExit) as e:
        run_tar_lab_logic(args)
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Input archive is required" in captured.err

@patch("shared.tar_lab.TarManager.list")
def test_cli_list(mock_list, tmp_path, capsys):
    mock_list.return_value = ["file1.txt", "dir1/file2.txt"]

    args = argparse.Namespace(
        action="list",
        input=str(tmp_path / "archive.tar.gz")
    )

    with pytest.raises(SystemExit) as e:
        run_tar_lab_logic(args)

    assert e.value.code == 0
    mock_list.assert_called_once()

    captured = capsys.readouterr()
    assert "file1.txt" in captured.out
    assert "dir1/file2.txt" in captured.out

def test_cli_list_no_input(capsys):
    args = argparse.Namespace(
        action="list",
        input=None
    )
    with pytest.raises(SystemExit) as e:
        run_tar_lab_logic(args)
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Input archive is required" in captured.err

def test_cli_exception(capsys):
    args = argparse.Namespace(
        action="list",
        input="somefile.tar.gz"
    )
    with patch("shared.tar_lab.TarManager.list", side_effect=ValueError("Some error")):
        with pytest.raises(SystemExit) as e:
            run_tar_lab_logic(args)
        assert e.value.code == 1
        captured = capsys.readouterr()
        assert "Error: Some error" in captured.err

def test_run_tar_lab_no_action(capsys):
    from main import run_tar_lab
    args = argparse.Namespace(action=None)
    with pytest.raises(SystemExit) as e:
        run_tar_lab(args)
    assert e.value.code == 1
    captured = capsys.readouterr()
    assert "Error: No action specified for tar-lab" in captured.err


# TUI Tests
pytest.importorskip("textual")

@pytest.mark.asyncio
async def test_tui_tar_lab_app_create():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static, Select

    app = TarLabApp()
    async with app.run_test() as pilot:
        inputs = app.query_one("#create-inputs", Input)
        inputs.value = "file1.txt"

        output = app.query_one("#create-output", Input)
        output.value = "out.tar.gz"

        compression = app.query_one("#create-compression", Select)
        compression.value = "gz"

        with patch("shared.tar_lab.TarManager.create") as mock_create:
            mock_create.return_value = Path("out.tar.gz")
            await pilot.click("#btn-create")
            mock_create.assert_called_once()

        status = app.query_one("#create-status", Static)
        assert "Success" in str(status.renderable)


@pytest.mark.asyncio
async def test_tui_tar_lab_app_create_no_inputs():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static

    app = TarLabApp()
    async with app.run_test() as pilot:
        inputs = app.query_one("#create-inputs", Input)
        inputs.value = ""

        await pilot.click("#btn-create")

        status = app.query_one("#create-status", Static)
        assert "Error: Please provide input paths" in str(status.renderable)

@pytest.mark.asyncio
async def test_tui_tar_lab_app_create_none_compression():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static, Select

    app = TarLabApp()
    async with app.run_test() as pilot:
        inputs = app.query_one("#create-inputs", Input)
        inputs.value = "file1.txt"

        output = app.query_one("#create-output", Input)
        output.value = "out.tar"

        compression = app.query_one("#create-compression", Select)
        compression.value = "none"

        with patch("shared.tar_lab.TarManager.create") as mock_create:
            mock_create.return_value = Path("out.tar")
            await pilot.click("#btn-create")
            mock_create.assert_called_once()
            args, kwargs = mock_create.call_args
            assert args[2] == ""

        status = app.query_one("#create-status", Static)
        assert "Success" in str(status.renderable)

@pytest.mark.asyncio
async def test_tui_tar_lab_app_create_exception():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static, Select

    app = TarLabApp()
    async with app.run_test() as pilot:
        inputs = app.query_one("#create-inputs", Input)
        inputs.value = "file1.txt"

        with patch("shared.tar_lab.TarManager.create", side_effect=Exception("Failed to create")):
            await pilot.click("#btn-create")

        status = app.query_one("#create-status", Static)
        assert "Error:" in str(status.renderable)
        assert "Failed to create" in str(status.renderable)


@pytest.mark.asyncio
async def test_tui_tar_lab_app_extract():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static

    app = TarLabApp()
    async with app.run_test() as pilot:
        input_tar = app.query_one("#extract-input", Input)
        input_tar.value = "out.tar.gz"

        output_dir = app.query_one("#extract-output", Input)
        output_dir.value = "outdir"

        with patch("shared.tar_lab.TarManager.extract") as mock_extract:
            mock_extract.return_value = Path("outdir")
            await pilot.click("#btn-extract")
            mock_extract.assert_called_once()

        status = app.query_one("#extract-status", Static)
        assert "Success" in str(status.renderable)

@pytest.mark.asyncio
async def test_tui_tar_lab_app_extract_no_input():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static

    app = TarLabApp()
    async with app.run_test() as pilot:
        input_tar = app.query_one("#extract-input", Input)
        input_tar.value = ""

        await pilot.click("#btn-extract")

        status = app.query_one("#extract-status", Static)
        assert "Error: Please provide an input archive" in str(status.renderable)


@pytest.mark.asyncio
async def test_tui_tar_lab_app_extract_exception():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static

    app = TarLabApp()
    async with app.run_test() as pilot:
        input_tar = app.query_one("#extract-input", Input)
        input_tar.value = "out.tar.gz"

        with patch("shared.tar_lab.TarManager.extract", side_effect=Exception("Extraction failed")):
            await pilot.click("#btn-extract")

        status = app.query_one("#extract-status", Static)
        assert "Error:" in str(status.renderable)
        assert "Extraction failed" in str(status.renderable)


@pytest.mark.asyncio
async def test_tui_tar_lab_app_list():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static

    app = TarLabApp()
    async with app.run_test() as pilot:
        input_tar = app.query_one("#list-input", Input)
        input_tar.value = "out.tar.gz"

        with patch("shared.tar_lab.TarManager.list") as mock_list:
            mock_list.return_value = ["file1.txt"]
            await pilot.click("#btn-list")
            mock_list.assert_called_once()

        status = app.query_one("#list-status", Static)
        assert "file1.txt" in str(status.renderable)

@pytest.mark.asyncio
async def test_tui_tar_lab_app_list_no_input():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static

    app = TarLabApp()
    async with app.run_test() as pilot:
        input_tar = app.query_one("#list-input", Input)
        input_tar.value = ""

        await pilot.click("#btn-list")

        status = app.query_one("#list-status", Static)
        assert "Error: Please provide an input archive" in str(status.renderable)

@pytest.mark.asyncio
async def test_tui_tar_lab_app_list_exception():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input, Button, Static

    app = TarLabApp()
    async with app.run_test() as pilot:
        input_tar = app.query_one("#list-input", Input)
        input_tar.value = "out.tar.gz"

        with patch("shared.tar_lab.TarManager.list", side_effect=Exception("Failed to list")):
            await pilot.click("#btn-list")

        status = app.query_one("#list-status", Static)
        assert "Error:" in str(status.renderable)
        assert "Failed to list" in str(status.renderable)

@pytest.mark.asyncio
async def test_tui_tar_lab_app_focus():
    from shared.tui_tar import TarLabApp
    from textual.widgets import Input

    app = TarLabApp()
    async with app.run_test() as pilot:
        app.action_focus_create()
        await pilot.pause()
        assert app.query_one("#create-inputs", Input).has_focus

        app.action_focus_extract()
        await pilot.pause()
        assert app.query_one("#extract-input", Input).has_focus

        app.action_focus_list()
        await pilot.pause()
        assert app.query_one("#list-input", Input).has_focus
