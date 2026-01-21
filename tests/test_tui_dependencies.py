
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from shared.tui import DependenciesTab

@pytest.fixture
def mock_project_dir(tmp_path):
    return tmp_path

@pytest.fixture
def mock_analyzer():
    analyzer = MagicMock()
    analyzer.scan = MagicMock(return_value={
        "python": [
            {
                "source": "requirements.txt",
                "dependencies": [
                    {"name": "requests", "version": "2.25.1", "type": "prod"}
                ]
            }
        ]
    })
    analyzer.check_updates = MagicMock(return_value={
        "python": [
            {
                "source": "requirements.txt",
                "dependencies": [
                    {"name": "requests", "version": "2.25.1", "latest": "2.28.0", "outdated": True, "type": "prod"}
                ]
            }
        ]
    })
    return analyzer

@pytest.fixture
def mock_updater():
    updater = MagicMock()
    updater.update_dependency = MagicMock(return_value=True)
    return updater

@pytest.mark.asyncio
async def test_dependencies_tab_initialization(mock_project_dir):
    """Test that the tab initializes and scans dependencies on mount."""
    with patch("shared.tui.DependencyAnalyzer") as MockAnalyzer:
        with patch("shared.tui.DependencyUpdater") as MockUpdater:
            tab = DependenciesTab(mock_project_dir)

            # Verify analyzers created
            MockAnalyzer.assert_called_with(mock_project_dir)
            MockUpdater.assert_called_with(mock_project_dir)

@pytest.mark.asyncio
async def test_scan_dependencies(mock_project_dir, mock_analyzer):
    """Test scanning logic."""
    with patch("shared.tui.DependencyAnalyzer", return_value=mock_analyzer):
        tab = DependenciesTab(mock_project_dir)
        tab.query_one = MagicMock() # Mock UI query
        tab._refresh_table = MagicMock()
        tab.notify = MagicMock()

        await tab.scan_dependencies()

        assert tab.current_data == mock_analyzer.scan.return_value
        tab._refresh_table.assert_called_once()
        tab.notify.assert_any_call("Scan complete.")

@pytest.mark.asyncio
async def test_check_updates(mock_project_dir, mock_analyzer):
    """Test check updates logic."""
    with patch("shared.tui.DependencyAnalyzer", return_value=mock_analyzer):
        tab = DependenciesTab(mock_project_dir)
        tab.query_one = MagicMock()
        tab._refresh_table = MagicMock()
        tab.notify = MagicMock()

        # Pre-set data
        input_data = mock_analyzer.scan.return_value
        tab.current_data = input_data

        await tab.check_updates()

        mock_analyzer.check_updates.assert_called_with(input_data, verbose=False)
        assert tab.current_data == mock_analyzer.check_updates.return_value
        tab._refresh_table.assert_called_once()

@pytest.mark.asyncio
async def test_update_selected(mock_project_dir, mock_analyzer, mock_updater):
    """Test update selected logic."""
    with patch("shared.tui.DependencyAnalyzer", return_value=mock_analyzer), \
         patch("shared.tui.DependencyUpdater", return_value=mock_updater), \
         patch("textual.widgets.DataTable") as MockDataTable:

        tab = DependenciesTab(mock_project_dir)

        # Mock UI elements
        mock_table = MagicMock()
        mock_table.cursor_row = 0
        mock_table.coordinate_to_cell_key.return_value.row_key = "row1"

        tab.query_one = MagicMock(return_value=mock_table)
        tab.notify = MagicMock()
        tab.scan_dependencies = AsyncMock() # avoid real scan call

        # Setup row map simulating a selected outdated dependency
        file_path = mock_project_dir / "requirements.txt"
        tab.row_map = {
            "row1": {
                "file_path": file_path,
                "name": "requests",
                "latest": "2.28.0",
                "type": "prod",
                "outdated": True
            }
        }

        await tab.update_selected()

        mock_updater.update_dependency.assert_called_with(
            file_path, "requests", "2.28.0", "prod"
        )
        tab.notify.assert_any_call("Successfully updated requests.")
        tab.scan_dependencies.assert_awaited_once()
