import sys
import unittest
from unittest.mock import MagicMock
from pathlib import Path

# Add shared to path
sys.path.append(str(Path(__file__).parent.parent))  # noqa: E402

from shared.tui_pypi import PypiLabTab  # noqa: E402
from textual.widgets import Input, RichLog  # noqa: E402


class TestPypiLabTab(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tab = PypiLabTab()
        self.tab.pypi_manager = MagicMock()
        self.tab.query_one = MagicMock()
        self.mock_package_input = MagicMock(spec=Input)
        self.mock_version_input = MagicMock(spec=Input)
        self.mock_log = MagicMock(spec=RichLog)

        def query_side_effect(selector, type=None):
            if "package" in selector:
                return self.mock_package_input
            elif "version" in selector:
                return self.mock_version_input
            elif "log" in selector:
                return self.mock_log
            return MagicMock()

        self.tab.query_one.side_effect = query_side_effect

        # In Textual, app is a property. We can mock the notify method another way or avoid it.
        # Actually we can just mock notify directly on the tab since TUI widgets sometimes have notify,
        # but in textual it's usually `self.notify`. Our code uses `self.app.notify`.
        # To avoid property errors, we can mock out the `hasattr` or patch `app` at class level,
        # but the easiest is just mock `notify` on the tab if we switch to `self.notify` in the widget.
        # Let's patch `PypiLabTab.app` property for tests.
        self.app_mock = MagicMock()
        self.original_app_property = getattr(type(self.tab), 'app', None)
        type(self.tab).app = property(lambda self: getattr(self, "_mock_app"))
        self.tab._mock_app = self.app_mock

    def tearDown(self):
        # Restore the original `app` property to avoid test pollution
        if self.original_app_property:
            type(self.tab).app = self.original_app_property
        else:
            del type(self.tab).app

    async def test_run_info_success(self):
        self.mock_package_input.value = "requests"
        self.tab.pypi_manager.get_info = MagicMock(return_value={
            "name": "requests",
            "version": "2.31.0",
            "summary": "Python HTTP for Humans.",
            "author": "Kenneth Reitz",
            "license": "Apache 2.0",
            "home_page": "https://requests.readthedocs.io",
            "package_url": "https://pypi.org/project/requests/"
        })

        await self.tab.run_info()

        self.tab.pypi_manager.get_info.assert_called_with("requests")
        self.mock_log.write.assert_any_call("[bold]Name:[/bold] requests")
        self.mock_log.write.assert_any_call("[bold]Version:[/bold] 2.31.0")

    async def test_run_info_error(self):
        self.mock_package_input.value = "not_found_pkg"
        self.tab.pypi_manager.get_info = MagicMock(side_effect=ValueError("Package not found"))

        await self.tab.run_info()

        self.mock_log.write.assert_any_call("[bold red]Error:[/bold red] Package not found")
        self.app_mock.notify.assert_called_with("Package not found", severity="error")

    async def test_run_releases_success(self):
        self.mock_package_input.value = "requests"
        self.tab.pypi_manager.get_releases = MagicMock(return_value={
            "2.31.0": [{"upload_time": "2023-05-22T00:00:00"}],
            "2.30.0": [{"upload_time": "2023-05-03T00:00:00"}]
        })

        await self.tab.run_releases()

        self.tab.pypi_manager.get_releases.assert_called_with("requests")
        self.mock_log.write.assert_any_call("  2023-05-22 : 2.31.0")
        self.mock_log.write.assert_any_call("  2023-05-03 : 2.30.0")

    async def test_run_deps_success(self):
        self.mock_package_input.value = "requests"
        self.mock_version_input.value = ""
        self.tab.pypi_manager.get_dependencies = MagicMock(return_value=[
            "charset-normalizer (<4,>=2)",
            "idna (<4,>=2.5)"
        ])

        await self.tab.run_deps()

        self.tab.pypi_manager.get_dependencies.assert_called_with("requests", None)
        self.mock_log.write.assert_any_call("  - charset-normalizer (<4,>=2)")
        self.mock_log.write.assert_any_call("  - idna (<4,>=2.5)")

    async def test_run_files_success(self):
        self.mock_package_input.value = "requests"
        self.mock_version_input.value = "2.31.0"
        self.tab.pypi_manager.get_files = MagicMock(return_value=[
            {
                "filename": "requests-2.31.0-py3-none-any.whl",
                "packagetype": "bdist_wheel",
                "size": 62000,
                "url": "https://example.com/requests.whl",
                "digests": {"sha256": "abcdef"}
            }
        ])

        await self.tab.run_files()

        self.tab.pypi_manager.get_files.assert_called_with("requests", "2.31.0")
        self.mock_log.write.assert_any_call("    URL: https://example.com/requests.whl")
        self.mock_log.write.assert_any_call("    SHA256: abcdef")

    async def test_empty_input(self):
        self.mock_package_input.value = ""
        await self.tab.run_info()
        self.mock_log.write.assert_called_with("[red]Please enter a package name.[/red]")


if __name__ == "__main__":
    unittest.main()
