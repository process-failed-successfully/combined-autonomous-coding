import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

pytest.importorskip("textual")
from shared.tui import AgentTUI
from shared.database import init_db

@pytest.fixture
def app(tmp_path):
    init_db(tmp_path / ".agent_db.sqlite")

    # Create some dummy files in the tmp_path
    (tmp_path / "test1.txt").write_text("hello")
    (tmp_path / "test_dir").mkdir()

    app = AgentTUI(project_dir=tmp_path, start_tab="tab-fs")
    return app

@pytest.mark.asyncio
async def test_fs_tab_find(app, tmp_path):
    with patch('shared.tui_fs.FsLabManager.find', return_value=[tmp_path / "test1.txt"]) as mock_find:
        async with app.run_test(size=(200, 100)) as pilot:
            await pilot.pause(2)

            # Switch to tab
            app.query_one("#main-tabs").active = "tab-fs"
            await pilot.pause(2)

            # Manually trigger button press
            btn = app.query_one("#btn-fs-find")
            btn.press()
            await pilot.pause(2)

            mock_find.assert_called_once()

            log = app.query_one("#fslab-log")
            lines = str(list(log.lines))
            assert "Finding files" in lines
            assert "test1.txt" in lines

@pytest.mark.asyncio
async def test_fs_tab_clean(app, tmp_path):
    mock_stats = {"files": 2, "dirs": 1, "space": 1024}
    with patch('shared.tui_fs.FsLabManager.clean', return_value=mock_stats) as mock_clean:
        async with app.run_test(size=(200, 100)) as pilot:
            await pilot.pause(2)

            # Switch to tab
            app.query_one("#main-tabs").active = "tab-fs"
            await pilot.pause(2)

            # Manually trigger button press
            btn = app.query_one("#btn-fs-clean")
            btn.press()
            await pilot.pause(2)

            mock_clean.assert_called_once()

            log = app.query_one("#fslab-log")
            # Textual RichLog uses Rich segments for display, which split strings.
            # Instead of looking for exact strings, we will inspect the rendered plain text
            lines = "\n".join([line.text for line in log.lines])
            assert "Cleaning" in lines
            assert "Files: 2" in lines

@pytest.mark.asyncio
async def test_fs_tab_dedup(app, tmp_path):
    mock_duplicates = {"hash123": [tmp_path / "test1.txt", tmp_path / "test2.txt"]}
    with patch('shared.tui_fs.FsLabManager.dedup', return_value=mock_duplicates) as mock_dedup:
        async with app.run_test(size=(200, 100)) as pilot:
            await pilot.pause(2)

            # Switch to tab
            app.query_one("#main-tabs").active = "tab-fs"
            await pilot.pause(2)

            # Manually trigger button press
            btn = app.query_one("#btn-fs-dedup")
            btn.press()
            await pilot.pause(2)

            mock_dedup.assert_called_once()

            log = app.query_one("#fslab-log")
            lines = str(list(log.lines))
            assert "Deduplicating" in lines
            assert "Duplicate Group" in lines

@pytest.mark.asyncio
async def test_fs_tab_select_file_enables_buttons(app, tmp_path):
    async with app.run_test() as pilot:
        await pilot.pause(2)

        # Switch to tab
        app.query_one("#main-tabs").active = "tab-fs"
        await pilot.pause(2)

        # We need to manually set the selected path or directly trigger the event in tests
        # since DirectoryTree manipulation can be tricky
        tab = app.query_one("FsLabTab")
        tab.selected_path = tmp_path / "test1.txt"
        tab._enable_path_buttons()
        await pilot.pause(1)

        info_btn = app.query_one("#btn-fs-info")
        shred_btn = app.query_one("#btn-fs-shred")
        usage_btn = app.query_one("#btn-fs-usage")

        assert not info_btn.disabled
        assert not shred_btn.disabled
        assert not usage_btn.disabled

@pytest.mark.asyncio
async def test_fs_tab_shred(app, tmp_path):
    with patch('shared.tui_fs.FsLabManager.shred', return_value=True) as mock_shred:
        async with app.run_test(size=(200, 100)) as pilot:
            await pilot.pause(2)

            # Switch to tab
            app.query_one("#main-tabs").active = "tab-fs"
            await pilot.pause(2)

            # Set checkbox to disable dry run
            chk = app.query_one("#chk-fs-dry-run")
            chk.value = False

            # Select file via manual assignment for stability
            tab = app.query_one("FsLabTab")
            tab.selected_path = tmp_path / "test1.txt"
            tab._enable_path_buttons()
            await pilot.pause(1)

            # Manually trigger button press
            btn = app.query_one("#btn-fs-shred")
            btn.press()
            await pilot.pause(2)

            mock_shred.assert_called_once()

            log = app.query_one("#fslab-log")
            lines = str(list(log.lines))
            assert "Successfully shredded" in lines
